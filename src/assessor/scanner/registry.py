from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from assessor.models import Finding


def is_documentation(path: Path) -> bool:
    """Return True if the file path indicates a documentation file."""
    name = path.name.lower()
    parts = [p.lower() for p in path.parts]

    # Check for documentation directories
    doc_dirs = {"docs", "doc", "examples", "samples"}
    if any(p in doc_dirs for p in parts):
        return True

    # Check for documentation file extensions
    doc_extensions = {".md", ".rst", ".txt"}
    if path.suffix.lower() in doc_extensions:
        return True

    # Check for special documentation files (case-insensitive)
    special_files = {
        "changelog",
        "license",
        "notice",
        "readme",
        "contributing",
        "authors",
        "history",
        "news",
        "changes",
        "todo",
        "copying",
    }
    if name in special_files or any(name.startswith(s + ".") for s in special_files):
        return True

    return False


def is_test_or_example(path: Path) -> bool:
    """Return True if the file path indicates a test or example file."""
    name = path.name.lower()
    parts = [p.lower() for p in path.parts]

    # Check for test/example directories
    test_dirs = {"tests", "test", "fixtures", "examples", "samples"}
    if any(p in test_dirs for p in parts):
        return True

    # Check for test file patterns
    test_patterns = [
        "conftest.py",
        "test_",
        "_test.py",
    ]
    if any(name == p or name.startswith(p) for p in test_patterns):
        return True

    # Check for example file patterns
    example_patterns = ["example_", "sample_"]
    if any(name.startswith(p) for p in example_patterns):
        return True

    return False


def mask_value(line: str) -> str:
    """Mask only the secret VALUE in a line, keeping the identifier.
    Example: 'app.secret_key = "supersecret123"' -> 'app.secret_key = "su****"'
    """
    # Match quoted strings (single or double quotes) after = or :
    # Pattern: key = "value" or key = 'value' or key: "value"
    import re

    def mask_quoted(match):
        full_match = match.group(0)
        # Find the quoted part
        if '"' in full_match:
            quote_char = '"'
        elif "'" in full_match:
            quote_char = "'"
        else:
            return full_match

        # Split on the quote character
        parts = full_match.split(quote_char)
        if len(parts) >= 3:
            # parts[0] = prefix, parts[1] = value, parts[2] = suffix
            value = parts[1]
            if len(value) <= 2:
                masked = "****"
            else:
                masked = value[:2] + "****"
            return quote_char.join([parts[0], masked, quote_char] + parts[3:])
        return full_match

    # Pattern to match key = "value" or key = 'value' or key: "value" etc.
    pattern = re.compile(r'(\w+\s*[:=]\s*["\'])[^"\']*(["\'])')
    return pattern.sub(mask_quoted, line)


@dataclass
class ScanContext:
    root: Path
    files: list[Path] = field(default_factory=list)
    _cache: dict[str, str] = field(default_factory=dict, repr=False)

    def read(self, path: Path | str) -> str:
        key = str(path)
        if key in self._cache:
            return self._cache[key]
        full = self.root / path if not isinstance(path, Path) or not path.is_absolute() else path
        try:
            # Skip symlinks
            if full.is_symlink():
                return ""
            # Ensure resolved path is still inside root
            root_resolved = self.root.resolve()
            full_resolved = full.resolve()
            if not full_resolved.is_relative_to(root_resolved):
                return ""
            content = full_resolved.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = ""
        self._cache[key] = content
        return content


RuleFn = Callable[[ScanContext], list[Finding]]

_rules: dict[str, tuple[RuleFn, str, str]] = {}


def rule(rule_id: str, category: str, severity_default: str):
    def decorator(fn: RuleFn) -> RuleFn:
        if rule_id in _rules:
            raise ValueError(f"Duplicate rule id: {rule_id}")
        _rules[rule_id] = (fn, category, severity_default)
        return fn

    return decorator


def run_all(ctx: ScanContext) -> list[Finding]:
    all_findings: list[Finding] = []
    for rule_id, (fn, category, severity_default) in _rules.items():
        try:
            findings = fn(ctx)
            for f in findings:
                if not f.id:
                    f.id = rule_id
            all_findings.extend(findings)
        except Exception as e:
            all_findings.append(
                Finding(
                    id="SCAN-ERR",
                    category=category,
                    severity=severity_default,
                    title=f"Rule {rule_id} failed",
                    description=f"Scanner error: {e}",
                    remediation="Fix the scanner implementation",
                )
            )
    return all_findings
