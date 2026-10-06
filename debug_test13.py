import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'app')

from pathlib import Path
from assessor.models import AssessmentResult, Finding, Severity, Category, PlanStep
from datetime import datetime, UTC

BASE_DIR = Path(r"C:\Users\Liam\Documents\Default Project")

import streamlit as st
from streamlit.testing.v1 import AppTest

app_path = str(BASE_DIR / "app" / "streamlit_app.py")
at = AppTest.from_file(app_path, default_timeout=30)
at.run()
print('Initial run done')

# Check AppTest methods
print('AppTest methods:', [x for x in dir(at) if 'tab' in x.lower() or 'switch' in x.lower()])

# Manually set session state to simulate analysis done
result = AssessmentResult(
    repo_url="https://github.com/test/stateful-app",
    scanned_at=datetime.now(UTC),
    files_scanned=3,
    findings=[
        Finding(
            id="CTR-001",
            category=Category.CONTAINER,
            severity=Severity.HIGH,
            title="No Dockerfile found",
            description="Project has no Dockerfile; cannot containerize for Kubernetes",
            file=None,
            line=None,
            evidence="No Dockerfile in repository root",
            remediation="Create a Dockerfile to containerize the application",
            eks_hint="Containerize first"
        )
    ],
    score=88,
    readiness="Ready",
    summary=None,
    plan=[
        PlanStep(phase=1, title="Containerization", why="Dockerfile, non-root user, pinned base image, health checks", actions=["Create Dockerfile for the application"], finding_ids=["CTR-001"], effort="M")
    ],
    stored_at=[]
)

plan = [
    PlanStep(phase=1, title="Containerization", why="Dockerfile, non-root user, pinned base image, health checks", actions=["Create Dockerfile for the application"], finding_ids=["CTR-001"], effort="M")
]

md_path = Path("/tmp/reports/session/report-test.md")
md_path.parent.mkdir(parents=True, exist_ok=True)
md_path.write_text("# Test Report\n\nTest content")

at.session_state["analysis_done"] = True
at.session_state["result"] = result
at.session_state["plan"] = plan
at.session_state["md_path"] = md_path
at.session_state["repo_root"] = Path("/tmp/test")
at.session_state["use_llm"] = False

at.run()
print('After setting session state and run')

# Try to switch tab by setting session state
# Streamlit tabs use session state key like "_st_tab_<hash>"
# Let's check what session state keys exist
print('Session state keys:', list(at.session_state.keys()))

# Try to find tab-related session state
for key, val in at.session_state.items():
    if 'tab' in key.lower():
        print(f'  Tab-related: {key} = {val}')