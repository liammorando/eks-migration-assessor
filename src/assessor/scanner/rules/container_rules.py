from __future__ import annotations

import re

from assessor.models import Category, Finding, Severity
from assessor.scanner.registry import ScanContext, rule


@rule("CTR-001", Category.CONTAINER, Severity.HIGH)
def check_no_dockerfile(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    has_dockerfile = any(path.name.lower() == "dockerfile" for path in ctx.files)
    if not has_dockerfile:
        findings.append(
            Finding(
                id="CTR-001",
                category=Category.CONTAINER,
                severity=Severity.HIGH,
                title="No Dockerfile found",
                description="Project has no Dockerfile; cannot containerize for Kubernetes",
                file=None,
                line=None,
                evidence="No Dockerfile in repository root",
                remediation="Create a Dockerfile to containerize the application",
                eks_hint="Containerize first",
            )
        )
    return findings


@rule("CTR-002", Category.CONTAINER, Severity.MEDIUM)
def check_dockerfile_no_user(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    for path in ctx.files:
        if path.name.lower() != "dockerfile":
            continue
        content = ctx.read(path)
        if not content:
            continue
        rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
        has_user = bool(re.search(r'^\s*USER\s+\w+', content, re.MULTILINE | re.IGNORECASE))
        if not has_user:
            findings.append(
                Finding(
                    id="CTR-002",
                    category=Category.CONTAINER,
                    severity=Severity.MEDIUM,
                    title="Dockerfile runs as root (no USER directive)",
                    description="Dockerfile does not specify a non-root USER; container runs as root",
                    file=str(rel_path),
                    line=1,
                    evidence="No USER directive found",
                    remediation="Add USER directive in Dockerfile; use runAsNonRoot: true in pod securityContext",
                    eks_hint="runAsNonRoot",
                )
            )
    return findings


@rule("CTR-003", Category.CONTAINER, Severity.MEDIUM)
def check_dockerfile_latest_tag(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    for path in ctx.files:
        if path.name.lower() != "dockerfile":
            continue
        content = ctx.read(path)
        if not content:
            continue
        rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(r'^\s*FROM\s+\S+:\s*latest\s*', line, re.IGNORECASE):
                findings.append(
                    Finding(
                        id="CTR-003",
                        category=Category.CONTAINER,
                        severity=Severity.MEDIUM,
                        title="Dockerfile uses :latest tag",
                        description="Base image uses :latest tag which is not reproducible",
                        file=str(rel_path),
                        line=i,
                        evidence=line.strip()[:200],
                        remediation="Use pinned image tags (e.g., python:3.12-slim) for reproducible builds",
                        eks_hint="Pinned image tags",
                    )
                )
            elif re.search(r'^\s*FROM\s+[^:\s]+$', line, re.IGNORECASE) and not re.search(r':\d', line):
                findings.append(
                    Finding(
                        id="CTR-003",
                        category=Category.CONTAINER,
                        severity=Severity.MEDIUM,
                        title="Dockerfile uses base image without tag",
                        description="Base image has no tag; defaults to :latest",
                        file=str(rel_path),
                        line=i,
                        evidence=line.strip()[:200],
                        remediation="Use pinned image tags (e.g., python:3.12-slim) for reproducible builds",
                        eks_hint="Pinned image tags",
                    )
                )
    return findings


@rule("CTR-004", Category.CONTAINER, Severity.MEDIUM)
def check_no_healthcheck(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    health_endpoint_patterns = [
        re.compile(r'@app\.route\s*\(\s*["\']/health'),
        re.compile(r'@app\.route\s*\(\s*["\']/healthz'),
        re.compile(r'@app\.route\s*\(\s*["\']/ready'),
        re.compile(r'def\s+healthz'),
        re.compile(r'def\s+health'),
        re.compile(r'def\s+ready'),
    ]
    for path in ctx.files:
        if path.name.lower() != "dockerfile":
            continue
        content = ctx.read(path)
        if not content:
            continue
        rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
        has_healthcheck = bool(re.search(r'^\s*HEALTHCHECK', content, re.MULTILINE | re.IGNORECASE))
        if not has_healthcheck:
            # Check if app has health endpoint
            has_health_endpoint = False
            for p in ctx.files:
                if p.suffix == ".py":
                    app_content = ctx.read(p)
                    if any(pat.search(app_content) for pat in health_endpoint_patterns):
                        has_health_endpoint = True
                        break
            if not has_health_endpoint:
                findings.append(
                    Finding(
                        id="CTR-004",
                        category=Category.CONTAINER,
                        severity=Severity.MEDIUM,
                        title="No HEALTHCHECK in Dockerfile and no health endpoint in code",
                        description="Container has no health check; Kubernetes cannot verify liveness/readiness",
                        file=str(rel_path),
                        line=1,
                        evidence="No HEALTHCHECK directive and no /health, /healthz, or /ready endpoint found",
                        remediation="Add HEALTHCHECK to Dockerfile and implement /healthz and /ready endpoints in application",
                        eks_hint="Liveness/readiness probes",
                    )
                )
    return findings
