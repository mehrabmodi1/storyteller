# Frontend Documentation

Engineering reference for the Storyteller frontend — a React 18 + TypeScript SPA that visualises branching story graphs and streams narrative content via SSE.

---

## Architecture Overview

```
App.tsx (state + handlers)
├── AppContext (username, persona, corpus, theme)
├── Dropdowns (username, persona, corpus, journey)
├── useSSE (streaming connection)
├── GraphView (ReactFlow canvas)
│   ├── Tree mode → useELKLayout (hierarchical)
│   └── Row mode  → useRowLayout (horizontal scroll)
└── api.ts (all backend calls)
```

Single-page app. All state lives in `App.tsx` (local) and `AppContext` (global). The graph is received from the backend as `{nodes, links}` JSON, transformed to ReactFlow format, then laid out by either ELK (tree) or a custom row engine.

---

## Directory Structure

```
storyteller_frontend/
├── src/
│   ├── App.tsx                     # Main component — all state + handlers
│   ├── main.tsx                    # React entry point
│   ├── context/
│   │   └── AppContext.tsx          # Global state provider (username, persona, corpus, theme)
│   ├── services/
│   │   ├── api.ts                  # All backend API calls
│   │   └── api.config.ts           # Endpoint URLs + URL builder
│   ├── hooks/
│   │   ├── useSSE.ts              # Server-Sent Events connection
│   │   ├── useELKLayout.ts        # ELK hierarchical layout
│   │   ├── useRowLayout.ts        # Horizontal row layout
│   │   └── useLocalStorage.ts     # localStorage-backed state
│   ├── components/
│   │   ├── graph/
│   │   │   ├── GraphView.tsx      # ReactFlow canvas + mode switching
│   │   │   ├── StoryNode.tsx      # Story chapter card (text + image)
│   │   │   └── ChoiceNode.tsx     # Choice prompt card (editable)
│   │   ├── dropdowns/
│   │   │   ├── BaseDropdown.tsx   # Generic dropdown (keyboard nav, tooltips)
│   │   │   ├── PersonaDropdown.tsx
│   │   │   ├── CorpusDropdown.tsx
│   │   │   ├── JourneyDropdown.tsx
│   │   │   └── UsernameDropdown.tsx
│   │   ├── debug/
│   │   │   └── GraphDebugPanel.tsx # Raw JSON inspector
│   │   ├── ReadingPanel.tsx       # Story text overlay
│   │   ├── ParagraphCountSlider.tsx
│   │   └── ErrorBoundary.tsx      # React error boundary
│   ├── types/
│   │   ├── graph.types.ts         # GraphNode, GraphEdge, GraphData, ReactFlow types
│   │   └── api.types.ts           # CorpusInfo, PersonaInfo, JourneyMeta, etc.
│   ├── utils/
│   │   ├── graphTransform.ts      # Backend graph → ReactFlow nodes/edges
│   │   ├── elkConfig.ts           # ReactFlow → ELK graph builder
│   │   ├── rowLayoutEngine.ts     # Row mode layout computation
│   │   └── themeUtils.ts          # Theme ring class helper
│   ├── config/
│   │   └── graph.config.ts        # Node dimensions, edge style, row mode constants
│   └── styles/
│       └── globals.css            # Tailwind base styles
├── package.json                   # React 18.3.1, Vite 6.0.1, ReactFlow 11.11.4
├── vite.config.ts                 # Port 3000, /api proxy → localhost:8000
├── tailwind.config.js             # Persona color safelist
└── tsconfig.json                  # Strict mode, @/* path alias
```

---

## Configuration

### `vite.config.ts`

- **Dev server port:** 3000
- **API proxy:** `/api/*` → `http://localhost:8000` (avoids CORS in development)
- **Path alias:** `@` → `./src/`
- **Test environment:** jsdom (vitest)

### `config/graph.config.ts`

```typescript
GRAPH_VISUAL_CONFIG = {
  storyNode:  { width: 320, height: 520 },
  choiceNode: { width: 260, height: 160 },
  edge:       { color: '#94a3b8', width: 1.5, animated: false },
  rowMode: {
    storyY: 100,              // fixed Y position for story row
    choiceGap: 40,            // gap between story and choices
    spacing: 400,             // horizontal spacing between stories
    scaleFalloff: 0.3,        // scale reduction per position from center
    opacityFalloff: 0.4,      // opacity reduction per position from center
    visibleStoryNodes: 5,     // stories visible in window (center +/- 2)
    visibleChoiceDepth: 0,    // show choices for center node only
  },
}
```

### `services/api.config.ts`

```typescript
API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  endpoints: {
    streamStory:    '/api/stream_story',
    personas:       '/api/personas',
    corpuses:       '/api/corpuses',
    listUsers:      '/api/list_users',
    listGraphs:     '/api/list_graphs',
    loadGraph:      '/api/load_graph',
    getLoadedGraph: '/api/get_loaded_graph',
    health:         '/health',
  },
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |

---

## State Management

### `context/AppContext.tsx` — Global State

Provides shared state to all components via React Context.

```typescript
interface AppContextType {
  username: string;          // persisted to localStorage
  setUsername: (v) => void;
  corpus: string;            // persisted to localStorage
  setCorpus: (v) => void;
  persona: string;           // session only (not persisted)
  setPersona: (v) => void;
  personas: PersonaInfo[];   // fetched from backend on mount
  personasLoading: boolean;
  personasError: string | null;
  theme: ColorTheme | null;  // derived from selected persona
}
```

**Default theme** (when no persona selected):
```typescript
{ background: 'bg-gray-900', button: 'bg-blue-600',
  button_hover: 'hover:bg-blue-500', input: 'bg-gray-800',
  ring: 'focus:ring-blue-500' }
```

### `App.tsx` — Local State

All story/graph state lives in `AppContent`:

| State | Type | Purpose |
|-------|------|---------|
| `rawGraph` | `GraphData \| null` | Latest graph from backend |
| `journeyPersona` | `string \| null` | Persona from loaded journey |
| `promptInput` | `string` | New journey text input |
| `streamUrl` | `string \| null` | SSE URL (triggers connection) |
| `showDebug` | `boolean` | Debug panel toggle |
| `showReadingPanel` | `boolean` | Story reading overlay |
| `currentStoryTitle` | `string` | Title for reading panel |
| `activeChoice` | `{id, prompt} \| null` | Currently editing choice |
| `journeyError` | `string \| null` | Error banner text |
| `viewingStoryText` | `string \| null` | Full story text for reading |
| `currentGraphId` | `string \| null` | Active journey ID |
| `paragraphCount` | `number` | Story length (1-8) |
| `graphMode` | `'tree' \| 'row'` | Visualization mode |
| `rowDepth` | `number` | Current depth in row mode |

**Key handlers:**
- `handleStartNewJourney()` — Builds SSE URL, creates placeholder node, initiates stream
- `handleSelectChoice(nodeId)` — Opens choice edit panel; if explored, navigates to child story
- `handleSelectStoryNode(nodeId)` — Opens reading panel with story text
- `handleSubmitContinuation(textOverride)` — Continues story from a choice node via SSE
- `handleToggleMode()` — Switches between tree and row visualization

---

## Hooks

### `useSSE(url: string | null)`

Manages the EventSource connection for streaming story generation.

```typescript
interface UseSSEResult {
  streamingText: string;          // accumulated story tokens
  graphData: GraphData | null;    // final graph after generation
  isStreaming: boolean;
  error: Error | null;
  guardrailMessage: string | null;
  closeStream: () => void;
}
```

**SSE event handling:**

| Event | Action |
|-------|--------|
| `story_chunk` | Append token to `streamingText` |
| `message` / `graph_data` | Parse JSON, set `graphData` |
| `guardrail_reject` | Set message, close connection |
| `end` | Close connection, set `isStreaming = false` |
| `error` | Set error state, close connection |

When `url` is null, the hook is inactive. Setting a new URL opens a new connection and resets state.

### `useELKLayout(graph: TransformedGraph | null)`

Computes hierarchical tree layout using ELK.js.

```typescript
interface Result {
  layout: { nodes, edges, latestStoryNodeId, latestStoryTimestamp } | null;
  isRunning: boolean;
}
```

**ELK options:** `layered` algorithm, `DOWN` direction, 120px between layers, 140px between nodes, balanced alignment. Applies CSS transitions on updates (0.4s ease). Cancels pending computations when input changes.

### `useRowLayout(graph, rowDepth, containerWidth, containerHeight)`

Computes horizontal row layout for a single depth level.

```typescript
interface UseRowLayoutResult {
  nodes: StoryReactFlowNode[];
  edges: StoryReactFlowEdge[];
  maxDepth: number;
  centeredNodeId: string | null;
  onViewportChange: (viewport) => void;
  centerOnNode: (nodeId) => void;
}
```

**Row mode behaviour:**
- Stories positioned horizontally at fixed Y; choices centered below their parent
- 5 visible story nodes centered on current (with scale + opacity falloff)
- Choices shown only for the centered story node
- Explored choices rendered with dashed borders + reduced opacity (0.35)
- Auto-centers on story click (300ms animation, 400ms detection suppression)
- Vertical zoom auto-fits content; horizontal pan for scrolling

### `useLocalStorage<T>(key, initialValue)`

Standard localStorage-backed `useState` replacement. Handles JSON parse/stringify, gracefully catches private browsing and quota errors.

---

## Components

### `graph/GraphView.tsx`

ReactFlow canvas wrapper. Handles mode switching between tree and row layouts.

**Props:**
```typescript
interface GraphCanvasProps {
  graph: TransformedGraph | null;
  onSelectChoice?: (nodeId: string) => void;
  onSelectStoryNode?: (nodeId: string) => void;
  activeChoiceId?: string | null;
  editablePrompt?: string;
  onChangePrompt?: (value: string) => void;
  onSubmitPrompt?: (text?: string) => void;
  onCancelEdit?: () => void;
  mode?: 'tree' | 'row';
  rowDepth?: number;
  onRowDepthChange?: (depth: number) => void;
}
```

**Tree mode:** MiniMap enabled, zoom 0.1-1.8x, fitView on layout changes.
**Row mode:** Horizontal pan only, zoomOnScroll/pinch disabled, zoom 0.3-1x, depth navigation buttons on left side.

Injects `choiceProps` into choice node data dynamically for edit state management. Uses `ResizeObserver` to track container dimensions for row layout.

### `graph/StoryNode.tsx`

Story chapter card: title, scrollable text, 1:1 image, timestamp, persona badge.

- **Dimensions:** 320w x 520h
- **Placeholder state:** Spinning loader + "Generating story..." (dashed border)
- **Selected state:** Ring highlight + shadow
- **Row mode:** Scale/opacity falloff based on `distanceFromCenter`

### `graph/ChoiceNode.tsx`

Choice prompt card: label text, optional edit mode.

- **Dimensions:** 260w x 160h (224h when editing)
- **Inactive:** Shows prompt text + "Press Enter to generate follow-up" hint
- **Active (editing):** Textarea + Cancel/Continue Journey buttons
- **Explored:** Dashed border + 0.35 opacity
- **Keyboard:** Enter = submit, Escape = cancel

### `dropdowns/BaseDropdown.tsx`

Generic reusable dropdown with:
- Click-outside to close
- Arrow key navigation, Enter to select, Escape to close
- Hover tooltips (positioned right with arrow)
- ARIA listbox roles
- Scrollable menu (max-h-60)

Used by all 4 dropdown components (PersonaDropdown, CorpusDropdown, JourneyDropdown, UsernameDropdown).

### `dropdowns/UsernameDropdown.tsx`

Merges backend `listUsers()` with localStorage usernames. "Add New" option opens inline text input. Saves new usernames to localStorage.

### `dropdowns/JourneyDropdown.tsx`

Fetches `listGraphs(username)` when username changes. On select, calls `loadGraph()`. Tooltip shows timestamp, persona, corpus, chapter count. Disabled if no username set.

### `dropdowns/CorpusDropdown.tsx`

Fetches `listCorpuses()` on mount, filters to `is_active: true`. Tooltip shows description + chunk count.

### `ReadingPanel.tsx`

Floating overlay showing streaming/complete story text. Status badge (Streaming/Complete). Manual scroll, close button.

### `ParagraphCountSlider.tsx`

Range input 1-8. Shows word target (200-1600). Disabled while streaming.

### `ErrorBoundary.tsx`

Class component. Shows error details + expandable stack trace. Reload/Go Home buttons.

---

## Utilities

### `utils/graphTransform.ts`

```typescript
transformGraphData(graph: GraphData, options?: TransformOptions): TransformedGraph
```

Converts raw backend `{nodes, links}` to ReactFlow format:
- Sets node dimensions from `GRAPH_VISUAL_CONFIG`
- Maps node types to custom components (`storyNode`, `choiceNode`)
- Resolves theme from node data or options
- Finds latest story node by timestamp
- Edges use `smoothstep` type

### `utils/elkConfig.ts`

```typescript
buildElkGraph(graph: TransformedGraph): ElkNode
```

Converts transformed graph to ELK input format with layout options (layered, DOWN direction, spacing, thoroughness).

### `utils/rowLayoutEngine.ts`

Core layout computation for row mode:

1. **buildStoryGraph()** — Extracts story-only adjacency (story → choice → story edges collapsed)
2. **computeLeafDistances()** — Hop-distance from each node to descendant leaves
3. **getRowNodes()** — Selects nodes at a specific leaf-distance (the "row")
4. **dfsOrder()** — DFS pre-order for consistent horizontal ordering
5. **computeRowLayout()** — Orchestrator returning `{orderedNodeIds, distances, maxDepth}`

---

## Type Definitions

### `types/graph.types.ts`

```typescript
type NodeType = 'story' | 'choice';

interface GraphNode {
  id: string; type: NodeType; label: string;
  story?: string; image_url?: string; timestamp?: string;
  persona?: string; theme?: ColorTheme; isPlaceholder?: boolean;
}

interface GraphEdge { source: string; target: string; }

interface GraphData {
  nodes: GraphNode[]; links: GraphEdge[];
  graph?: { graph_name?: string; [key: string]: unknown };
}

interface ReactFlowNodeData extends GraphNode {
  distanceFromCenter?: number;  // row mode
  isExplored?: boolean;         // row mode
}
```

### `types/api.types.ts`

```typescript
interface CorpusInfo {
  name: string; display_name: string; description: string;
  is_active: boolean; chunk_count: number; needs_rebuild: boolean;
  missing_components: string[];
}

interface PersonaInfo {
  name: string; short_description: string; color_theme: ColorTheme;
  system_prompt?: string; temperature?: number;
}

interface ColorTheme {
  background: string; button: string; button_hover: string;
  input: string; ring: string;
}

interface JourneyMeta {
  graph_id: string; username: string; timestamp: string;
  initial_prompt: string; last_prompt: string; persona: string;
  corpus_name: string; num_story_nodes: number;
}
```

---

## API Client (`services/api.ts`)

All backend communication goes through typed functions:

| Function | Method | Endpoint | Returns |
|----------|--------|----------|---------|
| `buildStreamStoryURL(params)` | — | `/api/stream_story?...` | URL string (for EventSource) |
| `listUsers()` | GET | `/api/list_users` | `string[]` |
| `listPersonas()` | GET | `/api/personas` | `PersonaInfo[]` |
| `createPersona(persona)` | POST | `/api/personas` | `PersonaInfo` |
| `updatePersona(name, data)` | PUT | `/api/personas/{name}` | `PersonaInfo` |
| `deletePersona(name)` | DELETE | `/api/personas/{name}` | `{success, message}` |
| `listCorpuses()` | GET | `/api/corpuses` | `CorpusInfo[]` |
| `createCorpus(data)` | POST | `/api/corpuses` | `{success, message}` |
| `updateCorpus(name, updates)` | PUT | `/api/corpuses/{name}` | `CorpusInfo` |
| `deleteCorpus(name)` | DELETE | `/api/corpuses/{name}` | `{success, message}` |
| `listGraphs(username)` | GET | `/api/list_graphs?username=` | `JourneyListResponse` |
| `loadGraph(request)` | POST | `/api/load_graph` | `LoadGraphResponse` |
| `getLoadedGraph()` | GET | `/api/get_loaded_graph` | `GetLoadedGraphResponse` |
| `healthCheck()` | GET | `/health` | `HealthResponse` |

Generic wrapper `apiFetch<T>(endpoint, options?)` handles headers and error responses.

---

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Vite dev server (port 3000, HMR) |
| `npm run build` | TypeScript check + Vite production build |
| `npm run preview` | Preview production build |
| `npm run lint` | ESLint |
| `npm run type-check` | TypeScript validation (no emit) |
| `npm run test` | Vitest (pass with no tests) |
| `npm run test:watch` | Vitest watch mode |

---

## Styling

**Tailwind CSS 3.4** with persona color safelist in `tailwind.config.js`. Each persona defines 5 Tailwind classes (background, button, button_hover, input, ring) that are applied dynamically via the `theme` object from AppContext.

The safelist ensures Tailwind doesn't purge persona-specific classes like `bg-amber-950`, `hover:bg-red-600`, etc., since they're only referenced at runtime.
