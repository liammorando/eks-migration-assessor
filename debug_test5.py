import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'app')

import streamlit as st
from streamlit.testing.v1 import AppTest
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Liam\Documents\Default Project")

app_path = str(BASE_DIR / "app" / "streamlit_app.py")
at = AppTest.from_file(app_path, default_timeout=30)
at.run()
print('Initial run done', flush=True)

# Check elements
print('Tabs:', at.get("tabs"), flush=True)
print('Tab count:', len(at.get("tabs")), flush=True)
print('Containers:', len(at.get("container")), flush=True)
print('Markdown:', len(at.get("markdown")), flush=True)