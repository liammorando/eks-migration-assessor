from __future__ import annotations

import re

from assessor.models import Category, Finding, Severity
from assessor.scanner.registry import ScanContext, is_documentation, rule


@rule("STATE-001", Category.STATE, Severity.HIGH)
def check_local_writes(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    patterns = [
        (re.compile(r'open\s*\(\s*["\'][^"\']*(?:/var/data|/tmp)[^"\']*["\']\s*,\s*["\']w'), "write to persistent local path"),
        (re.compile(r'open\s*\(\s*["\'][^"\']*["\']\s*,\s*["\']w'), "file write"),
        (re.compile(r'os\.makedirs\s*\(\s*["\'][/][^"\']*["\']'), "makedirs on absolute path"),
        (re.compile(r'os\.makedirs\s*\(\s*\w+\s*,\s*exist_ok\s*=\s*True'), "makedirs on variable path with exist_ok"),
        (re.compile(r'pathlib.*mkdir.*parents.*True'), "mkdir with parents on absolute path"),
        (re.compile(r'shutil\.(copy|move)\s*\([^)]*["\'][/][^"\']*["\']'), "copy/move to absolute path"),
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
                            id="STATE-001",
                            category=Category.STATE,
                            severity=Severity.HIGH,
                            title="Local filesystem write detected",
                            description=f"Code writes to local filesystem ({desc})",
                            file=str(rel_path),
                            line=i,
                            evidence=line.strip()[:200],
                            remediation="Use PVC with EBS CSI Driver for persistent storage, or use S3 for object storage",
                            eks_hint="PVC with EBS CSI Driver, or S3",
                        )
                    )
    return findings


@rule("STATE-002", Category.STATE, Severity.HIGH)
def check_in_memory_state(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    patterns = [
        (re.compile(r'(?:^|\s)SESSIONS\s*=\s*\{'), "module-level dict for sessions"),
        (re.compile(r'(?:^|\s)sessions\s*=\s*\{'), "module-level dict for sessions"),
        (re.compile(r'(?:^|\s)SESSION_STORE\s*=\s*\{'), "module-level dict for session store"),
        (re.compile(r'session\s*\[.*\]\s*='), "direct session dict assignment"),
        (re.compile(r'flask\.session\s*\[.*\]\s*='), "Flask session used without external store"),
        (re.compile(r'from\s+flask\s+import\s+.*session'), "Flask session import (check for external store)"),
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
                            id="STATE-002",
                            category=Category.STATE,
                            severity=Severity.HIGH,
                            title="In-memory session/state storage detected",
                            description=f"Application uses in-memory storage for sessions ({desc})",
                            file=str(rel_path),
                            line=i,
                            evidence=line.strip()[:200],
                            remediation="Use Redis/ElastiCache or DynamoDB for session storage; run stateless pods",
                            eks_hint="Redis/ElastiCache, stateless pods",
                        )
                    )
    return findings


@rule("STATE-003", Category.STATE, Severity.HIGH)
def check_sqlite_local_db(ctx: ScanContext) -> list[Finding]:
    findings: list[Finding] = []
    patterns = [
        (re.compile(r'sqlite3', re.IGNORECASE), "sqlite3 import"),
        (re.compile(r'\.db["\']', re.IGNORECASE), "database file reference"),
        (re.compile(r'\.sqlite', re.IGNORECASE), "sqlite file reference"),
        (re.compile(r'sqlite://', re.IGNORECASE), "sqlite connection string"),
        (re.compile(r'CREATE TABLE', re.IGNORECASE), "SQL DDL in code"),
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
                            id="STATE-003",
                            category=Category.STATE,
                            severity=Severity.HIGH,
                            title="SQLite or local database file detected",
                            description=f"Application uses local database ({desc})",
                            file=str(rel_path),
                            line=i,
                            evidence=line.strip()[:200],
                            remediation="Use RDS (PostgreSQL/MySQL) or a StatefulSet with PVC for persistent databases",
                            eks_hint="RDS or StatefulSet with PVC",
                        )
                    )
    return findings
