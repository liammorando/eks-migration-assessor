#!/usr/bin/env python3
"""
Generate rules documentation from the scanner registry.
Outputs to docs/rules.md
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from assessor.models import Category, Severity
from assessor.scanner.registry import _rules

# Mapping of rule_id to human-readable title and description
RULE_METADATA = {
    # State rules
    "STATE-001": {
        "title": "Local filesystem writes detected",
        "description": "Application writes to local filesystem (e.g., open() with write mode, os.makedirs on absolute paths) which is ephemeral in Kubernetes.",
        "category": Category.STATE,
        "severity": Severity.HIGH,
    },
    "STATE-002": {
        "title": "In-memory session/state storage",
        "description": "Application stores session or state in memory (module-level dicts, Flask session without external store) which is not shared across pods.",
        "category": Category.STATE,
        "severity": Severity.HIGH,
    },
    "STATE-003": {
        "title": "SQLite or local database file",
        "description": "Application uses SQLite or local database files which don't work in distributed Kubernetes environments.",
        "category": Category.STATE,
        "severity": Severity.HIGH,
    },

    # Config rules
    "CFG-001": {
        "title": "Hardcoded secrets",
        "description": "Hardcoded secrets, passwords, API keys, or AWS credentials in source code.",
        "category": Category.CONFIG,
        "severity": Severity.CRITICAL,
    },
    "CFG-002": {
        "title": "No environment variable configuration",
        "description": "Application doesn't use environment variables for configuration (12-factor app violation).",
        "category": Category.CONFIG,
        "severity": Severity.MEDIUM,
    },

    # Network rules
    "NET-001": {
        "title": "Hardcoded IP addresses or localhost",
        "description": "Application uses hardcoded localhost, 127.0.0.1, or private IP addresses (10.x, 172.16-31.x, 192.168.x) which won't work in Kubernetes.",
        "category": Category.NETWORKING,
        "severity": Severity.MEDIUM,
    },
    "NET-002": {
        "title": "Hardcoded ports without env override",
        "description": "Application uses hardcoded port numbers without environment variable override.",
        "category": Category.NETWORKING,
        "severity": Severity.LOW,
    },

    # Container rules
    "CTR-001": {
        "title": "No Dockerfile",
        "description": "Project has no Dockerfile, cannot be containerized for Kubernetes.",
        "category": Category.CONTAINER,
        "severity": Severity.HIGH,
    },
    "CTR-002": {
        "title": "Dockerfile runs as root",
        "description": "Dockerfile doesn't specify a non-root USER; container runs as root.",
        "category": Category.CONTAINER,
        "severity": Severity.MEDIUM,
    },
    "CTR-003": {
        "title": "Dockerfile uses :latest tag",
        "description": "Dockerfile uses :latest tag or no tag, making builds non-reproducible.",
        "category": Category.CONTAINER,
        "severity": Severity.MEDIUM,
    },
    "CTR-004": {
        "title": "No health check endpoint",
        "description": "No HEALTHCHECK in Dockerfile and no /health, /healthz, or /ready endpoint in application code.",
        "category": Category.CONTAINER,
        "severity": Severity.MEDIUM,
    },

    # Logging rules
    "LOG-001": {
        "title": "Logging to files instead of stdout",
        "description": "Application logs to files (FileHandler, /var/log) instead of stdout, preventing log aggregation.",
        "category": Category.LOGGING,
        "severity": Severity.MEDIUM,
    },

    # Lifecycle rules
    "LIFE-001": {
        "title": "No SIGTERM/graceful shutdown handling",
        "description": "Application doesn't handle SIGTERM for graceful shutdown, causing abrupt termination.",
        "category": Category.LIFECYCLE,
        "severity": Severity.LOW,
    },

    # Compose rules
    "CMP-001": {
        "title": "Host bind mounts in docker-compose",
        "description": "docker-compose.yml uses host bind mounts (absolute host paths) which are not portable to Kubernetes.",
        "category": Category.CONTAINER,
        "severity": Severity.HIGH,
    },
    "CMP-002": {
        "title": "Privileged or host network mode in docker-compose",
        "description": "docker-compose.yml uses privileged: true or network_mode: host, which are not allowed in Kubernetes.",
        "category": Category.CONTAINER,
        "severity": Severity.CRITICAL,
    },
    "CMP-003": {
        "title": "Fixed container_name or depends_on for startup ordering",
        "description": "docker-compose.yml uses fixed container_name or depends_on for startup ordering, which don't translate to Kubernetes.",
        "category": Category.CONTAINER,
        "severity": Severity.LOW,
    },
    "CMP-004": {
        "title": "Missing Dockerfile for build context",
        "description": "docker-compose.yml references build: context but no Dockerfile exists there.",
        "category": Category.CONTAINER,
        "severity": Severity.HIGH,
    },

    # Positive rules (OK-001)
    "OK-001": {
        "title": "Positive practice detected",
        "description": "Good practice found: stdout logging, env config, health endpoint, non-root user, HEALTHCHECK, or pinned tag.",
        "category": Category.CONFIG,
        "severity": Severity.INFO,
    },
}


def severity_badge(severity: Severity) -> str:
    """Return a markdown badge for the severity."""
    colors = {
        Severity.CRITICAL: "🔴",
        Severity.HIGH: "🟠",
        Severity.MEDIUM: "🟡",
        Severity.LOW: "🟢",
        Severity.INFO: "🔵",
    }
    return f"{colors.get(severity, '⚪')} {severity.value.upper()}"


def category_badge(category: Category) -> str:
    """Return a markdown badge for the category."""
    return f"`{category.value}`"


def generate_rules_doc() -> str:
    """Generate the rules documentation in markdown format."""
    lines = [
        "# EKS Migration Assessor - Rule Catalog",
        "",
        "This document lists all detection rules used by the EKS Migration Assessor.",
        "Rules are organized by category and include severity, description, and EKS remediation hints.",
        "",
        "## Documentation File Handling",
        "",
        "The scanner treats certain files as **documentation** and applies special handling:",
        "",
        "- **Code-pattern rules** (STATE-001, STATE-002, STATE-003, NET-001, NET-002, LOG-001, LIFE-001) **skip** documentation files entirely to avoid false positives from examples, SQL snippets, or configuration examples in docs.",
        "- **Secret detection (CFG-001)** still runs on documentation files but **downgrades severity by one level** (e.g., CRITICAL → HIGH) since secrets in docs are often placeholders or examples.",
        "",
        "Files considered documentation:",
        "- Any file with extension `.md`, `.rst`, `.txt`",
        "- Any file under `docs/`, `doc/`, `examples/`, or `samples/` directories (case-insensitive)",
        "- Special files: `CHANGELOG*`, `LICENSE*`, `NOTICE*`, `README*`, `CONTRIBUTING*`, `AUTHORS*`, `HISTORY*`, `NEWS*`, `CHANGES*`, `TODO*`, `COPYING*` (case-insensitive, with or without extension)",
        "",
        "## Rule Summary",
        "",
        "| ID | Severity | Category | Title |",
        "|----|----------|----------|-------|",
    ]

    # Sort rules by category then ID
    sorted_rules = sorted(_rules.keys())

    for rule_id in sorted_rules:
        fn, category, severity_default = _rules[rule_id]
        meta = RULE_METADATA.get(rule_id, {})
        title = meta.get("title", "Unknown")
        severity = meta.get("severity", Severity(severity_default))
        category = meta.get("category", Category(category))

        lines.append(f"| {rule_id} | {severity_badge(severity)} | {category_badge(category)} | {title} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed rule descriptions
    lines.append("## Detailed Rule Descriptions")
    lines.append("")

    for rule_id in sorted_rules:
        fn, category, severity_default = _rules[rule_id]
        meta = RULE_METADATA.get(rule_id, {})
        title = meta.get("title", "Unknown")
        description = meta.get("description", "No description available.")
        severity = meta.get("severity", Severity(severity_default))
        category = meta.get("category", Category(category))

        lines.append(f"### {rule_id}: {title}")
        lines.append("")
        lines.append(f"**Severity:** {severity_badge(severity)}  ")
        lines.append(f"**Category:** {category_badge(category)}  ")
        lines.append("")
        lines.append(description)
        lines.append("")

        # Add EKS hint if available
        eks_hints = {
            "STATE-001": "Use PVC with EBS CSI Driver, or S3 for object storage",
            "STATE-002": "Use Redis/ElastiCache or DynamoDB for session storage; run stateless pods",
            "STATE-003": "Use RDS (PostgreSQL/MySQL) or a StatefulSet with PVC",
            "CFG-001": "Use AWS Secrets Manager with Pod Identity, or Kubernetes Secrets; never commit secrets to code",
            "CFG-002": "Use environment variables for configuration (12-factor); use ConfigMap in Kubernetes",
            "NET-001": "Use Kubernetes Service DNS names (e.g., service-name.namespace.svc.cluster.local)",
            "NET-002": "Use environment variable for port (e.g., PORT=8080); Kubernetes injects container port via Service",
            "CTR-001": "Create a Dockerfile to containerize the application",
            "CTR-002": "Add USER directive in Dockerfile; use runAsNonRoot: true in pod securityContext",
            "CTR-003": "Use pinned image tags (e.g., python:3.12-slim) for reproducible builds",
            "CTR-004": "Add HEALTHCHECK to Dockerfile and implement /healthz and /ready endpoints in application; configure livenessProbe and readinessProbe in deployment",
            "LOG-001": "Log to stdout/stderr; use CloudWatch agent or Fluent Bit for log aggregation in EKS",
            "LIFE-001": "Add signal handler for SIGTERM; set terminationGracePeriodSeconds in pod spec",
            "CMP-001": "Replace host bind mounts with PVC volumes in Kubernetes",
            "CMP-002": "Remove privileged: true; use securityContext with specific capabilities if needed; remove network_mode: host",
            "CMP-003": "Remove container_name; use initContainers or readiness probes for startup ordering",
            "CMP-004": "Create Dockerfile in the build context or fix the build path",
            "OK-001": "Good practice - no action needed",
        }

        hint = eks_hints.get(rule_id)
        if hint:
            lines.append(f"**EKS Remediation:** {hint}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    output_dir = Path(__file__).parent.parent / "docs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "rules.md"
    content = generate_rules_doc()

    output_file.write_text(content, encoding="utf-8")
    print(f"Generated {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
