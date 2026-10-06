"""Pure UI helper functions (no Streamlit imports)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from assessor.models import Finding

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


def severity_rank(sev: str) -> int:
    """Return numeric rank for severity (lower = more severe)."""
    try:
        return SEVERITY_ORDER.index(sev.lower())
    except ValueError:
        return len(SEVERITY_ORDER)


@dataclass(frozen=True)
class FindingGroup:
    """Grouped findings by rule_id with aggregated metadata."""
    rule_id: str
    title: str
    severity: str
    category: str
    count: int
    findings: list[Finding]
    remediation: str
    eks_hint: str | None


def group_findings(findings: list[Finding]) -> list[FindingGroup]:
    """Group findings by rule_id (finding.id), taking highest severity in group.
    Sorted by severity rank then by count descending.
    """
    groups: dict[str, list[Finding]] = {}
    for f in findings:
        groups.setdefault(f.id, []).append(f)

    result: list[FindingGroup] = []
    for rule_id, group in groups.items():
        # Highest severity = lowest rank number
        sorted_group = sorted(group, key=lambda f: severity_rank(f.severity.value))
        highest = sorted_group[0]
        result.append(
            FindingGroup(
                rule_id=rule_id,
                title=highest.title,
                severity=highest.severity.value,
                category=highest.category.value,
                count=len(group),
                findings=group,
                remediation=highest.remediation,
                eks_hint=highest.eks_hint,
            )
        )

    # Sort by severity rank, then count descending
    result.sort(key=lambda g: (severity_rank(g.severity), -g.count))
    return result


def severity_counts(findings: list[Finding]) -> dict[str, int]:
    """Return count per severity, including zeros for all 5 severities."""
    counts = dict.fromkeys(SEVERITY_ORDER, 0)
    for f in findings:
        sev = f.severity.value.lower()
        if sev in counts:
            counts[sev] += 1
    return counts


def top_priorities(groups: list[FindingGroup], n: int = 3) -> list[FindingGroup]:
    """Return first n groups with severity critical/high/medium."""
    priority_severities = {"critical", "high", "medium"}
    return [g for g in groups if g.severity in priority_severities][:n]


def readiness_tone(readiness: str) -> str:
    """Map readiness string to tone: good | warn | bad."""
    r = readiness.strip().lower()
    if r in ("ready", "ready with minor changes"):
        return "good"
    if r == "needs significant work":
        return "warn"
    if r == "not ready":
        return "bad"
    return "warn"


# SVG color constants (full opacity for stroke)
_SUCCESS = "#22C55E"
_WARNING = "#F59E0B"
_DANGER = "#EF4444"


def gauge_svg(score: int) -> str:
    """Return an SVG ring gauge (viewBox 0 0 120 120).
    Score clamped to 0..100, cast to int first.
    Stroke color by tone: >=65 success, 40-64 warning, <40 danger.
    """
    s = int(max(0, min(100, score)))
    # Circumference = 2 * pi * r, r = 50 => ~314.16
    circumference = 314.16
    offset = circumference * (1 - s / 100)

    if s >= 65:
        stroke = _SUCCESS
    elif s >= 40:
        stroke = _WARNING
    else:
        stroke = _DANGER

    # Title text for accessibility
    title_text = f"Score {s} out of 100"

    svg = (
        f'<svg viewBox="0 0 120 120" width="120" height="120" '
        f'role="img" aria-label="{title_text}" xmlns="http://www.w3.org/2000/svg">'
        f'<title>{title_text}</title>'
        f'<circle cx="60" cy="60" r="50" fill="none" stroke="#22314D" stroke-width="10"/>'
        f'<circle cx="60" cy="60" r="50" fill="none" stroke="{stroke}" stroke-width="10" '
        f'stroke-dasharray="{circumference}" stroke-dashoffset="{offset}" '
        f'stroke-linecap="round" transform="rotate(-90 60 60)"/>'
        f'<text x="60" y="68" text-anchor="middle" font-size="28" font-weight="700" '
        f'fill="#E6EDF7" font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif">'
        f'{s}</text>'
        f'</svg>'
    )
    return svg


def severity_bar_svg(counts: dict[str, int]) -> str:
    """Return a horizontal stacked bar SVG, widths proportional to counts.
    SVG: width="100%", height="10", viewBox="0 0 100 10", preserveAspectRatio="none",
    style="display:block;max-width:100%", role="img", with <title> containing counts.
    Segment widths are INTEGERS summing to 100 (largest remainder method).
    Order: critical, high, medium, low, info. Non-zero severities get at least 2 units.
    When total is 0, draws one gray segment of 100.
    Colors: critical #EF4444, high #F97316, medium #EAB308, low #22C55E, info #38BDF8.
    Rounded ends via clipPath with rx=5.
    """
    # Color mapping
    colors = {
        "critical": "#EF4444",
        "high": "#F97316",
        "medium": "#EAB308",
        "low": "#22C55E",
        "info": "#38BDF8",
    }

    # Compute exact proportional widths
    total = sum(counts.get(sev, 0) for sev in SEVERITY_ORDER)
    target_width = 100

    if total == 0:
        # All zero: gray bar
        return (
            '<svg width="100%" height="10" viewBox="0 0 100 10" preserveAspectRatio="none" '
            'style="display:block;max-width:100%" role="img" aria-label="No findings">'
            '<title>No findings</title>'
            '<rect x="0" y="0" width="100" height="10" fill="#8FA1BF" rx="5"/>'
            '</svg>'
        )

    # First pass: compute exact widths and floors
    exact_widths = {}
    floors = {}
    remainders = {}
    for sev in SEVERITY_ORDER:
        count = counts.get(sev, 0)
        exact = (count / total) * target_width
        exact_widths[sev] = exact
        floor_val = int(exact)
        floors[sev] = floor_val
        remainders[sev] = exact - floor_val

    # Ensure non-zero severities get at least 2 units
    sum_floors = sum(floors.values())
    for sev in SEVERITY_ORDER:
        count = counts.get(sev, 0)
        if count > 0 and floors[sev] < 2:
            needed = 2 - floors[sev]
            sum_floors += needed
            floors[sev] = 2

    # Distribute remaining units by largest remainder
    remaining = target_width - sum_floors
    if remaining > 0:
        # Sort by remainder descending
        sorted_sev = sorted(
            [sev for sev in SEVERITY_ORDER if counts.get(sev, 0) > 0],
            key=lambda s: remainders[s],
            reverse=True
        )
        for sev in sorted_sev:
            if remaining <= 0:
                break
            floors[sev] += 1
            remaining -= 1

    # Build segments
    segments = []
    x = 0
    title_parts = []
    for sev in SEVERITY_ORDER:
        count = counts.get(sev, 0)
        if count == 0:
            continue
        width = floors[sev]
        if width <= 0:
            continue
        color = colors[sev]
        segments.append(
            f'<rect x="{x}" y="0" width="{width}" height="10" fill="{color}" rx="0" ry="0"/>'
        )
        title_parts.append(f"{sev.capitalize()}: {count}")
        x += width

    # Round ends via clipPath
    clip_path_id = f"bar-clip-{id(counts)}"
    clip_path = (
        f'<clipPath id="{clip_path_id}">'
        f'<rect x="0" y="0" width="100" height="10" rx="5"/>'
        f'</clipPath>'
    )
    segments_svg = "".join(segments)
    title_text = ", ".join(title_parts)

    svg = (
        f'<svg width="100%" height="10" viewBox="0 0 100 10" preserveAspectRatio="none" '
        f'style="display:block;max-width:100%" role="img" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<title>{title_text}</title>'
        f'{clip_path}'
        f'<g clip-path="url(#{clip_path_id})">'
        f'<rect x="0" y="0" width="100" height="10" fill="#22314D" rx="5"/>'
        f'{segments_svg}'
        f'</g>'
        f'</svg>'
    )
    return svg


def validate_ollama_host(value: str) -> tuple[bool, str]:
    """Validate Ollama host URL.
    Must be http:// or https://, have a host, numeric port if present,
    no credentials, no path other than '/'.
    Returns (ok, normalized_value_or_error_message).
    """
    v = value.strip()
    if not v:
        return False, "Empty host"

    # Must start with http:// or https://
    if not (v.startswith("http://") or v.startswith("https://")):
        return False, "Must start with http:// or https://"

    # Parse URL manually to avoid urllib issues with invalid URLs
    # Remove protocol
    rest = v[7:] if v.startswith("http://") else v[8:]

    # No credentials allowed (no @ before host)
    if "@" in rest:
        return False, "Credentials not allowed in URL"

    # Split host:port from path
    if "/" in rest:
        host_port, path = rest.split("/", 1)
        if path != "":
            return False, "Path not allowed (only '/' permitted)"
    else:
        host_port = rest
        path = ""

    if not host_port:
        return False, "Missing host"

    # Split host and port
    if ":" in host_port:
        host, port_str = host_port.rsplit(":", 1)
        if not host:
            return False, "Missing host"
        # Port must be numeric
        if not port_str.isdigit():
            return False, f"Invalid port: {port_str} (must be numeric)"
        port = int(port_str)
        if not (1 <= port <= 65535):
            return False, f"Port out of range: {port}"
    else:
        host = host_port
        # Default ports
        port = 80 if v.startswith("http://") else 443

    # Basic host validation (hostname or IP)
    if not _is_valid_host(host):
        return False, f"Invalid host: {host}"

    # Normalize: ensure path is just '/'
    normalized = f"{v.split('://')[0]}://{host}"
    if ":" in host_port:
        normalized += f":{port}"
    normalized += "/"

    return True, normalized


def _is_valid_host(host: str) -> bool:
    """Validate hostname or IP address."""
    # IPv4
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ipv4_pattern, host):
        parts = host.split(".")
        return all(0 <= int(p) <= 255 for p in parts)

    # IPv6 in brackets
    if host.startswith("[") and host.endswith("]"):
        # Simplified check
        return True

    # Hostname (labels separated by dots)
    if len(host) > 253:
        return False
    labels = host.split(".")
    for label in labels:
        if not label or len(label) > 63:
            return False
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$", label):
            return False
    return True


def relative_time(dt: datetime, now: datetime | None = None) -> str:
    """Return human-readable relative time string."""
    if now is None:
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 0:
        seconds = 0

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} min ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} h ago"
    days = seconds // 86400
    return f"{days} d ago"


def truncate(text: str, n: int = 160) -> str:
    """Truncate text to n characters with ellipsis."""
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


# Severity circles for expander labels (plain text, no HTML)
_SEVERITY_CIRCLES = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
    "info": "🔵",
}


def group_label(group: FindingGroup) -> str:
    """Return plain text label for expander, never containing '<' or '>'.
    Format: "🔴 CRITICAL · CFG-001 · Hardcoded secret detected (20)"
    """
    circle = _SEVERITY_CIRCLES.get(group.severity.lower(), "⚪")
    # Sanitize title to remove any angle brackets (security)
    safe_title = group.title.replace("<", "[").replace(">", "]")
    return f"{circle} {group.severity.upper()} · {group.rule_id} · {safe_title} ({group.count})"
