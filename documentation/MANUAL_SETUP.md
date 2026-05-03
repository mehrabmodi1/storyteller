# Storyteller — Architecture & Developer Guide

This document is a deeper companion to the [README](../README.md). The README covers how to run the app; this doc covers **how the system is put together**: the layers, the data flow, the conventions, and the extension points. Read this if you intend to modify backend code, add a provider, ingest a new corpus, or debug an unusual failure.

For setup instructions (Poetry, npm, `.env`, run commands), see the [README Quick Start](../README.md#quick-start).

---

## Table of contents

1. [System overview](#1-system-overview)
2. [Backend layers](#2-backend-layers)
3. [Story-generation flow (LangGraph)](#3-story-generation-flow-langgraph)
4. [Provider abstraction](#4-provider-abstraction)
5. [Corpus ingestion pipeline](#5-corpus-ingestion-pipeline)
6. [Loading pre-built corpus data](#6-loading-pre-built-corpus-data)
7. [Hybrid retrieval](#7-hybrid-retrieval)
8. [Frontend architecture](#8-frontend-architecture)
9. [Extension points](#9-extension-points)
10. [Common gotchas](#10-common-gotchas)

---

## 1. System overview

Storyteller is a **dual-project monorepo** with two independently-runnable services:

- `storyteller_backend/` — FastAPI + LangGraph + ChromaDB (Python 3.12, Poetry)
- `storyteller_frontend/` — React + Vite + ReactFlow (Node 18+, npm)

They communicate over HTTP/SSE. The backend persists user journeys to `saved_graphs/` (JSON) and reads pre-built corpora from `data/`.

```
User -> Frontend (3000) -SSE-> Backend (8000) -> Provider API (Gemini / OpenAI)
                                       |
                                       +-- ChromaDB (data/chroma_db/<corpus>_<provider>/)
                                       +-- BM25 index (data/bm25_indexes/<corpus>_bm25)
```

Each turn = one user prompt -> one new "story node" + three "choice nodes" appended to a `networkx` graph that the frontend renders with ReactFlow.

---

## 2. Backend layers

```
storyteller_backend/
├── api/                        # FastAPI surface
│   ├── main.py                 # App + uvicorn entry; mounts static images
│   ├── dependencies.py         # Singletons (graph state, etc.)
│   └── routes/
│       ├── stories.py          # POST /api/stream_story — main SSE endpoint
│       ├── journeys.py         # CRUD on saved graphs
│       ├── personas.py         # CRUD on personas
│       ├── corpuses.py         # CRUD + status on corpora
│       └── auth.py             # Per-request key validation
├── services/
│   ├── story_agent.py          # LangGraph state machine (the heart)
│   ├── image_generator.py      # DALL-E 2 / Gemini image routing
│   ├── llm.py                  # get_chat_llm() — single chat-model factory
│   └── auth_service.py         # Provider-aware auth (e.g. OpenAI moderation)
├── embed_retrieve/
│   ├── build_database.py       # Corpus ingestion CLI + builder class
│   ├── retriever.py            # HybridRetriever (BM25 + Chroma + RRF)
│   ├── corpus_registry.py      # Loads/saves data/corpus_registry.json
│   ├── manage_corpuses.py      # CLI: list / add / build corpora
│   ├── paths.py                # Shared provider_chroma_path() helper
│   └── config.py               # Chunking/context constants (CHUNK_SIZE, CACHE_DIR, …)
├── models/
│   ├── api_models.py           # Pydantic request/response models
│   └── chunk.py                # Chunk + DocumentPosition
├── config/
│   ├── settings.py             # Provider enum, profiles, all knobs
│   ├── personas.json           # Six personas + system prompts + colour themes
│   └── .env(.example)          # Secrets only (API keys)
└── tests/                      # pytest
```

**Boundary rules:**
- `config/settings.py` does not import from `services/` or `embed_retrieve/`.
- `services/` and `embed_retrieve/` may import from `config/`.
- `api/` is the only layer that imports from FastAPI.
- API keys are read **only** from `.env` via `Secrets(BaseSettings)`. Everything else (model names, RPMs, paths) is hard-coded in `Config` / `PROVIDER_PROFILES`.

---

## 3. Story-generation flow (LangGraph)

Every `/api/stream_story` request walks the same LangGraph state machine, defined in [`services/story_agent.py`](../storyteller_backend/services/story_agent.py):

```
start
  |
  v
screen_prompt              # safety classifier + (OpenAI moderation if available)
  |
  v
build_path_context         # walk the existing graph, summarise the journey so far
  |
  v
generate_search_query      # structured-output: SearchQuery
  |
  v
retrieve_chunks            # HybridRetriever.search() — BM25 + Chroma fused
  |
  v
generate_story             # STREAMING; emits chunks over SSE
  |                            \
  v                             > on text-threshold, image_generator runs in parallel
update_graph_with_story        /
  |
  v
generate_choices           # structured-output: Choices (3 follow-ups)
  |
  v
update_graph_with_choices
  |
  v
end -> SSE final message: full serialized graph
```

Notable details:

- **Streaming.** `generate_story` uses `astream`, and the upstream FastAPI route ([`api/routes/stories.py`](../storyteller_backend/api/routes/stories.py)) listens to `astream_events("v1")` and forwards `on_chat_model_stream` events to the SSE channel. The frontend renders text token-by-token.
- **Image gen runs in parallel.** As soon as ~25% of the expected story length has streamed in, image generation kicks off as an `asyncio.Task` so it overlaps with the rest of the story emission.
- **Structured output.** `screen_prompt`, `generate_search_query`, and `generate_choices` use Pydantic models via `.with_structured_output(Schema)`. Provider-native JSON mode is used where supported.
- **Persona injection.** The selected persona's `system_prompt` is interpolated into the chat prompt template before grounding constraints are appended last (so persona prompts can't override grounding rules).

---

## 4. Provider abstraction

Lives in [`config/settings.py`](../storyteller_backend/config/settings.py). Three pieces:

```python
class Provider(StrEnum):
    GEMINI = "gemini"
    OPENAI = "openai"

@dataclass(frozen=True)
class ProviderProfile:
    chat_model: str
    embedding_model: str
    image_model: str
    image_size: str
    chat_rpm: int
    embedding_rpm: int
    langchain_chat_provider: str
    langchain_embeddings_provider: str
    image_quality: Optional[str] = None      # OpenAI-only
    thinking_budget: Optional[int] = None    # Gemini-only

PROVIDER_PROFILES: dict[Provider, ProviderProfile] = { ... }
```

The active provider is set on `Config.provider`. `Settings.chat_model`, `Settings.embedding_model`, etc. delegate to `PROVIDER_PROFILES[active]`. Switching providers is one assignment.

**Why `thinking_budget=0` is set for Gemini:** `gemini-2.5-flash` defaults to thinking mode, which consumes ~1500 reasoning tokens before any visible output. With our default `max_tokens=1200` for stories, the entire budget got eaten by thinking → ~40-word truncated stories. Setting `thinking_budget=0` disables that.

The single chat-model construction site is [`services/llm.py:get_chat_llm()`](../storyteller_backend/services/llm.py). All seven `init_chat_model` callers go through it. It auto-applies the provider's `thinking_budget` so callers don't need to know.

**Adding a third provider:**
1. Add a new `Provider` enum member.
2. Add a new entry to `PROVIDER_PROFILES`.
3. If the provider needs special wiring inside `get_chat_llm`, branch there.
4. Wire any provider-specific image-gen path inside [`services/image_generator.py`](../storyteller_backend/services/image_generator.py).
5. Add an API key field to `Secrets`.

---

## 5. Corpus ingestion pipeline

Defined in [`embed_retrieve/build_database.py`](../storyteller_backend/embed_retrieve/build_database.py). The pipeline is **provider-aware** (chunks land in `data/chroma_db/<corpus>_<provider>/`) and **resumable** at every phase.

```
phase 1: chunk + summarise (chat)
   PDF -> PyMuPDF -> tiktoken chunks
                          |
                          v
                    chat: contextual summary (per chunk)
                          |
                          v
              cache JSON to data/processed_chunks/<corpus>/
   (skipped entirely if cache exists)

phase 2: embed (vectors)
   for each cached chunk:
     if id already in Chroma collection -> skip
     else -> embed via provider, upsert into Chroma
   rate-limited at chat_rpm / embedding_rpm

phase 3: BM25 (provider-agnostic)
   read data/processed_chunks/<corpus>/
   build BM25Okapi over all chunk texts
   write data/bm25_indexes/<corpus>_bm25
```

Cost per phase:
- **Phase 1:** N chat calls (one per chunk) — only on first build of a new corpus
- **Phase 2:** N embedding calls — runs every time you ingest under a new provider
- **Phase 3:** zero API calls — local indexing

The CLI:

```bash
poetry run python -m embed_retrieve.build_database --corpus <name> [--force-rebuild]
poetry run python -m embed_retrieve.manage_corpuses build <name>
poetry run python -m embed_retrieve.manage_corpuses list
poetry run python -m embed_retrieve.manage_corpuses add <name> <display> <desc> <source.pdf>
```

Failure modes:
- **Daily quota hit (HTTP 429 with `PerDay` in message)** → builder logs a notice and re-raises. Re-run any time after midnight (PT) and phase 2 picks up where it left off.
- **Per-minute rate limit (`429` with `retry in Ns`)** → builder backs off and retries automatically up to `MAX_RETRIES=3`.
- **Network blips** → standard exception, caller decides. Re-run is safe (idempotent upsert).

---

## 6. Loading pre-built corpus data

If you already have a snapshot of pre-built corpus data (typically distributed as a tarball or Google Drive folder), you can skip the ingestion pipeline entirely and just drop it into place.

A snapshot has the following layout (one per provider, since vector embeddings are provider-specific):

```
<snapshot_root>/
├── corpus_registry.json
├── chroma_db/
│   ├── arabian_nights/
│   ├── jataka_tales/
│   ├── locus_platform_docs/
│   ├── mahabharata/
│   ├── odyssey/
│   └── volsunga_saga/
├── bm25_indexes/
│   ├── arabian_nights_bm25.pkl
│   ├── jataka_tales_bm25.pkl
│   └── ...
└── processed_chunks/                  # optional; needed only if you'll re-build
    ├── arabian_nights/<chunk>.json
    └── ...
```

### Steps

1. **Place the snapshot at `<repo>/data/`.** The `data/` directory is gitignored except for `corpus_registry.json`, so it's safe to drop large binaries here.
   ```bash
   # From the snapshot's location
   cp -R <snapshot_root>/. <repo>/data/
   ```

2. **Add the `_<provider>` suffix to each chroma directory** to match the layout the build/retrieve layer expects. Skip this if the snapshot was already produced post-May-2026 and uses the suffixed layout. For an OpenAI snapshot:
   ```bash
   cd <repo>/data/chroma_db
   for c in arabian_nights jataka_tales locus_platform_docs mahabharata odyssey volsunga_saga; do
     mv "$c" "${c}_openai"
   done
   ```
   For a Gemini snapshot, use `_gemini` instead.

3. **Verify the registry path layout.** The repo's `data/corpus_registry.json` is the source of truth. If the snapshot's registry differs, prefer the repo's (it's tracked; theirs is point-in-time). Quick check:
   ```bash
   grep chroma_db_path data/corpus_registry.json
   # Each non-mahabharata corpus should be: data/chroma_db/<name>
   # Mahabharata should be:                  data/chroma_db/mahabharata
   ```

4. **Smoke test** — open a Python REPL in `storyteller_backend/` and instantiate a retriever:
   ```python
   from embed_retrieve.retriever import HybridRetriever
   r = HybridRetriever(corpus_name="mahabharata")
   print(r.chroma_collection.count())   # should be > 0
   ```

If the count is 0 or the collection isn't found, the most common cause is a mismatch between the snapshot's chroma layout and the active provider's expected suffix (step 2 above).

### Producing a snapshot

To package the current `data/` for sharing:

```bash
cd <repo>
tar czf storyteller_data_snapshot.tar.gz \
  data/corpus_registry.json \
  data/chroma_db/ \
  data/bm25_indexes/ \
  data/processed_chunks/      # omit for a smaller snapshot if recipients won't re-build
```

Note that `chroma_db/` carries the per-provider suffix, so a single snapshot is provider-specific. To support both providers, package both `<corpus>_openai/` and `<corpus>_gemini/` directories (or distribute provider-specific tarballs).

---

## 7. Hybrid retrieval

[`embed_retrieve/retriever.py`](../storyteller_backend/embed_retrieve/retriever.py) implements `HybridRetriever`, which fuses two ranked lists:

1. **BM25** — keyword scoring against the full chunk text (`Context: ... Text: ...`).
2. **Vector** — semantic similarity via the active provider's embeddings, queried against the per-corpus Chroma collection.

The two ranked lists are merged via **Reciprocal Rank Fusion** (`rrf_k = 60`), and the top-K (default 10) chunks are returned. Both lists' weights are configurable in `settings.py` (`bm25_weight`, `semantic_weight`, `retrieval_top_k`).

Path resolution goes through [`embed_retrieve/paths.py:provider_chroma_path()`](../storyteller_backend/embed_retrieve/paths.py) — the same helper the build script uses, so writer and reader can never disagree on layout.

---

## 8. Frontend architecture

```
storyteller_frontend/src/
├── App.tsx                # Top-level layout
├── context/AppContext.tsx # Global state (current persona/corpus, journey list, etc.)
├── components/
│   ├── graph/             # ReactFlow nodes (StoryNode, ChoiceNode), edges, controls
│   ├── dropdowns/         # Persona / Corpus pickers
│   └── debug/             # Dev panels
├── hooks/
│   ├── useSSE.ts          # SSE client wrapping /api/stream_story
│   ├── useELKLayout.ts    # ELK-based graph layout
│   └── useLocalStorage.ts # Persist UI prefs
└── services/api.ts        # All HTTP calls to the backend
```

**State flow on a new story turn:**
1. User submits prompt → `useSSE` opens a stream against `/api/stream_story`.
2. Tokens arrive → progressively populate a draft "story" node in modal/overlay.
3. Final SSE message contains the full serialized graph (nodes + edges) → React commits it via `setGraph`.
4. ELK lays out the new graph; ReactFlow renders.

---

## 9. Extension points

| Goal | Where to start |
|---|---|
| Add a new provider | `Provider` enum + `PROVIDER_PROFILES` in `config/settings.py`; review `services/llm.py` and `services/image_generator.py` for provider branches |
| Add a new corpus | `manage_corpuses.py add ...` then `build_database.py --corpus <name>` |
| Add a new persona | Append to `config/personas.json` — pick a unique color theme |
| Add a graph node | Define the node fn in `services/story_agent.py`, wire it into the StateGraph in `_build_workflow()` |
| Add an API endpoint | New file in `api/routes/`, mount it in `api/main.py` |
| Tune retrieval | `bm25_weight`, `semantic_weight`, `retrieval_top_k` in `Config` |
| Tune chunking | `CHUNK_SIZE`, `CHUNK_OVERLAP`, `CONTEXT_WINDOW_SIZE` in `embed_retrieve/config.py` (note: changing chunking invalidates existing summary caches) |

---

## 10. Common gotchas

- **`chromadb` version drift permanently destroys vector data.** Always use `poetry install`. Never `pip install`.
- **Backend cwd matters.** `embed_retrieve/config.py:CACHE_DIR` is a relative path (`../data/processed_chunks`). Run backend commands from `storyteller_backend/`.
- **Ingesting under a new provider doesn't reuse old vectors.** Each provider's embeddings live in `<corpus>_<provider>/`. Switching providers means re-running phase 2 of the build for each corpus you want to use.
- **Free-tier image-gen on Gemini is 0/day.** Stories will still complete; image generation will silently no-op (the exception is caught and logged).
- **`gemini-2.5-flash` thinking mode**: handled automatically via `thinking_budget=0` in the Gemini profile. If you ever construct a chat model directly without going through `services/llm.py`, replicate that setting or expect truncated output.
- **The interactive scripts at `embed_retrieve/test_build.py` and `embed_retrieve/test_retriever.py` are stale** — they predate the current builder API. Use the `pytest tests/` suite for automation.

---

For the user-facing setup walkthrough, see the [README](../README.md). For the (historical) project plan and roadmap, see [`next_steps.md`](next_steps.md).
