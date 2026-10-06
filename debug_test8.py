import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'app')

import streamlit as st
from streamlit.testing.v1 import AppTest
from pathlib import Path
from assessor.models import AssessmentResult, Finding, Severity, Category, PlanStep
from datetime import datetime, UTC

BASE_DIR = Path(r"C:\Users\Liam\Documents\Default Project")

app_path = str(BASE_DIR / "app" / "streamlit_app.py")
at = AppTest.from_file(app_path, default_timeout=30)
at.run()
print('Initial run done', flush=True)

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

at.run()
print('After setting session state and run', flush=True)

# Check the tabs element directly from the tree
tabs_elem = at._tree.tabs
print('Tabs elem:', tabs_elem, flush=True)
print('Tabs elem type:', type(tabs_elem), flush=True)
if hasattr(tabs_elem, 'children'):
    print('Tabs children:', tabs_elem.children, flush=True)

# Also check get("tabs") 
print('\nTabs via get:', at.get("tabs"), flush=True)
print('Tab count via get:', len(at.get("tabs")), flush=True)

# Check if we can access tabs by key
print('\nTrying to get tabs by key...', flush=True)
try:
    tabs_by_key = at.get_by_key("tabs")
    print('Tabs by key:', tabs_by_key, flush=True)
except Exception as e:
    print('Error getting by key:', e, flush=True)