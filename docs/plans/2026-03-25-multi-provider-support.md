# Multi-Provider Support (Gemini + OpenAI) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Google Gemini as a configurable, zero-cost default provider alongside OpenAI for all AI capabilities (chat, embeddings, image gen).

**Architecture:** A `provider` config field (`"gemini"` | `"openai"`) in `settings.py` drives model selection. Chat completions use LangChain's `init_chat_model`, embeddings use `init_embeddings` (or direct `GoogleGenerativeAIEmbeddings` fallback), and image generation uses a provider branch (DALL-E vs Gemini). Only ChromaDB paths are provider-namespaced.

**Tech Stack:** Python 3.12, LangChain 0.3.13+, `langchain-google-genai`, `google-genai`, FastAPI, ChromaDB

**Spec:** `docs/specs/2026-03-24-gemini-provider-design.md`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `storyteller_backend/config/settings.py` | Modify | Provider config, model mappings, key resolution, startup validation |
| `storyteller_backend/services/story_agent.py` | Modify | `init_chat_model` for all 5 LLM sites, moderation skip, generalized API key |
| `storyteller_backend/services/image_generator.py` | Modify | `init_chat_model` for prompt gen, provider branch for image gen |
| `storyteller_backend/services/auth_service.py` | Modify | Guard OpenAI client creation against missing key |
| `storyteller_backend/embed_retrieve/config.py` | Modify | Remove hardcoded model constants, provider-aware ChromaDB path |
| `storyteller_backend/embed_retrieve/corpus_registry.py` | Modify | Provider-suffix in `check_corpus_status()` |
| `storyteller_backend/embed_retrieve/retriever.py` | Modify | `init_embeddings`, remove raw OpenAI client |
| `storyteller_backend/embed_retrieve/build_database.py` | Modify | `init_embeddings`, `init_chat_model` for summaries |
| `storyteller_backend/.env.example` | Modify | Add `GEMINI_API_KEY`, make `OPENAI_API_KEY` optional |
| `pyproject.toml` | Modify | Add `langchain-google-genai`, `google-genai` |
| `storyteller_backend/tests/test_settings_provider.py` | Create | Tests for provider config resolution |
| `storyteller_backend/tests/test_screen_prompt.py` | Modify | Update mocks from `ChatOpenAI` to `init_chat_model` |

---

### Task 1: Install Dependencies

**Files:**
- Modify: `pyproject.toml:8-25`

- [ ] **Step 1: Add new dependencies via Poetry**

```bash
cd storyteller_backend && poetry add langchain-google-genai google-genai
```

This adds both packages and updates `poetry.lock`.

- [ ] **Step 2: Verify installation**

```bash
cd storyteller_backend && poetry run python -c "from langchain_google_genai import ChatGoogleGenerativeAI; print('langchain-google-genai OK')"
cd storyteller_backend && poetry run python -c "from google import genai; print('google-genai OK')"
```

Expected: Both print OK.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml poetry.lock
git commit -m "deps: add langchain-google-genai and google-genai"
```

---

### Task 2: Configuration Layer (settings.py + .env.example)

**Files:**
- Modify: `storyteller_backend/config/settings.py`
- Modify: `storyteller_backend/.env.example`
- Create: `storyteller_backend/tests/test_settings_provider.py`

- [ ] **Step 1: Write failing tests for provider config**

Create `storyteller_backend/tests/test_settings_provider.py`:

```python
import pytest
from unittest.mock import patch


class TestProviderConfig:

    def test_default_provider_is_gemini(self):
        """Config defaults to gemini provider."""
        from config.settings import Config
        c = Config()
        assert c.provider == "gemini"

    def test_chat_model_resolves_for_gemini(self):
        """chat_model returns gemini model when provider=gemini."""
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "gemini"
            assert s.chat_model == "gemini-2.5-flash"

    def test_chat_model_resolves_for_openai(self):
        """chat_model returns openai model when provider=openai."""
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "openai"
            assert s.chat_model == "gpt-4o-mini"

    def test_langchain_chat_provider_mapping(self):
        """langchain_chat_provider maps gemini -> google_genai."""
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "gemini"
            assert s.langchain_chat_provider == "google_genai"

    def test_langchain_chat_provider_mapping_openai(self):
        """langchain_chat_provider maps openai -> openai."""
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "openai"
            assert s.langchain_chat_provider == "openai"

    def test_image_size_resolves_per_provider(self):
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "gemini"
            assert s.image_size == "1K"
            s._config.provider = "openai"
            assert s.image_size == "256x256"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd storyteller_backend && poetry run pytest tests/test_settings_provider.py -v
```

Expected: FAIL -- `Config` has no `provider` field, `Settings` has no `langchain_chat_provider`, etc.

- [ ] **Step 3: Implement Config changes**

In `storyteller_backend/config/settings.py`, replace the `Config` class (lines 45-92). The full new `Config` class:

```python
class Config:
    """
    Application configuration with hardcoded defaults.
    These values are NOT loaded from environment variables.
    """

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Provider Selection
    provider: Literal["gemini", "openai"] = "gemini"

    # Gemini Models
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_image_model: str = "gemini-2.5-flash-image"
    gemini_image_size: str = "1K"

    # OpenAI Models
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_image_model: str = "dall-e-2"
    openai_image_size: str = "256x256"
    openai_image_quality: str = "standard"

    # Data Paths (relative to storyteller_backend/)
    data_dir: str = "../data"
    saved_graphs_dir: str = "../saved_graphs"
    personas_file: str = "config/personas.json"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Retrieval
    retrieval_top_k: int = 10
    bm25_weight: float = 0.5
    semantic_weight: float = 0.5

    # Story Generation
    default_paragraph_count: int = 4
    min_paragraph_count: int = 1
    max_paragraph_count: int = 8
    words_per_paragraph: int = 200
    max_tokens_per_paragraph: int = 300

    # Authentication
    auth_mode: Literal["self_hosted", "per_request_key", "credit_system"] = "self_hosted"

    # Image Storage
    local_image_storage: bool = True
    image_storage_limit_mb: int = 100
```

Note: `summary_model`, `guardrail_model`, `embedding_model`, `chat_model`, `image_model`, `image_generation_size`, `image_generation_quality` are all removed from `Config`. They become computed properties on `Settings`.

- [ ] **Step 4: Implement Secrets changes**

In `storyteller_backend/config/settings.py`, update the `Secrets` class (lines 21-38):

```python
class Secrets(BaseSettings):
    """
    Secrets that must be provided via .env file.
    These are the ONLY values loaded from environment variables.
    """

    # Provider API keys (at least one required, validated by Settings)
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # OPTIONAL
    platform_openai_key: Optional[str] = None  # For credit_system mode (Phase 3+)

    model_config = {
        "env_file": str(ENV_FILE_PATH),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
```

- [ ] **Step 5: Implement Settings changes**

Replace the entire `Settings` class (lines 99-260) with:

```python
class Settings:
    """
    Combined settings object with both secrets and configuration.

    Usage:
        from config.settings import settings
        settings.chat_model      # Resolves per provider
        settings.provider        # "gemini" or "openai"
    """

    def __init__(self):
        self._secrets = Secrets()
        self._config = Config()
        self.__validate_api_key()

    def __validate_api_key(self):
        """Validate that the required API key for the active provider is present."""
        if self._config.provider == "gemini" and not self._secrets.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required in .env when provider=gemini. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        if self._config.provider == "openai" and not self._secrets.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required in .env when provider=openai. "
                "Get a key at https://platform.openai.com/api-keys"
            )

    # ============================================
    # Provider
    # ============================================
    @property
    def provider(self) -> str:
        return self._config.provider

    @property
    def langchain_chat_provider(self) -> str:
        return "google_genai" if self.provider == "gemini" else "openai"

    @property
    def langchain_embeddings_provider(self) -> str:
        return "google_genai" if self.provider == "gemini" else "openai"

    # ============================================
    # Model Resolution (provider-aware)
    # ============================================
    @property
    def chat_model(self) -> str:
        return self._config.gemini_chat_model if self.provider == "gemini" else self._config.openai_chat_model

    @property
    def embedding_model(self) -> str:
        return self._config.gemini_embedding_model if self.provider == "gemini" else self._config.openai_embedding_model

    @property
    def image_model(self) -> str:
        return self._config.gemini_image_model if self.provider == "gemini" else self._config.openai_image_model

    @property
    def image_size(self) -> str:
        return self._config.gemini_image_size if self.provider == "gemini" else self._config.openai_image_size

    @property
    def image_quality(self) -> str:
        """Only used by OpenAI/DALL-E path."""
        return self._config.openai_image_quality

    # ============================================
    # API Keys
    # ============================================
    @property
    def api_key(self) -> str:
        """Return the API key for the active provider."""
        if self.provider == "gemini":
            return self._secrets.gemini_api_key
        return self._secrets.openai_api_key

    def resolve_api_key(self, override: Optional[str] = None) -> str:
        """Return an API key, defaulting to the configured secret."""
        return override or self.api_key

    @property
    def openai_api_key(self) -> Optional[str]:
        """Direct access to OpenAI key (needed for moderation endpoint)."""
        return self._secrets.openai_api_key

    @property
    def platform_openai_key(self) -> Optional[str]:
        return self._secrets.platform_openai_key

    # ============================================
    # Configuration (direct passthrough)
    # ============================================
    @property
    def api_host(self) -> str:
        return self._config.api_host

    @property
    def api_port(self) -> int:
        return self._config.api_port

    @property
    def api_reload(self) -> bool:
        return self._config.api_reload

    @property
    def data_dir(self) -> str:
        return self._config.data_dir

    @property
    def saved_graphs_dir(self) -> str:
        return self._config.saved_graphs_dir

    @property
    def personas_file(self) -> str:
        return self._config.personas_file

    @property
    def cors_origins(self) -> List[str]:
        return self._config.cors_origins

    @property
    def retrieval_top_k(self) -> int:
        return self._config.retrieval_top_k

    @property
    def bm25_weight(self) -> float:
        return self._config.bm25_weight

    @property
    def semantic_weight(self) -> float:
        return self._config.semantic_weight

    @property
    def default_paragraph_count(self) -> int:
        return self._config.default_paragraph_count

    @property
    def min_paragraph_count(self) -> int:
        return self._config.min_paragraph_count

    @property
    def max_paragraph_count(self) -> int:
        return self._config.max_paragraph_count

    @property
    def words_per_paragraph(self) -> int:
        return self._config.words_per_paragraph

    @property
    def max_tokens_per_paragraph(self) -> int:
        return self._config.max_tokens_per_paragraph

    @property
    def auth_mode(self) -> Literal["self_hosted", "per_request_key", "credit_system"]:
        return self._config.auth_mode

    @property
    def local_image_storage(self) -> bool:
        return self._config.local_image_storage

    @property
    def image_storage_limit_mb(self) -> int:
        return self._config.image_storage_limit_mb

    # ============================================
    # Computed Properties
    # ============================================
    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).resolve()

    @property
    def saved_graphs_path(self) -> Path:
        return Path(self.saved_graphs_dir).resolve()

    @property
    def personas_path(self) -> Path:
        return Path(self.personas_file).resolve()

    @property
    def image_storage_path(self) -> Path:
        return self.saved_graphs_path / "images"


# Global settings instance
settings = Settings()
```

- [ ] **Step 6: Update .env.example**

Replace `storyteller_backend/.env.example` with:

```env
# ============================================
# STORYTELLER BACKEND - ENVIRONMENT VARIABLES
# ============================================
# This file contains ONLY secrets (API keys, connection strings).
# All other configuration is in config/settings.py with hardcoded defaults.
# Set provider in config/settings.py (default: gemini)

# ============================================
# GEMINI API Key (default provider -- free, no credit card)
# ============================================
# Get your key from https://aistudio.google.com/apikey
GEMINI_API_KEY="your-gemini-api-key-here"

# ============================================
# OPTIONAL: OpenAI API Key (only if provider=openai in settings.py)
# ============================================
# Get your key from https://platform.openai.com/api-keys
# OPENAI_API_KEY="sk-YOUR_OPENAI_API_KEY_HERE"

# ============================================
# OPTIONAL: Platform OpenAI Key (Phase 3+ - credit system mode)
# ============================================
# Only needed if you set auth_mode="credit_system" in settings.py
# PLATFORM_OPENAI_KEY="sk-YOUR_PLATFORM_OPENAI_KEY_HERE"
```

- [ ] **Step 7: Update .env for local development**

Add `GEMINI_API_KEY` to `storyteller_backend/.env` (your actual key). This file is gitignored.

- [ ] **Step 8: Run tests**

```bash
cd storyteller_backend && poetry run pytest tests/test_settings_provider.py -v
```

Expected: All PASS. (Note: the tests mock around `__validate_api_key` so they don't need real keys.)

- [ ] **Step 9: Run existing tests to check for regressions**

```bash
cd storyteller_backend && poetry run pytest tests/ -v
```

Expected: Some existing tests may fail due to `settings.summary_model` / `settings.guardrail_model` / `settings.image_generation_size` no longer existing. These will be fixed in subsequent tasks. Note which tests fail.

- [ ] **Step 10: Commit**

```bash
git add storyteller_backend/config/settings.py storyteller_backend/.env.example storyteller_backend/tests/test_settings_provider.py
git commit -m "feat: add provider config layer (gemini default, openai optional)"
```

---

### Task 3: Story Agent -- Chat Completions (story_agent.py)

**Files:**
- Modify: `storyteller_backend/services/story_agent.py`
- Modify: `storyteller_backend/tests/test_screen_prompt.py`

- [ ] **Step 1: Update imports and module-level key**

In `storyteller_backend/services/story_agent.py`, replace lines 18-45:

Replace:
```python
from langchain_openai import ChatOpenAI
```
with:
```python
from langchain.chat_models import init_chat_model
```

Replace:
```python
ACTIVE_OPENAI_API_KEY = settings.openai_api_key


def _set_active_api_key(override: Optional[str] = None) -> None:
    """Update the module-level API key used for ChatOpenAI instances."""
    global ACTIVE_OPENAI_API_KEY
    ACTIVE_OPENAI_API_KEY = settings.resolve_openai_key(override)
```
with:
```python
ACTIVE_API_KEY = settings.api_key


def _set_active_api_key(override: Optional[str] = None) -> None:
    """Update the module-level API key."""
    global ACTIVE_API_KEY
    ACTIVE_API_KEY = settings.resolve_api_key(override)
```

Keep `from openai import AsyncOpenAI` -- still needed for moderation.

- [ ] **Step 2: Update `_generate_node_summary` (line 158)**

Replace the `ChatOpenAI` instantiation:
```python
        summary_llm = ChatOpenAI(
            temperature=0,
            model_name=settings.summary_model,
            api_key=api_key,
        )
```
with:
```python
        summary_llm = init_chat_model(
            settings.chat_model,
            model_provider=settings.langchain_chat_provider,
            temperature=0,
            api_key=api_key,
        )
```

- [ ] **Step 3: Update `_check_moderation` (line 182)**

Add provider check -- skip moderation for non-OpenAI providers:

Replace the function body:
```python
async def _check_moderation(prompt: str, api_key: str) -> bool:
    """
    Returns True if the prompt passes OpenAI moderation (not flagged).
    Skipped for non-OpenAI providers (returns True).
    Fails closed: uncertain prompts are rejected.
    """
    if settings.provider != "openai":
        return True
    try:
        client = AsyncOpenAI(api_key=api_key)
        result = await client.moderations.create(input=prompt)
        return not result.results[0].flagged
    except Exception as e:
        print(f"[moderation] API error: {e}. Failing closed (reject).")
        return False
```

- [ ] **Step 4: Update `_classify_intent` (line 225)**

Replace:
```python
        classifier_llm = ChatOpenAI(
            temperature=0,
            model_name=settings.guardrail_model,
            api_key=api_key,
        ).with_structured_output(PromptScreenResult)
```
with:
```python
        classifier_llm = init_chat_model(
            settings.chat_model,
            model_provider=settings.langchain_chat_provider,
            temperature=0,
            api_key=api_key,
        ).with_structured_output(PromptScreenResult)
```

- [ ] **Step 5: Update `screen_prompt` (line 253)**

Replace:
```python
    api_key = ACTIVE_OPENAI_API_KEY
```
with:
```python
    api_key = ACTIVE_API_KEY
```

- [ ] **Step 6: Update `generate_search_query` (line 295)**

Replace:
```python
    llm_for_query = ChatOpenAI(
        temperature=0,
        model_name=settings.chat_model,
        api_key=ACTIVE_OPENAI_API_KEY,
    ).with_structured_output(SearchQuery)
```
with:
```python
    llm_for_query = init_chat_model(
        settings.chat_model,
        model_provider=settings.langchain_chat_provider,
        temperature=0,
        api_key=ACTIVE_API_KEY,
    ).with_structured_output(SearchQuery)
```

- [ ] **Step 7: Update `generate_story` (line 430)**

Replace:
```python
    story_llm = ChatOpenAI(
        temperature=0.9,
        model_name=settings.chat_model,
        streaming=True,
        api_key=ACTIVE_OPENAI_API_KEY,
        max_tokens=token_ceiling,
    )
```
with:
```python
    story_llm = init_chat_model(
        settings.chat_model,
        model_provider=settings.langchain_chat_provider,
        temperature=0.9,
        streaming=True,
        api_key=ACTIVE_API_KEY,
        max_tokens=token_ceiling,
    )
```

- [ ] **Step 8: Update `generate_choices` (line 592)**

Replace:
```python
    choices_llm = ChatOpenAI(
        temperature=0.7,
        model_name=settings.chat_model,
        api_key=ACTIVE_OPENAI_API_KEY,
    ).with_structured_output(Choices)
```
with:
```python
    choices_llm = init_chat_model(
        settings.chat_model,
        model_provider=settings.langchain_chat_provider,
        temperature=0.7,
        api_key=ACTIVE_API_KEY,
    ).with_structured_output(Choices)
```

- [ ] **Step 9: Update `update_graph_with_story` (line 527)**

Replace:
```python
    summary = await _generate_node_summary(story, last_message, ACTIVE_OPENAI_API_KEY)
```
with:
```python
    summary = await _generate_node_summary(story, last_message, ACTIVE_API_KEY)
```

- [ ] **Step 10: Update `get_story_agent` (line 722)**

Replace:
```python
    resolved_key = settings.resolve_openai_key(api_key)
```
with:
```python
    resolved_key = settings.resolve_api_key(api_key)
```

- [ ] **Step 11: Update test mocks in `test_screen_prompt.py`**

In `TestClassifyIntent`, replace both occurrences of:
```python
        with patch("services.story_agent.ChatOpenAI", return_value=mock_llm):
```
with:
```python
        with patch("services.story_agent.init_chat_model", return_value=mock_llm):
```

In `TestCheckModeration`, add a new test for Gemini skip:

```python
    @pytest.mark.asyncio
    async def test_skips_moderation_for_non_openai_provider(self):
        with patch("services.story_agent.settings") as mock_settings:
            mock_settings.provider = "gemini"
            result = await _check_moderation("any prompt", "test-key")
        assert result is True
```

- [ ] **Step 12: Run tests**

```bash
cd storyteller_backend && poetry run pytest tests/test_screen_prompt.py -v
```

Expected: All PASS.

- [ ] **Step 13: Commit**

```bash
git add storyteller_backend/services/story_agent.py storyteller_backend/tests/test_screen_prompt.py
git commit -m "feat: switch story_agent to init_chat_model, provider-agnostic"
```

---

### Task 4: Embeddings -- Config and Retriever (embed_retrieve/)

**Files:**
- Modify: `storyteller_backend/embed_retrieve/config.py`
- Modify: `storyteller_backend/embed_retrieve/retriever.py`

- [ ] **Step 1: Update `embed_retrieve/config.py`**

Replace the entire file with:

```python
# Configuration for the data processing pipeline

from config.settings import settings

# --- Chunking Parameters ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# --- Contextualization Parameters ---
CONTEXT_WINDOW_SIZE = 5000
CONTEXT_SUMMARY_TOKENS = 200

# --- Path Parameters ---
CACHE_DIR = "data/processed_chunks"

def get_chroma_db_path() -> str:
    """Provider-namespaced ChromaDB path."""
    return f"data/chroma_db_{settings.provider}"

CHROMA_COLLECTION_NAME = "mahabharata_chunks"
PDF_PATH = "raw_texts/The Complete Mahabharata .pdf"
BM25_INDEX_PATH = "data/bm25_index.pkl"
```

Note: `EMBEDDING_MODEL` and `CONTEXT_MODEL` constants are removed. `CHROMA_DB_PATH` becomes `get_chroma_db_path()`.

- [ ] **Step 2: Update `embed_retrieve/retriever.py`**

Replace the entire file. Key changes: remove `import openai`, replace OpenAI client with `init_embeddings`, use provider-suffixed ChromaDB path.

```python
import chromadb
import pickle
from typing import List, Dict, Optional

from langchain.embeddings import init_embeddings
from .corpus_registry import get_registry
from models.chunk import Chunk
from . import config
from config.settings import settings


def _get_embeddings_model():
    """Create a provider-agnostic embeddings model via LangChain."""
    try:
        return init_embeddings(
            settings.embedding_model,
            provider=settings.langchain_embeddings_provider,
            api_key=settings.api_key,
        )
    except Exception:
        if settings.provider == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model=settings.embedding_model,
                google_api_key=settings.api_key,
            )
        else:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model=settings.embedding_model,
                api_key=settings.api_key,
            )


def _provider_chroma_path(base_path: str) -> str:
    """Append provider suffix to a ChromaDB base path."""
    return f"{base_path}_{settings.provider}"


class HybridRetriever:
    """
    Performs hybrid search by combining results from a keyword-based (BM25)
    and a semantic (ChromaDB) search system using Reciprocal Rank Fusion.
    """

    def __init__(self, corpus_name: Optional[str] = None, api_key: Optional[str] = None):
        self.embeddings = _get_embeddings_model()

        # Get corpus configuration
        self.corpus_name = corpus_name or "mahabharata"
        self.registry = get_registry()
        self.corpus_config = self.registry.get_corpus(self.corpus_name)

        if not self.corpus_config:
            raise ValueError(f"Corpus '{self.corpus_name}' not found in registry. Available corpuses: {list(self.registry.corpuses.keys())}")

        if not self.corpus_config.is_active:
            raise ValueError(f"Corpus '{self.corpus_name}' is not active.")

        # Load ChromaDB with provider-namespaced path
        chroma_path = _provider_chroma_path(self.corpus_config.chroma_db_path)
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.chroma_collection = self.chroma_client.get_collection(name=self.corpus_config.collection_name)

        # Load BM25 Index (shared, not provider-namespaced)
        try:
            with open(self.corpus_config.bm25_index_path, "rb") as f:
                bm25_data = pickle.load(f)
                self.bm25_index = bm25_data['model']
                self.bm25_chunk_ids = bm25_data['chunk_ids']
        except FileNotFoundError:
            raise FileNotFoundError(f"BM25 index not found at {self.corpus_config.bm25_index_path}. Please run the build script first for corpus '{self.corpus_name}'.")

    def _get_query_embedding(self, query: str) -> List[float]:
        try:
            return self.embeddings.embed_query(query)
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return []

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Performs a hybrid search and returns a ranked list of results.
        """
        if not query:
            return []

        # 1. Semantic Search (ChromaDB)
        query_embedding = self._get_query_embedding(query)
        semantic_results = self.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        semantic_ids = semantic_results['ids'][0]

        # 2. Keyword Search (BM25)
        tokenized_query = query.lower().split(" ")
        bm25_scores = self.bm25_index.get_scores(tokenized_query)

        top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
        keyword_ids = [self.bm25_chunk_ids[i] for i in top_bm25_indices]

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_k = 60
        fused_scores: Dict[str, float] = {}

        for rank, doc_id in enumerate(semantic_ids):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (rrf_k + rank + 1)

        for rank, doc_id in enumerate(keyword_ids):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (rrf_k + rank + 1)

        # 4. Sort by fused score
        reranked_results = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)

        # 5. Fetch full documents for the top results
        final_results = []
        top_ids = [doc_id for doc_id, _ in reranked_results[:top_k]]

        if not top_ids:
            return []

        retrieved_docs = self.chroma_collection.get(
            ids=top_ids,
            include=['metadatas', 'documents']
        )

        docs_map: Dict[str, Dict] = {}
        for i, doc_id in enumerate(retrieved_docs['ids']):
            docs_map[doc_id] = {
                "metadata": retrieved_docs['metadatas'][i],
                "document": retrieved_docs['documents'][i]
            }

        for doc_id, score in reranked_results[:top_k]:
            doc_info = docs_map.get(doc_id)
            if doc_info:
                final_results.append({
                    "chunk_id": doc_id,
                    "score": score,
                    "base_text": doc_info['metadata'].get('base_text', 'Base text not found'),
                    "context": doc_info['document'].split('\\n\\nText:')[0].replace('Context: ', ''),
                })

        return final_results
```

- [ ] **Step 3: Verify no references to removed constants**

```bash
cd storyteller_backend && grep -rn "config\.EMBEDDING_MODEL\|config\.CONTEXT_MODEL\|config\.CHROMA_DB_PATH" embed_retrieve/ --include="*.py"
```

Expected: Only `build_database.py` references remain (fixed in Task 5). No references in `retriever.py`.

- [ ] **Step 4: Commit**

```bash
git add storyteller_backend/embed_retrieve/config.py storyteller_backend/embed_retrieve/retriever.py
git commit -m "feat: switch retriever to init_embeddings, provider-namespaced ChromaDB"
```

---

### Task 5: Embeddings -- Build Database (build_database.py)

**Files:**
- Modify: `storyteller_backend/embed_retrieve/build_database.py`

- [ ] **Step 1: Update imports**

Replace lines 1-16 with:

```python
import fitz  # PyMuPDF
import tiktoken
import os
from typing import List, Optional
import chromadb
import json
from tqdm import tqdm
import pickle
from rank_bm25 import BM25Okapi
import argparse

from langchain.chat_models import init_chat_model
from langchain.embeddings import init_embeddings
from . import config
from models.chunk import Chunk, DocumentPosition
from config.settings import settings
```

- [ ] **Step 2: Update `__init__`**

Replace lines 27-48 with:

```python
    def __init__(self, pdf_path: str, api_key: Optional[str] = None):
        self.api_key = settings.resolve_api_key(api_key)
        self.pdf_path = pdf_path

        # Tokenizer for chunking (OpenAI tokenizer used for text splitting regardless of provider)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # LangChain embeddings model
        try:
            self.embeddings = init_embeddings(
                settings.embedding_model,
                provider=settings.langchain_embeddings_provider,
                api_key=self.api_key,
            )
        except Exception:
            if settings.provider == "gemini":
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model=settings.embedding_model,
                    google_api_key=self.api_key,
                )
            else:
                from langchain_openai import OpenAIEmbeddings
                self.embeddings = OpenAIEmbeddings(
                    model=settings.embedding_model,
                    api_key=self.api_key,
                )

        # Initialize ChromaDB client with provider-namespaced path
        chroma_path = config.get_chroma_db_path()
        os.makedirs(chroma_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME
        )

        self.tokens: List[int] = []
        self.chunks: List[Chunk] = []
```

- [ ] **Step 3: Update `_get_contextual_summary`**

Replace lines 98-120 with:

```python
    def _get_contextual_summary(self, chunk: Chunk) -> str:
        start = max(0, chunk.document_position.start_token_index - (config.CONTEXT_WINDOW_SIZE // 2))
        end = min(len(self.tokens), chunk.document_position.end_token_index + (config.CONTEXT_WINDOW_SIZE // 2))

        context_tokens = self.tokens[start:end]
        context_text = self.tokenizer.decode(context_tokens)

        try:
            llm = init_chat_model(
                settings.chat_model,
                model_provider=settings.langchain_chat_provider,
                temperature=0,
                api_key=self.api_key,
                max_tokens=config.CONTEXT_SUMMARY_TOKENS,
            )
            messages = [
                ("system", "You are a helpful assistant. Summarize the following text in about 200 tokens, focusing on the main characters, events, and themes."),
                ("user", context_text),
            ]
            response = llm.invoke(messages)
            return response.content or ""
        except Exception as e:
            print(f"Error generating summary for chunk {chunk.chunk_id}: {e}")
            return ""
```

- [ ] **Step 4: Update `_get_embedding`**

Replace lines 122-134 with:

```python
    def _get_embedding(self, text: str) -> List[float]:
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
```

- [ ] **Step 5: Update embedding model reference in `build` and add cache mismatch detection**

In the `build` method, replace:
```python
                chunk.embedding_model = config.EMBEDDING_MODEL
```
with:
```python
                chunk.embedding_model = settings.embedding_model
```

Also, in the cache hit path (lines 148-155), add a check for embedding model mismatch. If the cached chunk was embedded with a different model, re-embed it:

After loading from cache (after `chunk.embedding_model = data['embedding_model']`), add:
```python
            if chunk.embedding_model != settings.embedding_model:
                # Cached embedding is from a different provider -- re-embed
                tqdm.write(f"Re-embedding chunk {chunk.chunk_id[:8]} (model mismatch: {chunk.embedding_model} != {settings.embedding_model})")
                document_to_embed = f"Context: {chunk.context}\n\nText: {chunk.base_text}"
                chunk.embedding = self._get_embedding(document_to_embed)
                chunk.embedding_model = settings.embedding_model
                # Update cache
                with open(cache_path, 'w') as f:
                    json.dump(chunk.model_dump(), f, indent=2)
```

This ensures that switching providers triggers re-embedding automatically, even without `--force-rebuild`. Text chunks and context summaries are reused; only embeddings are regenerated.

**Important:** This means the cache will be updated in-place with the new provider's embeddings. If a user switches back to the old provider, the cache hit will detect the mismatch again and re-embed. This is correct behavior -- the cache serves as an optimization, not a multi-provider store.

- [ ] **Step 6: Verify no remaining references to removed constants**

```bash
cd storyteller_backend && grep -rn "config\.EMBEDDING_MODEL\|config\.CONTEXT_MODEL\|config\.CHROMA_DB_PATH\b" embed_retrieve/ --include="*.py"
```

Expected: No matches.

- [ ] **Step 7: Commit**

```bash
git add storyteller_backend/embed_retrieve/build_database.py
git commit -m "feat: switch build_database to init_embeddings and init_chat_model"
```

---

### Task 6: Image Generator (image_generator.py)

**Files:**
- Modify: `storyteller_backend/services/image_generator.py`

- [ ] **Step 1: Update imports and `__init__`**

Replace lines 1-43 with:

```python
"""
Image Generator Service

Handles AI image generation for story chapters:
- Creates descriptive prompts via LangChain (provider-agnostic)
- Generates images with DALL-E (OpenAI) or Gemini
"""

from typing import Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import asyncio
import base64

from langchain.chat_models import init_chat_model
from config.settings import settings


STYLE_PREFIX = (
    "impressionist watercolour sketch, soft pastel colour palette, "
    "loose gestural brushstrokes, minimal detail, no text, warm dreamlike atmosphere -- "
)


class ImageGenerator:
    """
    Generates images for story chapters using an image gen model.

    The service creates high-quality image prompts based on story text,
    then generates images that maintain visual continuity across a journey.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = settings.resolve_api_key(api_key)
        self.enable_generation = True
```

- [ ] **Step 2: Replace `_generate_image_prompt` with `init_chat_model`**

Replace lines 45-88 with:

```python
    async def _generate_image_prompt(
        self,
        story_text: str,
        parent_image_prompt: Optional[str] = None
    ) -> Optional[str]:
        system_content = """Describe a single visual scene from the story text in one concise sentence or short paragraph.

You MUST include at least one main character from the passage -- name them and briefly describe their appearance or posture as it appears in the text.
Focus on: that character in their setting, the dominant mood, and one central action or moment.
Do NOT include any style, artistic, or colour instructions -- those are handled separately.
Do NOT include any text, labels, or captions in your description."""

        if parent_image_prompt:
            system_content += f"\n\nMaintain visual continuity with the previous image, which was described as: '{parent_image_prompt}'. Ensure characters and locations look consistent, while adhering to the specified artistic style."

        try:
            llm = init_chat_model(
                settings.chat_model,
                model_provider=settings.langchain_chat_provider,
                temperature=0,
                api_key=self.api_key,
                max_tokens=250,
            )
            messages = [
                ("system", system_content),
                ("user", story_text),
            ]
            response = await llm.ainvoke(messages)
            image_prompt = response.content
            print(f"Generated Image Prompt: {image_prompt}")
            return image_prompt

        except Exception as e:
            print(f"Error generating image prompt: {e}")
            return None
```

- [ ] **Step 3: Replace `_generate_dalle_image` with provider-branching `_generate_image`**

Replace lines 90-118 with:

```python
    async def _generate_image(self, image_prompt: str) -> Union[Optional[str], Optional[bytes]]:
        """Generate an image using the configured provider."""
        if settings.provider == "gemini":
            return await self._generate_gemini_image(image_prompt)
        else:
            return await self._generate_dalle_image(image_prompt)

    async def _generate_gemini_image(self, image_prompt: str) -> Optional[bytes]:
        """Generate an image using Gemini."""
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.image_model,
                contents=STYLE_PREFIX + image_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )

            if (response.candidates and
                response.candidates[0].content and
                response.candidates[0].content.parts):
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        print(f"Generated Gemini image ({len(part.inline_data.data)} bytes)")
                        return part.inline_data.data

            print("Gemini image generation returned no image data")
            return None

        except Exception as e:
            print(f"Error generating Gemini image: {e}")
            return None

    async def _generate_dalle_image(self, image_prompt: str) -> Union[Optional[str], Optional[bytes]]:
        """Generate an image using DALL-E."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            use_b64 = settings.local_image_storage
            response = await client.images.generate(
                model=settings.image_model,
                prompt=STYLE_PREFIX + image_prompt,
                n=1,
                size=settings.image_size,
                response_format="b64_json" if use_b64 else "url",
            )

            if use_b64:
                image_bytes = base64.b64decode(response.data[0].b64_json)
                print(f"Generated image ({len(image_bytes)} bytes)")
                return image_bytes
            else:
                image_url = response.data[0].url
                print(f"Generated Image URL: {image_url}")
                return image_url

        except Exception as e:
            print(f"Error generating DALL-E image: {e}")
            return None
```

- [ ] **Step 4: Update `generate_image` to use `_generate_image` and handle bytes/URL**

Replace the `generate_image` method body (lines 175-192) with:

```python
    async def generate_image(
        self,
        story_text: str,
        parent_image_prompt: Optional[str] = None,
        story_node_id: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate an image for a story chapter.

        Returns:
            Tuple of (image_ref, image_prompt).
            image_ref is a UUID (local storage) or a URL (cloud), or None.
        """
        print(f"--- Triggering Image Generation @ {datetime.now()} ---")

        if not self.enable_generation:
            return None, None

        try:
            image_prompt = await self._generate_image_prompt(story_text, parent_image_prompt)
            if not image_prompt:
                return None, None

            result = await self._generate_image(image_prompt)
            if not result:
                return None, image_prompt

            if isinstance(result, bytes):
                image_id = self._save_image_locally(result)
                return image_id, image_prompt

            return result, image_prompt  # URL string from DALL-E

        except Exception as e:
            print(f"An error occurred during image generation: {e}")
            return None, None
```

- [ ] **Step 5: Keep `_save_image_locally`, `_enforce_storage_limit`, `resolve_image_urls`, `get_image_generator` unchanged**

These methods don't reference OpenAI and work as-is.

- [ ] **Step 6: Commit**

```bash
git add storyteller_backend/services/image_generator.py
git commit -m "feat: add Gemini image generation, provider-agnostic prompt gen"
```

---

### Task 7: Auth Service & Corpus Registry Fixes

**Files:**
- Modify: `storyteller_backend/services/auth_service.py`
- Modify: `storyteller_backend/services/__init__.py`
- Modify: `storyteller_backend/embed_retrieve/corpus_registry.py`

- [ ] **Step 1: Guard auth_service.py against missing OpenAI key**

`auth_service.py` creates `OpenAI(api_key=settings.openai_api_key)` clients. When `provider=gemini`, `settings.openai_api_key` is `None`, which crashes `OpenAI()`. Guard the self_hosted path in both `get_client` and `get_async_client`:

In `get_client`, replace the self_hosted branch (line 43-47):
```python
        if self.auth_mode == "self_hosted":
            if self._default_client is None:
                api_key_val = settings.openai_api_key
                if not api_key_val:
                    raise ValueError(
                        "OpenAI client requested but no OPENAI_API_KEY configured. "
                        "Set provider=openai in settings.py or provide an API key."
                    )
                self._default_client = OpenAI(api_key=api_key_val)
            return self._default_client
```

Apply the same guard to `get_async_client` self_hosted branch (line 86-90):
```python
        if self.auth_mode == "self_hosted":
            if self._default_async_client is None:
                api_key_val = settings.openai_api_key
                if not api_key_val:
                    raise ValueError(
                        "Async OpenAI client requested but no OPENAI_API_KEY configured. "
                        "Set provider=openai in settings.py or provide an API key."
                    )
                self._default_async_client = AsyncOpenAI(api_key=api_key_val)
            return self._default_async_client
```

- [ ] **Step 2: Update `corpus_registry.py` -- provider-suffix in `check_corpus_status`**

In `storyteller_backend/embed_retrieve/corpus_registry.py`, the `check_corpus_status` method (line 198) uses `corpus_config.chroma_db_path` directly to check if ChromaDB exists. This needs the provider suffix.

Add a helper import at the top of `corpus_registry.py`:
```python
from config.settings import settings
```
(Note: this import already exists inside `__init__` and `_load_registry` as a lazy import. Add it at module level for `check_corpus_status`.)

In `check_corpus_status`, replace line 198:
```python
            chroma_client = chromadb.PersistentClient(path=corpus_config.chroma_db_path)
```
with:
```python
            chroma_path = f"{corpus_config.chroma_db_path}_{settings.provider}"
            chroma_client = chromadb.PersistentClient(path=chroma_path)
```

- [ ] **Step 3: Check `services/__init__.py` for broken imports**

Read the file and verify exports still work. `get_openai_client` and `get_async_openai_client` are still exported but now raise clear errors when no OpenAI key is configured.

- [ ] **Step 4: Commit**

```bash
git add storyteller_backend/services/auth_service.py storyteller_backend/services/__init__.py storyteller_backend/embed_retrieve/corpus_registry.py
git commit -m "fix: guard auth_service against missing OpenAI key, provider-suffix corpus status"
```

---

### Task 8: Run Full Test Suite and Fix Regressions

**Files:**
- Potentially modify any test file

- [ ] **Step 1: Run full test suite**

```bash
cd storyteller_backend && poetry run pytest tests/ -v
```

Note all failures.

- [ ] **Step 2: Fix any remaining regressions**

Common expected issues:
- Tests referencing `settings.summary_model` or `settings.guardrail_model` (removed)
- Tests referencing `settings.image_generation_size` (now `settings.image_size`)
- Tests mocking `ChatOpenAI` (now `init_chat_model`)
- Tests that import from `services` expecting `get_openai_client` etc.

Fix each failing test.

- [ ] **Step 3: Run tests again**

```bash
cd storyteller_backend && poetry run pytest tests/ -v
```

Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add -A storyteller_backend/tests/
git commit -m "fix: update tests for multi-provider support"
```

---

### Task 9: Smoke Test with Gemini

- [ ] **Step 1: Ensure `.env` has `GEMINI_API_KEY` and `settings.py` has `provider = "gemini"`**

- [ ] **Step 2: Start backend**

```bash
cd storyteller_backend && poetry run python -m api.main &
```

- [ ] **Step 3: Health check**

```bash
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", ...}`

- [ ] **Step 4: Start frontend and test in browser**

```bash
cd storyteller_frontend && npm run dev &
```

Navigate to `http://localhost:3000`. Submit a story prompt and verify:
- Story generates (streamed text appears)
- Image generates (watercolor illustration appears)
- Choices appear after story completes

- [ ] **Step 5: Commit any fixes found during smoke test**

```bash
git add -A
git commit -m "fix: smoke test fixes for Gemini provider"
```

---

### Task 10: Build Gemini Corpus Embeddings

This task creates the Gemini-specific ChromaDB embeddings for the shipped corpus.

- [ ] **Step 1: Verify processed chunks cache exists**

```bash
ls data/processed_chunks/ | head -5
```

Expected: JSON chunk files exist (from previous OpenAI build).

- [ ] **Step 2: Run the build with Gemini provider**

With `provider = "gemini"` in settings:

```bash
cd storyteller_backend && poetry run python -m embed_retrieve.build_database --force-rebuild
```

This reuses cached text chunks but re-embeds them with Gemini's embedding model into `data/chroma_db_gemini/`.

- [ ] **Step 3: Verify Gemini ChromaDB was created**

```bash
ls data/chroma_db_gemini/
```

Expected: ChromaDB files present.

- [ ] **Step 4: Rename existing OpenAI ChromaDB**

```bash
mv data/chroma_db data/chroma_db_openai
```

- [ ] **Step 5: Commit the Gemini embeddings**

```bash
git add data/chroma_db_gemini/ data/chroma_db_openai/
git commit -m "data: add Gemini corpus embeddings, rename OpenAI corpus"
```
