from __future__ import annotations

import re

from assessor.models import Category, Finding, Severity
from assessor.scanner.registry import ScanContext, is_documentation, rule


@rule("LOG-001", Category.LOGGING, Severity.MEDIUM)
def check_file_logging(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    patterns = [
        (re.compile(r'FileHandler\s*\('), "FileHandler"),
        (re.compile(r'logging\.FileHandler'), "logging.FileHandler"),
        (re.compile(r'RotatingFileHandler'), "RotatingFileHandler"),
        (re.compile(r'TimedRotatingFileHandler'), "TimedRotatingFileHandler"),
        (re.compile(r'/var/log'), "/var/log path"),
        (re.compile(r'open\s*\(\s*["\'][^"\']*/var/log[^"\']*["\']'), "open on /var/log"),
        (re.compile(r'open\s*\(\s*["\'][^"\']*\.log["\']\s*,\s*["\']a'), "append to .log file"),
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
                            id="LOG-001",
                            category=Category.LOGGING,
                            severity=Severity.MEDIUM,
                            title="Logging to file instead of stdout",
                            description=f"Application logs to file ({desc}) instead of stdout",
                            file=str(rel_path),
                            line=i,
                            evidence=line.strip()[:200],
                            remediation="Log to stdout/stderr; use CloudWatch agent or Fluent Bit for log aggregation in EKS",
                            eks_hint="stdout + CloudWatch/Fluent Bit",
                        )
                    )
    return findings
