# Backend Documentation

Engineering reference for the Storyteller backend — a FastAPI application that generates branching interactive narratives using LangGraph, ChromaDB, and OpenAI.

---

## Architecture Overview

```
Request → FastAPI routes → LangGraph 9-node pipeline → SSE response
                              ├── HybridRetriever (ChromaDB + BM25)
                              ├── OpenAI GPT-4o-mini (story + choices)
                              ├── DALL-E 2 (images)
                              └── NetworkX graph (persistence)
```

The backend is a single-process FastAPI server. Story generation is orchestrated by a LangGraph `StateGraph` that streams tokens via Server-Sent Events. Graph state is held in memory (one active graph per server) with JSON persistence to disk.

---

## Directory Structure

```
storyteller_backend/
├── api/
│   ├── main.py                 # FastAPI app, CORS, lifespan, health endpoints
│   ├── dependencies.py         # GraphState singleton (async-safe, asyncio.Lock)
│   └── routes/
│       ├── stories.py          # GET /api/stream_story (SSE)
│       ├── personas.py         # Persona CRUD
│       ├── corpuses.py         # Corpus CRUD
│       └── journeys.py         # Journey load/save/list
├── services/
│   ├── story_agent.py          # LangGraph pipeline (9 nodes)
│   ├── auth_service.py         # OpenAI client factory (3 auth modes)
│   ├── journey_manager.py      # Graph persistence (JSON files)
│   └── image_generator.py      # DALL-E prompt generation + image storage
├── models/
│   ├── api_models.py           # Pydantic request/response models
│   ├── state.py                # StorytellerState TypedDict (LangGraph state)
│   └── chunk.py                # Text chunk + embedding model
├── config/
│   ├── settings.py             # Config (hardcoded) + Secrets (.env)
│   ├── personas.json           # 6 storyteller personas with system prompts
│   └── jobs.yaml               # Corpus definitions (6 corpuses)
├── embed_retrieve/
│   ├── retriever.py            # HybridRetriever (ChromaDB + BM25 + RRF)
│   ├── corpus_registry.py      # CorpusRegistry, CorpusConfig, CorpusStatus
│   ├── build_database.py       # Single corpus indexing pipeline
│   ├── batch_ingest.py         # Bulk corpus processing
│   ├── manage_corpuses.py      # Registry CLI operations
│   ├── preprocess_multi_files.py # Multi-file chunking
│   ├── config.py               # Retriever constants
│   └── db_update.py            # Incremental updates
├── data/
│   └── corpus_registry.json    # Runtime corpus metadata
└── tests/
    ├── conftest.py             # Shared pytest fixtures
    ├── test_build_path_context.py
    ├── test_paragraph_count.py
    └── test_screen_prompt.py
```

---

## Configuration

### `config/settings.py`

Two-tier system — secrets come from `.env`, everything else is hardcoded.

**Secrets** (loaded from `storyteller_backend/.env`):

| Env Var | Required | Purpose |
|---------|----------|---------|
| `OPENAI_API_KEY` | Yes | Main API key for all OpenAI calls |
| `PLATFORM_OPENAI_KEY` | No | For future credit_system auth mode |

**Configuration** (hardcoded defaults):

| Setting | Default | Notes |
|---------|---------|-------|
| `api_host` | `0.0.0.0` | |
| `api_port` | `8000` | |
| `chat_model` | `gpt-4o-mini` | |
| `embedding_model` | `text-embedding-3-small` | |
| `image_model` | `dall-e-2` | |
| `image_size` | `256x256` | |
| `data_dir` | `../data` | Relative to backend dir |
| `saved_graphs_dir` | `../saved_graphs` | |
| `default_paragraph_count` | `4` | Range: 1-8 |
| `words_per_paragraph` | `200` | |
| `retrieval_top_k` | `10` | |
| `bm25_weight` / `semantic_weight` | `0.5` / `0.5` | RRF weights |
| `auth_mode` | `self_hosted` | Options: `self_hosted`, `per_request_key`, `credit_system` |
| `local_image_storage` | `True` | Save images to disk vs. use URL |
| `image_storage_limit_mb` | `100` | Auto-prune oldest when exceeded |

**Key methods**: `settings.resolve_openai_key(override)`, `settings.data_path`, `settings.image_storage_path`

### `config/personas.json`

Array of 6 personas:

| Persona | Temperature | Voice |
|---------|-------------|-------|
| Grandmother | 0.7 | Warm, nostalgic, conversational |
| Professor | 0.2 | Formal, academic, detailed |
| Extreme Summariser | 0.2 | Bulleted facts, no narrative |
| HAL 9000 | 0.2 | Calm, logical, ominous |
| Pirate | 0.7 | Boisterous, dramatic |
| Freud | 0.2 | Analytical, psychological |

Each persona has: `name`, `short_description`, `system_prompt`, `type`, `temperature`, `color_theme` (Tailwind classes: background, button, button_hover, input, ring).

### `config/jobs.yaml`

Defines all corpuses with paths to source files, ChromaDB directories, BM25 indexes, and chunk caches. Loaded by `CorpusRegistry.load_jobs_from_yaml()`.

---

## API Reference

### Health

| Method | Path | Response |
|--------|------|----------|
| `GET` | `/` | `{status, service, version, docs}` |
| `GET` | `/health` | `{status, api_host, api_port, auth_mode}` |

### Story Generation

**`GET /api/stream_story`** — SSE stream

| Query Param | Type | Default | Notes |
|-------------|------|---------|-------|
| `prompt` | string | required | min 1, max 500 chars |
| `choice_id` | string | null | Selected choice node ID |
| `new_journey` | bool | false | Clears graph, starts fresh |
| `paragraph_count` | int | 4 | Range: 1-8 |
| `persona_name` | string | null | Must match a persona name |
| `randomize_retrieval` | bool | false | Shuffle retrieval scores |
| `username` | string | null | For journey persistence |
| `corpus_name` | string | `"mahabharata"` | Must be active corpus |
| `graph_id` | string | null | Graph ID for continuation |

**SSE event types:**

| Event | Data | When |
|-------|------|------|
| `story_chunk` | token string | Each generated token |
| `message` | serialized graph JSON | Generation complete |
| `guardrail_reject` | rejection message | Prompt failed screening |
| `end` | `"Stream ended."` | Normal completion |
| `error` | error message | Exception occurred |

### Personas (CRUD)

| Method | Path | Body/Response |
|--------|------|---------------|
| `GET` | `/api/personas` | `List[PersonaInfo]` |
| `POST` | `/api/personas` | `{name, short_description, system_prompt, color_theme, temperature}` — 201 |
| `PUT` | `/api/personas/{name}` | partial update — updated persona |
| `DELETE` | `/api/personas/{name}` | `{success, message}` |

### Corpuses (CRUD)

| Method | Path | Body/Response |
|--------|------|---------------|
| `GET` | `/api/corpuses` | `List[CorpusInfo]` (includes status, chunk_count, missing_components) |
| `POST` | `/api/corpuses` | `{name, display_name, description, source_file, file_type}` — 202 |
| `PUT` | `/api/corpuses/{name}` | `{display_name?, description?, is_active?}` — updated corpus |
| `DELETE` | `/api/corpuses/{name}?delete_data=bool` | `{success, message, data_deleted}` |

### Journeys

| Method | Path | Params/Body | Response |
|--------|------|-------------|----------|
| `GET` | `/api/list_users` | — | `{users: string[]}` |
| `GET` | `/api/list_graphs` | `?username=` | `{journeys: JourneyMeta[]}` sorted newest first |
| `POST` | `/api/load_graph` | `{username, graph_id}` | `{success, meta, graph}` |
| `GET` | `/api/get_loaded_graph` | — | `{graph: GraphData}` |

### Static Files

If `local_image_storage=True`, images are served at `GET /images/{uuid}.png`.

---

## Services

### `story_agent.py` — LangGraph Pipeline

The core story generation workflow. Built with `langgraph.graph.StateGraph` operating on `StorytellerState`.

**9-node pipeline:**

```
get_last_story → build_path_context → screen_prompt ─┬─ (rejected) → END
                                                      └─ (passed) → generate_search_query
→ retrieve_chunks → generate_story → update_graph_with_story → generate_choices → update_graph_with_choices
```

**Node details:**

1. **get_last_story** — Finds parent story node from `current_choice_id` for continuity. Returns `last_story`, `parent_image_prompt`.

2. **build_path_context** — Walks the graph root-to-current-choice, collecting story summaries. Returns a numbered list of prior chapter summaries for narrative continuity.

3. **screen_prompt** — Runs two parallel guardrail checks:
   - OpenAI Moderation API (generic toxicity)
   - Custom intent classifier (corpus-aware, distinguishes faithful exploration from malicious prompts)
   - Fails closed — uncertain prompts are rejected.
   - Conditional edge: rejected → END, passed → continue.

4. **generate_search_query** — GPT converts user prompt into a targeted retrieval query. Structured output: `SearchQuery {query: str}`.

5. **retrieve_chunks** — `HybridRetriever.search()` combines ChromaDB semantic + BM25 keyword results via Reciprocal Rank Fusion. Optionally randomizes scores for exploration.

6. **generate_story** — Constructs system prompt (persona voice, journey context, grounding constraints). Streams tokens via `ChatOpenAI(streaming=True)`. Concurrently triggers image generation after 1/4 of content is produced. Structured output: `Story {story: str}`.

7. **update_graph_with_story** — Creates story node (UUID), links parent choice → story, generates summary (async), saves graph to disk.

8. **generate_choices** — GPT generates 3 follow-up prompts from the story. Persona-specific voice if selected. Structured output: `Choices {choices: List[str]}`.

9. **update_graph_with_choices** — Creates 3 choice nodes (UUIDs), links story → choices, saves final graph, serializes for frontend (resolves image URLs).

**Key functions:**
- `create_story_agent(api_key) → compiled StateGraph`
- `get_story_agent(api_key) → cached compiled workflow`

### `auth_service.py` — Authentication

Three modes (only `self_hosted` is currently active):

| Mode | Behavior |
|------|----------|
| `self_hosted` | Uses `OPENAI_API_KEY` from `.env` |
| `per_request_key` | Client provides key in header (not yet wired in routes) |
| `credit_system` | Platform key + credit tracking (not yet implemented) |

**Key functions:** `get_openai_client(api_key)`, `get_async_openai_client(api_key)` — lazy-initialized global singletons.

### `journey_manager.py` — Graph Persistence

File-based JSON persistence at `saved_graphs/{username}/{graph_id}`.

**Graph file format:**
```json
{
  "meta": {
    "username": "mehrab",
    "graph_name": "20250101_120000_Arjun.json",
    "timestamp": "2025-01-01T12:00:00.000000",
    "initial_prompt": "tell me a story about Arjun",
    "last_prompt": "What happens next?",
    "persona": "Professor",
    "corpus_name": "mahabharata",
    "num_story_nodes": 3,
    "last_story_timestamp": "2025-01-01T12:05:00.000000"
  },
  "graph": { "directed": true, "nodes": [...], "links": [...] }
}
```

Graph IDs are filenames: `YYYYMMDD_HHMMSS_{prompt_25_chars}.json`.

**Key methods:**
- `save_graph(graph, username, ...) → graph_id`
- `load_graph(username, graph_id) → (nx.DiGraph, meta)`
- `list_journeys(username) → List[JourneyMeta]` — enriched with corpus availability
- `list_users() → List[str]`

### `image_generator.py` — DALL-E Integration

**Pipeline:** story text → GPT prompt generation → DALL-E image → local storage

- Prompt generation: GPT-4o-mini creates a 1-2 sentence scene description with character names
- Visual continuity: passes parent image prompt to maintain style across chapters
- Style prefix: `"impressionist watercolour sketch, soft pastel colour palette, loose gestural brushstrokes, minimal detail, no text, warm dreamlike atmosphere — "`
- Output: 256x256 PNG, base64 decoded, saved as `saved_graphs/images/{uuid}.png`
- Storage limit enforced (default 100 MB) by deleting oldest files

**URL resolution:** `resolve_image_urls(serializable_graph)` converts local UUIDs to serving URLs (`/images/{uuid}.png`) before returning graph to frontend.

---

## Models

### `models/state.py` — StorytellerState

TypedDict passed between all LangGraph nodes:

| Field | Type | Purpose |
|-------|------|---------|
| `messages` | `List[BaseMessage]` | Conversation history |
| `graph` | `nx.DiGraph` | Story graph structure |
| `current_choice_id` | `Optional[str]` | Selected choice node |
| `latest_story_node_id` | `Optional[str]` | Most recent story node |
| `search_query` | `str` | Generated search query |
| `retrieved_chunks` | `List[str]` | Text chunks from retriever |
| `randomize_retrieval` | `bool` | Shuffle retrieval results |
| `corpus_name` | `str` | Active corpus |
| `story` | `str` | Generated story text |
| `paragraph_count` | `int` | 1-8 paragraphs |
| `path_context` | `str` | Journey summaries (root to parent) |
| `guardrail_rejected` | `bool` | Prompt failed screening |
| `last_story` | `Optional[str]` | Previous chapter for continuity |
| `persona_name` | `Optional[str]` | Selected persona |
| `choices` | `List[str]` | Generated follow-up prompts |
| `image_url` | `Optional[str]` | Image URL or UUID |
| `image_prompt` | `Optional[str]` | Generated image prompt |
| `parent_image_prompt` | `Optional[str]` | Previous image prompt |
| `username` | `Optional[str]` | User for persistence |
| `initial_prompt` | `Optional[str]` | First prompt (metadata) |
| `serializable_graph` | `Optional[dict]` | Final graph for frontend |

### `models/api_models.py` — Pydantic Models

Key models: `StoryRequest`, `CorpusInfo`, `PersonaInfo`, `ColorTheme`, `JourneyMeta`, `GraphNode`, `GraphEdge`, `GraphData`, `LoadGraphRequest/Response`, `JourneyListResponse`, `PromptScreenResult`.

`GraphNode` allows extra fields via `model_config = ConfigDict(extra="allow")`.

### `models/chunk.py` — Text Chunk

```python
class Chunk(BaseModel):
    base_text: str
    document_position: DocumentPosition  # start/end token indexes
    context: Optional[str]               # surrounding context
    embedding: Optional[List[float]]
    chunk_id: str  # computed: SHA256 of base_text
```

---

## Retrieval System

### `embed_retrieve/retriever.py` — HybridRetriever

Combines semantic and keyword search using Reciprocal Rank Fusion (RRF).

**Search flow:**
1. Embed query with OpenAI `text-embedding-3-small`
2. Query ChromaDB collection for semantic matches
3. Tokenize query and score with BM25 index
4. Fuse results with RRF: `score = sum(1 / (k + rank + 1))` where `k = 60`
5. Return top-k results: `{chunk_id, score, base_text, context}`

Constructor validates corpus exists and is active, loads ChromaDB client and BM25 pickle.

### `embed_retrieve/corpus_registry.py` — CorpusRegistry

Central registry for all corpuses, persisted as `data/corpus_registry.json`.

**CorpusConfig fields:** name, display_name, description, source_file, file_type, collection_name, cache_dir, bm25_index_path, chroma_db_path, is_active, created_at, last_processed, chunk_count.

**CorpusStatus:** Checks existence of chunks, ChromaDB, and BM25 index. Reports `needs_rebuild` and `missing_components`.

**Default behavior:** If no registry file exists, creates a default with the Mahabharata corpus. Loads all corpuses from `config/jobs.yaml` at startup.

---

## Shared State

### `api/dependencies.py` — GraphState

Thread-safe singleton for the active story graph.

```python
class GraphState:
    async get_graph() → nx.DiGraph    # returns a copy
    async set_graph(graph)            # replace entire graph
    async clear_graph()               # reset to empty
    async is_empty() → bool
```

Uses `asyncio.Lock` to prevent race conditions. One graph active per server at a time.

---

## Data Flow

```
User clicks choice / types prompt
    ↓
GET /api/stream_story (query params)
    ↓
stories.py validates corpus, loads graph from memory or disk
    ↓
get_story_agent().astream_events(initial_state, version="v1")
    ↓
LangGraph 9-node pipeline:
    get_last_story → build_path_context → screen_prompt
    → generate_search_query → retrieve_chunks
    → generate_story (streams tokens + concurrent image gen)
    → update_graph_with_story → generate_choices
    → update_graph_with_choices (saves to disk)
    ↓
SSE events yielded to frontend:
    story_chunk (tokens) → message (final graph) → end
    ↓
Frontend renders updated graph with new story + choices
```

**Key async patterns:**
- Story generation streams tokens via LangChain's streaming callback
- Image generation triggered concurrently after 1/4 of story text
- Summary generation awaited before graph save
- Guardrail checks (moderation + intent classifier) run in parallel

---

## Error Handling

**HTTP errors:** 400 (bad params), 404 (not found), 409 (conflict/duplicate), 500 (unexpected).

**Stream errors:** `error` SSE event with message string, then stream terminates.

**Graph sync:** If client requests a `choice_id` not in the server graph, the route attempts to reload from disk. If the choice is still missing, returns an out-of-sync error.

---

## Testing

```bash
cd storyteller_backend
poetry run pytest tests/ -v
```

Tests use pytest + pytest-asyncio. Fixtures in `conftest.py`. Current test files cover path context assembly, paragraph count validation, and prompt screening.

---

## Dependencies

Managed by Poetry 2.x. The lockfile (`poetry.lock`) is at the repo root.

**Critical:** Never use `pip install` — ChromaDB version changes trigger database migrations that permanently destroy embedded vector data in `data/chroma_db/`. Always use `poetry install` or `poetry add`.

Key packages: fastapi 0.115.5, langgraph 0.2.59, langchain 0.3.13, chromadb 1.3.7, networkx 3.4.2, sse-starlette 2.2.1, pydantic 2.10.3, openai 1.58.1.
