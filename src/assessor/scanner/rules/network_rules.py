from __future__ import annotations

import re

from assessor.models import Category, Finding, Severity
from assessor.scanner.registry import ScanContext, is_documentation, rule


@rule("NET-001", Category.NETWORKING, Severity.MEDIUM)
def check_hardcoded_ips(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    patterns = [
        (re.compile(r'\b(?:localhost|127\.0\.0\.1)\b'), "localhost/127.0.0.1"),
        (re.compile(r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), "10.x.x.x private IP"),
        (re.compile(r'\b172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}\b'), "172.16-31.x.x private IP"),
        (re.compile(r'\b192\.168\.\d{1,3}\.\d{1,3}\b'), "192.168.x.x private IP"),
    ]
    for path in ctx.files:
        if is_documentation(path):
            continue
        content = ctx.read(path)
        if not content:
            continue
        rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
        for i, line in enumerate(content.splitlines(), 1):
            for pattern, desc in patterns:
                if pattern.search(line):
                    findings.append(
                        Finding(
                            id="NET-001",
                            category=Category.NETWORKING,
                            severity=Severity.MEDIUM,
                            title="Hardcoded IP address or localhost",
                            description=f"Code references {desc} which won't work in Kubernetes",
                            file=str(rel_path),
                            line=i,
                            evidence=line.strip()[:200],
                            remediation="Use Kubernetes Service DNS names (e.g., service-name.namespace.svc.cluster.local)",
                            eks_hint="Kubernetes Service DNS names",
                        )
                    )
    return findings


@rule("NET-002", Category.NETWORKING, Severity.LOW)
def check_hardcoded_ports(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    patterns = [
        (re.compile(r'(?:port|PORT)\s*[=:]\s*\d{2,5}'), "hardcoded port"),
        (re.compile(r'(?:listen|bind)\s*[:=]\s*["\']?\d{2,5}'), "hardcoded listen port"),
    ]
    for path in ctx.files:
        if is_documentation(path):
            continue
        content = ctx.read(path)
        if not content:
            continue
        has_env_port = bool(re.search(r'os\.getenv\s*\(\s*["\']PORT', content)) or bool(re.search(r'os\.environ\s*\[\s*["\']PORT', content))
        rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
        for i, line in enumerate(content.splitlines(), 1):
            for pattern, desc in patterns:
                if pattern.search(line) and not has_env_port:
                    findings.append(
                        Finding(
                            id="NET-002",
                            category=Category.NETWORKING,
                            severity=Severity.LOW,
                            title="Hardcoded port without environment variable override",
                            description=f"Port is hardcoded ({desc}) without env var override",
                            file=str(rel_path),
                            line=i,
                            evidence=line.strip()[:200],
                            remediation="Use environment variable for port (e.g., PORT=8080); Kubernetes injects container port via Service",
                            eks_hint="Container port + Service",
                        )
                    )
    return findings
