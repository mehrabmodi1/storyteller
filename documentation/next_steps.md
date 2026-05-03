# Storyteller Project: Current Status & Next Steps

**Last Updated:** May 3, 2026

---

## 📍 CURRENT STATUS (May 2026)

This document was originally drafted in November 2025 as a Phase 1/2/3 roadmap. Most of that work is now complete or has been superseded. **Treat the section below as authoritative; everything beyond it is a historical snapshot kept for context.**

### What's done

- **Modular backend** (`storyteller_backend/`) — FastAPI + LangGraph + ChromaDB, Poetry-managed, 11 API endpoints, SSE streaming, full CRUD on personas/corpuses/journeys, 41-test pytest suite, 6 personas, 6 corpora.
- **Frontend** (`storyteller_frontend/`) — React 18 + Vite + ReactFlow + Tailwind. Story graph, SSE streaming, choice interactions, persona/corpus dropdowns, ELK layout, journey save/load all working. (Earlier docs called this "Phase 2 - Coming Soon"; that's stale.)
- **Provider abstraction** — `Provider` enum + `ProviderProfile` dataclass keyed map in `config/settings.py`. Switching between Gemini and OpenAI is one line. Each provider's chat / embedding / image model + RPM bundled in one place.
- **Build/retrieve unification** — both `embed_retrieve/build_database.py` and `embed_retrieve/retriever.py` resolve paths through a shared helper (`embed_retrieve/paths.py`). Per-corpus, provider-suffixed layout: `data/chroma_db/<corpus>_<provider>/<corpus>_chunks/`. No more legacy single-root layout.
- **Gemini support** — chat (`gemini-2.5-flash-lite` default, `flash` available), embeddings (`gemini-embedding-001`), image gen (`gemini-2.5-flash-image`, paid tier only). `thinking_budget=0` applied automatically via `services/llm.py:get_chat_llm()` to prevent gemini-2.5-flash from consuming the entire output budget on internal reasoning.
- **Resilient corpus build pipeline** — rate-limited, retried, batch upserts, resumable across daily-quota interruptions.
- **Corpus migration to per-provider layout** — all six corpora's existing OpenAI data renamed `<corpus>_openai/`. Five of six rebuilt under Gemini (arabian_nights paused at 400/484 by daily embedding cap, will resume on next run).

### What's open

- **arabian_nights Gemini embeddings** — 84 chunks remaining; resume with `poetry run python -m embed_retrieve.build_database --corpus arabian_nights --force-rebuild`.
- **Image generation on Gemini free tier** — quota is 0/day, so journeys get no images while Gemini billing is disabled. Story generation is unaffected. Three options for later: (a) enable Gemini billing, (b) decouple `image_provider` from `chat_provider` and route images to OpenAI/DALL-E, (c) integrate a free third-party image API (e.g. Pollinations.ai).
- **Reflex admin panel** (Phase 3 in original plan) — not started; CRUD endpoints exist on the backend but no admin UI was built. May not be needed depending on future direction.
- **Per-request-key auth mode** (Phase 2+ in original plan) — `auth_mode` field in `Config` exists but only `self_hosted` is wired. The other modes (`per_request_key`, `credit_system`) are scaffolding only.
- **Build script: PDF-only.** Text-source corpora must already have a populated `data/processed_chunks/<name>/` cache (true for all current corpora). Adding text-source ingestion is straightforward but out of scope so far.

### Recently retired / superseded

- The original "Phase 1 / 2 / 3" framing — both Phase 1 (backend refactor) and Phase 2 (frontend) are essentially done. Treat them as history.
- The old `src/` directory (legacy Next.js + agent code) — gone.
- FAISS — never adopted; the project has always used ChromaDB plus a separate BM25 index.
- The "DALL-E 3" mention in old docs — actually `dall-e-2`.
- `documentation/MANUAL_SETUP.md` — replaced (May 2026) with an architecture-focused developer guide. The setup steps now live in the [README](../README.md).

For the up-to-date setup walkthrough, see the [README](../README.md). For deeper architectural detail, see [`MANUAL_SETUP.md`](MANUAL_SETUP.md).

---

> **Below this line: historical roadmap snapshot from November 2025.** Kept for context — design rationale, decisions taken, alternatives considered. Specifics about file layouts, tech choices, and "next phase" framing may not match current state.

---

## 🎉 PHASE 1 COMPLETE: Backend Refactoring

**Status:** ✅ **COMPLETED** (November 23, 2025)

The `storyteller_backend/` project is now fully operational with:
- ✅ 37 new files created (~3,500 lines of code)
- ✅ Modular architecture (config, models, services, api)
- ✅ Complete API layer with 11 endpoints
- ✅ Full CRUD for personas and corpuses (admin panel ready)
- ✅ SSE streaming story generation
- ✅ 10/10 tests passing
- ✅ Production-ready, cloud deployment ready

**Next Phase:** Phase 2 - React Frontend Development

See [`cursor_chat_8.md`](cursor_chats/cursor_chat_8.md) for complete session documentation.

---

## 📊 Current Implementation Status

### ✅ COMPLETED FEATURES

#### 1. **NEW Backend Architecture** (`storyteller_backend/`)

**Configuration & Settings:**
- ✅ Pydantic-based configuration (`config/settings.py`)
  - Strict separation: secrets in `.env`, config hardcoded
  - Environment-based secret loading
  - Type-safe settings with computed properties
- ✅ Personas configuration (`config/personas.json`)
- ✅ Jobs configuration (`config/jobs.yaml`)

**Data Models:**
- ✅ API contracts (`models/api_models.py`)
  - StoryRequest/Response, CorpusInfo, PersonaInfo
  - JourneyMeta, GraphNode/Edge/Data
- ✅ LangGraph state (`models/state.py`)
- ✅ Chunk models (`models/chunk.py`)

**Services Layer:**
- ✅ **Story Agent** (`services/story_agent.py`) - 7-node LangGraph pipeline:
  1. `get_last_story`: Find parent story for continuity
  2. `generate_search_query`: Convert prompt to search query
  3. `retrieve_chunks`: Hybrid retrieval (ChromaDB + BM25)
  4. `generate_story`: Streaming story generation with GPT-4o-mini
  5. `update_graph_with_story`: Add story node to graph
  6. `generate_choices`: Generate 3 follow-up prompts
  7. `update_graph_with_choices`: Add choice nodes, save graph
- ✅ **Auth Service** (`services/auth_service.py`)
  - OpenAI client management
  - Support for 3 auth modes: self_hosted, per_request_key, credit_system
- ✅ **Journey Manager** (`services/journey_manager.py`)
  - Save/load/list/delete journeys
  - Legacy graph support with metadata extraction
  - Corpus validation
- ✅ **Image Generator** (`services/image_generator.py`)
  - DALL-E image generation
  - Image prompt creation with GPT-4o-mini
  - Visual continuity across story nodes

**Corpus System:**
- ✅ Migrated `embed_retrieve/` module with all tools
- ✅ Hybrid retrieval (ChromaDB + BM25) with Reciprocal Rank Fusion
- ✅ 6 active corpuses:
  - The Mahabharata ✅
  - The Odyssey ✅
  - The Arabian Nights ✅
  - The Volsunga Saga ✅
  - The Jataka Tales ✅
  - Locus Platform Documentation ✅
- ✅ Batch ingestion system
- ✅ Corpus registry with status tracking

**API Layer:**
- ✅ FastAPI application (`api/main.py`)
  - CORS middleware
  - Lifespan management
  - Auto-generated docs at `/docs`
- ✅ Global graph state management (`api/dependencies.py`)
- ✅ **11 API Endpoints:**
  - Stories:
    - `GET /api/stream_story` - SSE streaming story generation
  - Personas (Full CRUD for admin panel):
    - `GET /api/personas` - List all personas
    - `POST /api/personas` - Create new persona
    - `PUT /api/personas/{name}` - Update persona
    - `DELETE /api/personas/{name}` - Delete persona
  - Corpuses (Full CRUD for admin panel):
    - `GET /api/corpuses` - List all corpuses with status
    - `POST /api/corpuses` - Trigger corpus ingestion
    - `PUT /api/corpuses/{name}` - Update corpus metadata
    - `DELETE /api/corpuses/{name}` - Delete corpus
  - Journeys:
    - `GET /api/list_graphs` - List user's saved journeys
    - `POST /api/load_graph` - Load a saved journey
    - `GET /api/get_loaded_graph` - Get currently loaded graph

**Testing:**
- ✅ Incremental testing framework (`test_setup.py`)
- ✅ 10 comprehensive tests, all passing
- ✅ Tests for: config, models, services, corpus registry, auth, journey manager, image generator, story agent

#### 2. **OLD Frontend - Next.js Application** (`src/app/`) [TO BE REPLACED]
- ✅ Single-page React application using Next.js 15.3.4
- ✅ ReactFlow-based graph visualization
  - Custom StoryNode component (displays story + image)
  - Custom ChoiceNode component (interactive, editable prompts)
  - ELK (Eclipse Layout Kernel) for automatic hierarchical layout
- ✅ SSE integration for streaming story display
- ✅ Four dropdown components:
  - Username selector (localStorage-based)
  - Persona selector (fetches from backend)
  - Journey selector (loads saved graphs)
  - Corpus selector (switches text corpus)
- ✅ Dynamic theming based on selected persona
- ✅ Suggestion cards for initial prompts
- ✅ Story length slider (quick read ↔ richer detail)
- ✅ Streaming modal that displays story generation in real-time
- ✅ Inline editing of choice nodes (click to edit, Enter to submit)
- ✅ Image loading with expiry detection (Azure SAS tokens)
- ✅ LocalStorage for user preferences (username, corpus)

#### 3. **Data Infrastructure**
- ✅ 6 complete corpuses ingested and indexed
- ✅ ChromaDB vector stores for all corpuses
- ✅ BM25 keyword indexes for all corpuses
- ✅ Central corpus registry (`data/corpus_registry.json`)
- ✅ User-specific journey storage (`saved_graphs/{username}/`)
- ✅ Environment configuration via `.env` file

---

## ⚠️ KNOWN ISSUES & TECHNICAL DEBT

### Architecture Issues

1. **Monolithic Frontend Component** 🔴
   - `src/app/app/page.tsx` is 834 lines
   - Violates Single Responsibility Principle
   - Manages state, API communication, layout, events, and rendering
   - Difficult to test and maintain

2. **Code Duplication in Dropdowns** 🔴
   - Four dropdown components share ~70% identical code
   - No base dropdown component
   - Each implements own click-outside handling, theming, tooltips

3. **Complex State Management** 🟡
   - 15+ pieces of state in main component
   - Cascading state updates (username change → clear graph → show suggestions)
   - No clear data flow
   - Mixing UI state with business logic

4. **Hard-coded Configuration** 🟡
   - API URLs hard-coded as `http://localhost:8000`
   - Should use environment variables
   - Port numbers not configurable

5. **Layout Performance** 🟡
   - ELK layout runs on every node count change with 100ms debounce
   - No memoization of layout calculations
   - Can cause lag with large graphs
   - Graph viewport cropping issue (can't see full graph even when zoomed out)

6. **Error Handling** 🔴
   - No error boundaries in React components
   - Failed API requests only log to console
   - Image loading failures silent (only warnings)
   - No user-facing error messages

7. **Image URL Expiration Logic** 🟡
   - Duplicate code in two places (lines 389-416 and 615-650)
   - Azure Blob Storage URL parsing done inline
   - Should be extracted to utility function

8. **LocalStorage Usage** 🟡
   - Direct localStorage calls without abstraction
   - No error handling for localStorage failures
   - Could break in private browsing mode

### Project Structure Issues

9. **Mono-repo Without Separation** 🟡
   - Backend and frontend share same repo
   - Frontend lives in `src/app/` alongside backend code
   - Shared `package.json` and `requirements.txt` at different levels
   - Unclear dependency management

10. **No Separate Admin Interface** 🟡
    - Corpus management done via command line
    - No GUI for managing corpuses, personas, users
    - No analytics dashboard

---

## 🎯 PLANNED REFACTORING: storyteller_app

### Overview
Rebuild the application with a modular, Python-first architecture while maintaining the ability to swap graph visualization implementations.

### Architecture Decision
Based on analysis of Reflex.dev capabilities:
- **Backend:** Python (FastAPI) - 95% of business logic
- **Frontend:** Minimal React app - ONLY for graph visualization
- **Admin Panel:** Reflex.dev - Corpus/persona management (future)

### Why Not Full Reflex?
- Reflex lacks native support for dynamic, auto-layout graph visualizations
- Complex interactive graphs (like ReactFlow) require significant custom integration
- Wrapping ReactFlow in Reflex would require deep knowledge of both frameworks
- Better to use React for what it does best (interactive UI widgets)

### Rationale
1. **Python-First:** Maximizes team's Python expertise (95% of code)
2. **Right Tool for Right Job:** React excels at interactive graph widgets
3. **Modularity:** Clear separation of concerns
4. **Swappable Views:** Easy to experiment with different graph libraries
5. **Maintainability:** Each component has single responsibility

---

## 📋 IMPLEMENTATION PLAN

### ✅ Phase 1: Backend Restructuring (COMPLETED - November 23, 2025)

**Goal:** Create a clean, standalone Python backend in `storyteller_backend/` with clear API contracts and modular architecture.

**Status:** ✅ **COMPLETE** - See [`cursor_chat_8.md`](cursor_chats/cursor_chat_8.md) for full documentation.

**What Was Built:**
- ✅ Project structure with config, models, services, api layers
- ✅ Pydantic-based configuration with secret separation
- ✅ Complete data models (API contracts, LangGraph state, chunks)
- ✅ 4 core services (auth, journey manager, image generator, story agent)
- ✅ Migrated embed_retrieve module with all corpus tools
- ✅ Complete API layer with 11 endpoints
- ✅ Full CRUD for personas and corpuses (admin panel ready)
- ✅ SSE streaming story generation
- ✅ 10 comprehensive tests, all passing
- ✅ Production-ready architecture

**Commands:**
```bash
cd storyteller_backend
source .venv_bk/bin/activate
python test_setup.py  # Run tests
python -m uvicorn api.main:app --reload  # Run server
```

---

### 🚧 Phase 2: React Frontend (IN PROGRESS)

**Goal:** Create a lightweight React app in `storyteller_frontend/` that handles graph visualization and admin panel.

#### 1.1 Project Structure Setup

```
storyteller_backend/               # Independent backend project
├── .venv/                         # Isolated virtual environment
├── requirements.txt               # Backend dependencies
├── .env                           # Environment configuration (gitignored)
├── .env.example                   # Environment template
├── README.md                      # Backend-specific documentation
├── Dockerfile                     # For containerization (future)
├── test_setup.py                  # Incremental testing script
├── config/
│   ├── __init__.py
│   ├── settings.py                # Centralized config (Pydantic Settings)
│   └── personas.json              # Persona definitions
├── api/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── story.py               # Story generation endpoints
│   │   ├── personas.py            # Persona endpoints
│   │   ├── corpuses.py            # Corpus endpoints
│   │   └── journeys.py            # Journey management endpoints
│   └── dependencies.py            # Shared dependencies (DB, retriever, etc.)
├── services/
│   ├── __init__.py
│   ├── story_agent.py             # LangGraph agent logic
│   ├── retrieval.py               # Hybrid retriever
│   ├── corpus_manager.py          # Corpus registry wrapper
│   ├── journey_manager.py         # Journey save/load logic
│   └── image_generator.py         # DALL-E integration
├── models/
│   ├── __init__.py
│   ├── state.py                   # LangGraph state definitions
│   ├── graph_data.py              # Graph structure models
│   └── api_models.py              # Pydantic request/response models
├── utils/
│   ├── __init__.py
│   ├── graph_utils.py             # NetworkX helpers
│   └── sse_utils.py               # SSE streaming helpers
└── tests/
    ├── __init__.py
    ├── test_api.py
    ├── test_services.py
    └── test_retrieval.py
```

#### 1.2 Configuration Management

**Task:** Replace hard-coded values with environment-based configuration

```python
# storyteller_backend/config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # OpenAI Configuration
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    image_model: str = "dall-e-3"
    
    # Azure Storage
    azure_storage_connection_string: Optional[str] = None
    azure_container_name: Optional[str] = None
    
    # Data Paths (relative to project root)
    data_dir: str = "../../data"
    saved_graphs_dir: str = "../../saved_graphs"
    personas_file: str = "config/personas.json"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Retrieval Settings
    retrieval_top_k: int = 10
    bm25_weight: float = 0.5
    semantic_weight: float = 0.5
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

#### 1.3 Modular FastAPI Application

**Task:** Break monolithic server into modular routes

```python
# storyteller_backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import story, personas, corpuses, journeys
from ..config.settings import settings

app = FastAPI(
    title="Storyteller API",
    description="Generative storytelling with branching narratives",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(story.router, prefix="/api/story", tags=["story"])
app.include_router(personas.router, prefix="/api/personas", tags=["personas"])
app.include_router(corpuses.router, prefix="/api/corpuses", tags=["corpuses"])
app.include_router(journeys.router, prefix="/api/journeys", tags=["journeys"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

#### 1.4 Service Layer Extraction

**Task:** Extract business logic from routes into services

```python
# storyteller_backend/services/story_agent.py
"""
Encapsulates the LangGraph agent logic.
Migrated from src/agent/graph.py with improvements.
"""
from typing import AsyncGenerator
from ..models.state import StorytellerState
from ..models.graph_data import GraphData, StoryNode, ChoiceNode

class StoryAgent:
    def __init__(self, retriever, image_generator, config):
        self.retriever = retriever
        self.image_generator = image_generator
        self.config = config
        self._build_graph()
    
    def _build_graph(self):
        # Build LangGraph with nodes: query → retrieve → story → choices → update
        pass
    
    async def generate_story_stream(
        self, 
        prompt: str, 
        current_graph: nx.DiGraph,
        **kwargs
    ) -> AsyncGenerator[dict, None]:
        """
        Streams story chunks and final graph data.
        Yields: {"type": "chunk", "data": "..."} or {"type": "graph", "data": {...}}
        """
        pass
```

#### 1.5 API Models with Pydantic

**Task:** Define clear request/response contracts

```python
# storyteller_backend/models/api_models.py
from pydantic import BaseModel, Field
from typing import Optional, List

class StoryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    choice_id: Optional[str] = None
    new_journey: bool = False
    story_length: int = Field(1500, ge=500, le=3000)
    persona_name: Optional[str] = None
    randomize_retrieval: bool = False
    username: Optional[str] = None
    corpus_name: str = "mahabharata"

class CorpusInfo(BaseModel):
    name: str
    display_name: str
    description: str
    is_active: bool
    chunk_count: int
    last_processed: Optional[str]
    needs_rebuild: bool
    missing_components: List[str]

class JourneyMeta(BaseModel):
    graph_id: str
    username: str
    timestamp: str
    initial_prompt: str
    last_prompt: str
    persona: str
    corpus_name: str
    num_story_nodes: int
```

#### 1.6 Migration Tasks

1. **Extract graph.py logic** → `services/story_agent.py` ✅
2. **Extract retriever.py** → `services/retrieval.py` (reuse existing) ✅
3. **Extract corpus_registry.py** → `services/corpus_manager.py` (reuse existing) ✅
4. **Create settings.py** with Pydantic Settings ✅
5. **Split server.py** into modular routes ✅
6. **Create API models** for all endpoints ✅
7. **Add error handling middleware** ✅
8. **Write unit tests** for services ✅

#### 1.7 Success Criteria

- ✅ Backend runs independently with `python -m uvicorn api.main:app`
- ✅ All 6 API endpoints functional with new structure
- ✅ Configuration via `.env` file (no hard-coded values)
- ✅ Services are testable in isolation
- ✅ API documentation auto-generated at `/docs`
- ✅ Existing data directories compatible (no migration needed)

---

**Sub-Goals:**
1. Create lightweight React app (Vite + TypeScript)
2. Implement admin panel for personas/corpuses CRUD
3. Migrate ReactFlow graph visualization
4. Implement SSE streaming
5. Create swappable graph interface

#### 2.1 Project Structure

```
storyteller_frontend/              # Independent frontend project (Phase 2)
├── package.json
├── tsconfig.json
├── vite.config.ts                # Using Vite instead of Next.js (faster)
├── .env.local
├── .env.local.example            # Environment template
├── README.md                     # Frontend-specific documentation
├── Dockerfile                    # For containerization (future)
├── index.html
├── src/
│   ├── main.tsx                # App entry point
│   ├── App.tsx                 # Root component (thin wrapper)
│   ├── config/
│   │   └── api.config.ts       # API base URL from env
│   ├── components/
│   │   ├── graph-views/        # Swappable graph visualizations
│   │   │   ├── GraphView.interface.ts
│   │   │   ├── GraphViewSwitcher.tsx
│   │   │   ├── ReactFlowGraph/
│   │   │   │   ├── ReactFlowGraph.tsx
│   │   │   │   ├── StoryNode.tsx
│   │   │   │   ├── ChoiceNode.tsx
│   │   │   │   └── useELKLayout.ts
│   │   │   ├── CytoscapeGraph/   # Alternative (future)
│   │   │   │   └── CytoscapeGraph.tsx
│   │   │   └── D3Graph/           # Alternative (future)
│   │   │       └── D3Graph.tsx
│   │   ├── controls/
│   │   │   ├── PromptInput.tsx
│   │   │   ├── StoryLengthSlider.tsx
│   │   │   └── SuggestionCards.tsx
│   │   ├── dropdowns/
│   │   │   ├── BaseDropdown.tsx   # DRY: Single dropdown component
│   │   │   ├── UsernameDropdown.tsx
│   │   │   ├── PersonaDropdown.tsx
│   │   │   ├── JourneyDropdown.tsx
│   │   │   └── CorpusDropdown.tsx
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── MainContainer.tsx
│   │   │   └── StreamingModal.tsx
│   │   └── ErrorBoundary.tsx   # Global error handling
│   ├── hooks/
│   │   ├── useSSE.ts           # Reusable SSE hook
│   │   ├── useLocalStorage.ts  # Safe localStorage wrapper
│   │   ├── useGraphData.ts     # Graph state management
│   │   └── useTheme.ts         # Persona theme management
│   ├── services/
│   │   └── api.ts              # API client functions
│   ├── types/
│   │   ├── graph.types.ts
│   │   ├── api.types.ts
│   │   └── theme.types.ts
│   ├── utils/
│   │   ├── imageLoader.ts      # Image expiry logic
│   │   └── graphTransform.ts   # NetworkX → ReactFlow conversion
│   └── styles/
│       └── globals.css
└── public/
    └── assets/
```

#### 2.2 Key Design Patterns

**2.2.1 Swappable Graph Views**

```typescript
// src/components/graph-views/GraphView.interface.ts
export interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick: (nodeId: string) => void;
  onNodeEdit: (nodeId: string, newLabel: string) => void;
  theme: ColorTheme;
  isLoading: boolean;
}

export interface IGraphView {
  fitView: () => void;
  centerNode: (nodeId: string) => void;
  exportImage: () => Promise<Blob>;
}

// src/components/graph-views/GraphViewSwitcher.tsx
export const GraphViewSwitcher: React.FC<{ viewType: string }> = ({ viewType }) => {
  switch (viewType) {
    case 'reactflow':
      return <ReactFlowGraph {...props} />;
    case 'cytoscape':
      return <CytoscapeGraph {...props} />;
    case 'd3':
      return <D3Graph {...props} />;
    default:
      return <ReactFlowGraph {...props} />;
  }
};
```

**2.2.2 Reusable SSE Hook**

```typescript
// src/hooks/useSSE.ts
export function useSSE(url: string | null) {
  const [streamingText, setStreamingText] = useState('');
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!url) return;
    
    const eventSource = new EventSource(url);
    setIsStreaming(true);
    setStreamingText('');
    setError(null);
    
    const handleChunk = (event: MessageEvent) => {
      setStreamingText(prev => prev + event.data);
    };
    
    const handleGraph = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      setGraphData(data);
    };
    
    const handleError = () => {
      setError(new Error('Connection failed'));
      eventSource.close();
      setIsStreaming(false);
    };
    
    const handleEnd = () => {
      eventSource.close();
      setIsStreaming(false);
    };
    
    eventSource.addEventListener('story_chunk', handleChunk);
    eventSource.addEventListener('message', handleGraph);
    eventSource.addEventListener('error', handleError);
    eventSource.addEventListener('end', handleEnd);
    
    return () => {
      eventSource.close();
      setIsStreaming(false);
    };
  }, [url]);

  return { streamingText, graphData, isStreaming, error };
}
```

**2.2.3 Base Dropdown Component (DRY)**

```typescript
// src/components/dropdowns/BaseDropdown.tsx
interface BaseDropdownProps<T> {
  items: T[];
  selectedItem: T | null;
  onSelect: (item: T) => void;
  getLabel: (item: T) => string;
  renderTooltip?: (item: T) => React.ReactNode;
  disabled?: boolean;
  theme?: ColorTheme;
  placeholder?: string;
}

export function BaseDropdown<T>({
  items,
  selectedItem,
  onSelect,
  getLabel,
  renderTooltip,
  ...props
}: BaseDropdownProps<T>) {
  // All common dropdown logic here
  // Click-outside, keyboard navigation, theming
  // Eliminates 70% code duplication!
}

// Usage in specific dropdowns:
export const PersonaDropdown = () => (
  <BaseDropdown
    items={personas}
    selectedItem={selectedPersona}
    onSelect={setSelectedPersona}
    getLabel={(p) => p.name}
    renderTooltip={(p) => <div>{p.short_description}</div>}
  />
);
```

**2.2.4 Context for App State**

```typescript
// src/context/AppContext.tsx
interface AppContextType {
  username: string;
  setUsername: (username: string) => void;
  corpus: string;
  setCorpus: (corpus: string) => void;
  persona: string;
  setPersona: (persona: string) => void;
  theme: ColorTheme;
}

export const AppProvider: React.FC = ({ children }) => {
  const [username, setUsername] = useLocalStorage('username', '');
  const [corpus, setCorpus] = useLocalStorage('corpus', 'mahabharata');
  const [persona, setPersona] = useState('Grandmother');
  
  const theme = useMemo(() => 
    personas.find(p => p.name === persona)?.color_theme
  , [persona]);
  
  return (
    <AppContext.Provider value={{ username, setUsername, corpus, setCorpus, persona, setPersona, theme }}>
      {children}
    </AppContext.Provider>
  );
};
```

#### 2.3 Migration Tasks

1. **Setup Vite project** with React + TypeScript ✅
2. **Create BaseDropdown** component (eliminate duplication) ✅
3. **Extract useSSE hook** from page.tsx ✅
4. **Extract useLocalStorage hook** with error handling ✅
5. **Create GraphViewSwitcher** with interface ✅
6. **Migrate ReactFlowGraph** from old app ✅
7. **Create AppContext** for global state ✅
8. **Add ErrorBoundary** component ✅
9. **Extract image utils** (URL expiry logic) ✅
10. **Configure environment variables** (.env.local) ✅
11. **Write integration tests** with React Testing Library ✅

#### 2.4 Fixing Known Issues

| Issue | Solution |
|-------|----------|
| 🔴 Monolithic 834-line component | Split into 20+ small components |
| 🔴 Code duplication in dropdowns | Single BaseDropdown component |
| 🔴 No error boundaries | Add ErrorBoundary at root |
| 🟡 Hard-coded API URLs | Environment variables via Vite |
| 🟡 Complex state management | Context API + custom hooks |
| 🟡 Layout performance | Memoize ELK calculations, debounce properly |
| 🟡 Image expiry duplication | Single utility function |
| 🟡 LocalStorage errors | Safe wrapper hook with try/catch |
| 🟡 Graph viewport cropping | Fix ReactFlow fitView parameters |

#### 2.5 Success Criteria

- ✅ App runs with `npm run dev` on port 3000
- ✅ Connects to backend on configurable port
- ✅ All 4 dropdowns use BaseDropdown (no duplication)
- ✅ Main App.tsx < 100 lines (just composition)
- ✅ Graph view can be swapped via config
- ✅ Error messages shown to users (not just console)
- ✅ LocalStorage failures handled gracefully
- ✅ Image expiry logic in single utility
- ✅ Full graph visible when zoomed out

---

### Phase 3: Reflex Admin Panel (Future Enhancement)

**Goal:** Create a Python-based admin dashboard for corpus and persona management (not MVP, but nice-to-have).

#### 3.1 Use Cases for Reflex

Reflex is **perfect** for:
- ✅ Data tables (corpus list, user list)
- ✅ Forms (add/edit persona, add corpus)
- ✅ Status dashboards (corpus health, rebuild status)
- ✅ Analytics (user engagement, popular corpuses)

Reflex is **not suitable** for:
- ❌ Interactive graph visualization (our main app)

#### 3.2 Admin Panel Structure

```
storyteller_app/admin/
├── .venv/
├── requirements.txt            # Reflex + shared backend code
├── rxconfig.py
├── admin_app/
│   ├── admin_app.py           # Main Reflex app
│   ├── state/
│   │   ├── corpus_state.py    # Corpus management state
│   │   ├── persona_state.py   # Persona management state
│   │   └── analytics_state.py # Usage analytics state
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── dashboard.py       # Overview page
│   │   ├── corpuses.py        # Corpus management
│   │   ├── personas.py        # Persona management
│   │   └── analytics.py       # Usage analytics
│   └── components/
│       ├── corpus_table.py
│       ├── rebuild_button.py
│       └── status_badge.py
└── assets/
```

#### 3.3 Example Admin Pages

```python
# admin_app/pages/corpuses.py
import reflex as rx
from ..state.corpus_state import CorpusState

def corpus_management() -> rx.Component:
    return rx.vstack(
        rx.heading("Corpus Management", size="lg"),
        
        # Status overview
        rx.hstack(
            rx.stat(
                rx.stat_label("Total Corpuses"),
                rx.stat_number(CorpusState.total_count),
            ),
            rx.stat(
                rx.stat_label("Active"),
                rx.stat_number(CorpusState.active_count),
                rx.stat_help_text("✅", color="green"),
            ),
            rx.stat(
                rx.stat_label("Need Rebuild"),
                rx.stat_number(CorpusState.rebuild_count),
                rx.stat_help_text("⚠️", color="yellow"),
            ),
        ),
        
        # Corpus table
        rx.data_table(
            data=CorpusState.corpuses,
            columns=["name", "display_name", "chunks", "status"],
            actions=[
                ("Rebuild", CorpusState.rebuild_corpus),
                ("Deactivate", CorpusState.deactivate_corpus),
            ]
        ),
        
        # Add new corpus form
        rx.accordion(
            rx.accordion_item(
                rx.accordion_button("➕ Add New Corpus"),
                rx.accordion_panel(
                    rx.form(
                        rx.input(placeholder="Corpus name", name="name"),
                        rx.input(placeholder="Display name", name="display_name"),
                        rx.text_area(placeholder="Description", name="description"),
                        rx.upload(accept=[".txt", ".pdf"], name="source_file"),
                        rx.button("Add Corpus", type="submit"),
                        on_submit=CorpusState.add_corpus,
                    )
                ),
            ),
        ),
    )
```

#### 3.4 Implementation Timeline

- **Not required for MVP** - Main app works without admin panel
- **Estimated: 1 week** after Phases 1 & 2 are stable
- **Benefits:**
  - No command-line corpus management
  - Visual corpus health monitoring
  - Easy persona editing with color picker
  - User analytics dashboard

---

## 🛠️ Development Workflow

### Setting Up the New App

```bash
# 1. Create backend virtual environment
cd storyteller_backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Copy .env file
cp ../.env .env

# 3. Run backend (Phase 1)
python -m uvicorn api.main:app --reload

# 4. Setup frontend (Phase 2)
cd ../storyteller_frontend
npm install
npm run dev

# 5. Access application
# Backend API docs: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

### Testing Strategy

```bash
# Backend tests
cd storyteller_backend
pytest tests/ -v --cov=api --cov=services

# Frontend tests
cd storyteller_frontend
npm test

# Integration tests
npm run test:integration
```

### Migration Strategy

1. **Parallel Development:** Build new app while old app runs
2. **Gradual Feature Parity:** Implement one feature at a time
3. **Side-by-Side Testing:** Run both apps, compare outputs
4. **Cutover Plan:** Switch to new app when feature parity reached
5. **Deprecation:** Keep old app for 1 month as backup

---

## 🎯 Success Metrics

### Phase 1 Complete When:
- [ ] Backend runs independently
- [ ] All endpoints return correct responses
- [ ] Configuration via .env (no hard-coded values)
- [ ] Services have >80% test coverage
- [ ] API documentation complete

### Phase 2 Complete When:
- [ ] Frontend connects to new backend
- [ ] All features from old app working
- [ ] Graph viewport issue fixed
- [ ] No code duplication in dropdowns
- [ ] Error boundaries catch and display errors
- [ ] Can swap graph views via config

### Phase 3 Complete When:
- [ ] Admin panel deployed
- [ ] Can manage corpuses via GUI
- [ ] Can edit personas via GUI
- [ ] Analytics dashboard functional

---

## 📊 Comparison: Old vs New

| Aspect | Old App | New App |
|--------|---------|---------|
| Backend Structure | Monolithic server.py (270 lines) | Modular routes + services |
| Frontend Size | 834-line component | 20+ components < 50 lines each |
| Configuration | Hard-coded | Environment variables |
| State Management | 15+ useState hooks | Context + custom hooks |
| Dropdown Code | 662 lines (4 components) | ~200 lines (1 base + 4 wrappers) |
| Error Handling | Console logs only | User-facing messages + boundaries |
| Testing | None | Unit + integration tests |
| Graph Views | ReactFlow only | Swappable (ReactFlow/Cytoscape/D3) |
| Admin Interface | Command line only | GUI (Reflex - Phase 3) |
| Maintainability | Difficult | Easy |

---

## 🌐 Deployment & Authentication Strategy

### Deployment Architecture Decision

**Our architecture supports multiple deployment models:**

```
┌─────────────────────────────────────────────────────────┐
│              FLEXIBLE DEPLOYMENT OPTIONS                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✅ Current Focus: Self-Hosted (Phase 1)               │
│  ┌──────────┐         ┌──────────┐                     │
│  │ Frontend │ ◄─────► │ Backend  │                     │
│  │ (Local)  │         │ (Local)  │                     │
│  └──────────┘         └─────┬────┘                     │
│                             │                           │
│                             ├──► User's .env (API key)  │
│                             └──► User's data/           │
│                                                         │
│  🔮 Future: Hosted Backend (Phase 2+)                  │
│  ┌──────────┐         ┌──────────┐                     │
│  │ Frontend │ ◄─────► │ Backend  │                     │
│  │ (Local)  │         │ (Cloud)  │                     │
│  └──────────┘         └──────────┘                     │
│     Users configure: VITE_API_BASE_URL=your-domain.com │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Architectural Benefits

**1. Frontend/Backend Separation**
- Frontend can connect to ANY backend (local or deployed)
- Configuration via environment variables
- No code changes needed to switch deployment models

```typescript
// Frontend configuration (Vite)
// .env.local
VITE_API_BASE_URL=http://localhost:8000    # Development
VITE_API_BASE_URL=https://api.your-domain  # Production

// All API calls automatically use configured URL
const response = await fetch(`${API_BASE_URL}/api/story`)
```

**2. Clear API Contracts**
- FastAPI with OpenAPI documentation at `/docs`
- Pydantic models ensure type safety
- Easy to version and evolve

**3. Multiple Deployment Paths**

| Model | Users | Backend | Frontend | Use Case |
|-------|-------|---------|----------|----------|
| **Self-Hosted** ✅ | Technical users | Run locally | Run locally | Phase 1 (Current) |
| **Hybrid** | Anyone | Cloud (optional) | Local or web | Phase 2+ (Future) |
| **Full SaaS** | Anyone | Cloud (you manage) | Web app | Phase 3+ (Optional) |

### Authentication Strategy

**Phase 1 (Current): Self-Hosted Mode**

```python
# storyteller_backend/config/settings.py
class Settings(BaseSettings):
    # Users set their own API key in .env
    openai_api_key: str  # Required in .env file
    
    # Authentication mode (for future expansion)
    auth_mode: str = "self_hosted"  # Options: self_hosted, per_request_key, credit_system
```

**User setup:**
```bash
# User creates their own .env file
echo "OPENAI_API_KEY=sk-user-key-here" > .env

# Their key never leaves their machine
# Maximum security and control
```

**Pros of Self-Hosted Auth:**
- ✅ User maintains full control of API key
- ✅ Key never transmitted over network
- ✅ No trust required in external backend
- ✅ No billing/payment infrastructure needed
- ✅ Simplest to implement (Phase 1)

**Cons:**
- ❌ Requires technical users
- ❌ Users must manage their own OpenAI account

---

### Future Authentication Options (Supported by Architecture)

Our service layer design with dependency injection supports adding ANY authentication model later without refactoring:

```python
# storyteller_backend/services/auth_service.py
class AuthService:
    """
    Handles different authentication modes.
    Easy to extend without changing business logic!
    """
    def get_openai_client(
        self,
        user_provided_key: Optional[str] = None
    ) -> AsyncOpenAI:
        if settings.auth_mode == "self_hosted":
            # Phase 1: Use key from .env
            return AsyncOpenAI(api_key=settings.openai_api_key)
        
        elif settings.auth_mode == "per_request_key":
            # Phase 2+: User sends key in header
            if not user_provided_key:
                raise HTTPException(401, "X-OpenAI-Key header required")
            return AsyncOpenAI(api_key=user_provided_key)
        
        elif settings.auth_mode == "credit_system":
            # Phase 3+: Platform manages key, users buy credits
            return AsyncOpenAI(api_key=settings.platform_openai_key)
```

**Phase 2 Option: Per-Request Key**
- User sends API key in HTTP header with each request
- Backend never stores keys (stateless)
- Works with deployed backend
- User still controls their own OpenAI account

**Phase 3 Option: Credit/Token System (SaaS)**
- Users buy credits from you
- You manage OpenAI relationship
- Best UX (no OpenAI account needed)
- Requires payment infrastructure (Stripe)

---

### Why This Architecture Works

**1. Clean Service Layer**
```python
# Business logic doesn't care about auth details
class StoryAgent:
    def __init__(self, openai_client: AsyncOpenAI):  # Injected!
        self.client = openai_client
    
    async def generate_story(self, prompt: str):
        # Works regardless of how client was created
        response = await self.client.chat.completions.create(...)
```

**2. Environment-Based Configuration**
```python
# Easy to switch modes without code changes
AUTH_MODE=self_hosted        # Phase 1
AUTH_MODE=per_request_key    # Phase 2
AUTH_MODE=credit_system      # Phase 3
```

**3. CORS Configuration**
```python
# Backend accepts connections from anywhere
cors_origins: list[str] = [
    "http://localhost:3000",          # Local dev
    "http://localhost:*",              # Any local port
    "https://app.yourdomain.com",     # Future hosted frontend
]
```

---

### Migration Path

```
Phase 1 (Now - Week 1-2):
├─ Implement self_hosted auth mode
├─ Users run everything locally
├─ Focus: Clean architecture & modularity
└─ Goal: Feature parity with current app

Phase 2 (Future - If deploying):
├─ Deploy backend to cloud
├─ Add per_request_key auth mode (optional)
├─ Update CORS for production domain
└─ Goal: Share with non-technical users

Phase 3 (Future - If monetizing):
├─ Implement credit_system auth mode
├─ Add user authentication (JWT)
├─ Integrate payment system (Stripe)
└─ Goal: SaaS business model
```

---

### Implementation Decisions for Phase 1

**✅ Confirmed Decisions:**

1. **Deployment:** Self-hosted (local backend + local frontend)
2. **Authentication:** Self-hosted mode (user's .env file)
3. **Target Users:** Technical users comfortable with Python/terminals
4. **API Design:** Clean contracts that support future expansion
5. **Service Layer:** Dependency injection allows swapping auth later

**🔮 Deferred Decisions:**

1. Cloud deployment strategy (Docker, AWS, etc.)
2. Per-request authentication implementation
3. Credit/billing system design
4. Multi-tenancy and user management
5. Frontend build tool (Vite vs Next.js) - leaning toward Vite

**📝 Documentation Requirements:**

1. Clear setup instructions for self-hosted mode
2. `.env.example` file with all required variables
3. OpenAPI docs at `/docs` endpoint
4. README with architecture overview

---

## 🚀 Getting Started

**Immediate Next Steps:**

1. ✅ Review deployment & authentication strategy (completed)
2. ✅ Approve Phase 1 architecture (self-hosted focus)
3. ✅ Decide on project structure (Option A: Independent projects)
4. Create `storyteller_backend/` directory structure
5. Begin backend migration following Phase 1 tasks
6. Iterate and refine as we build

**Resolved Questions:**

1. ✅ **Deployment:** Start with self-hosted, architecture supports future cloud deployment
2. ✅ **Authentication:** Self-hosted mode (user's OpenAI key in .env), extensible to other modes
3. ✅ **Project Structure:** Option A - Independent projects (`storyteller_backend/`, `storyteller_frontend/`)
4. ✅ **Frontend tool:** Vite (faster, simpler than Next.js, better for deployment)
5. **Graph libraries:** ReactFlow initially, design supports adding Cytoscape/D3 later
6. **Timeline:** No specific constraints, focus on quality and maintainability

---

## 📂 Current Project Structure

```
storyteller/
├── data/                           # Data storage
│   ├── corpus_registry.json       # Corpus metadata
│   ├── processed_chunks/          # Chunked text files (6 corpuses)
│   ├── bm25_indexes/              # BM25 keyword indexes (6 corpuses)
│   └── chroma_db/                 # Vector embeddings (6 corpuses)
├── raw_texts/                      # Source text files
├── saved_graphs/                   # User journey storage
│   ├── mehrab/
│   ├── mike/
│   └── {username}/
├── src/
│   ├── agent/                      # Story generation (Python)
│   │   ├── graph.py               # LangGraph agent (508 lines)
│   │   ├── server.py              # FastAPI server (270 lines)
│   │   ├── state.py               # State management
│   │   ├── config.py              # Agent configuration
│   │   └── personas.json          # Persona definitions
│   ├── embed_retrieve/             # Corpus management (Python)
│   │   ├── corpus_registry.py     # Corpus registry system
│   │   ├── retriever.py           # Hybrid retrieval
│   │   ├── batch_ingest.py        # Batch ingestion
│   │   ├── build_database.py      # Database builder
│   │   ├── preprocess_multi_files.py
│   │   ├── manage_corpuses.py
│   │   ├── jobs.yaml              # Corpus configurations
│   │   └── config.py              # Retrieval configuration
│   ├── app/                        # Frontend (Next.js) - TO BE REPLACED
│   │   ├── app/
│   │   │   ├── page.tsx           # Main component (834 lines) 🔴
│   │   │   ├── layout.tsx
│   │   │   ├── globals.css
│   │   │   └── components/
│   │   │       ├── UsernameDropdown.tsx (191 lines)
│   │   │       ├── PersonaDropdown.tsx (105 lines)
│   │   │       ├── JourneyDropdown.tsx (206 lines)
│   │   │       └── CorpusDropdown.tsx (160 lines)
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── schemas/
│       └── schemas.py             # Pydantic models
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
├── .env.example                    # Environment template
└── documentation/
    ├── MANUAL_SETUP.md
    ├── next_steps.md (this file)
    └── cursor_chats/
        └── cursor_chat_7.md       # Current refactoring discussion
```

## 📝 Notes

- **Legacy App:** Current frontend (`src/app/`) will be retained as reference during refactoring
- **No Breaking Changes Yet:** All current functionality remains intact
- **Next Planning Session:** Will define detailed architecture for `storyteller_app/`
- **Team Skills:** Python-first, minimal JavaScript maintenance required

---

## 📚 Key Technologies

### Backend
- **Python 3.11+**
- **LangGraph** - Agent orchestration
- **LangChain** - LLM integrations
- **FastAPI** - API framework
- **ChromaDB** - Vector database
- **NetworkX** - Graph data structure
- **OpenAI API** - GPT-4o-mini, DALL-E 3
- **SSE (Server-Sent Events)** - Streaming

### Frontend (Current)
- **Next.js 15.3.4** - React framework
- **React 19** - UI library
- **ReactFlow 11.11.4** - Graph visualization
- **ELK.js 0.10.0** - Graph layout
- **Tailwind CSS** - Styling
- **TypeScript 5** - Type safety

### Data
- **ChromaDB** - Vector search (text-embedding-3-small)
- **BM25** - Keyword search
- **Reciprocal Rank Fusion** - Hybrid ranking
- **Azure Blob Storage** - Image hosting

---

## ✨ Highlights & Achievements

### Phase 1 (COMPLETE):
1. ✅ **Modular Backend Architecture:** Clean separation of concerns with config, models, services, and API layers
2. ✅ **11 API Endpoints:** Full CRUD for admin panel + story generation + journey management
3. ✅ **Type-Safe Configuration:** Pydantic models with strict secret separation
4. ✅ **Comprehensive Testing:** 10 tests covering all core functionality
5. ✅ **Production-Ready:** Independent project, cloud deployment ready
6. ✅ **Full CRUD Support:** Admin panel can manage personas and corpuses via API

### Original Features (Maintained):
1. **Fully Functional Story Generation:** Users can generate branching narratives from 6 different corpuses
2. **Persona System:** 5 distinct storyteller personalities
3. **Image Generation:** DALL-E images for visual storytelling
4. **Multi-User Support:** User-specific journeys and preferences
5. **Corpus Flexibility:** Easy to add new text corpuses
6. **Streaming UX:** Real-time story generation via SSE
7. **Graph Persistence:** Users can save and reload story journeys
8. **Hybrid Retrieval:** Combines semantic and keyword search effectively

---

## 📚 Quick Reference

### Important Files:
- **Backend Entry:** `storyteller_backend/api/main.py`
- **Tests:** `storyteller_backend/test_setup.py`
- **Configuration:** `storyteller_backend/config/settings.py`
- **Secrets:** `storyteller_backend/.env` (not in git)
- **Session Docs:** `documentation/cursor_chats/cursor_chat_8.md`

### Commands:
```bash
# Test backend
cd storyteller_backend
source .venv_bk/bin/activate
python test_setup.py

# Run backend server
python -m uvicorn api.main:app --reload

# API Documentation
open http://localhost:8000/docs
```

### API Endpoints:
- Stories: `GET /api/stream_story` (SSE)
- Personas: `GET/POST/PUT/DELETE /api/personas`
- Corpuses: `GET/POST/PUT/DELETE /api/corpuses`
- Journeys: `GET /api/list_graphs`, `POST /api/load_graph`, `GET /api/get_loaded_graph`

### Project Structure:
```
storyteller/
├── storyteller_backend/     # ✅ Phase 1 COMPLETE
│   ├── api/                 # FastAPI routes
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   ├── embed_retrieve/      # Corpus management
│   └── config/              # Settings
├── storyteller_frontend/    # 🚧 Phase 2 (TODO)
├── data/                    # Shared corpus data
├── saved_graphs/            # User journeys
└── src/                     # Old implementation (reference only)
```

---

**Last Updated:** November 23, 2025 - Phase 1 Complete, Phase 2 Ready to Begin
