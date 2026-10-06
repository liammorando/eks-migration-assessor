"""Migration Plan tab component for the EKS Migration Assessor app."""
from __future__ import annotations

import streamlit as st

from assessor.i18n import get_text
from assessor.models import PlanStep


def _t(key: str, lang: str) -> str:
    """Get translation for key."""
    return get_text(key, lang)


def render_plan_tab(plan: list[PlanStep]) -> None:
    """Render the Migration Plan tab with each phase as a card."""
    lang = st.session_state.get("lang", "en")

    if not plan:
        with st.container(border=True, key="empty_plan"):
            st.markdown(":material/route:")
            st.markdown(f"### {_t('no_plan', lang)}")
            st.caption("No migration plan generated.")
        return

    for step in plan:
        with st.container(border=True, key=f"phase_{step.phase}"):
            col_badge, col_title, col_effort = st.columns([1, 6, 1])
            with col_badge:
                st.markdown(f"**Phase {step.phase}**")
            with col_title:
                st.markdown(f"### {step.title}")
            with col_effort:
                st.caption(step.effort)

            st.caption(step.why)

            st.markdown(f"**{_t('actions', lang)}**")
            for action in step.actions:
                st.markdown(f"- {action}")

            # Related finding IDs as small monospace tags
            if step.finding_ids:
                finding_tags = " ".join(
                    f"`{fid}`" for fid in step.finding_ids
                )
                st.markdown(f"**{_t('related_findings', lang)}:** {finding_tags}")
