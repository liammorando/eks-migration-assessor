"""Report tab component for the EKS Migration Assessor app."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from assessor.i18n import get_text
from assessor.models import AssessmentResult


def _t(key: str, lang: str) -> str:
    """Get translation for key."""
    return get_text(key, lang)


def render_report_tab(
    result: AssessmentResult,
    md_content: str,
    md_path: Path | None,
    loaded: bool = False,
) -> None:
    """Render the Report tab with markdown in a bordered container and download buttons."""
    lang = st.session_state.get("lang", "en")

    # Download buttons row
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if md_path and md_path.exists():
            with open(md_path, "rb") as f:
                st.download_button(
                    label=_t("download_md", lang),
                    data=f,
                    file_name=md_path.name,
                    mime="text/markdown",
                    use_container_width=True,
                    icon=":material/download:",
                )
    with col2:
        if md_path:
            json_path = md_path.with_suffix(".json")
            if json_path.exists():
                with open(json_path, "rb") as f:
                    st.download_button(
                        label=_t("download_json", lang),
                        data=f,
                        file_name=json_path.name,
                        mime="application/json",
                        use_container_width=True,
                        icon=":material/download:",
                    )

    # Report content in bordered container with comfortable reading width
    if md_content:
        with st.container(border=True, key="report_content"):
            st.markdown(md_content)
    else:
        with st.container(border=True, key="empty_report"):
            st.markdown(":material/description:")
            st.markdown(f"### {_t('report_content', lang)}")
            st.caption("No report content available.")

    # Show stored URIs if available
    if result.stored_at:
        st.success(_t("stored_at", lang))
        for uri in result.stored_at:
            st.code(uri, language=None)
