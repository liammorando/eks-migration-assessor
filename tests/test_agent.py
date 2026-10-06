from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from assessor.agent import (
    _make_tools_for_testing,
    _run_scan,
    ask,
    build_model,
    get_model_error,
    summarize,
)
from assessor.models import AssessmentResult


class TestAgentModel:
    def test_build_model_none_provider(self):
        """Test that build_model returns None when MODEL_PROVIDER=none."""
        os.environ["MODEL_PROVIDER"] = "none"
        try:
            model = build_model()
            assert model is None
            assert get_model_error() == "MODEL_PROVIDER=none"
        finally:
            os.environ.pop("MODEL_PROVIDER", None)

    def test_build_model_no_ollama(self):
        """Test that build_model returns None when Ollama is unreachable."""
        from assessor.agent import _reset_model_cache
        _reset_model_cache()
        os.environ["MODEL_PROVIDER"] = "ollama"
        os.environ["OLLAMA_HOST"] = "http://127.0.0.1:9999"  # Unreachable
        try:
            model = build_model()
            assert model is None
            error = get_model_error()
            assert error is not None
            assert "Ollama unavailable" in error or "Failed to import" in error
        finally:
            os.environ.pop("MODEL_PROVIDER", None)
            os.environ.pop("OLLAMA_HOST", None)
            _reset_model_cache()


class TestAgentScan:
    def test_run_scan_stateful_app(self):
        """Test running scan on stateful-app fixture."""
        fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
        findings, score, readiness, plan = _run_scan(fixture)

        assert len(findings) > 0
        assert isinstance(score, int)
        assert 0 <= score <= 100
        assert readiness in ["Ready", "Ready with minor changes", "Needs significant work", "Not ready"]
        assert isinstance(plan, list)


class TestAgentSummarize:
    def test_summarize_no_model(self):
        """Test that summarize returns None when no model is available."""
        os.environ["MODEL_PROVIDER"] = "none"
        try:
            fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
            findings, score, readiness, plan = _run_scan(fixture)
            result = AssessmentResult(
                repo_url=f"file://{fixture}",
                files_scanned=len(list(fixture.rglob("*"))),
                findings=findings,
                score=score,
                readiness=readiness,
                plan=plan,
            )
            summary = summarize(result, plan, fixture)
            assert summary is None
        finally:
            os.environ.pop("MODEL_PROVIDER", None)


class TestAgentAsk:
    def test_ask_no_model(self):
        """Test that ask returns a message when LLM is disabled."""
        os.environ["MODEL_PROVIDER"] = "none"
        try:
            fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
            answer = ask(fixture, "What are the main issues?")
            assert "LLM is disabled" in answer
        finally:
            os.environ.pop("MODEL_PROVIDER", None)


class TestAgentTools:
    def test_list_repo_files(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "ready-app"
        tools = _make_tools_for_testing(fixture)
        list_repo_files = next(t for t in tools if t.tool_name == "list_repo_files")
        files = list_repo_files()
        assert len(files) > 0
        assert "app.py" in files

    def test_read_repo_file(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "ready-app"
        tools = _make_tools_for_testing(fixture)
        read_repo_file = next(t for t in tools if t.tool_name == "read_repo_file")
        content = read_repo_file("app.py")
        assert "Flask" in content
        assert len(content) > 0

    def test_read_repo_file_path_traversal(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "ready-app"
        tools = _make_tools_for_testing(fixture)
        read_repo_file = next(t for t in tools if t.tool_name == "read_repo_file")
        # Try to read outside the repo
        content = read_repo_file("../stateful-app/app.py")
        assert content == ""

    def test_search_repo(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
        tools = _make_tools_for_testing(fixture)
        search_repo = next(t for t in tools if t.tool_name == "search_repo")
        results = search_repo("SECRET_KEY")
        assert len(results) >= 1
        assert any("SECRET_KEY" in r["text"] for r in results)

    def test_run_scan(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "ready-app"
        tools = _make_tools_for_testing(fixture)
        run_scan = next(t for t in tools if t.tool_name == "run_scan")
        result = run_scan()
        data = json.loads(result)
        assert "findings" in data
        assert "score" in data
        assert "readiness" in data

    def test_get_score(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "ready-app"
        tools = _make_tools_for_testing(fixture)
        get_score = next(t for t in tools if t.tool_name == "get_score")
        result = get_score()
        assert "score" in result
        assert "readiness" in result
        assert "total_findings" in result


def _ollama_reachable() -> bool:
    """Check if Ollama is reachable."""
    import urllib.request
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        urllib.request.urlopen(f"{host}/api/tags", timeout=2)
        return True
    except Exception:
        return False


def _ollama_reachable_decorator(test_class):
    """Decorator to skip tests if Ollama is not reachable."""
    def _should_skip() -> bool:
        return (
            os.getenv("MODEL_PROVIDER", "ollama").lower() == "none" or
            not _ollama_reachable()
        )
    return pytest.mark.skipif(
        _should_skip,
        reason="Ollama not running or MODEL_PROVIDER=none"
    )(test_class)


@_ollama_reachable_decorator
class TestAgentWithLLM:
    def test_summarize_with_llm(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
        findings, score, readiness, plan = _run_scan(fixture)
        result = AssessmentResult(
            repo_url=f"file://{fixture}",
            files_scanned=len(list(fixture.rglob("*"))),
            findings=findings,
            score=score,
            readiness=readiness,
            plan=plan,
        )
        summary = summarize(result, plan, fixture)
        assert summary is not None
        assert len(summary) > 0

    def test_ask_with_llm(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
        answer = ask(fixture, "What is the main security issue?")
        assert len(answer) > 0
        assert "LLM is disabled" not in answer
