"""Results dashboard component for the EKS Migration Assessor app."""
from __future__ import annotations

from datetime import UTC, datetime

import streamlit as st

from assessor.i18n import get_text
from assessor.models import AssessmentResult
from assessor.ui_helpers import (
    gauge_svg,
    group_findings,
    group_label,
    readiness_tone,
    severity_bar_svg,
    severity_counts,
    top_priorities,
    truncate,
)


def _t(key: str, lang: str) -> str:
    """Get translation for key."""
    return get_text(key, lang)


def _readiness_badge(readiness: str) -> str:
    """Return HTML for readiness badge - 13px bold, padding 4px 12px, 1px border."""
    tone = readiness_tone(readiness)
    tone_colors = {
        "good": ("#22C55E", "#22C55E"),    # border, text
        "warn": ("#F59E0B", "#F59E0B"),
        "bad": ("#EF4444", "#EF4444"),
    }
    border_color, text_color = tone_colors.get(tone, ("#F59E0B", "#F59E0B"))
    return (
        f'<span style="display:inline-block;font-size:13px;font-weight:700;'
        f'padding:4px 12px;border:1px solid {border_color};'
        f'border-radius:999px;color:{text_color};">{readiness}</span>'
    )


def _severity_badge(severity: str) -> str:
    """Return HTML for severity badge using design system."""
    css_class = {
        "critical": "badge-critical",
        "high": "badge-high",
        "medium": "badge-medium",
        "low": "badge-low",
        "info": "badge-info",
    }.get(severity.lower(), "badge-info")
    return f'<span class="badge {css_class}">{severity.upper()}</span>'


def _severity_color(severity: str) -> str:
    """Get color for severity - uses CSS variables."""
    colors = {
        "critical": "#EF4444",
        "high": "#F97316",
        "medium": "#EAB308",
        "low": "#22C55E",
        "info": "#38BDF8",
    }
    return colors.get(severity.lower(), "#8FA1BF")


def render_results_overview(result: AssessmentResult) -> None:
    """Render the Overview tab with KPI cards, priorities, strengths, and executive summary."""
    lang = st.session_state.get("lang", "en")

    groups = group_findings(result.findings)
    counts = severity_counts(result.findings)
    priorities = top_priorities(groups, 3)

    # KPI Row - 4 columns using st.columns
    kpi_cols = st.columns(4)

    # KPI 1: Score with gauge and readiness badge
    with kpi_cols[0]:
        with st.container(border=True, height=190, key="kpi_score"):
            st.caption(_t("score", lang))
            st.markdown(gauge_svg(result.score), unsafe_allow_html=True)
            # Center the readiness badge under the gauge
            st.markdown(
                f'<div style="text-align:center;margin-top:4px;">{_readiness_badge(result.readiness)}</div>',
                unsafe_allow_html=True,
            )

    # KPI 2: Findings total with severity bar
    total_findings = sum(counts.values())
    # Build legend as single line: colored dot + severity name + count
    legend_items = []
    for sev in ["critical", "high", "medium", "low", "info"]:
        if counts[sev] > 0:
            color = _severity_color(sev)
            legend_items.append(
                f'<span style="display:inline-flex;align-items:center;gap:4px;">'
                f'<span style="width:8px;height:8px;border-radius:50%;background:{color};display:inline-block;"></span>'
                f'{sev.capitalize()}: {counts[sev]}</span>'
            )
    legend_html = "&nbsp;&nbsp;".join(legend_items)
    with kpi_cols[1]:
        with st.container(border=True, height=190, key="kpi_findings"):
            st.caption(f'{_t("tab_findings", lang)} ({total_findings})')
            st.markdown(
                f'<div style="width:100%;overflow:hidden;">{severity_bar_svg(counts)}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="display: flex; gap: 16px; margin-top: 8px; flex-wrap: wrap; font-size: 13px;">{legend_html}</div>',
                unsafe_allow_html=True,
            )

    # KPI 3: Files scanned
    with kpi_cols[2]:
        with st.container(border=True, height=190, key="kpi_files"):
            st.caption(_t("files_scanned", lang))
            st.markdown(
                f'<div style="font-size:32px;font-weight:700;color:var(--primary);line-height:1.1;">{result.files_scanned:,}</div>',
                unsafe_allow_html=True,
            )
            st.caption(_t("files_analyzed", lang))

    # KPI 4: Repository name and duration
    repo_name = result.repo_url.split("/")[-1].replace(".git", "")
    duration_str = ""
    if hasattr(result, "scanned_at") and result.scanned_at:
        now = datetime.now(UTC)
        diff = now - result.scanned_at
        seconds = int(diff.total_seconds())
        if seconds < 60:
            duration_str = f"{seconds}s"
        elif seconds < 3600:
            duration_str = f"{seconds // 60}m {seconds % 60}s"
        else:
            duration_str = f"{seconds // 3600}h {(seconds % 3600) // 60}m"
    with kpi_cols[3]:
        with st.container(border=True, height=190, key="kpi_repo"):
            st.caption(_t("repository", lang))
            st.markdown(
                f'<div style="font-size:1rem;font-weight:600;color:var(--text-primary);'
                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{repo_name}</div>',
                unsafe_allow_html=True,
            )
            if duration_str:
                st.caption(f"Analyzed in {duration_str}")

    st.divider()

    # Top Priorities Card
    if priorities:
        with st.container(border=True, key="top_priorities"):
            st.markdown("### Top priorities")
            for g in priorities:
                with st.container(border=True, key=f"priority_{g.rule_id}"):
                    # Line 1: group_label (circle + SEVERITY + rule id + title + count) in bold 15px
                    st.markdown(f"**{group_label(g)}**")
                    # Line 2: category and occurrences as a 13px muted caption
                    st.caption(f"{g.category} · {g.count} occurrence(s)")
                    # Line 3: remediation in 14px normal text
                    st.write(truncate(g.remediation, 160))
    else:
        # No critical/high/medium findings - all good
        with st.container(border=True, key="top_priorities_empty"):
            st.markdown("### Top priorities")
            st.caption("No critical, high, or medium severity findings.")

    st.divider()

    # Strengths Card - OK-001 findings
    ok_findings = [f for f in result.findings if f.id.startswith("OK-") or f.id == "OK-001"]
    if ok_findings:
        with st.container(border=True, key="strengths"):
            st.markdown("### :material/check_circle: Strengths")
            for idx, f in enumerate(ok_findings[:5]):  # Limit to 5
                with st.container(border=False, key=f"strength_{f.id}_{idx}"):
                    st.markdown(f"✅ **{f.title}**")
                    st.caption(truncate(f.description, 160))

            if len(ok_findings) > 5:
                st.caption(f"+ {len(ok_findings) - 5} more")

    st.divider()

    # Executive Summary Card
    if result.summary:
        with st.container(border=True, key="executive_summary"):
            st.markdown(f"### :material/summarize: {_t('tab_report', lang)}")
            st.markdown(
                f'<div style="color: var(--text-primary); line-height: 1.6; '
                f'white-space: pre-wrap;">{result.summary}</div>',
                unsafe_allow_html=True,
            )
