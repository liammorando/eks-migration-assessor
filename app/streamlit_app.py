from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from assessor.i18n import get_text
from assessor.models import AssessmentResult, PlanStep
from assessor.ui_helpers import relative_time, validate_ollama_host
from ui import (
    inject_css,
    render_analyze_card,
    render_empty_state,
    render_findings_tab,
    render_header,
    render_plan_tab,
    render_report_tab,
    render_results_overview,
)

# --- Page Config ---
st.set_page_config(
    page_title="EKS Migration Readiness Assessor",
    page_icon=":material/cloud:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Inject Design System CSS ---
inject_css()

# --- Constants ---
MAX_REPO_MB = int(os.getenv("MAX_REPO_MB", "100"))
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "./workspace")).resolve()
REPORTS_DIR = WORKSPACE_DIR / "reports"

# --- Session ID for isolation ---
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

SESSION_REPORTS_DIR = REPORTS_DIR / st.session_state["session_id"]
SESSION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize session state for history
if "history" not in st.session_state:
    st.session_state["history"] = []


def t(key: str) -> str:
    """Get translation for current language."""
    lang = st.session_state.get("lang", "en")
    return get_text(key, lang)


# --- Sidebar ---
def render_sidebar() -> tuple[bool, str, str, int]:
    """Render sidebar and return (use_llm, ollama_host, ollama_model, max_mb)."""
    with st.sidebar:
        # Analysis section header
        st.subheader(t("settings"))

        # LLM Configuration - toggle only (no duplicate sub-header)
        use_llm = st.toggle(
            t("use_llm"),
            value=st.session_state.get("use_llm", False),
            help=t("use_llm_help"),
            key="use_llm_toggle",
        )

        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

        # Initialize ollama_status in session state if not present
        if "ollama_status" not in st.session_state:
            st.session_state["ollama_status"] = ("pending", "Not checked")

        if use_llm:
            with st.expander("LLM settings", expanded=True):
                ollama_host = st.text_input(
                    t("ollama_host"),
                    value=st.session_state.get("ollama_host", ollama_host),
                    help=t("ollama_host_help") + " (Press Enter or click outside to apply)",
                    key="ollama_host_input",
                    on_change=lambda: st.session_state.update({"_ollama_host_changed": True}),
                )
                ollama_model = st.text_input(
                    t("ollama_model"),
                    value=st.session_state.get("ollama_model", ollama_model),
                    help=t("ollama_model_help") + " (Press Enter or click outside to apply)",
                    key="ollama_model_input",
                    on_change=lambda: st.session_state.update({"_ollama_model_changed": True}),
                )

                # Validate and ping Ollama on change
                if st.session_state.get("_ollama_host_changed") or st.session_state.get(
                    "_ollama_model_changed"
                ):
                    st.session_state["_ollama_host_changed"] = False
                    st.session_state["_ollama_model_changed"] = False
                    ok, msg = validate_ollama_host(ollama_host)
                    if not ok:
                        st.session_state["ollama_status"] = ("error", msg)
                    else:
                        try:
                            import json as json_mod
                            import urllib.request

                            req = urllib.request.Request(f"{ollama_host}/api/tags")
                            response = urllib.request.urlopen(req, timeout=3)
                            data = json_mod.loads(response.read())
                            models = [m["name"] for m in data.get("models", [])]
                            st.session_state["ollama_status"] = (
                                "success",
                                f"Connected, {len(models)} model(s)",
                            )
                        except Exception as e:
                            st.session_state["ollama_status"] = (
                                "error",
                                f"Not reachable: {e}",
                            )

                # Show status from session state
                ollama_status = st.session_state["ollama_status"]
                if ollama_status[0] == "success":
                    status_class = "status-connected"
                elif ollama_status[0] == "error":
                    status_class = "status-disconnected"
                else:
                    status_class = "status-disconnected"
                st.markdown(
                    f"""
                    <div class="status-indicator {status_class}">
                        <span class="status-dot"></span>
                        <span>{ollama_status[1]}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption(t("ollama_status"))

        # Divider between Analysis and History
        st.divider()

        # Analysis Settings (compact)
        max_mb = st.number_input(
            t("max_repo_size"),
            min_value=10,
            max_value=MAX_REPO_MB,
            value=min(100, MAX_REPO_MB),
            step=10,
            label_visibility="collapsed",
            key="max_mb_input",
        )

        # Divider between Analysis and History
        st.divider()

        # History section
        st.subheader(t("history"))
        if st.session_state["history"]:
            for i, entry in enumerate(st.session_state["history"][:10]):
                with st.container(border=True, key=f"history_{i}"):
                    st.markdown(f"**{entry['repo_name']}**")
                    st.caption(f"Score: {entry['score']} · {relative_time(entry['timestamp'])}")
                    if st.button("Load", key=f"load_{entry['id']}", use_container_width=True):
                        # Load the report
                        md_path = Path(entry["md_path"])
                        json_path = Path(entry["json_path"])
                        if json_path.exists():
                            with open(json_path) as f:
                                data = json.load(f)
                            result = AssessmentResult(
                                **{k: v for k, v in data.items() if k != "plan"}
                            )
                            result.plan = [PlanStep(**p) for p in data.get("plan", [])]
                            with open(md_path) as f:
                                md_content = f.read()
                            st.session_state["loaded_result"] = result
                            st.session_state["loaded_plan"] = result.plan
                            st.session_state["loaded_md"] = md_content
                            st.session_state["loaded_md_path"] = md_path
                            st.rerun()
        else:
            st.caption(t("no_reports"))

        # Divider between History and Environment
        st.divider()

        # Footer: Environment expander
        with st.expander("Environment", expanded=False):
            st.code(f"Workspace: {WORKSPACE_DIR}")
            st.code(f"Session: {st.session_state['session_id']}")
            st.caption(t("footer_warn"))

    return use_llm, ollama_host, ollama_model, max_mb


# --- Main ---
def main() -> None:
    # Render header
    render_header()

    # Render sidebar and get settings
    use_llm, ollama_host, ollama_model, max_mb = render_sidebar()

    # ALWAYS render analyze card (compact when results exist)
    render_analyze_card(
        workspace_dir=WORKSPACE_DIR,
        reports_dir=REPORTS_DIR,
        session_reports_dir=SESSION_REPORTS_DIR,
        max_repo_mb=MAX_REPO_MB,
        use_llm=use_llm,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
    )

    # Check if we have analysis results
    has_results = st.session_state.get("analysis_done") or "loaded_result" in st.session_state

    if not has_results:
        # Empty state - show step cards
        render_empty_state()
    else:
        # Load result
        if "loaded_result" in st.session_state:
            result = st.session_state["loaded_result"]
            plan = st.session_state["loaded_plan"]
            md_content = st.session_state.get("loaded_md", "")
            md_path = st.session_state.get("loaded_md_path")
            loaded = True
        else:
            result = st.session_state["result"]
            plan = st.session_state["plan"]
            md_path = st.session_state.get("md_path")
            md_content = md_path.read_text() if md_path and md_path.exists() else ""
            loaded = False

        # Tabs: Overview, Findings, Migration Plan, Report, Ask the Agent
        tab_labels = [
            f":material/dashboard: {t('tab_findings').replace('Findings', 'Overview')}",
            f":material/search: {t('tab_findings')}",
            f":material/route: {t('tab_plan')}",
            f":material/description: {t('tab_report')}",
            f":material/chat: {t('tab_agent')}",
        ]
        tab_overview, tab_findings, tab_plan, tab_report, tab_agent = st.tabs(tab_labels)

        # --- Tab 1: Overview ---
        with tab_overview:
            render_results_overview(result)

        # --- Tab 2: Findings ---
        with tab_findings:
            render_findings_tab(result)

        # --- Tab 3: Migration Plan ---
        with tab_plan:
            render_plan_tab(plan)

        # --- Tab 4: Report ---
        with tab_report:
            render_report_tab(result, md_content, md_path, loaded=loaded)

        # --- Tab 5: Ask the Agent ---
        with tab_agent:
            if use_llm:
                st.caption(t("agent_caption"))

                if "chat_history" not in st.session_state:
                    st.session_state["chat_history"] = []

                # Display chat history
                for msg in st.session_state["chat_history"]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                # Determine repo root for agent
                repo_root = st.session_state.get("repo_root")
                if repo_root is None:
                    if result.repo_url.startswith("file://"):
                        repo_root = Path(result.repo_url[7:])
                    else:
                        repo_name = result.repo_url.split("/")[-1].replace(".git", "")
                        potential_root = WORKSPACE_DIR / repo_name
                        if potential_root.exists():
                            repo_root = potential_root

                # Chat input - disabled if repo doesn't exist
                if repo_root is None:
                    st.info(
                        "Chat is disabled because the repository was removed after analysis. "
                        "Re-run the analysis to enable chat.",
                        icon=":material/info:",
                    )
                    st.chat_input(t("chat_input"), disabled=True)
                else:
                    if prompt := st.chat_input(t("chat_input")):
                        st.session_state["chat_history"].append(
                            {"role": "user", "content": prompt}
                        )
                        with st.chat_message("user"):
                            st.markdown(prompt)

                        with st.chat_message("assistant"):
                            with st.spinner("Thinking..."):
                                try:
                                    from assessor.agent import ask

                                    answer = ask(
                                        repo_root,
                                        prompt,
                                        session_key=st.session_state["session_id"],
                                        ollama_host=ollama_host,
                                        ollama_model=ollama_model,
                                    )
                                    st.markdown(answer)
                                    st.session_state["chat_history"].append(
                                        {"role": "assistant", "content": answer}
                                    )
                                except Exception as e:
                                    st.error(f"Error: {e}")
                                    st.session_state["chat_history"].append(
                                        {"role": "assistant", "content": f"Error: {e}"}
                                    )
            else:
                st.info(t("agent_disabled"), icon=":material/info:")

    # Footer
    st.markdown(
        f"""
        <div class="app-footer">
            {t("footer")}<br>
            {t("footer_warn")}
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
