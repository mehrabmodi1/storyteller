"""Tests that build_database is registry-driven.

The bug we're guarding against: build writing to one location while retrieve
reads from another. These tests pin the contract that HybridRetrieverBuilder
resolves chroma path / collection name / bm25 path from the registry, with
the same provider suffix the retriever uses.
"""

import pytest
from unittest.mock import MagicMock

from config.settings import settings, Provider
from embed_retrieve.corpus_registry import CorpusConfig


@pytest.fixture
def fake_registry(monkeypatch):
    """Replace the global registry with a single fake corpus."""
    fake_corpus = CorpusConfig(
        name="fake_corpus",
        display_name="Fake",
        description="test",
        source_file="/tmp/fake.pdf",
        file_type="pdf",
        collection_name="fake_corpus_chunks",
        cache_dir="/tmp/fake_cache",
        bm25_index_path="/tmp/fake_bm25.pkl",
        chroma_db_path="/tmp/chroma_db/fake_corpus",
    )
    fake = MagicMock()
    fake.get_corpus.side_effect = lambda name: fake_corpus if name == "fake_corpus" else None
    fake.corpuses = {"fake_corpus": fake_corpus}
    monkeypatch.setattr("embed_retrieve.build_database.get_registry", lambda: fake)
    return fake_corpus


@pytest.fixture
def stub_heavy_init(monkeypatch):
    """Stub out chromadb + embedding client so the builder can be instantiated cheaply."""
    fake_chroma_client = MagicMock()
    fake_chroma_client.get_or_create_collection.return_value = MagicMock()

    constructed = {}

    def fake_persistent_client(path):
        constructed["chroma_path"] = path
        return fake_chroma_client

    monkeypatch.setattr(
        "embed_retrieve.build_database.chromadb.PersistentClient",
        fake_persistent_client,
    )
    monkeypatch.setattr(
        settings.__class__, "resolve_api_key", lambda self, override=None: "fake-key"
    )
    # Skip real Gemini SDK import
    fake_genai = MagicMock()
    fake_genai_types = MagicMock()
    monkeypatch.setitem(__import__("sys").modules, "google.genai", fake_genai)
    monkeypatch.setitem(__import__("sys").modules, "google.genai.types", fake_genai_types)

    return constructed


def test_build_corpus_raises_on_unknown(fake_registry):
    from embed_retrieve.build_database import build_corpus
    with pytest.raises(ValueError, match="Corpus 'nonexistent' not found"):
        build_corpus("nonexistent")


def test_builder_uses_registry_chroma_path_with_gemini_suffix(
    monkeypatch, fake_registry, stub_heavy_init
):
    monkeypatch.setattr(settings._config, "provider", Provider.GEMINI)
    from embed_retrieve.build_database import HybridRetrieverBuilder

    builder = HybridRetrieverBuilder(corpus_name="fake_corpus")

    assert stub_heavy_init["chroma_path"] == "/tmp/chroma_db/fake_corpus_gemini"
    assert builder.corpus_config.collection_name == "fake_corpus_chunks"
    assert builder.corpus_config.bm25_index_path == "/tmp/fake_bm25.pkl"


def test_builder_uses_registry_chroma_path_with_openai_suffix(
    monkeypatch, fake_registry, stub_heavy_init
):
    monkeypatch.setattr(settings._config, "provider", Provider.OPENAI)
    # OpenAI path goes through langchain_openai.OpenAIEmbeddings instead of google.genai
    monkeypatch.setitem(
        __import__("sys").modules,
        "langchain_openai",
        MagicMock(OpenAIEmbeddings=lambda **_: MagicMock()),
    )
    from embed_retrieve.build_database import HybridRetrieverBuilder

    HybridRetrieverBuilder(corpus_name="fake_corpus")

    assert stub_heavy_init["chroma_path"] == "/tmp/chroma_db/fake_corpus_openai"
