from __future__ import annotations

from assessor.models import Finding, PlanStep

PHASES = [
    (1, "Containerization", "container", "Dockerfile, non-root user, pinned base image, health checks"),
    (2, "Configuration and Secrets", "config", "ConfigMap/Secret, Secrets Manager via Pod Identity"),
    (3, "State and Storage", "state", "PVC + EBS CSI Driver, external DB/cache/S3"),
    (4, "Networking", "networking", "Kubernetes Services, DNS, port configuration"),
    (5, "Observability and Lifecycle", "logging", "stdout logging, probes, SIGTERM handling"),
]

CATEGORY_EFFORT = {
    "container": "M",
    "config": "S",
    "state": "L",
    "networking": "S",
    "logging": "S",
    "lifecycle": "S",
}


def build_migration_plan(findings: list[Finding]) -> list[PlanStep]:
    # Filter out OK-001 positive findings
    relevant = [f for f in findings if f.id != "OK-001"]

    # Group findings by category and eks_hint
    by_category: dict[str, list[Finding]] = {}
    for f in relevant:
        by_category.setdefault(f.category.value, []).append(f)

    plan: list[PlanStep] = []

    for phase_num, title, category, why in PHASES:
        category_findings = by_category.get(category, [])
        if not category_findings:
            continue

        finding_ids = [f.id for f in category_findings]
        actions = _actions_for_category(category, category_findings)
        effort = CATEGORY_EFFORT.get(category, "M")

        plan.append(
            PlanStep(
                phase=phase_num,
                title=title,
                why=why,
                actions=actions,
                finding_ids=finding_ids,
                effort=effort,
            )
        )

    return plan


def _actions_for_category(category: str, findings: list[Finding]) -> list[str]:
    actions_set: set[str] = set()

    for f in findings:
        hint = f.eks_hint or ""
        remediation = f.remediation or ""

        if "PVC" in hint or "EBS" in hint:
            actions_set.add("Provision EBS volumes via PVC and EBS CSI Driver")
            actions_set.add("Mount PVCs to pods for persistent storage")
        if "S3" in hint:
            actions_set.add("Use S3 for object storage instead of local filesystem")
        if "Redis" in hint or "ElastiCache" in hint:
            actions_set.add("Deploy ElastiCache Redis for session/state storage")
            actions_set.add("Update application to use external Redis")
        if "RDS" in hint or "StatefulSet" in hint:
            actions_set.add("Migrate to RDS (PostgreSQL/MySQL) or use StatefulSet with PVC")
        if "Secrets Manager" in hint or "Pod Identity" in hint:
            actions_set.add("Store secrets in AWS Secrets Manager")
            actions_set.add("Use EKS Pod Identity for pod access")
        if "ConfigMap" in hint:
            actions_set.add("Externalize configuration into ConfigMaps")
        if "Service DNS" in hint:
            actions_set.add("Replace hardcoded IPs/localhost with Kubernetes Service DNS names")
        if "runAsNonRoot" in hint:
            actions_set.add("Add USER directive in Dockerfile and set runAsNonRoot in pod spec")
        if "Pinned" in hint or "latest" in hint.lower():
            actions_set.add("Pin base image tags (e.g., python:3.12-slim)")
        if "HEALTHCHECK" in hint or "Liveness" in hint or "readiness" in hint.lower():
            actions_set.add("Add HEALTHCHECK to Dockerfile")
            actions_set.add("Implement /healthz and /ready endpoints in application")
            actions_set.add("Configure livenessProbe and readinessProbe in deployment")
        if "stdout" in hint or "CloudWatch" in hint or "Fluent Bit" in hint:
            actions_set.add("Configure application to log to stdout")
            actions_set.add("Deploy CloudWatch agent or Fluent Bit for log aggregation")
        if "terminationGracePeriod" in hint:
            actions_set.add("Add SIGTERM handler in application")
            actions_set.add("Set terminationGracePeriodSeconds in pod spec")
        if "Containerize" in hint:
            actions_set.add("Create Dockerfile for the application")

        # Also derive from remediation
        if remediation:
            actions_set.add(remediation)

    # Limit and sort actions
    return sorted(list(actions_set))[:8]
