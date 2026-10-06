import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'app')

# Test the exact flow
from unittest.mock import patch
from pathlib import Path

def mock_clone_repo(url, workspace, **kwargs):
    print(f'mock_clone_repo called with url={url}', flush=True)
    return Path('/tmp/test')

def mock_validate(url):
    print(f'mock_validate called with url={url}', flush=True)
    return url

with patch('assessor.service.clone_repo', side_effect=mock_clone_repo):
    with patch('assessor.service.validate_repo_url', side_effect=mock_validate):
        with patch('assessor.repo.clone_repo', side_effect=mock_clone_repo):
            with patch('assessor.repo.validate_repo_url', side_effect=mock_validate):
                with patch('app.ui.analyze.validate_repo_url', side_effect=mock_validate):
                    # Now import and test
                    from app.ui.analyze import render_analyze_card
                    print('Import successful')
                    import streamlit as st
                    from streamlit.testing.v1 import AppTest
                    
                    test_script = '''
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, r"C:/Users/Liam/Documents/Default Project/src")
sys.path.insert(0, r"C:/Users/Liam/Documents/Default Project/app")

from app.ui.analyze import render_analyze_card
from unittest.mock import patch

def mock_clone_repo(url, workspace, **kwargs):
    print(f"mock_clone_repo called with url={url}", flush=True)
    return Path("/tmp/test")

def mock_validate(url):
    print(f"mock_validate called with url={url}", flush=True)
    return url

with patch("assessor.service.clone_repo", side_effect=mock_clone_repo):
    with patch("assessor.service.validate_repo_url", side_effect=mock_validate):
        with patch("assessor.repo.clone_repo", side_effect=mock_clone_repo):
            with patch("assessor.repo.validate_repo_url", side_effect=mock_validate):
                with patch("app.ui.analyze.validate_repo_url", side_effect=mock_validate):
                    st.set_page_config(page_title="Test", layout="wide")
                    render_analyze_card(
                        workspace_dir=Path("/tmp/workspace"),
                        reports_dir=Path("/tmp/reports"),
                        session_reports_dir=Path("/tmp/reports/session"),
                        max_repo_mb=100,
                        use_llm=False,
                        ollama_host="http://localhost:11434",
                        ollama_model="llama3.2",
                    )
'''
                    at = AppTest.from_string(test_script, default_timeout=30)
                    at.run()
                    print('AppTest ran')
                    print('Exception:', at.exception)
                    
                    # Check for buttons and interact
                    print('Buttons:', at.get("button"))
                    text_inputs = at.get("text_input")
                    print('Text inputs:', len(text_inputs))
                    if text_inputs:
                        text_inputs[0].input("https://github.com/test/stateful-app").run()
                        print('After input')
                        buttons = at.get("button")
                        print('Buttons after input:', buttons)
                        for b in buttons:
                            label = getattr(b, "label", "")
                            if "Analyze" in label or "search" in str(label).lower():
                                print(f'Clicking analyze button: {label}')
                                b.click().run()
                                print('After click')
                                print('Exception:', at.exception)
                                print('Session state:', at.session_state)
                                break