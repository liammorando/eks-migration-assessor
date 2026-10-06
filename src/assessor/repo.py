from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$"
)
GITLAB_URL_PATTERN = re.compile(
    r"^https://gitlab\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$"
)

# Pattern for valid owner/repo segments: must start with alphanumeric, contain only alphanumeric, underscore, hyphen, dot
SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

SKIP_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    }

SKIP_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".dat",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".webp",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".ttf",
    ".woff",
    ".woff2",
    ".eot",
    ".otf",
    ".class",
    ".jar",
    ".war",
    ".ear",
    }

BINARY_SIGNATURES = {b"\x00", b"\xff\xfe", b"\xfe\xff"}


def validate_repo_url(url: str) -> str:
    url = url.strip()
    if not (GITHUB_URL_PATTERN.match(url) or GITLAB_URL_PATTERN.match(url)):
        raise ValueError(
            "Invalid repository URL. Must be a public HTTPS GitHub or GitLab URL "
            "(e.g., https://github.com/owner/repo or https://gitlab.com/owner/repo)."
        )

    # Extract owner and repo from URL for additional validation
    # URL format: https://github.com/owner/repo[.git][/]
    # Extract the path part after the domain
    match = re.match(r"^https://(?:github\.com|gitlab\.com)/([^/]+)/([^/.]+(?:\.[^/.]+)*)(?:\.git)?/?$", url)
    if not match:
        raise ValueError("Invalid repository URL format")

    owner, repo = match.group(1), match.group(2)

    # Validate owner and repo segments
    for segment, name in [(owner, "owner"), (repo, "repo")]:
        if not SEGMENT_PATTERN.match(segment):
            raise ValueError(f"Invalid {name} segment: '{segment}'. Must start with alphanumeric and contain only alphanumeric, underscore, hyphen, or dot.")
        if segment in (".", ".."):
            raise ValueError(f"Invalid {name} segment: '{segment}'")

    # Strip trailing .git suffix only at the end
    if url.endswith(".git"):
        url = url.removesuffix(".git")

    return url


def _get_dir_size_mb(path: Path) -> float:
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            try:
                total += entry.stat().st_size
            except OSError:
                pass
    return total / (1024 * 1024)


def clone_repo(url: str, workspace: Path, timeout: int = 30, max_mb: int = 100, max_files: int = 5000, max_total_bytes: int = 100 * 1024 * 1024) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)

    # Extract repo name for display purposes, but use UUID for directory name
    repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
    # Sanitize repo name to be safe for filesystem
    safe_repo_name = re.sub(r"[^A-Za-z0-9_.-]", "_", repo_name)
    unique_dir = workspace / "clones" / uuid.uuid4().hex / safe_repo_name
    unique_dir.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"
    env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes"

    try:
        subprocess.run(
            [
                "git",
                "-c", "protocol.file.allow=never",
                "-c", "protocol.ext.allow=never",
                "-c", "core.hooksPath=/dev/null",
                "-c", "credential.helper=",
                "clone",
                "--depth", "1",
                "--single-branch",
                "--no-tags",
                "--no-recurse-submodules",
                url,
                str(unique_dir),
            ],
            check=True,
            timeout=timeout,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except subprocess.TimeoutExpired as e:
        if unique_dir.exists():
            shutil.rmtree(unique_dir, ignore_errors=True)
        raise TimeoutError(f"git clone timed out after {timeout}s") from e
    except subprocess.CalledProcessError as e:
        if unique_dir.exists():
            shutil.rmtree(unique_dir, ignore_errors=True)
        raise RuntimeError(f"git clone failed: {e.stderr.decode().strip()}") from e

    size_mb = _get_dir_size_mb(unique_dir)
    if size_mb > max_mb:
        shutil.rmtree(unique_dir, ignore_errors=True)
        raise ValueError(f"Repository size ({size_mb:.1f} MB) exceeds limit of {max_mb} MB")

    # Count files and check total bytes
    file_count = 0
    total_bytes = 0
    for entry in unique_dir.rglob("*"):
        if entry.is_file():
            file_count += 1
            try:
                total_bytes += entry.stat().st_size
            except OSError:
                pass

    if file_count > max_files:
        shutil.rmtree(unique_dir, ignore_errors=True)
        raise ValueError(f"Repository file count ({file_count}) exceeds limit of {max_files}")

    if total_bytes > max_total_bytes:
        shutil.rmtree(unique_dir, ignore_errors=True)
        raise ValueError(f"Repository total bytes ({total_bytes} bytes) exceeds limit of {max_total_bytes} bytes")

    return unique_dir


def _is_binary(filepath: Path) -> bool:
    try:
        with filepath.open("rb") as f:
            chunk = f.read(1024)
            return any(sig in chunk for sig in BINARY_SIGNATURES)
    except OSError:
        return True


def iter_files(root: Path, max_file_kb: int = 512, max_files: int = 5000, max_total_bytes: int = 100 * 1024 * 1024):
    max_bytes = max_file_kb * 1024
    root_resolved = root.resolve()
    file_count = 0
    total_bytes = 0
    for path in root.rglob("*"):
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

        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        if path.suffix.lower() in SKIP_EXTS:
            continue

        try:
            stat = path.stat()
            if stat.st_size > max_bytes:
                continue
        except OSError:
            continue

        if _is_binary(path):
            continue

        file_count += 1
        if file_count > max_files:
            break

        try:
            total_bytes += path.stat().st_size
        except OSError:
            pass
        if total_bytes > max_total_bytes:
            break

        yield path.relative_to(root)
