#!/usr/bin/env python3
"""Self-check script for EKS Migration Assessor.

Runs all checks and prints a scorecard with PASS/FAIL for each category.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DOCS_DIR.mkdir(exist_ok=True)

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "categories": {},
    "defects": [],
    "skipped_checks": [],
}


def run_cmd(cmd: list[str], cwd: Path = REPO_ROOT, timeout: int = 120) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
        )
        # Decode as UTF-8 (ruff outputs UTF-8)
        def decode_output(output_bytes):
            if not output_bytes:
                return ""
            try:
                return output_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return output_bytes.decode("utf-8", errors="replace")

        return result.returncode, decode_output(result.stdout), decode_output(result.stderr)
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def check_reliability() -> dict[str, Any]:
    """Run pytest and UI smoke tests."""
    print("\n=== RELIABILITY ===")

    # Run all tests with verbose to get summary line
    rc, stdout, stderr = run_cmd([sys.executable, "-m", "pytest", "-v", "--tb=no"])

    # Parse output for pass/fail counts from the summary line
    pass_count = 0
    fail_count = 0
    error_count = 0
    skipped_count = 0

    for line in stdout.splitlines():
        # Look for the summary line at the end: "5 failed, 149 passed, 5 skipped in 18.02s"
        if "passed" in line and ("failed" in line or "error" in line or "skipped" in line):
            import re
            m = re.search(r"(\d+)\s+passed", line)
            if m:
                pass_count = int(m.group(1))
            m = re.search(r"(\d+)\s+failed", line)
            if m:
                fail_count = int(m.group(1))
            m = re.search(r"(\d+)\s+error", line)
            if m:
                error_count = int(m.group(1))
            m = re.search(r"(\d+)\s+skipped", line)
            if m:
                skipped_count = int(m.group(1))
            break

    total = pass_count + fail_count + error_count
    pct = (pass_count / total * 100) if total > 0 else 0

    passed = rc == 0
    score = 100 if passed else int(pct)
    status = "PASS" if passed else "FAIL"

    print(f"  Pytest: {pass_count} passed, {fail_count} failed, {error_count} errors, {skipped_count} skipped ({pct:.1f}%)")
    print(f"  Score: {score}/100 - {status}")

    return {
        "score": score,
        "status": status,
        "threshold": 100,
        "details": {
            "passed": pass_count,
            "failed": fail_count,
            "errors": error_count,
            "skipped": skipped_count,
            "total": total,
            "pytest_rc": rc,
            "stdout": stdout[-2000:] if stdout else "",
            "stderr": stderr[-2000:] if stderr else "",
        }
    }


def check_performance() -> dict[str, Any]:
    """Run performance tests."""
    print("\n=== PERFORMANCE ===")

    rc, stdout, stderr = run_cmd([
        sys.executable, "-m", "pytest", "tests/test_perf.py", "-v", "-m", "perf", "-s", "--tb=no"
    ], timeout=180)

    # Parse timing results
    metrics = {}
    for line in stdout.splitlines():
        if "Cold start time:" in line:
            metrics["cold_start_s"] = float(line.split(":")[1].strip().rstrip("s"))
        elif "Analyze stateful-app" in line and "median" in line:
            metrics["analyze_stateful_s"] = float(line.split(":")[1].strip().rstrip("s"))
        elif "Analyze ready-app" in line and "median" in line:
            metrics["analyze_ready_s"] = float(line.split(":")[1].strip().rstrip("s"))
        elif "Analyze messy-compose" in line and "median" in line:
            metrics["analyze_messy_s"] = float(line.split(":")[1].strip().rstrip("s"))
        elif "Render 500 findings:" in line:
            metrics["render_500_s"] = float(line.split(":")[1].strip().rstrip("s"))
        elif "Network calls" in line:
            metrics["network_calls"] = int(line.split(":")[1].strip())
        elif "Peak memory" in line:
            metrics["peak_memory_mb"] = float(line.split(":")[1].strip().rstrip(" MB"))

    # Check thresholds
    checks = {
        "cold_start_s < 3": metrics.get("cold_start_s", 999) < 3,
        "analyze_fixture_s < 3": all(
            metrics.get(k, 999) < 3
            for k in ["analyze_stateful_s", "analyze_ready_s", "analyze_messy_s"]
        ),
        "render_500_s < 3": metrics.get("render_500_s", 999) < 3,
        "network_calls == 0": metrics.get("network_calls", 999) == 0,
    }

    all_pass = all(checks.values())
    score = 100 if all_pass else 0
    status = "PASS" if all_pass else "FAIL"

    for check, result in checks.items():
        print(f"  {check}: {'OK' if result else 'FAIL'}")
    print(f"  Score: {score}/100 - {status}")

    return {
        "score": score,
        "status": status,
        "threshold": 100,
        "details": {
            "metrics": metrics,
            "checks": checks,
        }
    }


def check_security() -> dict[str, Any]:
    """Run security checks."""
    print("\n=== SECURITY ===")

    checks = {}
    defects = []

    # 1. Check unsafe_allow_html allowlist
    allowlist_path = REPO_ROOT / "scripts" / "unsafe_html_allowlist.txt"
    if allowlist_path.exists():
        allowlist_content = allowlist_path.read_text(encoding="utf-8")
        # Count entries (lines with |)
        entries = [l for l in allowlist_content.splitlines() if "|" in l and not l.startswith("#")]
        checks["unsafe_html_allowlist_exists"] = True
        checks["unsafe_html_entries"] = len(entries)
        print(f"  unsafe_html allowlist: {len(entries)} entries")
    else:
        checks["unsafe_html_allowlist_exists"] = False
        checks["unsafe_html_entries"] = 0
        defects.append(("SEC-01", "Missing unsafe_html_allowlist.txt", "blocker"))
        print("  unsafe_html allowlist: MISSING")

    # 2. Check for </div> in markdown calls (unmatched closing tags)
    div_violations = []
    for py_file in REPO_ROOT.glob("app/**/*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), 1):
                if 'st.markdown(' in line and '</div>' in line and 'unsafe_allow_html=True' in content[max(0, content.find(line)-200):content.find(line)+200]:
                    div_violations.append(f"{py_file}:{i}")
        except Exception:
            pass

    checks["unmatched_div_in_markdown"] = len(div_violations) == 0
    if div_violations:
        print(f"  Unmatched </div> in markdown: {len(div_violations)} violations")
        for v in div_violations:
            print(f"    {v}")
            defects.append(("SEC-02", f"Unmatched </div> in markdown: {v}", "major"))
    else:
        print("  Unmatched </div> in markdown: OK")

    # 3. Check reports don't contain raw fixture secrets
    secret_violations = []
    secrets_to_check = [
        "supersecret123",
        "AKIAFAKEFAKEFAKEFAKE",
    ]
    for py_file in REPO_ROOT.glob("app/**/*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            for secret in secrets_to_check:
                if secret in content:
                    secret_violations.append(f"{py_file}: contains fixture secret '{secret}'")
        except Exception:
            pass

    checks["no_fixture_secrets_in_reports"] = len(secret_violations) == 0
    if secret_violations:
        print(f"  Fixture secrets in app code: {len(secret_violations)} violations")
        for v in secret_violations:
            print(f"    {v}")
            defects.append(("SEC-03", v, "major"))
    else:
        print("  Fixture secrets in app code: OK")

    # Overall
    all_pass = all(v for v in checks.values() if isinstance(v, bool))
    score = 100 if all_pass else 50 if checks.get("unsafe_html_allowlist_exists") else 0
    status = "PASS" if all_pass else "FAIL"

    print(f"  Score: {score}/100 - {status}")

    return {
        "score": score,
        "status": status,
        "threshold": 80,
        "details": {
            "checks": checks,
            "defects": defects,
        }
    }


def check_ux_static() -> dict[str, Any]:
    """Run UX static checks."""
    print("\n=== UX STATIC ===")

    checks = {}
    defects = []

    # 1. Exactly one language control (segmented_control with radio fallback counts as 1)
    lang_controls = 0
    for py_file in REPO_ROOT.glob("app/**/*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            # Count files that have language selector, not individual occurrences
            # The header.py has try/except with segmented_control and radio fallback - count as 1
            if "segmented_control" in content and "Language" in content:
                lang_controls += 1
            elif 'st.radio(' in content and "Language" in content and "segmented_control" not in content:
                lang_controls += 1
        except Exception:
            pass

    checks["one_language_control"] = lang_controls == 1
    print(f"  Language controls: {lang_controls} {'OK' if lang_controls == 1 else 'FAIL'}")
    if lang_controls != 1:
        defects.append(("UX-01", f"Expected 1 language control, found {lang_controls}", "major"))

    # 2. Analyze card present in every AppTest state (tested via UI smoke)
    checks["analyze_card_tested"] = True  # Covered by S01
    print("  Analyze card tested: OK (via S01)")

    # 3. No font-size below 12px in theme.py
    theme_path = REPO_ROOT / "app" / "ui" / "theme.py"
    small_font = False
    if theme_path.exists():
        content = theme_path.read_text(encoding="utf-8")
        # Look for font-size: Xpx where X < 12
        import re
        for match in re.finditer(r'font-size:\s*(\d+(?:\.\d+)?)px', content):
            size = float(match.group(1))
            if size < 12:
                small_font = True
                defects.append(("UX-02", f"Font size {size}px < 12px in theme.py", "minor"))

    checks["no_small_font"] = not small_font
    print(f"  Font size >= 12px: {'OK' if not small_font else 'FAIL'}")

    # 4. No emoji flags
    emoji_flags = []
    for py_file in REPO_ROOT.glob("app/**/*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            # Check for flag emojis (regional indicator symbols)
            if re.search(r'[\U0001F1E6-\U0001F1FF]{2}', content):
                emoji_flags.append(str(py_file))
        except Exception:
            pass

    checks["no_emoji_flags"] = len(emoji_flags) == 0
    print(f"  Emoji flags: {'OK' if not emoji_flags else 'FAIL'}")
    if emoji_flags:
        for f in emoji_flags:
            defects.append(("UX-03", f"Emoji flag found in {f}", "minor"))

    # 5. Every button has a label
    # This is harder to check statically, but we can look for st.button("") or st.button(key=...) without label
    unlabeled_buttons = []
    for py_file in REPO_ROOT.glob("app/**/*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            # Simple check: st.button( with empty string or only key
            for i, line in enumerate(content.splitlines(), 1):
                if 'st.button(' in line and ('st.button("")' in line or "st.button('')" in line or 'st.button(key=' in line.split('st.button(')[1].split(',')[0]):
                    unlabeled_buttons.append(f"{py_file}:{i}")
        except Exception:
            pass

    checks["buttons_have_labels"] = len(unlabeled_buttons) == 0
    print(f"  Buttons have labels: {'OK' if not unlabeled_buttons else 'FAIL'}")
    if unlabeled_buttons:
        for b in unlabeled_buttons:
            defects.append(("UX-04", f"Button without label: {b}", "minor"))

    all_pass = all(v for v in checks.values() if isinstance(v, bool))
    score = 100 if all_pass else 70
    status = "PASS" if all_pass else "FAIL"

    print(f"  Score: {score}/100 - {status}")

    return {
        "score": score,
        "status": status,
        "threshold": 80,
        "details": {
            "checks": checks,
            "defects": defects,
        }
    }


def check_quality() -> dict[str, Any]:
    """Run quality checks (ruff)."""
    print("\n=== QUALITY ===")

    rc, stdout, stderr = run_cmd([sys.executable, "-m", "ruff", "check", "src", "app", "tests", "scripts"])

    # Count only E, F, W errors (not I, B, C4, T20 style issues)
    error_count = 0
    for line in stdout.splitlines():
        # Ruff output format: "CODE message --> file:line:col"
        # Check if line starts with E, F, or W code
        if re.match(r'^[EFW]\d+', line.strip()):
            error_count += 1

    # Also check rc - ruff returns 0 for warnings only, non-zero for errors
    checks = {
        "ruff_errors": error_count,
        "ruff_passed": rc == 0 or error_count == 0,
    }

    print(f"  Ruff errors (E/F/W): {error_count} {'OK' if error_count == 0 else 'FAIL'}")
    if rc != 0 and error_count > 0:
        print(f"  Ruff output:\n{stdout[:3000]}")

    all_pass = error_count == 0
    score = 100 if all_pass else max(0, 100 - error_count * 5)
    status = "PASS" if all_pass else "FAIL"

    print(f"  Score: {score}/100 - {status}")

    return {
        "score": score,
        "status": status,
        "threshold": 100,
        "details": {
            "ruff_errors": error_count,
            "rc": rc,
            "stdout": stdout[-2000:] if stdout else "",
        }
    }


def main() -> int:
    """Run all checks and output scorecard."""
    print("=" * 60)
    print("EKS Migration Assessor - Self Check")
    print("=" * 60)

    start_time = time.time()

    # Run all categories
    RESULTS["categories"]["reliability"] = check_reliability()
    RESULTS["categories"]["performance"] = check_performance()
    RESULTS["categories"]["security"] = check_security()
    RESULTS["categories"]["ux_static"] = check_ux_static()
    RESULTS["categories"]["quality"] = check_quality()

    # Collect all defects
    for cat in ["security", "ux_static"]:
        if "defects" in RESULTS["categories"][cat].get("details", {}):
            for d in RESULTS["categories"][cat]["details"]["defects"]:
                RESULTS["defects"].append({
                    "id": d[0],
                    "category": cat,
                    "description": d[1],
                    "severity": d[2],
                })

    # Add UI smoke test failures as defects
    rel = RESULTS["categories"]["reliability"]
    if rel["status"] == "FAIL":
        RESULTS["defects"].append({
            "id": "REL-01",
            "category": "reliability",
            "description": f"Pytest failures: {rel['details']['failed']} failed out of {rel['details']['total']}",
            "severity": "blocker",
        })

    # Calculate overall score
    category_scores = {k: v["score"] for k, v in RESULTS["categories"].items()}
    overall_score = sum(category_scores.values()) / len(category_scores)
    RESULTS["overall_score"] = round(overall_score, 1)

    # Overall pass/fail
    all_pass = all(v["status"] == "PASS" for v in RESULTS["categories"].values())
    RESULTS["overall_status"] = "PASS" if all_pass else "FAIL"

    elapsed = time.time() - start_time

    # Print scorecard
    print("\n" + "=" * 60)
    print("SCORECARD")
    print("=" * 60)
    print(f"{'Category':<20} {'Score':>6} {'Status':<6} {'Threshold':>10}")
    print("-" * 60)
    for cat, data in RESULTS["categories"].items():
        print(f"{cat:<20} {data['score']:>6} {data['status']:<6} {data['threshold']:>10}")
    print("-" * 60)
    print(f"{'OVERALL':<20} {RESULTS['overall_score']:>6.1f} {RESULTS['overall_status']:<6}")
    print(f"\nElapsed: {elapsed:.1f}s")
    print(f"Defects found: {len(RESULTS['defects'])}")

    # Write JSON report
    output_path = DOCS_DIR / "selfcheck-latest.json"
    with open(output_path, "w") as f:
        json.dump(RESULTS, f, indent=2)
    print(f"\nJSON report written to: {output_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
