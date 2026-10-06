import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'app')

from unittest.mock import patch
from pathlib import Path
import os

BASE_DIR = Path(r"C:\Users\Liam\Documents\Default Project")
os.chdir(BASE_DIR)

def mock_clone_repo(url, workspace, **kwargs):
    raise TimeoutError("git clone timed out after 30s")

def mock_validate(url):
    if url.startswith("https://github.com/test/") or url.startswith("https://gitlab.com/test/"):
        return url
    raise ValueError("Invalid repository URL")

with patch('assessor.service.clone_repo', side_effect=mock_clone_repo):
    with patch('assessor.service.validate_repo_url', side_effect=mock_validate):
        with patch('assessor.repo.clone_repo', side_effect=mock_clone_repo):
            with patch('assessor.repo.validate_repo_url', side_effect=mock_validate):
                with patch('app.ui.analyze.validate_repo_url', side_effect=mock_validate):
                    import streamlit as st
                    from streamlit.testing.v1 import AppTest
                    
                    app_path = str(BASE_DIR / "app" / "streamlit_app.py")
                    at = AppTest.from_file(app_path, default_timeout=30)
                    at.run()
                    print('Initial run done')
                    
                    # Enter valid URL
                    text_inputs = at.get("text_input")
                    url_input = text_inputs[0]
                    url_input.input("https://github.com/test/repo").run()
                    print('After URL input')
                    
                    # Click Analyze
                    buttons = at.get("button")
                    analyze_btn = None
                    for b in buttons:
                        label = getattr(b, "label", "")
                        if "Analyze" in label or "search" in str(label).lower():
                            analyze_btn = b
                            break
                    
                    analyze_btn.click().run()
                    print('After analyze click')
                    print('Exception:', at.exception)
                    
                    # Run again to see if error appears
                    at.run()
                    print('After second run')
                    print('Exception:', at.exception)
                    
                    # Check all elements
                    print('\nAll elements:')
                    for attr in ['error', 'status', 'exception', 'info', 'warning', 'toast', 'markdown', 'text']:
                        elements = at.get(attr)
                        if elements:
                            print(f'  {attr}: {len(elements)}')
                            for i, el in enumerate(elements[:3]):
                                val = getattr(el, "value", "")
                                if val:
                                    print(f'    [{i}] {val[:200]}')
                                else:
                                    print(f'    [{i}] {el}')