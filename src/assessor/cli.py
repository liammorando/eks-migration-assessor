from __future__ import annotations

import argparse
import sys
from pathlib import Path

from assessor.service import analyze


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="EKS Migration Readiness Assessor",
        prog="assessor",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan a repository or directory")
    scan_parser.add_argument("target", help="GitHub/GitLab repository URL (HTTPS) or local directory path")
    scan_parser.add_argument("--workspace", default=".workspace", help="Workspace directory for clones")
    scan_parser.add_argument("--out", default=".", help="Output directory for reports")
    scan_parser.add_argument("--no-llm", action="store_true", help="Disable LLM summary")
    scan_parser.add_argument("--max-mb", type=int, default=100, help="Maximum repository size in MB")

    args = parser.parse_args(argv)

    if args.command != "scan":
        parser.print_help()
        return 1

    target = args.target
    out_dir = Path(args.out).resolve()
    workspace = Path(args.workspace).resolve()

    try:
        result, plan, md_path = analyze(
            repo_url=target,
            workspace=workspace,
            out_dir=out_dir,
            use_llm=not args.no_llm,
            max_mb=args.max_mb,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except (TimeoutError, RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Print summary
    print(f"\nScore: {result.score}/100")
    print(f"Readiness: {result.readiness}")
    print(f"Files scanned: {result.files_scanned}")
    print(f"Findings: {len(result.findings)}")

    # Top 5 findings by severity
    sorted_findings = sorted(
        [f for f in result.findings if f.id != "OK-001"],
        key=lambda f: SEVERITY_ORDER.get(f.severity, 5),
    )
    if sorted_findings:
        print("\nTop findings:")
        for f in sorted_findings[:5]:
            loc = f"{f.file}:{f.line}" if f.file and f.line else f.file or "N/A"
            print(f"  [{f.severity.value.upper()}] {f.id} - {f.title} ({loc})")

    print(f"\nReport saved to: {md_path}")

    return 0


SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


if __name__ == "__main__":
    sys.exit(main())
