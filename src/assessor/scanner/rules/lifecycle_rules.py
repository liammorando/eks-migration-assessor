from __future__ import annotations

import re

from assessor.models import Category, Finding, Severity
from assessor.scanner.registry import ScanContext, is_documentation, rule


@rule("LIFE-001", Category.LIFECYCLE, Severity.LOW)
def check_no_sigterm_handling(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    patterns = [
        re.compile(r'signal\.signal\s*\(\s*signal\.SIGTERM'),
        re.compile(r'signal\.signal\s*\(\s*signal\.SIGINT'),
        re.compile(r'def\s+handle_shutdown'),
        re.compile(r'def\s+graceful_shutdown'),
        re.compile(r'def\s+sigterm_handler'),
        re.compile(r'shutdown_event'),
        re.compile(r'atexit\.register'),
    ]
    for path in ctx.files:
        if path.suffix != ".py" or is_documentation(path):
            continue
        content = ctx.read(path)
        if not content:
            continue
        has_handler = any(p.search(content) for p in patterns)
        if not has_handler:
            rel_path = path.relative_to(ctx.root) if path.is_relative_to(ctx.root) else path
            findings.append(
                Finding(
                    id="LIFE-001",
                    category=Category.LIFECYCLE,
                    severity=Severity.LOW,
                    title="No SIGTERM/graceful shutdown handling",
                    description="Application does not handle SIGTERM for graceful shutdown",
                    file=str(rel_path),
                    line=1,
                    evidence="No signal.signal(SIGTERM) or shutdown handler found",
                    remediation="Add signal handler for SIGTERM; set terminationGracePeriodSeconds in pod spec",
                    eks_hint="terminationGracePeriodSeconds",
                )
            )
            break  # Only report once per project
    return findings
