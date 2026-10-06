"""Header component for the EKS Migration Assessor app."""
from __future__ import annotations

import streamlit as st

from assessor.i18n import get_available_languages, get_text

# Inline SVG logo - simple hexagon mark in primary color
_LOGO_SVG = (
    '<svg viewBox="0 0 32 32" width="32" height="32" '
    'xmlns="http://www.w3.org/2000/svg" role="img" '
    'aria-label="EKS Migration Assessor">'
    '<polygon points="16,2 30,8 30,24 16,30 2,24 2,8" '
    'fill="none" stroke="var(--primary)" stroke-width="2.5" stroke-linejoin="round"/>'
    '<polygon points="16,6 26,12 26,20 16,26 6,20 6,12" '
    'fill="var(--primary)" opacity="0.2"/>'
    '<line x1="16" y1="6" x2="16" y2="26" stroke="var(--primary)" '
    'stroke-width="1.5" stroke-linecap="round"/>'
    '<line x1="6" y1="12" x2="26" y2="20" stroke="var(--primary)" '
    'stroke-width="1.5" stroke-linecap="round"/>'
    '<line x1="26" y1="12" x2="6" y2="20" stroke="var(--primary)" '
    'stroke-width="1.5" stroke-linecap="round"/>'
    '</svg>'
)


def _t(key: str, lang: str) -> str:
    """Get translation for key."""
    return get_text(key, lang)


def render_header() -> None:
    """Render the compact header row with logo, title, tagline, and language selector."""
    lang = st.session_state.get("lang", "en")

    # Language selector - use st.segmented_control if available, otherwise st.radio
    available_langs = get_available_languages()
    lang_labels = {code: get_text(f"lang_{code}", lang) for code in available_langs}

    # Single row with logo+title in left column, language selector in right column
    header_cols = st.columns([8, 1], vertical_alignment="top")

    with header_cols[0]:
        # Static HTML block for logo + title + tagline
        header_html = f"""
        <header class="app-header">
            <div class="app-header-left">
                {_LOGO_SVG}
                <div class="app-title-block">
                    <h1 class="app-title">{_t("title", lang)}</h1>
                    <p class="app-subtitle">{_t("page_caption", lang)}</p>
                </div>
            </div>
        </header>
        """
        st.markdown(header_html, unsafe_allow_html=True)

    with header_cols[1]:
        # Language selector in the right column
        # Use label_visibility="collapsed" to hide the label but keep it for accessibility
        try:
            selected = st.segmented_control(
                label="Language",
                options=available_langs,
                format_func=lambda code: lang_labels[code],
                selection_mode="single",
                default=lang,
                key="header_lang_selector",
                label_visibility="collapsed",
            )
            if selected and selected != lang:
                st.session_state["lang"] = selected
                st.rerun()
        except AttributeError:
            # Fallback to radio horizontal
            selected = st.radio(
                label="Language",
                options=available_langs,
                format_func=lambda code: lang_labels[code],
                horizontal=True,
                index=available_langs.index(lang),
                key="header_lang_selector",
                label_visibility="collapsed",
            )
            if selected != lang:
                st.session_state["lang"] = selected
                st.rerun()
