"""Analyze card component for the EKS Migration Assessor app."""
from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

from assessor.i18n import get_text
from assessor.repo import validate_repo_url
from assessor.service import analyze as run_analysis

# Example repository URLs
EXAMPLE_REPOS = [
    "https://github.com/pallets/flask",
    "https://github.com/GoogleCloudPlatform/microservices-demo",
]


def _clear_analysis_state() -> None:
    """Clear analysis-related session state."""
    keys = [
        "result",
        "plan",
        "md_path",
        "analysis_done",
        "loaded_result",
        "loaded_plan",
        "loaded_md",
        "loaded_md_path",
    ]
    for key in keys:
        st.session_state.pop(key, None)


def _set_example_url(url: str) -> None:
    """Set the example URL in session state and rerun."""
    st.session_state["repo_url_input"] = url
    st.rerun()


def _add_to_history(repo_url: str, result, md_path) -> None:
    """Add analysis result to history."""
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    if repo_url.startswith("file://"):
        repo_name = Path(repo_url[7:]).name
    json_path = md_path.with_suffix(".json")
    entry = {
        "id": str(uuid.uuid4())[:8],
        "repo_name": repo_name,
        "score": result.score,
        "timestamp": datetime.now(UTC),
        "md_path": str(md_path),
        "json_path": str(json_path),
    }
    history = st.session_state.get("history", [])
    history.insert(0, entry)
    st.session_state["history"] = history[:10]


def _t(key: str, lang: str) -> str:
    """Get translation for key."""
    return get_text(key, lang)


def render_analyze_card(
    workspace_dir,
    reports_dir,
    session_reports_dir,
    max_repo_mb: int,
    use_llm: bool,
    ollama_host: str,
    ollama_model: str,
) -> None:
    """Render the analyze hero card with URL input, button, and example buttons."""
    lang = st.session_state.get("lang", "en")
    has_results = st.session_state.get("analysis_done") or "loaded_result" in st.session_state

    with st.container(border=True, key="hero"):
        # URL Input row with button
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            repo_url = st.text_input(
                label=_t("repo_url_label", lang),
                placeholder=_t("repo_url_placeholder", lang),
                help=_t("repo_url_help", lang),
                key="repo_url_input",
                label_visibility="collapsed",
            )
        with col_btn:
            analyze_disabled = st.session_state.get("analysis_running", False)
            analyze_clicked = st.button(
                f":material/search: {_t('analyze_btn', lang)}",
                type="primary",
                use_container_width=True,
                disabled=analyze_disabled,
            )

        # Example buttons row
        example_cols = st.columns(len(EXAMPLE_REPOS))
        for col, example_url in zip(example_cols, EXAMPLE_REPOS, strict=True):
            with col:
                st.button(
                    example_url,
                    key=f"example_{example_url}",
                    on_click=_set_example_url,
                    args=(example_url,),
                    use_container_width=True,
                    type="secondary",
                )

        # Muted note about accepted URLs
        st.caption(_t("repo_url_help", lang))

        # If results exist, show compact version
        if has_results:
            st.caption(f":material/check_circle: {_t('analyze_done', lang)}")

    # Validation and analysis
    if analyze_clicked:
        url = (repo_url or "").strip()
        if not url:
            st.error(_t("error_enter_url", lang), icon=":material/error:")
            return

        try:
            validate_repo_url(url)
        except ValueError as e:
            st.error(_t("error_invalid_url", lang).format(e), icon=":material/error:")
            return

        # Clear any previous analysis state
        _clear_analysis_state()
        st.session_state["analysis_running"] = True

        # Progress status
        status = st.status(_t("status_validating", lang), expanded=True)
        start_time = time.time()

        try:
            status.update(label=_t("status_cloning", lang), state="running")

            def update_progress(msg: str):
                status.update(label=msg, state="running")

            result, plan, md_path, clone_dir = run_analysis(
                repo_url=url,
                workspace=workspace_dir,
                out_dir=session_reports_dir,
                use_llm=use_llm,
                max_mb=max_repo_mb,
                ollama_host=ollama_host,
                ollama_model=ollama_model,
                progress_callback=update_progress,
            )

            elapsed = time.time() - start_time
            status.update(label=_t("status_done", lang).format(elapsed), state="complete")

            # Store in session state
            st.session_state["result"] = result
            st.session_state["plan"] = plan
            st.session_state["md_path"] = md_path
            st.session_state["analysis_done"] = True
            if clone_dir:
                st.session_state["repo_root"] = clone_dir

            # Add to history
            _add_to_history(url, result, md_path)

        except ValueError as e:
            status.update(label="Validation error", state="error")
            st.error(str(e), icon=":material/error:")
        except (TimeoutError, RuntimeError) as e:
            status.update(label="Error", state="error")
            st.error(f"Analysis failed: {e}", icon=":material/error:")
        except Exception as e:
            status.update(label="Error", state="error")
            st.error(f"Unexpected error: {e}", icon=":material/error:")
        finally:
            st.session_state["analysis_running"] = False
            st.rerun()


def render_empty_state() -> None:
    """Render the empty state with three step cards."""
    steps = [
        (
            ":material/code:",
            "1. Paste a repo URL",
            "Enter a public GitHub or GitLab HTTPS URL",
        ),
        (
            ":material/search:",
            "2. We scan it statically",
            "Deterministic analysis, no code execution",
        ),
        (
            ":material/assessment:",
            "3. Get a score and plan",
            "Readiness score, findings, and migration steps",
        ),
    ]

    cols = st.columns(3)
    for col, (icon, title, desc) in zip(cols, steps, strict=True):
        with col:
            with st.container(border=True, key=f"step_{title[0]}"):
                st.markdown(f"### {icon}")
                st.markdown(f"**{title}**")
                st.caption(desc)
