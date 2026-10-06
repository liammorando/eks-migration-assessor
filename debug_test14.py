import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'app')

from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Liam\Documents\Default Project")

with patch("assessor.service.clone_repo", side_effect=TimeoutError("git clone timed out after 30s")):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    
    test_script = """
import streamlit as st
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, r"C:\\\\Users\\\\Liam\\\\Documents\\\\Default Project\\\\src")
sys.path.insert(0, r"C:\\\\Users\\\\Liam\\\\Documents\\\\Default Project\\\\app")

from app.ui.analyze import render_analyze_card

# Mock at the service module level where it's actually called
with patch("assessor.service.clone_repo", side_effect=TimeoutError("git clone timed out after 30s")):
    st.set_page_config(page_title="Test", layout="wide")
    render_analyze_card(
        workspace_dir=Path(r"C:\\\\Users\\\\Liam\\\\AppData\\\\Local\\\\Temp\\\\eks_assessor_test_workspace"),
        reports_dir=Path(r"C:\\\\Users\\\\Liam\\\\AppData\\\\Local\\\\Temp\\\\eks_assessor_test_workspace\\\\reports"),
        session_reports_dir=Path(r"C:\\\\Users\\\\Liam\\\\AppData\\\\Local\\\\Temp\\\\eks_assessor_test_workspace\\\\reports\\\\session"),
        max_repo_mb=100,
        use_llm=False,
        ollama_host="http://localhost:11434",
        ollama_model="llama3.2",
    )
"""
    
    at = AppTest.from_string(test_script, default_timeout=30)
    at.run()
    print('Initial run done')
    
    # Enter URL and click analyze
    text_inputs = at.get("text_input")
    if len(text_inputs) > 0:
        text_inputs[0].input("https://github.com/test/repo").run()
        print('After URL input')
        
        buttons = at.get("button")
        analyze_btn = [b for b in buttons if "Analyze" in getattr(b, "label", "") or "search" in str(getattr(b, "label", "")).lower()][0]
        analyze_btn.click().run()
        print('After analyze click')
        print('Exception:', at.exception)
        
        # Check all elements
        print('\nAll elements:')
        for attr in ['error', 'status', 'exception', 'info', 'warning', 'toast']:
            elements = at.get(attr)
            if elements:
                print(f'  {attr}: {len(elements)}')
                for i, el in enumerate(elements):
                    print(f'    [{i}] {el}')
        
        # Check markdown for error message
        markdowns = at.get("markdown")
        for i, m in enumerate(markdowns):
            val = getattr(m, "value", "")
            if val and ("timeout" in val.lower() or "error" in val.lower() or "timed out" in val.lower()):
                print(f'Markdown {i}: {val[:200]}')