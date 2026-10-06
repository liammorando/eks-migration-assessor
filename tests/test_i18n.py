"""Tests for i18n module."""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from assessor.i18n import TRANSLATIONS, get_text, validate_key_sets


def test_key_sets_identical() -> None:
    """English and Spanish must have identical keys."""
    assert validate_key_sets()


def test_get_text_fallback() -> None:
    """Missing key returns key itself."""
    assert get_text("nonexistent_key", "en") == "nonexistent_key"
    assert get_text("nonexistent_key", "es") == "nonexistent_key"


def test_get_text_existing() -> None:
    """Existing keys return translated values."""
    assert get_text("page_title", "en") == "EKS Migration Readiness Assessor"
    assert get_text("page_title", "es") == "Evaluador de Preparación para Migración a EKS"
    assert get_text("lang_en", "en") == "EN"
    assert get_text("lang_es", "es") == "ES"


def test_all_keys_present_in_both() -> None:
    """Every key in en must exist in es and vice versa."""
    en_keys = set(TRANSLATIONS["en"].keys())
    es_keys = set(TRANSLATIONS["es"].keys())
    assert en_keys == es_keys
    # Check a few critical keys
    critical_keys = [
        "page_title",
        "title",
        "analyze_btn",
        "tab_findings",
        "tab_plan",
        "tab_report",
        "tab_agent",
        "lang_en",
        "lang_es",
    ]
    for k in critical_keys:
        assert k in en_keys
        assert k in es_keys
