import logging
import os
import shutil
import time
from pathlib import Path
from typing import NamedTuple, Tuple, Union

from assessor.agent import build_model, summarize
from assessor.models import AssessmentResult, PlanStep
from assessor.planner import build_migration_plan
from assessor.repo import clone_repo, iter_files, validate_repo_url
from assessor.report import save_report
from assessor.scanner.registry import ScanContext, _rules, run_all
from assessor.scoring import compute_score, readiness_level
from assessor.storage import get_store

# Debug: log registered rules
logging.getLogger(__name__).info(f"Registered rules: {list(_rules.keys())}")

# Default TTL for report files in days
REPORT_TTL_DAYS = int(os.getenv("REPORT_TTL_DAYS", "7"))


class AnalysisResult:
    """Analysis result that can be unpacked as 3 or 4 values for backward compatibility."""
    __slots__ = ("result", "plan", "md_path", "clone_dir")

    def __init__(self, result: AssessmentResult, plan: list[PlanStep], md_path: Path, clone_dir: Path | None = None):
        self.result = result
        self.plan = plan
        self.md_path = md_path
        self.clone_dir = clone_dir

    def __iter__(self):
        # Support both 3-tuple and 4-tuple unpacking for backward compatibility
        yield self.result
        yield self.plan
        yield self.md_path
        if self.clone_dir is not None:
            yield self.clone_dir

    def __len__(self):
        # Support both 3 and 4 element unpacking
        return 3 if self.clone_dir is None else 4

    def __getitem__(self, index):
        if index == 0:
            return self.result
        elif index == 1:
            return self.plan
        elif index == 2:
            return self.md_path
        elif index == 3:
            if self.clone_dir is not None:
                return self.clone_dir
            raise IndexError("tuple index out of range")
        raise IndexError("tuple index out of range")


def _cleanup_old_reports(out_dir: Path, ttl_days: int = REPORT_TTL_DAYS) -> None:
    """Delete report files older than ttl_days."""
    cutoff = time.time() - (ttl_days * 86400)
    try:
        for report_file in out_dir.glob("report-*.md"):
            try:
                if report_file.stat().st_mtime < cutoff:
                    report_file.unlink(missing_ok=True)
            except OSError:
                pass
            # Also clean up corresponding .json files
            json_file = report_file.with_suffix(".json")
            try:
                if json_file.exists() and json_file.stat().st_mtime < cutoff:
                    json_file.unlink(missing_ok=True)
            except OSError:
                pass
    except OSError:
        pass


def analyze(
    repo_url: str,
    workspace: Path,
    out_dir: Path,
    use_llm: bool = False,
    max_mb: int = 100,
    ollama_host: str = "http://localhost:11434",
    ollama_model: str = "llama3.2",
    progress_callback: callable = None,
) -> tuple[AssessmentResult, list[PlanStep], Path]:
    """Analyze a repository and return the result, plan, and report path.

    Args:
        repo_url: GitHub/GitLab repository URL (HTTPS) or local directory path
        workspace: Workspace directory for clones
        out_dir: Output directory for reports
        use_llm: Whether to generate LLM summary
        max_mb: Maximum repository size in MB

    Returns:
        Tuple of (AssessmentResult, plan, report_path)
    """
    workspace.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Clean up old reports
    _cleanup_old_reports(out_dir)

    target_path = Path(repo_url)
    clone_dir = None

    try:
        # Determine if target is a local path or URL
        if target_path.exists() and target_path.is_dir():
            # Local directory scan
            if progress_callback:
                progress_callback("Scanning local directory...")
            repo_root = target_path.resolve()
            files = list(iter_files(repo_root))
            logging.getLogger(__name__).info(f"LOCAL SCAN: {len(files)} files from {repo_root}, rules={len(_rules)}")
            if progress_callback:
                progress_callback(f"Running {len(_rules)} detection rules...")
            ctx = ScanContext(root=repo_root, files=files)
            findings = run_all(ctx)
            logging.getLogger(__name__).info(f"LOCAL SCAN: {len(findings)} findings from {len(_rules)} rules")

            score = compute_score(findings)
            readiness = readiness_level(score)
            plan = build_migration_plan(findings)

            result = AssessmentResult(
                repo_url=f"file://{repo_root}",
                files_scanned=len(files),
                findings=findings,
                score=score,
                readiness=readiness,
                plan=plan,
            )
        else:
            # URL scan
            validate_repo_url(repo_url)
            if progress_callback:
                progress_callback("Cloning repository...")
            repo_root = clone_repo(repo_url, workspace, max_mb=max_mb)
            clone_dir = repo_root
            if progress_callback:
                progress_callback("Scanning files...")
            files = list(iter_files(repo_root))
            logging.getLogger(__name__).info(f"URL SCAN: {len(files)} files from {repo_root}, rules={len(_rules)}")
            if progress_callback:
                progress_callback(f"Running {len(_rules)} detection rules...")
            ctx = ScanContext(root=repo_root, files=files)
            findings = run_all(ctx)
            logging.getLogger(__name__).info(f"URL SCAN: {len(findings)} findings from {len(_rules)} rules")

            score = compute_score(findings)
            readiness = readiness_level(score)
            plan = build_migration_plan(findings)

            result = AssessmentResult(
                repo_url=repo_url,
                files_scanned=len(files),
                findings=findings,
                score=score,
                readiness=readiness,
                plan=plan,
            )

        # Generate LLM summary if requested
        if use_llm:
            if progress_callback:
                progress_callback("Initializing LLM...")
            model = build_model(ollama_host=ollama_host, ollama_model=ollama_model)
            if model is not None:
                if progress_callback:
                    progress_callback("Generating executive summary with Ollama...")
                summary = summarize(result, plan, repo_root, ollama_host=ollama_host, ollama_model=ollama_model)
                if summary:
                    result.summary = summary
                if progress_callback:
                    progress_callback("Summary generated")

        if progress_callback:
            progress_callback("Saving reports...")

        # Save reports
        md_path, json_path = save_report(result, plan, out_dir)

        # Store reports in configured backend (S3 or local)
        try:
            store = get_store()
            report_files = [md_path]
            if json_path.exists():
                report_files.append(json_path)
            stored_uris = store.save(report_files, result.scanned_at.strftime("%Y%m%d-%H%M%S"))
            result.stored_at = stored_uris
        except Exception as e:
            # Log warning but don't fail the analysis
            logging.getLogger(__name__).warning(f"Failed to store reports: {e}")

        # Re-save reports with stored_at populated
        save_report(result, plan, out_dir)

        return AnalysisResult(result, plan, md_path, clone_dir)
    finally:
        # Clean up cloned directory after report is saved (only if LLM not used)
        if clone_dir is not None and clone_dir.exists() and not use_llm:
            shutil.rmtree(clone_dir, ignore_errors=True)
