import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'app')

# Test the exact flow
from unittest.mock import patch
from pathlib import Path
import os

BASE_DIR = Path(r"C:\Users\Liam\Documents\Default Project")
os.chdir(BASE_DIR)

def mock_clone_repo(url, workspace, **kwargs):
    print(f'mock_clone_repo called with url={url}', flush=True)
    import shutil
    import uuid
    src = BASE_DIR / "fixtures" / "stateful-app"
    safe_name = "stateful-app".replace(".", "_").replace("-", "_")
    unique_dir = workspace / "clones" / uuid.uuid4().hex / safe_name
    unique_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, unique_dir, dirs_exist_ok=True)
    return unique_dir

def mock_validate(url):
    print(f'mock_validate called with url={url}', flush=True)
    if url.startswith("https://github.com/test/") or url.startswith("https://gitlab.com/test/"):
        return url
    if url.startswith("file://"):
        return url
    from assessor.repo import validate_repo_url as original_validate
    return original_validate(url)

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
                    print('Initial run done', flush=True)
                    
                    # Enter valid URL
                    text_inputs = at.get("text_input")
                    url_input = text_inputs[0]
                    url_input.input("https://github.com/test/stateful-app").run()
                    print('After URL input', flush=True)
                    
                    # Click Analyze
                    buttons = at.get("button")
                    analyze_btn = None
                    for b in buttons:
                        label = getattr(b, "label", "")
                        if "Analyze" in label or "search" in str(label).lower():
                            analyze_btn = b
                            break
                    
                    analyze_btn.click().run()
                    print('After analyze click', flush=True)
                    print('Exception:', at.exception, flush=True)
                    
                    # Check all element types
                    print('\n=== All Elements ===', flush=True)
                    for attr in dir(at):
                        if not attr.startswith('_') and attr not in ['run', 'session_state', '_tree', '_script_path', 'default_timeout', 'get', 'get_by_key', 'switch_page', 'exception', 'args', 'kwargs', '_page_hash', '_registered_pages', '_resolve_page_hash', '_run', '_from_string', '_bidi_component_manager', '_fragment_storage']:
                            val = getattr(at, attr, None)
                            if callable(val):
                                try:
                                    elements = val()
                                    if elements:
                                        print(f'  {attr}: {len(elements)} elements', flush=True)
                                        for i, el in enumerate(elements[:3]):
                                            print(f'    [{i}] {el}', flush=True)
                                except Exception as e:
                                    pass