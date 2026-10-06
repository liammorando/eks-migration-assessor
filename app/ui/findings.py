"""Findings tab component for the EKS Migration Assessor app."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from assessor.i18n import get_text
from assessor.models import AssessmentResult, Finding
from assessor.ui_helpers import group_findings, group_label, truncate


def _t(key: str, lang: str) -> str:
    """Get translation for key."""
    return get_text(key, lang)


def _severity_badge(severity: str) -> str:
    """Return HTML for severity badge using design system classes."""
    css_class = {
        "critical": "badge-critical",
        "high": "badge-high",
        "medium": "badge-medium",
        "low": "badge-low",
        "info": "badge-info",
    }.get(severity.lower(), "badge-info")
    return f'<span class="badge {css_class}">{severity.upper()}</span>'


def _filter_findings(
    findings: list[Finding],
    severity_filter: list[str],
    category_filter: list[str],
    search_query: str,
) -> list[Finding]:
    """Apply filters to findings."""
    filtered = findings

    if severity_filter:
        filtered = [f for f in filtered if f.severity.value in severity_filter]

    if category_filter:
        filtered = [f for f in filtered if f.category.value in category_filter]

    if search_query:
        query = search_query.lower()
        filtered = [
            f
            for f in filtered
            if query in (f.file or "").lower()
            or query in f.title.lower()
            or query in f.id.lower()
        ]

    return filtered


def render_findings_tab(result: AssessmentResult) -> None:
    """Render the Findings tab with toolbar, grouped view, and flat view."""
    lang = st.session_state.get("lang", "en")

    if not result.findings:
        with st.container(border=True, key="empty_findings"):
            st.markdown(":material/search_off:")
            st.markdown(f"### {_t('no_findings', lang)}")
            st.caption("No issues detected. Your codebase looks clean!")
        return

    total_findings = len(result.findings)

    # --- Toolbar ---
    with st.container(border=True, key="findings_toolbar"):
        # Severity pills/multiselect
        severity_options = ["critical", "high", "medium", "low", "info"]
        severity_labels = {s: s.capitalize() for s in severity_options}

        col_sev, col_cat, col_search, col_group = st.columns([3, 2, 3, 1])

        with col_sev:
            try:
                # Try st.pills (newer Streamlit)
                severity_filter = st.pills(
                    label=_t("filter_severity", lang),
                    options=severity_options,
                    format_func=lambda s: severity_labels[s],
                    selection_mode="multi",
                    default=severity_options,
                    key="severity_filter",
                    label_visibility="collapsed",
                )
            except AttributeError:
                # Fallback to multiselect
                severity_filter = st.multiselect(
                    label=_t("filter_severity", lang),
                    options=severity_options,
                    format_func=lambda s: severity_labels[s],
                    default=severity_options,
                    key="severity_filter",
                    label_visibility="collapsed",
                )

        with col_cat:
            categories = sorted({f.category.value for f in result.findings})
            try:
                category_filter = st.pills(
                    label=_t("filter_category", lang),
                    options=categories,
                    format_func=lambda s: s.capitalize(),
                    selection_mode="multi",
                    default=categories,
                    key="category_filter",
                    label_visibility="collapsed",
                )
            except AttributeError:
                category_filter = st.multiselect(
                    label=_t("filter_category", lang),
                    options=categories,
                    format_func=lambda s: s.capitalize(),
                    default=categories,
                    key="category_filter",
                    label_visibility="collapsed",
                )

        with col_search:
            search_query = st.text_input(
                label="Search",
                placeholder="Search file path, title, rule ID...",
                key="findings_search",
                label_visibility="collapsed",
            )

        with col_group:
            group_by_rule = st.toggle(
                "Group by rule",
                value=True,
                key="group_by_rule",
                help="Group findings by rule ID",
            )

        # Apply filters
        filtered_findings = _filter_findings(
            result.findings,
            severity_filter or [],
            category_filter or [],
            search_query or "",
        )

        filtered_groups = group_findings(filtered_findings)

        # Show count
        st.caption(
            f"Showing {len(filtered_findings)} of {total_findings} findings "
            f"({len(filtered_groups)} rules)"
        )

    # Empty state
    if not filtered_findings:
        st.info(
            "No findings match the current filters. "
            "Try adjusting your filters or search query.",
            icon=":material/search_off:",
        )
        return

    # Limit groups for performance
    MAX_GROUPS = 50
    show_load_more = len(filtered_groups) > MAX_GROUPS
    display_groups = filtered_groups[:MAX_GROUPS]

    if group_by_rule:
        # --- Grouped View ---
        for i, g in enumerate(display_groups):
            expander_label = group_label(g)
            with st.expander(expander_label, expanded=(i < 3)):
                # Remediation and EKS hint once per group
                st.markdown(f"**Remediation:** {g.remediation}")
                if g.eks_hint:
                    st.info(g.eks_hint, icon=":material/cloud:")

                # First 5 occurrences
                st.markdown("**Occurrences:**")
                for f in g.findings[:5]:
                    loc = f"{f.file}:{f.line}" if f.file else "Unknown location"
                    st.markdown(f"`{loc}`")
                    if f.evidence:
                        st.code(truncate(f.evidence, 200), language="text")

                if len(g.findings) > 5:
                    with st.expander(f"Show all {len(g.findings)} occurrences"):
                        for f in g.findings[5:]:
                            loc = f"{f.file}:{f.line}" if f.file else "Unknown location"
                            st.markdown(f"`{loc}`")
                            if f.evidence:
                                st.code(truncate(f.evidence, 200), language="text")

        # Load more button
        if show_load_more:
            if st.button(
                f"Load more ({len(filtered_groups) - MAX_GROUPS} groups)",
                key="load_more_groups",
            ):
                st.session_state["show_all_groups"] = True
                st.rerun()

        if st.session_state.get("show_all_groups"):
            for g in filtered_groups[MAX_GROUPS:]:
                expander_label = group_label(g)
                with st.expander(expander_label):
                    st.markdown(f"**Remediation:** {g.remediation}")
                    if g.eks_hint:
                        st.info(g.eks_hint, icon=":material/cloud:")
                    st.markdown("**Occurrences:**")
                    for f in g.findings:
                        loc = f"{f.file}:{f.line}" if f.file else "Unknown location"
                        st.markdown(f"`{loc}`")
                        if f.evidence:
                            st.code(truncate(f.evidence, 200), language="text")

    else:
        # --- Flat View (DataFrame) ---
        # Prepare data for dataframe
        rows = []
        for f in filtered_findings:
            rows.append({
                "severity": _severity_badge(f.severity.value),
                "rule_id": f.id,
                "file": f.file or "",
                "line": f.line or 0,
                "title": f.title,
            })

        df = pd.DataFrame(rows)

        # Configure columns
        column_config = {
            "severity": st.column_config.TextColumn("Severity", width="small"),
            "rule_id": st.column_config.TextColumn("Rule ID", width="medium"),
            "file": st.column_config.TextColumn("File", width="large"),
            "line": st.column_config.NumberColumn("Line", width="small", format="%d"),
            "title": st.column_config.TextColumn("Title", width="large"),
        }

        # Pagination
        PAGE_SIZE = 50
        total_pages = (len(df) + PAGE_SIZE - 1) // PAGE_SIZE

        if "findings_page" not in st.session_state:
            st.session_state["findings_page"] = 1

        page = st.session_state["findings_page"]
        start_idx = (page - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        page_df = df.iloc[start_idx:end_idx]

        st.dataframe(
            page_df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
        )

        # Pagination controls
        if total_pages > 1:
            col_prev, col_page, col_next = st.columns([1, 3, 1])
            with col_prev:
                if st.button("← Previous", disabled=(page <= 1), key="prev_page"):
                    st.session_state["findings_page"] = page - 1
                    st.rerun()
            with col_page:
                st.caption(f"Page {page} of {total_pages}")
            with col_next:
                if st.button("Next →", disabled=(page >= total_pages), key="next_page"):
                    st.session_state["findings_page"] = page + 1
                    st.rerun()
