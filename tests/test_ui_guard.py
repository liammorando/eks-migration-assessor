"""Guard test to detect unmatched <div> tags in Streamlit markdown calls."""
import re
from pathlib import Path


def test_analyze_card_called_once_outside_results_guard():
    """Verify render_analyze_card is called exactly once and NOT inside
    a results-dependent if block."""
    streamlit_app = Path("app/streamlit_app.py")
    content = streamlit_app.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Find all calls to render_analyze_card
    calls = []
    for i, line in enumerate(lines, 1):
        if "render_analyze_card(" in line:
            calls.append((i, line.strip()))

    # Must be exactly one call
    assert len(calls) == 1, (
        f"Expected exactly one call to render_analyze_card, "
        f"found {len(calls)}: {calls}"
    )

    # The call must NOT be inside an 'if not has_results:' or similar guard
    # Check the context around the call
    call_line_idx = calls[0][0] - 1  # 0-indexed
    # Look backwards for any if/else that could guard this call
    for j in range(call_line_idx, max(-1, call_line_idx - 15), -1):
        line = lines[j].strip()
        if (
            line.startswith("if not has_results")
            or line.startswith("if has_results")
            or line.startswith("if not analysis_done")
            or line.startswith("if analysis_done")
        ):
            raise AssertionError(
                f"render_analyze_card is inside a results-dependent guard "
                f"at line {j+1}: {line}"
            )


def test_no_unmatched_div_in_markdown():
    """Fail if any .py file under app/ contains unmatched <div> in
    st.markdown calls."""
    patterns = [
        # st.markdown("...<div...", unsafe_allow_html=True) without
        # closing </div> in same string
        re.compile(r'st\.markdown\(\s*f?["\']<div[^>]*>["\']\s*[,)]'),
        # st.markdown("...</div>", unsafe_allow_html=True) - closing
        # div without opening
        re.compile(r'st\.markdown\(\s*f?["\']\s*</div>["\']\s*[,)]'),
    ]

    violations = []
    for py_file in Path("app").rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            for pattern in patterns:
                if pattern.search(line):
                    violations.append(f"{py_file}:{i}: {line.strip()}")

    assert not violations, (
        "Found unmatched <div> in st.markdown:\n" + "\n".join(violations)
    )


def test_no_html_in_expander_labels():
    """Fail if any expander label contains HTML tags."""
    pattern = re.compile(r'st\.expander\([^)]*<[^>]+>')

    violations = []
    for py_file in Path("app").rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{py_file}:{i}: {line.strip()}")

    assert not violations, (
        "Found HTML in expander label:\n" + "\n".join(violations)
    )


if __name__ == "__main__":
    test_analyze_card_called_once_outside_results_guard()
    test_no_unmatched_div_in_markdown()
    test_no_html_in_expander_labels()
    print("All UI guard tests passed!")
