from __future__ import annotations

import re

from assessor.models import Category, Finding, Severity
from assessor.scanner.registry import (
    ScanContext,
    is_documentation,
    is_test_or_example,
    mask_value,
    rule,
)


@rule("CFG-001", Category.CONFIG, Severity.CRITICAL)
def check_hardcoded_secrets(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    patterns = [
        (re.compile(r'(?:password|passwd|pwd)\s*[=:]\s*["\']([^"\']{3,})["\']', re.IGNORECASE), "password"),
        (re.compile(r'(?:secret[_-]?key|secret_key)\s*[=:]\s*["\']([^"\']{3,})["\']', re.IGNORECASE), "secret_key"),
        (re.compile(r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']([^"\']{10,})["\']', re.IGNORECASE), "api_key"),
        (re.compile(r'(?:access[_-]?key|accesskey)\s*[=:]\s*["\']([^"\']{10,})["\']', re.IGNORECASE), "access_key"),
        (re.compile(r'(?:token)\s*[=:]\s*["\']([^"\']{10,})["\']', re.IGNORECASE), "token"),
        (re.compile(r'(AKIA[0-9A-Z]{16})'), "AWS access key ID"),
        (re.compile(r'(?:private[_-]?key|privatekey)\s*[=:]\s*["\']([^"\']{10,})["\']', re.IGNORECASE), "private_key"),
        (re.compile(r'(-----BEGIN (?:RSA |EC )?PRIVATE KEY-----)'), "private key block"),
    ]
    for path in ctx.files:
        content = ctx.read(path)
        if not content:
            continue
        rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
        is_doc = is_documentation(path)
        is_test = is_test_or_example(path)
        for i, line in enumerate(content.splitlines(), 1):
            for pattern, desc in patterns:
                match = pattern.search(line)
                if match:
                    masked_evidence = mask_value(line)
                    # Determine severity: downgrade for docs or test files
                    if is_doc or is_test:
                        severity = Severity.HIGH
                    else:
                        severity = Severity.CRITICAL
                    # Add suffix for test/example files
                    title = "Hardcoded secret detected"
                    if is_test:
                        title += " (test/example file)"
                    findings.append(
                        Finding(
                            id="CFG-001",
                            category=Category.CONFIG,
                            severity=severity,
                            title=title,
                            description=f"Possible hardcoded {desc} in source code",
                            file=str(rel_path),
                            line=i,
                            evidence=masked_evidence.strip()[:200],
                            remediation="Use AWS Secrets Manager with Pod Identity, or Kubernetes Secrets; never commit secrets to code",
                            eks_hint="Secrets Manager + Pod Identity, or K8s Secret",
                        )
                    )
    return findings


@rule("CFG-002", Category.CONFIG, Severity.MEDIUM)
def check_no_env_config(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    env_patterns = [
        re.compile(r'os\.getenv\s*\('),
        re.compile(r'os\.environ\.get\s*\('),
        re.compile(r'os\.environ\s*\['),
        re.compile(r'from\s+os\s+import\s+.*environ'),
        re.compile(r'from\s+os\s+import\s+.*getenv'),
        re.compile(r'from\s+dotenv\s+import'),
        re.compile(r'config\s*=\s*\{.*\}'),  # inline dict config
    ]
    # Check project-wide: does ANY file use env vars?
    has_env_usage = False
    for path in ctx.files:
        content = ctx.read(path)
        if not content:
            continue
        if any(p.search(content) for p in env_patterns):
            has_env_usage = True
            break

    if not has_env_usage:
        # Report only once, on the first relevant file
        for path in ctx.files:
            content = ctx.read(path)
            if not content:
                continue
            if path.suffix in (".py", ".js", ".ts", ".go", ".java", ".rb"):
                rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
                findings.append(
                    Finding(
                        id="CFG-002",
                        category=Category.CONFIG,
                        severity=Severity.MEDIUM,
                        title="No environment variable configuration detected",
                        description="Application appears to not use environment variables for configuration",
                        file=str(rel_path),
                        line=1,
                        evidence="No os.getenv, os.environ, or dotenv usage found in any file",
                        remediation="Use environment variables for configuration (12-factor); use ConfigMap in Kubernetes",
                        eks_hint="ConfigMap / env",
                    )
                )
                break  # Only report once per project
    return findings
