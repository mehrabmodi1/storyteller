# Storyteller Project: Current Status & Next Steps

**Last Updated:** November 22, 2025

---

## 📊 Current Implementation Status

### ✅ COMPLETED FEATURES

#### 1. **Backend - Story Generation Agent** (`src/agent/`)
- ✅ LangGraph-based story generation agent with 5-node pipeline:
  - `formulate_search_query`: Converts user prompts to search queries
  - `retrieve_from_corpus`: Hybrid retrieval (ChromaDB + BM25)
  - `generate_story`: Streaming story generation with GPT-4o-mini
  - `generate_choices`: Creates 3 follow-up prompts
  - `update_graph_with_choices`: Updates NetworkX graph structure
- ✅ Persona system with 5 storyteller personas (Grandmother, Scholar, Poet, Historian, Mystic)
  - Each persona has unique personality and color theme
  - Persona-specific prompting for story generation
- ✅ Image generation with DALL-E 3
  - Warm, impressionist-style sketches
  - Visual continuity across story nodes
  - Azure Blob Storage integration for image hosting
- ✅ Configurable story length (500-3000 tokens)
- ✅ Graph persistence (saved per user in `saved_graphs/`)
- ✅ Graph metadata tracking (initial prompt, timestamps, persona, corpus)

#### 2. **Backend - Multi-Corpus System** (`src/embed_retrieve/`)
- ✅ Corpus registry system (`corpus_registry.py`)
  - Centralized management of multiple text corpuses
  - Metadata tracking (display name, description, status, chunk count)
- ✅ Currently available corpuses (6 total):
  - The Mahabharata ✅
  - The Odyssey ✅
  - The Arabian Nights ✅
  - The Volsunga Saga ✅
  - The Jataka Tales ✅
  - Locus Platform Documentation ✅
- ✅ Hybrid retrieval system (ChromaDB + BM25) with Reciprocal Rank Fusion
- ✅ Isolated databases per corpus:
  - `data/chroma_db/{corpus_name}/` - Vector embeddings
  - `data/bm25_indexes/{corpus_name}_bm25.pkl` - Keyword index
  - `data/processed_chunks/{corpus_name}/` - Processed chunks
- ✅ Batch ingestion system (`batch_ingest.py`)
  - Smart recovery from partial failures
  - Status checking and validation
  - Force rebuild capability
- ✅ Multi-file corpus preprocessing (`preprocess_multi_files.py`)
- ✅ Jobs configuration via YAML (`jobs.yaml`)

#### 3. **Backend - FastAPI Server** (`src/agent/server.py`)
- ✅ RESTful API with 5 endpoints:
  - `GET /api/story` - Server-Sent Events (SSE) streaming
  - `GET /api/personas` - List available personas
  - `GET /api/corpuses` - List available corpuses with status
  - `GET /api/list_graphs` - List user's saved journeys
  - `POST /api/load_graph` - Load a saved journey
  - `POST /api/get_loaded_graph` - Get currently loaded graph
- ✅ SSE streaming for real-time story generation
- ✅ CORS configured for frontend communication
- ✅ In-memory graph state with async lock for concurrent requests
- ✅ Corpus validation (checks if corpus exists and is active)

#### 4. **Frontend - Next.js Application** (`src/app/`)
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

#### 5. **Data Infrastructure**
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

## 📋 IMPLEMENTATION PLAN: storyteller_app

### Phase 1: Backend Restructuring (Week 1)

**Goal:** Create a clean, standalone Python backend in `storyteller_app/backend/` with clear API contracts and modular architecture.

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

### Phase 2: Minimal React Frontend (Week 2)

**Goal:** Create a lightweight React app that ONLY handles graph visualization and delegates everything else to the backend.

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

1. **Fully Functional Story Generation:** Users can generate branching narratives from 6 different corpuses
2. **Persona System:** 5 distinct storyteller personalities with themed UI
3. **Image Generation:** DALL-E 3 images for visual storytelling
4. **Multi-User Support:** User-specific journeys and preferences
5. **Corpus Flexibility:** Easy to add new text corpuses
6. **Streaming UX:** Real-time story generation feels responsive
7. **Graph Persistence:** Users can save and reload story journeys
8. **Hybrid Retrieval:** Combines semantic and keyword search effectively

---

*This document will be updated with the new implementation plan once reviewed and approved.*
