"""Theme CSS injection for Streamlit app - Design System Implementation."""
from __future__ import annotations

import streamlit as st

_CSS = """
/* ============================================================
   EKS Migration Assessor - Design System CSS
   ============================================================ */

/* 1. CSS CUSTOM PROPERTIES (Design Tokens) */
:root {
  /* Dark Mode (Default) */
  --bg: #0B1220;
  --surface: #111A2C;
  --surface-2: #16223A;
  --border: #22314D;
  --text: #E6EDF7;
  --muted: #8FA1BF;
  --primary: #3B82F6;
  --success: #22C55E;
  --warning: #F59E0B;
  --danger: #EF4444;

  /* Severity (15% opacity bg, full color text) */
  --sev-critical: #EF4444;
  --sev-high: #F97316;
  --sev-medium: #EAB308;
  --sev-low: #22C55E;
  --sev-info: #38BDF8;

  /* Spacing */
  --space-1: 4px; --space-2: 8px; --space-3: 12px;
  --space-4: 16px; --space-5: 20px; --space-6: 24px;
  --space-8: 32px; --space-12: 48px;

  /* Border Radius */
  --radius-card: 10px;
  --radius-badge: 999px;

  /* Typography */
  --font-stack: Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}

/* 2. RESET & BASE */
.main .block-container,
[data-testid="stMainBlockContainer"] {
  max-width: 1200px !important;
  margin: 0 auto !important;
  padding-top: 2rem !important;
  padding-bottom: 3rem !important;
}

footer { visibility: hidden !important; }
.stDeployButton { display: none !important; }

/* Focus States */
*:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 3px var(--primary) !important;
  border-radius: 4px !important;
}

/* Skip Link - hidden until focus */
.skip-link {
  position: absolute; left: -9999px; top: auto;
  padding: var(--space-2) var(--space-4);
  background: var(--primary); color: white;
  border-radius: var(--radius-card); z-index: 9999;
}
.skip-link:focus { left: 8px; top: 8px; }

/* Hide "Press Enter to apply" hint */
[data-testid="InputInstructions"] { display: none !important; }

/* 3. TYPOGRAPHY */
html { font-family: var(--font-stack); font-size: 14px; }
.muted, .stCaption, [data-testid="stCaption"] { font-size: 12px !important; color: var(--muted) !important; }
[data-testid="stMarkdownContainer"] p { font-size: 14px; }
.stMarkdown { font-size: 14px; }

/* Sidebar labels - not uppercase 9px */
section[data-testid="stSidebar"] .stMarkdown { font-size: 14px !important; }
section[data-testid="stSidebar"] label { font-size: 14px !important; text-transform: none !important; }

/* Tab labels - 15px, remove icon prefix text */
.stTabs [data-baseweb="tab"] { font-size: 15px !important; }

/* 4. COMPONENTS - Only for .st-key-* containers */
.st-key-hero,
.st-key-sidebar-section,
.st-key-sidebar-section .stMarkdown,
.st-key-findings_toolbar,
.st-key-empty_findings,
.st-key-empty_plan,
.st-key-empty_report,
.st-key-step_1, .st-key-step_2, .st-key-step_3,
.st-key-kpi_score, .st-key-kpi_findings, .st-key-kpi_files, .st-key-kpi_repo,
.st-key-top_priorities, .st-key-top_priorities_empty,
.st-key-priority_*, .st-key-strengths, .st-key-strength_*,
.st-key-executive_summary,
.st-key-report_content, .st-key-empty_report,
.st-key-phase_* {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-card) !important;
  padding: var(--space-5) !important;
}

/* Gap between cards */
.st-key-kpi_score,
.st-key-kpi_findings,
.st-key-kpi_files,
.st-key-kpi_repo,
.st-key-top_priorities,
.st-key-top_priorities_empty,
.st-key-priority_*,
.st-key-strengths,
.st-key-executive_summary,
.st-key-report_content,
.st-key-empty_report,
.st-key-phase_* {
  margin-bottom: var(--space-4) !important;
}

/* KPI cards min-height fallback (if height param not supported) */
.st-key-kpi_score,
.st-key-kpi_findings,
.st-key-kpi_files,
.st-key-kpi_repo {
  min-height: 190px !important;
}

/* Ensure card content doesn't overflow */
.st-key-kpi_score,
.st-key-kpi_findings,
.st-key-kpi_files,
.st-key-kpi_repo {
  overflow: hidden !important;
}

/* Buttons */
.stButton > button[kind="primary"] {
  background: var(--primary) !important;
  color: white !important;
  border: none !important;
  border-radius: var(--radius-card) !important;
  font-weight: 600 !important;
}
.stButton > button:not([kind="primary"]) {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-card) !important;
  font-weight: 500 !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div[data-baseweb="select"] > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-card) !important;
  color: var(--text) !important;
}
.stTextInput > div > div > input:focus,
.stSelectbox > div > div > div[data-baseweb="select"]:focus-within {
  border-color: var(--primary) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  gap: var(--space-2); background: transparent;
  border-bottom: 2px solid var(--border); padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-radius: var(--radius-card) var(--radius-card) 0 0 !important;
  color: var(--muted) !important; font-weight: 500 !important;
  padding: 12px 20px !important; border: none !important;
}
.stTabs [aria-selected="true"] {
  color: var(--primary) !important; background: transparent !important;
}
.stTabs [aria-selected="true"]::after {
  content: ""; display: block; height: 3px;
  background: var(--primary); border-radius: 3px 3px 0 0; margin-top: -2px;
}

/* Metric */
[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-card) !important;
  padding: var(--space-4) !important;
}
[data-testid="stMetricLabel"] { font-size: 13px !important; font-weight: 500 !important; color: var(--muted) !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }
[data-testid="stMetricValue"] { font-size: 32px !important; font-weight: 700 !important; color: var(--primary) !important; font-variant-numeric: tabular-nums !important; }

/* Badge / Pill */
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 2px 10px; border-radius: var(--radius-badge); font-size: 12px; font-weight: 700; line-height: 1; }
.badge-critical { background: rgba(239,68,68,0.15); color: var(--sev-critical); }
.badge-high { background: rgba(249,115,22,0.15); color: var(--sev-high); }
.badge-medium { background: rgba(234,179,8,0.15); color: var(--sev-medium); }
.badge-low { background: rgba(34,197,94,0.15); color: var(--sev-low); }
.badge-info { background: rgba(56,189,248,0.15); color: var(--sev-info); }

/* Status Indicator */
.status-indicator { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: var(--radius-card); font-size: 13px; font-weight: 500; }
.status-connected { background: rgba(34,197,94,0.15); color: var(--success); }
.status-disconnected { background: rgba(239,68,68,0.15); color: var(--danger); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }

/* Header Layout */
.app-header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-4) 0; border-bottom: 1px solid var(--border); margin-bottom: var(--space-6); }
.app-header-left { display: flex; align-items: center; gap: var(--space-3); }
.app-title-block { display: flex; flex-direction: column; }
.app-title { font-size: 28px; font-weight: 700; color: var(--text); margin: 0; line-height: 1.2; }
.app-subtitle { font-size: 14px; color: var(--muted); margin: 4px 0 0 0; }
.app-header-right { display: flex; align-items: center; justify-content: flex-end; min-width: 120px; }

/* Footer */
.app-footer { margin-top: var(--space-12); padding-top: var(--space-6); border-top: 1px solid var(--border); text-align: center; color: var(--muted); font-size: 12px; }
"""

def inject_css() -> None:
    """Inject the design system CSS into the Streamlit app."""
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)
