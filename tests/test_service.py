from __future__ import annotations

from pathlib import Path

import pytest

from assessor.models import AssessmentResult
from assessor.service import analyze


class TestService:
    def test_analyze_local_fixture(self, tmp_path: Path):
        """Test analyze with a local fixture directory (skips cloning)."""
        # Use the ready-app fixture which should have good score
        fixture = Path(__file__).parent.parent / "fixtures" / "ready-app"
        out_dir = tmp_path / "reports"

        result, plan, md_path = analyze(
            repo_url=str(fixture),
            workspace=tmp_path / "workspace",
            out_dir=out_dir,
            use_llm=False,
            max_mb=100,
        )

        assert isinstance(result, AssessmentResult)
        assert result.score >= 85  # ready-app should be high score
        assert result.readiness in ["Ready", "Ready with minor changes"]
        assert len(result.findings) > 0
        assert md_path.exists()
        assert md_path.suffix == ".md"

        # JSON should also exist
        json_path = md_path.with_suffix(".json")
        assert json_path.exists()

    def test_analyze_stateful_fixture(self, tmp_path: Path):
        """Test analyze with stateful-app fixture (should have findings)."""
        fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
        out_dir = tmp_path / "reports"

        result, plan, md_path = analyze(
            repo_url=str(fixture),
            workspace=tmp_path / "workspace",
            out_dir=out_dir,
            use_llm=False,
            max_mb=100,
        )

        assert isinstance(result, AssessmentResult)
        assert result.score < 85  # stateful-app should have low score
        assert result.readiness in ["Needs significant work", "Not ready"]
        assert len(result.findings) > 0
        assert md_path.exists()

        # Should have critical/high findings
        critical_high = [f for f in result.findings if f.severity.value in ("critical", "high")]
        assert len(critical_high) > 0

    def test_analyze_invalid_url(self, tmp_path: Path):
        """Test that invalid URLs raise ValueError."""
        out_dir = tmp_path / "reports"

        with pytest.raises(ValueError):
            analyze(
                repo_url="file:///etc/passwd",
                workspace=tmp_path / "workspace",
                out_dir=out_dir,
                use_llm=False,
            )

    def test_analyze_localhost_url(self, tmp_path: Path):
        """Test that localhost URLs are rejected."""
        out_dir = tmp_path / "reports"

        with pytest.raises(ValueError):
            analyze(
                repo_url="http://localhost/repo",
                workspace=tmp_path / "workspace",
                out_dir=out_dir,
                use_llm=False,
            )
