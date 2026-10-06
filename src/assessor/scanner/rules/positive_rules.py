from __future__ import annotations

import re

from assessor.models import Category, Finding, Severity
from assessor.scanner.registry import ScanContext, rule


@rule("OK-001", Category.CONFIG, Severity.INFO)
def check_positive_practices(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []

    # Check for stdout logging
    stdout_logging = False
    for path in ctx.files:
        if path.suffix == ".py":
            content = ctx.read(path)
            if content and ("logging.basicConfig" in content or "stream=sys.stdout" in content or "StreamHandler" in content):
                stdout_logging = True
                rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
                findings.append(
                    Finding(
                        id="OK-001",
                        category=Category.CONFIG,
                        severity=Severity.INFO,
                        title="Positive: stdout logging configured",
                        description="Application logs to stdout (compatible with CloudWatch/Fluent Bit)",
                        file=str(rel_path),
                        line=None,
                        evidence="logging.basicConfig or StreamHandler found",
                        remediation="Good practice - no action needed",
                        eks_hint="stdout + CloudWatch/Fluent Bit",
                    )
                )
                break

    # Check for environment variable config
    env_config = False
    for path in ctx.files:
        if path.suffix == ".py":
            content = ctx.read(path)
            if content and ("os.getenv" in content or "os.environ" in content or "dotenv" in content):
                env_config = True
                rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
                findings.append(
                    Finding(
                        id="OK-001",
                        category=Category.CONFIG,
                        severity=Severity.INFO,
                        title="Positive: environment variable configuration used",
                        description="Application uses environment variables for configuration (12-factor)",
                        file=str(rel_path),
                        line=None,
                        evidence="os.getenv or os.environ usage found",
                        remediation="Good practice - no action needed",
                        eks_hint="ConfigMap / env",
                    )
                )
                break

    # Check for health endpoint
    health_endpoint = False
    for path in ctx.files:
        if path.suffix == ".py":
            content = ctx.read(path)
            if content and any(p in content for p in ["/healthz", "/health", "/ready", "def healthz", "def health", "def ready"]):
                health_endpoint = True
                rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
                findings.append(
                    Finding(
                        id="OK-001",
                        category=Category.CONFIG,
                        severity=Severity.INFO,
                        title="Positive: health endpoint present",
                        description="Application has /healthz, /health, or /ready endpoint",
                        file=str(rel_path),
                        line=None,
                        evidence="Health endpoint found in code",
                        remediation="Good practice - no action needed",
                        eks_hint="Liveness/readiness probes",
                    )
                )
                break

    # Check for non-root user in Dockerfile
    non_root = False
    for path in ctx.files:
        if path.name.lower() == "dockerfile":
            content = ctx.read(path)
            if content and re.search(r'^\s*USER\s+\w+', content, re.MULTILINE | re.IGNORECASE):
                non_root = True
                rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
                findings.append(
                    Finding(
                        id="OK-001",
                        category=Category.CONFIG,
                        severity=Severity.INFO,
                        title="Positive: non-root user in Dockerfile",
                        description="Dockerfile specifies non-root USER directive",
                        file=str(rel_path),
                        line=None,
                        evidence="USER directive found",
                        remediation="Good practice - no action needed",
                        eks_hint="runAsNonRoot",
                    )
                )
                break

    # Check for HEALTHCHECK in Dockerfile
    healthcheck = False
    for path in ctx.files:
        if path.name.lower() == "dockerfile":
            content = ctx.read(path)
            if content and re.search(r'^\s*HEALTHCHECK', content, re.MULTILINE | re.IGNORECASE):
                healthcheck = True
                rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
                findings.append(
                    Finding(
                        id="OK-001",
                        category=Category.CONFIG,
                        severity=Severity.INFO,
                        title="Positive: HEALTHCHECK in Dockerfile",
                        description="Dockerfile includes HEALTHCHECK directive",
                        file=str(rel_path),
                        line=None,
                        evidence="HEALTHCHECK directive found",
                        remediation="Good practice - no action needed",
                        eks_hint="Liveness/readiness probes",
                    )
                )
                break

    # Check for pinned image tag
    pinned_tag = False
    for path in ctx.files:
        if path.name.lower() == "dockerfile":
            content = ctx.read(path)
            if content and re.search(r'^\s*FROM\s+\S+:\d', content, re.MULTILINE | re.IGNORECASE):
                pinned_tag = True
                rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
                findings.append(
                    Finding(
                        id="OK-001",
                        category=Category.CONFIG,
                        severity=Severity.INFO,
                        title="Positive: pinned image tag in Dockerfile",
                        description="Dockerfile uses pinned base image tag",
                        file=str(rel_path),
                        line=None,
                        evidence="FROM with version tag found",
                        remediation="Good practice - no action needed",
                        eks_hint="Pinned image tags",
                    )
                )
                break

    return findings
