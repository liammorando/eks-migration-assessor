from __future__ import annotations

"""AgentCore entrypoint adapter.

This file is a portability adapter for AWS Bedrock AgentCore.
It is NOT deployed in this project - it's provided for portability only.

To use with AgentCore, install `bedrock-agentcore` and deploy this module.
"""

import json
import os
import sys
from pathlib import Path

try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
except ImportError:
    BedrockAgentCoreApp = None


def _run_assessment(repo_url: str, workspace: str, out_dir: str) -> dict:
    """Run the assessment and return the result as a dict."""
    # Add the current directory to sys.path to import assessor
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from assessor.agent import summarize
    from assessor.models import AssessmentResult
    from assessor.planner import build_migration_plan
    from assessor.repo import clone_repo, iter_files, validate_repo_url
    from assessor.report import to_json
    from assessor.scanner.registry import ScanContext, run_all
    from assessor.scoring import compute_score, readiness_level

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    workspace_path = Path(workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)

    # Validate repo_url
    validate_repo_url(repo_url)

    # Determine if target is a local path or URL
    target_path = Path(repo_url)
    if target_path.exists() and target_path.is_dir():
        # Local directory scan
        repo_root = target_path.resolve()
        files = list(iter_files(repo_root))
        ctx = ScanContext(root=repo_root, files=files)
        findings = run_all(ctx)
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
        repo_root = clone_repo(repo_url, workspace_path)
        files = list(iter_files(repo_root))
        ctx = ScanContext(root=repo_root, files=files)
        findings = run_all(ctx)
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

    # Generate summary if LLM is available
    if os.getenv("MODEL_PROVIDER", "ollama").lower() != "none":
        summary = summarize(result, plan, repo_root)
        if summary:
            result.summary = summary

    # Return JSON-serializable dict
    return json.loads(to_json(result, plan))


# Only create the app if bedrock_agentcore is available
if BedrockAgentCoreApp is not None:
    app = BedrockAgentCoreApp()

    @app.entrypoint
    def handler(payload: dict) -> dict:
        """AgentCore entrypoint handler.

        Expected payload:
        {
            "repo_url": "https://github.com/owner/repo"
        }

        workspace and out_dir are read from environment variables:
        - WORKSPACE_DIR (default: /tmp/workspace)
        - OUT_DIR (default: /tmp/out)
        """
        repo_url = payload.get("repo_url")
        if not repo_url:
            return {"error": "repo_url is required"}

        # Validate repo_url
        from assessor.repo import validate_repo_url
        try:
            validate_repo_url(repo_url)
        except ValueError as e:
            return {"error": str(e)}

        workspace = os.getenv("WORKSPACE_DIR", "/tmp/workspace")
        out_dir = os.getenv("OUT_DIR", "/tmp/out")

        try:
            return _run_assessment(repo_url, workspace, out_dir)
        except Exception as e:
            return {"error": str(e)}

else:
    # Provide a clear message when bedrock-agentcore is not installed
    def handler(payload: dict) -> dict:
        return {
            "error": "bedrock-agentcore is not installed. "
                     "Install it with: pip install bedrock-agentcore"
        }

    app = None

    print(
        "bedrock-agentcore not installed. "
        "This adapter requires 'bedrock-agentcore' package to run on AgentCore. "
        "Install with: pip install bedrock-agentcore",
        file=sys.stderr,
    )


if __name__ == "__main__":
    if BedrockAgentCoreApp is not None and app is not None:
        app.run()
    else:
        print("Run with AgentCore: bedrock-agentcore run src/assessor/agentcore_entrypoint.py")
        sys.exit(1)
