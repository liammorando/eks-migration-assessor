from __future__ import annotations

from collections import Counter

from assessor.models import Finding, Severity

SEVERITY_PENALTY = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 12,
    Severity.MEDIUM: 5,
    Severity.LOW: 2,
    Severity.INFO: 0,
}

MAX_PENALTY_PER_RULE = 2

# Rule IDs to ignore in scoring
IGNORED_RULE_IDS = {"SCAN-ERR", "OK-001"}


def compute_score(findings: list[Finding]) -> int:
    if not findings:
        return 100

    rule_counts: Counter[str] = Counter(f.id for f in findings)
    # Get severity for each rule (use max severity if multiple)
    rule_severity: dict[str, Severity] = {}
    for f in findings:
        if f.id not in rule_severity or SEVERITY_PENALTY[f.severity] > SEVERITY_PENALTY[rule_severity[f.id]]:
            rule_severity[f.id] = f.severity

    total_penalty = 0
    for rule_id, count in rule_counts.items():
        if rule_id in IGNORED_RULE_IDS:
            continue
        penalty = SEVERITY_PENALTY.get(rule_severity[rule_id], 0)
        capped_penalty = penalty * min(count, MAX_PENALTY_PER_RULE)
        total_penalty += capped_penalty

    score = 100 - total_penalty
    return max(0, min(100, score))


def readiness_level(score: int) -> str:
    if score >= 85:
        return "Ready"
    if score >= 65:
        return "Ready with minor changes"
    if score >= 40:
        return "Needs significant work"
    return "Not ready"
