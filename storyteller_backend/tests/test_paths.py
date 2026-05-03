"""Tests for the shared provider_chroma_path helper.

Pins the on-disk layout convention: <chroma_db_path>_<provider>. Both
build_database.py and retriever.py go through this helper, so this test
guards against drift between writer and reader.
"""

import pytest

from embed_retrieve.paths import provider_chroma_path
from config.settings import settings, Provider


def test_appends_gemini_suffix(monkeypatch):
    monkeypatch.setattr(settings._config, "provider", Provider.GEMINI)
    assert provider_chroma_path("data/chroma_db/odyssey") == "data/chroma_db/odyssey_gemini"


def test_appends_openai_suffix(monkeypatch):
    monkeypatch.setattr(settings._config, "provider", Provider.OPENAI)
    assert provider_chroma_path("data/chroma_db/odyssey") == "data/chroma_db/odyssey_openai"


def test_works_with_absolute_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(settings._config, "provider", Provider.GEMINI)
    base = str(tmp_path / "chroma_db" / "mahabharata")
    assert provider_chroma_path(base) == f"{base}_gemini"
