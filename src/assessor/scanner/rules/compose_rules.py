from __future__ import annotations

import yaml

from assessor.models import Category, Finding, Severity
from assessor.scanner.registry import ScanContext, rule


def _load_compose(ctx: ScanContext) -> dict | None:
    for path in ctx.files:
        if path.name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
            try:
                content = ctx.read(path)
                if content:
                    return yaml.safe_load(content)
            except Exception:
                pass
    return None


def _check_file_exists(ctx: ScanContext, build_context: str) -> bool:
    context_path = ctx.root / build_context
    if not context_path.exists():
        return False
    for path in ctx.files:
        full_path = context_path / path
        if full_path.exists() and path.name.lower() == "dockerfile":
            return True
    return False


@rule("CMP-001", Category.CONTAINER, Severity.HIGH)
def check_compose_host_binds(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    compose = _load_compose(ctx)
    if not compose:
        return findings
    services = compose.get("services", {})
    for svc_name, svc_config in services.items():
        volumes = svc_config.get("volumes", [])
        for vol in volumes:
            if isinstance(vol, str):
                parts = vol.split(":")
                if len(parts) >= 1 and parts[0].startswith("/"):
                    findings.append(
                        Finding(
                            id="CMP-001",
                            category=Category.CONTAINER,
                            severity=Severity.HIGH,
                            title="Host bind mount in docker-compose",
                            description=f"Service '{svc_name}' uses host bind mount '{parts[0]}' which is not portable to Kubernetes",
                            file="docker-compose.yml",
                            line=None,
                            evidence=vol[:200],
                            remediation="Replace host bind mounts with PVC volumes in Kubernetes",
                            eks_hint="PVC",
                        )
                    )
    return findings


@rule("CMP-002", Category.CONTAINER, Severity.CRITICAL)
def check_compose_privileged_network(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    compose = _load_compose(ctx)
    if not compose:
        return findings
    services = compose.get("services", {})
    for svc_name, svc_config in services.items():
        if svc_config.get("privileged") is True:
            findings.append(
                Finding(
                    id="CMP-002",
                    category=Category.CONTAINER,
                    severity=Severity.CRITICAL,
                    title="Privileged mode in docker-compose",
                    description=f"Service '{svc_name}' runs in privileged mode",
                    file="docker-compose.yml",
                    line=None,
                    evidence="privileged: true",
                    remediation="Remove privileged: true; use securityContext with specific capabilities if needed",
                    eks_hint="Remove; use securityContext / Services",
                )
            )
        if svc_config.get("network_mode") == "host":
            findings.append(
                Finding(
                    id="CMP-002",
                    category=Category.CONTAINER,
                    severity=Severity.CRITICAL,
                    title="Host network mode in docker-compose",
                    description=f"Service '{svc_name}' uses network_mode: host",
                    file="docker-compose.yml",
                    line=None,
                    evidence="network_mode: host",
                    remediation="Remove network_mode: host; use Kubernetes Services for networking",
                    eks_hint="Remove; use securityContext / Services",
                )
            )
    return findings


@rule("CMP-003", Category.CONTAINER, Severity.LOW)
def check_compose_fixed_name_depends_on(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    compose = _load_compose(ctx)
    if not compose:
        return findings
    services = compose.get("services", {})
    for svc_name, svc_config in services.items():
        if svc_config.get("container_name"):
            findings.append(
                Finding(
                    id="CMP-003",
                    category=Category.CONTAINER,
                    severity=Severity.LOW,
                    title="Fixed container_name in docker-compose",
                    description=f"Service '{svc_name}' has fixed container_name which prevents scaling",
                    file="docker-compose.yml",
                    line=None,
                    evidence=f"container_name: {svc_config['container_name']}",
                    remediation="Remove container_name; use initContainers or readiness probes for startup ordering",
                    eks_hint="initContainers/readiness probes",
                )
            )
        depends_on = svc_config.get("depends_on", {})
        if depends_on and not isinstance(depends_on, list):
            findings.append(
                Finding(
                    id="CMP-003",
                    category=Category.CONTAINER,
                    severity=Severity.LOW,
                    title="depends_on used for startup ordering",
                    description=f"Service '{svc_name}' uses depends_on with conditions (not supported in Kubernetes)",
                    file="docker-compose.yml",
                    line=None,
                    evidence=str(depends_on)[:200],
                    remediation="Use initContainers or readiness probes for startup ordering in Kubernetes",
                    eks_hint="initContainers/readiness probes",
                )
            )
    return findings


@rule("CMP-004", Category.CONTAINER, Severity.HIGH)
def check_compose_missing_dockerfile(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    compose = _load_compose(ctx)
    if not compose:
        return findings
    services = compose.get("services", {})
    for svc_name, svc_config in services.items():
        build = svc_config.get("build")
        if build:
            if isinstance(build, str):
                context = build
            elif isinstance(build, dict):
                context = build.get("context", ".")
            else:
                context = "."
            if not _check_file_exists(ctx, context):
                findings.append(
                    Finding(
                        id="CMP-004",
                        category=Category.CONTAINER,
                        severity=Severity.HIGH,
                        title="Compose service build points to missing Dockerfile",
                        description=f"Service '{svc_name}' has build context '{context}' but no Dockerfile exists there",
                        file="docker-compose.yml",
                        line=None,
                        evidence=f"build: {context}",
                        remediation="Create Dockerfile in the build context or fix the build path",
                        eks_hint="Fix the build context",
                    )
                )
    return findings
