# Multi-Provider Support: Gemini + OpenAI

**Date:** 2026-03-24
**Status:** Approved
**Goal:** Enable zero-spend usage by adding Google Gemini as a configurable alternative to OpenAI for all AI capabilities (chat completions, embeddings, image generation).

---

## Motivation

Users currently need an OpenAI API key (paid) to use Storyteller. By adding Gemini as the default provider, users can run the full app with a single free Google AI Studio API key — no credit card required.

---

## Design Decisions

- **Configurable provider** via `settings.py`: `"gemini"` (default) or `"openai"`
- **LangChain abstractions** for chat and embeddings: `init_chat_model` and `init_embeddings` — provider-agnostic, no import swapping
- **Provider branch for image gen only** — no LangChain abstraction exists for image generation
- **OpenAI moderation endpoint** used when available (`provider=openai`), skipped otherwise — the intent classifier is the primary guardrail regardless of provider
- **Provider-namespaced ChromaDB only** — processed chunks and BM25 indices are provider-agnostic and shared

---

## Section 1: Configuration Layer

### settings.py — Config class

New fields:

```python
provider: Literal["gemini", "openai"] = "gemini"

# Gemini models
gemini_chat_model: str = "gemini-2.5-flash"
gemini_embedding_model: str = "gemini-embedding-001"
gemini_image_model: str = "gemini-2.5-flash-image"
gemini_image_size: str = "1K"

# OpenAI models (existing, regrouped)
openai_chat_model: str = "gpt-4o-mini"
openai_embedding_model: str = "text-embedding-3-small"
openai_image_model: str = "dall-e-2"
openai_image_size: str = "256x256"
openai_image_quality: str = "standard"
```

The existing standalone fields (`chat_model`, `embedding_model`, `image_model`, `image_generation_size`, `image_generation_quality`) are removed from Config and replaced by provider-scoped fields above. The existing `summary_model` and `guardrail_model` fields are also removed — all chat completion call sites use `settings.chat_model`, which resolves based on provider.

Convenience properties resolve the active model based on provider:

```python
@property
def chat_model(self) -> str:
    return self.gemini_chat_model if self.provider == "gemini" else self.openai_chat_model

@property
def embedding_model(self) -> str:
    return self.gemini_embedding_model if self.provider == "gemini" else self.openai_embedding_model

@property
def image_model(self) -> str:
    return self.gemini_image_model if self.provider == "gemini" else self.openai_image_model

@property
def image_size(self) -> str:
    return self.gemini_image_size if self.provider == "gemini" else self.openai_image_size

@property
def image_quality(self) -> str:
    """Only used by OpenAI/DALL-E path."""
    return self.openai_image_quality
```

### LangChain provider mapping

LangChain's `init_chat_model` and `init_embeddings` use their own provider strings, which differ from our user-facing `"gemini"` / `"openai"`. A mapping property translates:

```python
@property
def langchain_chat_provider(self) -> str:
    return "google_genai" if self.provider == "gemini" else "openai"

@property
def langchain_embeddings_provider(self) -> str:
    return "google_genai" if self.provider == "gemini" else "openai"
```

All `init_chat_model` and `init_embeddings` calls use these properties, not the raw `provider` string.

**Note:** If `init_embeddings` does not support `"google_genai"` in the installed LangChain version, fall back to direct instantiation of `GoogleGenerativeAIEmbeddings` from `langchain_google_genai`. Verify at implementation time and use whichever works.

### settings.py — Secrets class

```python
gemini_api_key: Optional[str] = None   # Required when provider=gemini
openai_api_key: Optional[str] = None   # Required when provider=openai
```

**Important:** The existing `openai_api_key: str` (required) must change to `Optional[str] = None`. Without this, Pydantic will reject startup when no OpenAI key is present, even for Gemini-only users — before the startup validation can run.

Both keys are Optional. `resolve_api_key()` replaces `resolve_openai_key()`, returning the correct key based on provider.

### Startup validation

Add a validation check (in `Settings.__init__` or a `validate()` method) that raises a clear error if the required API key for the active provider is missing. Example:

```python
if self.provider == "gemini" and not self._secrets.gemini_api_key:
    raise ValueError("GEMINI_API_KEY is required in .env when provider=gemini")
if self.provider == "openai" and not self._secrets.openai_api_key:
    raise ValueError("OPENAI_API_KEY is required in .env when provider=openai")
```

---

## Section 2: Chat Completions (story_agent.py)

All 5 `ChatOpenAI()` instantiation sites switch to `init_chat_model`:

```python
from langchain.chat_models import init_chat_model

# Replaces: ChatOpenAI(temperature=0.9, model_name=settings.chat_model, api_key=...)
llm = init_chat_model(
    settings.chat_model,
    model_provider=settings.langchain_chat_provider,
    temperature=0.9,
    api_key=ACTIVE_API_KEY,
)
```

### Affected call sites

| Function | Current model field | After |
|---|---|---|
| `_generate_node_summary` | `settings.summary_model` | `settings.chat_model` (via `init_chat_model`) |
| `_classify_intent` | `settings.guardrail_model` | `settings.chat_model` (via `init_chat_model`) |
| `generate_search_query` | `settings.chat_model` | `settings.chat_model` (via `init_chat_model`) |
| `generate_story` | `settings.chat_model` | `settings.chat_model` (via `init_chat_model`) |
| `generate_choices` | `settings.chat_model` | `settings.chat_model` (via `init_chat_model`) |

All call sites use `settings.chat_model`, which resolves to the correct model for the active provider. The separate `summary_model` and `guardrail_model` config fields are removed.

### Moderation

`_check_moderation` uses the raw OpenAI `AsyncOpenAI` moderation endpoint. This is OpenAI-specific with no Gemini equivalent.

- `provider=openai`: runs moderation as before
- `provider=gemini`: skipped (returns True / passes)

The intent classifier (`_classify_intent`) remains the primary guardrail for both providers.

### API key management

- `ACTIVE_OPENAI_API_KEY` → `ACTIVE_API_KEY`
- `_set_active_api_key` resolves via `settings.resolve_api_key()`
- `from openai import AsyncOpenAI` stays but is only used when `provider=openai` (moderation)

---

## Section 3: Embeddings (embed_retrieve/)

### build_database.py and retriever.py

Replace raw OpenAI SDK embedding calls with LangChain's `init_embeddings`:

```python
from langchain.embeddings import init_embeddings

embeddings = init_embeddings(
    settings.embedding_model,
    provider=settings.langchain_embeddings_provider,
)
vector = embeddings.embed_query(text)
```

**Note:** The `init_embeddings` parameter is `provider`, not `model_provider` (unlike `init_chat_model`). If `init_embeddings` does not support `"google_genai"` in the installed version, instantiate `GoogleGenerativeAIEmbeddings` directly as a fallback.

The `openai.OpenAI` client construction and `import openai` are removed from both files. `resolve_openai_key` calls are replaced with `resolve_api_key`.

### build_database.py — context summary generation

Line 109 uses `openai_client.chat.completions.create()` for contextual summaries. Switches to `init_chat_model` (same pattern as story_agent).

### embed_retrieve/config.py — constant cleanup

The hardcoded constants `EMBEDDING_MODEL` and `CONTEXT_MODEL` are removed. All references in `build_database.py` and `retriever.py` use `settings.embedding_model` and `settings.chat_model` instead.

`CHROMA_DB_PATH` becomes provider-aware, reading `settings.provider` to resolve the correct path.

### Tokenizer note

`build_database.py` uses `tiktoken` with `cl100k_base` for chunking (token counting). This is an OpenAI tokenizer but is used purely for text splitting, not embedding. It stays as-is regardless of provider — chunk boundaries may differ slightly from Gemini's tokenizer, but this is a reasonable simplification.

### ChromaDB paths — provider-namespaced

Only ChromaDB vector stores are provider-specific:

- `data/chroma_db_gemini/` (default, shipped pre-built)
- `data/chroma_db_openai/` (renamed from existing `data/chroma_db/`)

### Corpus registry interaction

The corpus registry (`corpus_registry.py`) stores `chroma_db_path` per corpus. Provider namespacing is applied at runtime: the registry stores a base path (e.g., `data/chroma_db`), and the provider suffix is appended when resolving (e.g., `data/chroma_db_gemini`). This avoids duplicating registry entries per provider.

The `retriever.py` code that reads `self.corpus_config.chroma_db_path` appends the provider suffix before constructing the `PersistentClient`.

### Shared data (NOT namespaced)

- `data/processed_chunks/` — text + context summaries, provider-agnostic
- `data/bm25_index.pkl` — keyword-based, provider-agnostic

The build process reuses cached chunks and only re-runs the embedding step into the provider-specific ChromaDB when switching providers.

---

## Section 4: Image Generation (image_generator.py)

### Image prompt generation

`_generate_image_prompt` currently uses the raw `AsyncOpenAI` client for a chat completion. Switches to `init_chat_model` (same as Section 2).

### Image generation — provider branch

`_generate_dalle_image` becomes `_generate_image` with a provider branch:

**OpenAI path** (unchanged):
```python
response = await self.client.images.generate(
    model=settings.image_model,
    prompt=STYLE_PREFIX + image_prompt,
    size=settings.image_size,
    ...
)
```

**Gemini path** (new):
```python
from google import genai

client = genai.Client(api_key=api_key)
response = await client.aio.models.generate_content(
    model=settings.image_model,
    contents=STYLE_PREFIX + image_prompt,
    config={"response_modalities": ["IMAGE"], "image_config": {"image_size": settings.image_size}},
)
image_bytes = response.candidates[0].content.parts[0].inline_data.data
```

**Important:** The Gemini path must use the async variant (`client.aio.models.generate_content`) to avoid blocking the event loop, since `image_generator.py` is fully async. If the async method is not available in `google-genai`, wrap the sync call in `asyncio.to_thread()`.

### Config defaults

- Gemini: `gemini-2.5-flash-image` at `1K` resolution
- OpenAI: `dall-e-2` at `256x256` (unchanged)

---

## Section 5: Auth Service & Dependencies

### auth_service.py

Role shrinks with `init_chat_model` / `init_embeddings` handling most client creation. Remaining responsibilities:

- **OpenAI image gen**: `AsyncOpenAI` client for DALL-E (existing)
- **Gemini image gen**: `google.genai.Client` (new)
- **Moderation**: `AsyncOpenAI` client, only when `provider=openai`

### API key resolution

`settings.resolve_openai_key()` → `settings.resolve_api_key()`, returns the correct key based on provider.

### New dependencies (pyproject.toml)

| Package | Purpose |
|---|---|
| `langchain-google-genai` | Google GenAI chat + embeddings for LangChain |
| `google-genai` | Google SDK for image generation |

### Existing deps (stay)

| Package | Purpose |
|---|---|
| `langchain-openai` | OpenAI chat + embeddings for LangChain |
| `openai` | DALL-E image gen + moderation endpoint |

### .env.example

```env
# Choose your provider in config/settings.py (default: gemini)
GEMINI_API_KEY=your-gemini-api-key-here
# OPENAI_API_KEY=your-openai-api-key-here  # only needed if provider=openai
```

---

## Files Touched

| File | Changes |
|---|---|
| `config/settings.py` | Provider field, model mappings, key resolution, startup validation |
| `services/story_agent.py` | `init_chat_model`, generalized API key, moderation skip |
| `services/image_generator.py` | Provider branch for image gen, `init_chat_model` for prompts, async Gemini call |
| `services/auth_service.py` | Generalized key resolution, Gemini client support |
| `embed_retrieve/build_database.py` | `init_embeddings`, `init_chat_model` for summaries, remove `openai` client |
| `embed_retrieve/retriever.py` | `init_embeddings`, remove `openai` client and `resolve_openai_key` |
| `embed_retrieve/config.py` | Remove `EMBEDDING_MODEL`/`CONTEXT_MODEL` constants, provider-aware ChromaDB path |
| `embed_retrieve/corpus_registry.py` | Runtime provider-suffix on `chroma_db_path` resolution |
| `pyproject.toml` | Add `langchain-google-genai`, `google-genai` |
| `.env.example` | Add `GEMINI_API_KEY`, make `OPENAI_API_KEY` optional |

## Files NOT Touched

- Frontend (no changes)
- Prompts / system messages
- LangGraph workflow structure
- BM25 index / processed chunks cache
- Journey manager / graph serialization
