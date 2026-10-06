"""Tests for ui_helpers pure functions."""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from assessor.models import Category, Finding, Severity
from assessor.ui_helpers import (
    SEVERITY_ORDER,
    FindingGroup,
    gauge_svg,
    group_findings,
    readiness_tone,
    relative_time,
    severity_bar_svg,
    severity_counts,
    severity_rank,
    top_priorities,
    truncate,
    validate_ollama_host,
)


def test_severity_rank() -> None:
    assert severity_rank("critical") == 0
    assert severity_rank("high") == 1
    assert severity_rank("medium") == 2
    assert severity_rank("low") == 3
    assert severity_rank("info") == 4
    assert severity_rank("unknown") == 5  # not in list -> after all


def test_group_findings_ordering() -> None:
    # Create findings with different severities and same rule_id
    f1 = Finding(
        id="rule-1",
        category=Category.SECURITY,
        severity=Severity.HIGH,
        title="High finding",
        description="desc",
        remediation="fix",
    )
    f2 = Finding(
        id="rule-1",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        title="Critical finding",
        description="desc",
        remediation="fix",
    )
    f3 = Finding(
        id="rule-2",
        category=Category.CONFIG,
        severity=Severity.MEDIUM,
        title="Medium finding",
        description="desc",
        remediation="fix",
    )
    f4 = Finding(
        id="rule-3",
        category=Category.NETWORKING,
        severity=Severity.LOW,
        title="Low finding",
        description="desc",
        remediation="fix",
    )

    groups = group_findings([f1, f2, f3, f4])
    # Should have 3 groups (rule-1 grouped)
    assert len(groups) == 3
    # rule-1 group should have critical severity (highest)
    g1 = next(g for g in groups if g.rule_id == "rule-1")
    assert g1.severity == "critical"
    assert g1.count == 2
    # Order: critical first, then medium, then low
    assert groups[0].severity == "critical"
    assert groups[1].severity == "medium"
    assert groups[2].severity == "low"


def test_severity_counts_includes_zeros() -> None:
    f1 = Finding(
        id="r1",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        title="t",
        description="d",
        remediation="r",
    )
    f2 = Finding(
        id="r2",
        category=Category.CONFIG,
        severity=Severity.HIGH,
        title="t",
        description="d",
        remediation="r",
    )

    counts = severity_counts([f1, f2])
    assert counts == {
        "critical": 1,
        "high": 1,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    # All 5 keys present
    assert set(counts.keys()) == set(SEVERITY_ORDER)


def test_top_priorities() -> None:
    g1 = FindingGroup(
        rule_id="r1",
        title="Critical",
        severity="critical",
        category="security",
        count=1,
        findings=[],
        remediation="r",
        eks_hint=None,
    )
    g2 = FindingGroup(
        rule_id="r2",
        title="High",
        severity="high",
        category="config",
        count=1,
        findings=[],
        remediation="r",
        eks_hint=None,
    )
    g3 = FindingGroup(
        rule_id="r3",
        title="Medium",
        severity="medium",
        category="networking",
        count=1,
        findings=[],
        remediation="r",
        eks_hint=None,
    )
    g4 = FindingGroup(
        rule_id="r4",
        title="Low",
        severity="low",
        category="storage",
        count=1,
        findings=[],
        remediation="r",
        eks_hint=None,
    )
    g5 = FindingGroup(
        rule_id="r5",
        title="Info",
        severity="info",
        category="logging",
        count=1,
        findings=[],
        remediation="r",
        eks_hint=None,
    )

    groups = [g4, g5, g1, g2, g3]  # shuffled
    top = top_priorities(groups, n=3)
    assert len(top) == 3
    assert top[0].severity == "critical"
    assert top[1].severity == "high"
    assert top[2].severity == "medium"


def test_readiness_tone() -> None:
    assert readiness_tone("Ready") == "good"
    assert readiness_tone("ready with minor changes") == "good"
    assert readiness_tone("Ready with minor changes") == "good"
    assert readiness_tone("Needs significant work") == "warn"
    assert readiness_tone("Not ready") == "bad"
    assert readiness_tone("unknown") == "warn"
    assert readiness_tone("") == "warn"


def test_gauge_svg_clamping() -> None:
    # Over 100 clamped to 100
    svg1 = gauge_svg(150)
    assert "100" in svg1
    assert "<script" not in svg1.lower()
    # Title contains clamped value
    assert "Score 100 out of 100" in svg1

    # Under 0 clamped to 0
    svg2 = gauge_svg(-5)
    assert "0" in svg2
    assert "<script" not in svg2.lower()
    assert "Score 0 out of 100" in svg2

    # Normal values
    svg3 = gauge_svg(65)
    assert "Score 65 out of 100" in svg3
    assert "#22C55E" in svg3  # success color

    svg4 = gauge_svg(50)
    assert "#F59E0B" in svg4  # warning color

    svg5 = gauge_svg(30)
    assert "#EF4444" in svg5  # danger color

    # Check no unsafe content in any
    for svg in [svg1, svg2, svg3, svg4, svg5]:
        assert "<script" not in svg.lower()
        assert "onerror" not in svg.lower()
        assert "onclick" not in svg.lower()


def test_severity_bar_svg_safety() -> None:
    counts = {"critical": 2, "high": 1, "medium": 3, "low": 0, "info": 0}
    svg = severity_bar_svg(counts)
    # No script tags
    assert "<script" not in svg.lower()
    assert "onerror" not in svg.lower()
    assert "onclick" not in svg.lower()
    # Title attributes present
    assert "Critical: 2" in svg
    assert "High: 1" in svg
    assert "Medium: 3" in svg


def test_validate_ollama_host() -> None:
    # Valid cases
    ok, val = validate_ollama_host("http://localhost:11434")
    assert ok
    assert val == "http://localhost:11434/"

    ok, val = validate_ollama_host("https://host.docker.internal:11434")
    assert ok
    assert val == "https://host.docker.internal:11434/"

    ok, val = validate_ollama_host("http://172.29.208.1:11434")
    assert ok
    assert val == "http://172.29.208.1:11434/"

    ok, val = validate_ollama_host("https://example.com")
    assert ok
    assert val == "https://example.com/"

    ok, val = validate_ollama_host("http://example.com/")
    assert ok
    assert val == "http://example.com/"

    # Invalid cases
    ok, msg = validate_ollama_host("http://172.29.208.1:1143ad")  # non-numeric port
    assert not ok
    assert "Invalid port" in msg

    ok, msg = validate_ollama_host("javascript:alert(1)")
    assert not ok
    assert "http:// or https://" in msg

    ok, msg = validate_ollama_host("file:///etc/passwd")
    assert not ok
    assert "http:// or https://" in msg

    ok, msg = validate_ollama_host("http://user:pw@host")
    assert not ok
    assert "Credentials not allowed" in msg

    ok, msg = validate_ollama_host("http://host/path/extra")
    assert not ok
    assert "Path not allowed" in msg

    ok, msg = validate_ollama_host("")
    assert not ok
    assert "Empty" in msg

    ok, msg = validate_ollama_host("not-a-url")
    assert not ok
    assert "http:// or https://" in msg


def test_relative_time() -> None:
    now = datetime.datetime(2024, 1, 1, 12, 0, 0)
    dt = now - datetime.timedelta(seconds=30)
    assert relative_time(dt, now) == "just now"

    dt = now - datetime.timedelta(minutes=5)
    assert relative_time(dt, now) == "5 min ago"

    dt = now - datetime.timedelta(hours=2)
    assert relative_time(dt, now) == "2 h ago"

    dt = now - datetime.timedelta(days=3)
    assert relative_time(dt, now) == "3 d ago"

    # Future time -> just now
    dt = now + datetime.timedelta(hours=1)
    assert relative_time(dt, now) == "just now"


def test_truncate() -> None:
    assert truncate("short", 160) == "short"
    assert truncate("a" * 160, 160) == "a" * 160
    assert truncate("a" * 161, 160) == "a" * 159 + "…"
    assert truncate("hello world", 8) == "hello w…"
