"""Performance tests for the EKS Migration Assessor."""
from __future__ import annotations

import socket

# Add src to path
import sys
import time
import tracemalloc
from pathlib import Path
from statistics import median
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from assessor.service import analyze


@pytest.mark.perf
class TestPerformance:
    """Performance measurements."""

    def test_cold_start_app(self):
        """Measure cold start time of the app via AppTest."""
        from streamlit.testing.v1 import AppTest

        app_path = str(Path(__file__).parent.parent / "app" / "streamlit_app.py")

        start = time.perf_counter()
        at = AppTest.from_file(app_path, default_timeout=30)
        at.run()
        elapsed = time.perf_counter() - start

        print(f"\nCold start time: {elapsed:.3f}s")
        assert elapsed < 10, f"Cold start too slow: {elapsed:.3f}s"

    def test_analyze_fixture_stateful_app(self, tmp_path):
        """Measure analyze time for stateful-app fixture (clone patched)."""
        fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
        out_dir = tmp_path / "reports"
        workspace = tmp_path / "workspace"

        times = []
        for _ in range(3):
            start = time.perf_counter()
            result, plan, md_path = analyze(
                repo_url=str(fixture),
                workspace=workspace,
                out_dir=out_dir,
                use_llm=False,
                max_mb=100,
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        med = median(times)
        print(f"\nAnalyze stateful-app (median of 3): {med:.3f}s")
        assert med < 5, f"Analyze too slow: {med:.3f}s"

    def test_analyze_fixture_ready_app(self, tmp_path):
        """Measure analyze time for ready-app fixture."""
        fixture = Path(__file__).parent.parent / "fixtures" / "ready-app"
        out_dir = tmp_path / "reports"
        workspace = tmp_path / "workspace"

        times = []
        for _ in range(3):
            start = time.perf_counter()
            result, plan, md_path = analyze(
                repo_url=str(fixture),
                workspace=workspace,
                out_dir=out_dir,
                use_llm=False,
                max_mb=100,
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        med = median(times)
        print(f"\nAnalyze ready-app (median of 3): {med:.3f}s")
        assert med < 5, f"Analyze too slow: {med:.3f}s"

    def test_analyze_fixture_messy_compose(self, tmp_path):
        """Measure analyze time for messy-compose fixture."""
        fixture = Path(__file__).parent.parent / "fixtures" / "messy-compose"
        out_dir = tmp_path / "reports"
        workspace = tmp_path / "workspace"

        times = []
        for _ in range(3):
            start = time.perf_counter()
            result, plan, md_path = analyze(
                repo_url=str(fixture),
                workspace=workspace,
                out_dir=out_dir,
                use_llm=False,
                max_mb=100,
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        med = median(times)
        print(f"\nAnalyze messy-compose (median of 3): {med:.3f}s")
        assert med < 5, f"Analyze too slow: {med:.3f}s"

    def test_render_500_findings(self):
        """Measure rendering time of results page with 500 findings via AppTest."""
        from streamlit.testing.v1 import AppTest

        test_script = '''
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, r"%s")
sys.path.insert(0, r"%s")

from assessor.models import AssessmentResult, Finding, Severity, Category, PlanStep
from app.ui.findings import render_findings_tab
from app.ui.results import render_results_overview
from app.ui.plan import render_plan_tab

# Create 500 findings
findings = []
for i in range(500):
    sev = ["critical", "high", "medium", "low", "info"][i %% 5]
    findings.append(Finding(
        id=f"TEST-{i:03d}",
        category=Category.CONFIG,
        severity=Severity(sev),
        title=f"Test finding {i}",
        description=f"Description for finding {i}",
        file=f"file{i}.py",
        line=i,
        evidence=f"evidence {i}",
        remediation=f"Fix finding {i}",
        eks_hint=f"EKS hint {i}"
    ))

result = AssessmentResult(
    repo_url="https://github.com/test/500-findings",
    files_scanned=100,
    findings=findings,
    score=50,
    readiness="Needs significant work",
    plan=[]
)

plan = [
    PlanStep(phase=1, title="Phase 1", why="Reason", actions=["Action 1"], finding_ids=["TEST-001"], effort="M"),
    PlanStep(phase=2, title="Phase 2", why="Reason", actions=["Action 2"], finding_ids=["TEST-002"], effort="M"),
]

st.set_page_config(page_title="Test", layout="wide")
render_results_overview(result)
render_findings_tab(result)
render_plan_tab(plan)
''' % (str(Path(__file__).parent.parent / "src").replace("\\", "\\\\"),
       str(Path(__file__).parent.parent / "app").replace("\\", "\\\\"))

        start = time.perf_counter()
        at = AppTest.from_string(test_script, default_timeout=60)
        at.run()
        elapsed = time.perf_counter() - start

        print(f"\nRender 500 findings: {elapsed:.3f}s")
        assert elapsed < 10, f"Render too slow: {elapsed:.3f}s"

    def test_zero_network_calls_without_llm(self, tmp_path):
        """Count network calls during a non-LLM run - must be 0."""
        fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
        out_dir = tmp_path / "reports"
        workspace = tmp_path / "workspace"

        # Patch socket.create_connection to count calls
        original_create_connection = socket.create_connection
        call_count = [0]

        def counting_create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
            call_count[0] += 1
            return original_create_connection(address, timeout, source_address)

        with patch("socket.create_connection", side_effect=counting_create_connection):
            # Also patch urllib to catch HTTP calls
            import urllib.request
            original_urlopen = urllib.request.urlopen
            def counting_urlopen(*args, **kwargs):
                call_count[0] += 1
                raise ConnectionError("Network blocked in test")

            with patch("urllib.request.urlopen", side_effect=counting_urlopen):
                result, plan, md_path = analyze(
                    repo_url=str(fixture),
                    workspace=workspace,
                    out_dir=out_dir,
                    use_llm=False,
                    max_mb=100,
                )

        print(f"\nNetwork calls during non-LLM analyze: {call_count[0]}")
        assert call_count[0] == 0, f"Expected 0 network calls, got {call_count[0]}"

    def test_peak_memory_analysis(self, tmp_path):
        """Measure peak memory of the analysis using tracemalloc."""
        fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
        out_dir = tmp_path / "reports"
        workspace = tmp_path / "workspace"

        tracemalloc.start()

        result, plan, md_path = analyze(
            repo_url=str(fixture),
            workspace=workspace,
            out_dir=out_dir,
            use_llm=False,
            max_mb=100,
        )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / (1024 * 1024)
        print(f"\nPeak memory during analysis: {peak_mb:.2f} MB")
        assert peak_mb < 500, f"Peak memory too high: {peak_mb:.2f} MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "perf"])
