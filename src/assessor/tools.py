from __future__ import annotations

import re
from pathlib import Path


def list_files(root: Path, max_files: int = 5000) -> list[Path]:
    root_resolved = root.resolve()
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        # Skip symlinks
        if p.is_symlink():
            continue
        # Ensure resolved path is still inside root
        try:
            resolved = p.resolve()
            if not resolved.is_relative_to(root_resolved):
                continue
        except OSError:
            continue
        files.append(p)
        if len(files) >= max_files:
            break
    return files


def read_file(root: Path, rel_path: str, max_chars: int = 8000) -> str:
    try:
        root_resolved = root.resolve()
        requested = (root / rel_path).resolve()
        if not requested.is_relative_to(root_resolved):
            raise ValueError("Path traversal attempt blocked")
        content = requested.read_text(encoding="utf-8", errors="ignore")
        if len(content) > max_chars:
            return content[:max_chars] + f"\n... [truncated, {len(content)} total chars]"
        return content
    except (OSError, ValueError):
        return ""


def search_pattern(root: Path, regex: str, glob: str = "*", max_results: int = 200, max_file_kb: int = 512) -> list[tuple[Path, int, str]]:
    if len(regex) > 200:
        raise ValueError("Regex pattern too long (max 200 chars)")
    pattern = re.compile(regex)
    results: list[tuple[Path, int, str]] = []
    root_resolved = root.resolve()
    max_bytes = max_file_kb * 1024
    for path in root.rglob(glob):
        if not path.is_file():
            continue
        # Skip symlinks
        if path.is_symlink():
            continue
        # Ensure resolved path is still inside root
        try:
            resolved = path.resolve()
            if not resolved.is_relative_to(root_resolved):
                continue
        except OSError:
            continue
        # Check file size
        try:
            if path.stat().st_size > max_bytes:
                continue
        except OSError:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                results.append((path, i, line.strip()))
                if len(results) >= max_results:
                    return results
    return results
