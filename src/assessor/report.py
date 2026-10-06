from __future__ import annotations

import html
import json
from datetime import UTC, datetime
from pathlib import Path

from assessor.models import AssessmentResult, PlanStep, Severity

SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


def _escape_md(text: str) -> str:
    """Escape text for safe Markdown rendering."""
    if not text:
        return ""
    # Escape HTML special chars
    text = html.escape(text)
    # Escape Markdown special chars
    text = text.replace("|", "\\|").replace("`", "\\`").replace("*", "\\*").replace("_", "\\_")
    return text


def to_markdown(result: AssessmentResult, plan: list[PlanStep]) -> str:
    lines = [
        "# EKS Migration Readiness Assessment",
        "",
        f"**Repository:** {_escape_md(result.repo_url)}",
        f"**Scanned:** {result.scanned_at.isoformat()}",
        f"**Files Scanned:** {result.files_scanned}",
        f"**Score:** {result.score}/100",
        f"**Readiness:** {result.readiness}",
        "",
    ]

    if result.summary:
        lines.extend(["## Summary", "", _escape_md(result.summary), ""])

    # Show stored locations if available
    if result.stored_at:
        lines.extend(["## Storage Locations", ""])
        for uri in result.stored_at:
            lines.append(f"- {_escape_md(uri)}")
        lines.append("")

    # Findings table sorted by severity
    sorted_findings = sorted(result.findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 5))
    if sorted_findings:
        lines.extend([
            "## Findings",
            "",
            "| Severity | ID | Category | Title | Location | Evidence |",
            "|----------|-----|----------|-------|----------|----------|",
        ])
        for f in sorted_findings:
            loc = f"{f.file}:{f.line}" if f.file and f.line else f.file or "N/A"
            evidence = _escape_md((f.evidence or "")[:80])
            lines.append(f"| {f.severity.value.upper()} | {_escape_md(f.id)} | {_escape_md(f.category.value)} | {_escape_md(f.title)} | {_escape_md(loc)} | {evidence} |")
        lines.append("")

    # Strengths (OK-001)
    strengths = [f for f in result.findings if f.id == "OK-001"]
    if strengths:
        lines.extend(["## Strengths", ""])
        for s in strengths:
            lines.append(f"- **{_escape_md(s.title)}**: {_escape_md(s.description)}")
        lines.append("")

    # Migration Plan
    if plan:
        lines.extend(["## Migration Plan", ""])
        for step in plan:
            lines.append(f"### Phase {step.phase}: {_escape_md(step.title)}")
            lines.append(f"**Effort:** {_escape_md(step.effort)}")
            lines.append(f"**Why:** {_escape_md(step.why)}")
            lines.append("**Actions:**")
            for action in step.actions:
                lines.append(f"- {_escape_md(action)}")
            lines.append(f"**Related Findings:** {', '.join(step.finding_ids)}")
            lines.append("")

    # Suggested Kubernetes Building Blocks
    lines.extend([
        "## Suggested Kubernetes Building Blocks",
        "",
        "- **Compute**: EKS Managed Node Groups",
        "- **Networking**: VPC CNI, CoreDNS, Service resources, Ingress (ALB/Nginx)",
        "- **Storage**: EBS CSI Driver for PVCs, EFS CSI Driver for shared storage, S3 via EKS Pod Identity",
        "- **Database**: RDS (PostgreSQL/MySQL) or Aurora, or self-managed via StatefulSet + PVC",
        "- **Cache**: ElastiCache Redis (recommended) or self-managed Redis",
        "- **Secrets**: AWS Secrets Manager + EKS Pod Identity, or Kubernetes Secrets (sealed-secrets/External Secrets Operator)",
        "- **Config**: ConfigMaps, External Secrets Operator",
        "- **Observability**: CloudWatch Container Insights, Fluent Bit, Prometheus/Grafana, X-Ray",
        "- **CI/CD**: CodePipeline, ArgoCD, Flux, or GitHub Actions with OIDC",
        "- **Security**: Pod Security Standards, Network Policies, EKS Pod Identity, Kyverno/OPA",
        "",
    ])

    return "\n".join(lines)


def to_json(result: AssessmentResult, plan: list[PlanStep]) -> str:
    data = {
        "repo_url": result.repo_url,
        "scanned_at": result.scanned_at.isoformat(),
        "files_scanned": result.files_scanned,
        "score": result.score,
        "readiness": result.readiness,
        "summary": result.summary,
        "stored_at": result.stored_at,
        "findings": [
            {
                "id": f.id,
                "category": f.category.value,
                "severity": f.severity.value,
                "title": f.title,
                "description": f.description,
                "file": f.file,
                "line": f.line,
                "evidence": f.evidence,
                "remediation": f.remediation,
                "eks_hint": f.eks_hint,
            }
            for f in result.findings
        ],
        "plan": [
            {
                "phase": p.phase,
                "title": p.title,
                "why": p.why,
                "actions": p.actions,
                "finding_ids": p.finding_ids,
                "effort": p.effort,
            }
            for p in plan
        ],
    }
    return json.dumps(data, indent=2)


def save_report(result: AssessmentResult, plan: list[PlanStep], out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")

    # Extract a clean repo name from the URL
    if result.repo_url.startswith("file://"):
        # Local path - use the directory name
        path = Path(result.repo_url[7:])  # Remove "file://"
        repo_name = path.name
    else:
        # Remote URL - extract from URL
        repo_name = result.repo_url.split("/")[-1].replace(".git", "").replace(":", "-").replace("/", "-")

    base = f"report-{repo_name}-{timestamp}"

    md_path = out_dir / f"{base}.md"
    json_path = out_dir / f"{base}.json"

    md_path.write_text(to_markdown(result, plan), encoding="utf-8")
    json_path.write_text(to_json(result, plan), encoding="utf-8")

    return md_path, json_path
