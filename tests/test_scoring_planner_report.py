from __future__ import annotations

import json
import tempfile
from pathlib import Path

from assessor.models import AssessmentResult, Finding, PlanStep, Severity
from assessor.planner import build_migration_plan
from assessor.report import save_report, to_json, to_markdown
from assessor.scoring import compute_score, readiness_level


class TestScoring:
    def test_compute_score_empty(self):
        assert compute_score([]) == 100

    def test_compute_score_single_critical(self):
        findings = [
            Finding(id="TEST-001", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation="")
        ]
        # 100 - 25 = 75
        assert compute_score(findings) == 75

    def test_compute_score_multiple_same_rule_capped(self):
        findings = [
            Finding(id="TEST-001", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation=""),
            Finding(id="TEST-001", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation=""),
            Finding(id="TEST-001", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation=""),
        ]
        # Cap at 2x: 2 * 25 = 50, so 100 - 50 = 50
        assert compute_score(findings) == 50

    def test_compute_score_mixed_severities(self):
        findings = [
            Finding(id="A", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation=""),
            Finding(id="B", category="state", severity=Severity.HIGH, title="Test", description="", remediation=""),
            Finding(id="C", category="state", severity=Severity.MEDIUM, title="Test", description="", remediation=""),
            Finding(id="D", category="state", severity=Severity.LOW, title="Test", description="", remediation=""),
            Finding(id="E", category="state", severity=Severity.INFO, title="Test", description="", remediation=""),
        ]
        # 100 - 25 - 12 - 5 - 2 - 0 = 56
        assert compute_score(findings) == 56

    def test_compute_score_clamped(self):
        findings = [
            Finding(id="A", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation=""),
            Finding(id="B", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation=""),
            Finding(id="C", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation=""),
            Finding(id="D", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation=""),
            Finding(id="E", category="state", severity=Severity.CRITICAL, title="Test", description="", remediation=""),
        ]
        # 5 * 25 = 125, but capped at 2 per rule = 50, so 100 - 50 = 50
        # Wait, they're all different IDs, so 5 * 25 = 125 -> clamped to 0
        assert compute_score(findings) == 0

    def test_readiness_levels(self):
        assert readiness_level(90) == "Ready"
        assert readiness_level(85) == "Ready"
        assert readiness_level(84) == "Ready with minor changes"
        assert readiness_level(65) == "Ready with minor changes"
        assert readiness_level(64) == "Needs significant work"
        assert readiness_level(40) == "Needs significant work"
        assert readiness_level(39) == "Not ready"
        assert readiness_level(0) == "Not ready"


class TestPlanner:
    def test_build_migration_plan_stateful_app(self):
        findings = [
            Finding(id="STATE-001", category="state", severity=Severity.HIGH, title="Local write", description="", remediation="", eks_hint="PVC with EBS CSI Driver"),
            Finding(id="STATE-002", category="state", severity=Severity.HIGH, title="In-memory session", description="", remediation="", eks_hint="Redis/ElastiCache"),
            Finding(id="STATE-003", category="state", severity=Severity.HIGH, title="SQLite", description="", remediation="", eks_hint="RDS or StatefulSet with PVC"),
            Finding(id="NET-001", category="networking", severity=Severity.MEDIUM, title="Hardcoded IP", description="", remediation="", eks_hint="Kubernetes Service DNS names"),
            Finding(id="CFG-001", category="config", severity=Severity.CRITICAL, title="Hardcoded secret", description="", remediation="", eks_hint="Secrets Manager + Pod Identity"),
            Finding(id="LOG-001", category="logging", severity=Severity.MEDIUM, title="File logging", description="", remediation="", eks_hint="stdout + CloudWatch/Fluent Bit"),
            Finding(id="CTR-002", category="container", severity=Severity.MEDIUM, title="No USER", description="", remediation="", eks_hint="runAsNonRoot"),
            Finding(id="CTR-003", category="container", severity=Severity.MEDIUM, title="Latest tag", description="", remediation="", eks_hint="Pinned image tags"),
            Finding(id="CTR-004", category="container", severity=Severity.MEDIUM, title="No healthcheck", description="", remediation="", eks_hint="Liveness/readiness probes"),
            Finding(id="OK-001", category="config", severity=Severity.INFO, title="Positive", description="", remediation=""),
        ]
        plan = build_migration_plan(findings)
        assert len(plan) > 0

        # Check phase 1 (containerization) exists
        container_phase = next((p for p in plan if p.phase == 1), None)
        assert container_phase is not None
        assert container_phase.title == "Containerization"
        assert "CTR-002" in container_phase.finding_ids or "CTR-003" in container_phase.finding_ids or "CTR-004" in container_phase.finding_ids

        # Check phase 3 (state and storage) mentions PVC
        state_phase = next((p for p in plan if p.phase == 3), None)
        assert state_phase is not None
        assert state_phase.title == "State and Storage"
        assert "STATE-001" in state_phase.finding_ids or "STATE-002" in state_phase.finding_ids or "STATE-003" in state_phase.finding_ids
        # Should have PVC-related action
        actions_text = " ".join(state_phase.actions)
        assert "PVC" in actions_text or "EBS" in actions_text

    def test_build_migration_plan_ready_app(self):
        findings = [
            Finding(id="OK-001", category="config", severity=Severity.INFO, title="Positive: env config", description="", remediation=""),
            Finding(id="OK-001", category="config", severity=Severity.INFO, title="Positive: health endpoint", description="", remediation=""),
        ]
        plan = build_migration_plan(findings)
        # Should have no phases for OK-001 findings
        assert len(plan) == 0


class TestReport:
    def test_to_markdown_contains_score(self):
        result = AssessmentResult(
            repo_url="https://github.com/test/repo",
            files_scanned=10,
            findings=[],
            score=85,
            readiness="Ready",
        )
        plan = []
        md = to_markdown(result, plan)
        assert "85/100" in md
        assert "Ready" in md

    def test_to_markdown_contains_finding_ids(self):
        findings = [
            Finding(id="STATE-001", category="state", severity=Severity.HIGH, title="Test", description="", remediation="", file="app.py", line=10, evidence="code"),
            Finding(id="CFG-001", category="config", severity=Severity.CRITICAL, title="Test", description="", remediation="", file="config.py", line=5, evidence="secret"),
        ]
        result = AssessmentResult(
            repo_url="https://github.com/test/repo",
            files_scanned=2,
            findings=findings,
            score=50,
            readiness="Needs significant work",
        )
        plan = []
        md = to_markdown(result, plan)
        assert "STATE-001" in md
        assert "CFG-001" in md
        assert "app.py" in md
        assert "config.py" in md

    def test_to_json_roundtrip(self):
        result = AssessmentResult(
            repo_url="https://github.com/test/repo",
            files_scanned=1,
            findings=[
                Finding(id="TEST-001", category="state", severity=Severity.MEDIUM, title="Test", description="", remediation="", eks_hint="hint"),
            ],
            score=70,
            readiness="Ready with minor changes",
        )
        plan = [
            PlanStep(phase=1, title="Test", why="why", actions=["action1"], finding_ids=["TEST-001"], effort="M"),
        ]
        json_str = to_json(result, plan)
        data = json.loads(json_str)
        assert data["repo_url"] == "https://github.com/test/repo"
        assert data["score"] == 70
        assert len(data["findings"]) == 1
        assert data["findings"][0]["id"] == "TEST-001"
        assert len(data["plan"]) == 1
        assert data["plan"][0]["phase"] == 1

    def test_save_report_creates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = AssessmentResult(
                repo_url="https://github.com/test/repo",
                files_scanned=1,
                findings=[],
                score=80,
                readiness="Ready with minor changes",
            )
            plan = []
            md_path, json_path = save_report(result, plan, Path(tmpdir))
            assert md_path.exists()
            assert json_path.exists()
            assert md_path.suffix == ".md"
            assert json_path.suffix == ".json"
            # Check content
            md_content = md_path.read_text()
            assert "80/100" in md_content
            json_content = json_path.read_text()
            assert "80" in json_content


class TestCLI:
    def test_cli_scan_local_directory(self):
        import subprocess
        result = subprocess.run(
            [
                "python", "-m", "assessor.cli", "scan",
                "fixtures/stateful-app",
                "--no-llm",
                "--out", tempfile.gettempdir(),
            ],
            capture_output=True,
            text=True,
            cwd=".",
        )
        assert result.returncode == 0
        assert "Score:" in result.stdout
        assert "Readiness:" in result.stdout
        # Check that report files were created
        import glob
        md_files = glob.glob(f"{tempfile.gettempdir()}/report-stateful-app-*.md")
        json_files = glob.glob(f"{tempfile.gettempdir()}/report-stateful-app-*.json")
        assert len(md_files) >= 1
        assert len(json_files) >= 1
        # Cleanup
        for f in md_files + json_files:
            Path(f).unlink(missing_ok=True)
