# Row Mode — Design Spec

**Date:** 2026-03-22
**Branch:** FE-rebuild
**Status:** Draft

---

## Overview

Add a "Row Mode" alongside the existing "Tree Mode" for visualising the story graph. Row Mode shows a single horizontal row of story nodes at a user-selected depth level (leaf, leaf-1, leaf-2, etc.). The centered story node is rendered at full size and opacity; surrounding nodes scale down and fade based on their graph distance from the center. Each visible story node's choice nodes are rendered directly below it.

---

## Terminology

| Term | Definition |
|---|---|
| **Story-hop** | One edge in the story-only graph (ignoring choice nodes as intermediaries). S1→S2 via a choice node = 1 story-hop. |
| **Leaf-k row** | The set of story nodes that have at least one leaf exactly k story-hops below them. k=0 is the leaf row itself. A node can appear in multiple rows if it has leaves at different depths. |
| **Centered node** | The story node closest to the horizontal centre of the ReactFlow viewport. Determined dynamically by scroll position. |
| **Graph distance** | Shortest undirected path between two story nodes, counting story-hops only. |

---

## Row Membership Rules

Given the story-only subgraph (story nodes connected by directed parent→child edges, skipping choice intermediaries):

1. For each story node, compute the set of distances to all reachable leaf descendants.
2. A node is in the **leaf-k** row if `k` is in its distance set.
3. A node with leaves at multiple depths appears in multiple rows (e.g. if S1→S3 is 1 hop and S1→S2→S4 is 2 hops, S1 is in both leaf-1 and leaf-2).
4. A pure leaf node (k=0) does NOT appear in any leaf-k row where k>0.

**Example:**
```
S1 → S2 → S4 (leaf)
       → S5 (leaf)
  → S3 (leaf)

Leaf (k=0): S3, S4, S5
Leaf-1 (k=1): S2 (1 hop from S4/S5), S1 (1 hop from S3)
Leaf-2 (k=2): S1 (2 hops from S4/S5 via S2)
```

---

## Layout Within a Row

### Horizontal ordering

Nodes in a row are ordered by **DFS traversal order** from the root of the story graph. DFS naturally places siblings adjacent and preserves tree topology. No gaps between nodes.

### Fixed positions

All story nodes sit at a fixed y-coordinate (`STORY_Y`). Their x-coordinates are assigned sequentially: `x = index * SPACING`. SPACING is a constant (tunable) based on the maximum story node width plus a comfortable gap.

Choice nodes for a given story node are positioned at a fixed y-offset below their parent (`CHOICE_Y = STORY_Y + storyNodeHeight + choiceGap`). Choice nodes fan out horizontally below their parent, centered on the parent's x.

### Which choice nodes are rendered

Only the choice nodes belonging to the **centered node** and its **immediate left and right neighbours** in the row are included in the ReactFlow nodes array. All other choice nodes are omitted entirely (not hidden — not rendered). This means up to 3 × 3 = 9 choice nodes maximum.

### Edges

- **Story-to-choice edges** are rendered (for the 3 story nodes whose choices are visible).
- **Story-to-story edges** are NOT rendered in row mode.
- Edge styling matches the existing `defaultEdgeOptions` (smoothstep, same colour/width).

---

## Scale and Opacity

Each story node's visual size and opacity depend on its **graph distance** from the currently centered node:

```
scale(dist) = 1 / (1 + 0.3 * dist)
opacity(dist) = 1 / (1 + 0.4 * dist)
```

These are applied as inline CSS on the node wrapper:
```css
transform: scale(<computed>);
opacity: <computed>;
transition: transform 0.3s ease, opacity 0.3s ease;
```

The constants (0.3, 0.4) are tunable and defined in `graph.config.ts`.

Choice nodes inherit their parent story node's scale and opacity.

The centered node (dist=0) is always scale=1, opacity=1.

---

## Center Detection

Uses ReactFlow's `onMove` callback to read the viewport state `{ x, y, zoom }` on every pan:

1. Compute the flow-coordinate x of the viewport centre: `centerX = (-viewport.x + containerWidth / 2) / viewport.zoom`
2. Find the story node in the current row whose x-position is closest to `centerX`.
3. If the centered node ID has changed, recompute `distanceFromCenter` for all row nodes using precomputed pairwise graph distances.
4. Update each node's `data.distanceFromCenter` — this triggers the scale/opacity CSS transitions.

---

## Depth Navigation

**Up/Down arrow buttons** are rendered on the left side of the graph area, visible only in Row Mode:

- **▲** increments `rowDepth` (moving toward root). Disabled when `rowDepth === maxDepth`.
- **▼** decrements `rowDepth` (moving toward leaves). Disabled when `rowDepth === 0`.
- **Label** between the arrows shows the current level: "LEAF", "LEAF-1", "LEAF-2", etc.

`maxDepth` is the largest k for which any node exists in the leaf-k row.

When depth changes, the row is recomputed and the viewport snaps to center the most recently generated story node (if it exists in the new row), or the first node in the row.

---

## Mode Toggle

A button in the app controls area (next to the dropdowns, near "Graph Visualization" heading). Two states:

- **Tree** (default): existing ELK layout, full graph.
- **Row**: row layout as described here.

Switching tree→row: defaults to `rowDepth = 0` (leaf level), centers on the most recently generated story node.

Switching row→tree: restores the full ELK tree layout. No viewport state is preserved across mode switches.

---

## ReactFlow Configuration (Row Mode)

| Setting | Value | Reason |
|---|---|---|
| `translateExtent` | `[[-Infinity, STORY_Y - 100], [Infinity, CHOICE_Y + choiceHeight + 100]]` | Lock vertical panning; only horizontal movement. |
| `zoomOnScroll` | `false` | Scale is handled by distance falloff, not ReactFlow zoom. |
| `zoomOnPinch` | `false` | Same. |
| `panOnScroll` | `true` | Scroll wheel pans horizontally (natural scrolling feel). |
| `panOnScrollMode` | `PanOnScrollMode.Horizontal` | Restrict to horizontal. |
| `fitView` | `false` | We control centering manually. |
| `minZoom` / `maxZoom` | `1` / `1` | Fixed zoom level. |
| `MiniMap` | Hidden | Not useful for a single row. |

---

## New Files

### `src/utils/rowLayoutEngine.ts`

Pure functions, no React dependencies. Fully unit-testable.

```ts
// Types
interface StoryAdjacency {
  children: Map<string, string[]>;  // parentId → childIds (story-only)
  parents: Map<string, string>;     // childId → parentId
  roots: string[];                  // nodes with no story-parent
}

interface RowLayoutResult {
  orderedNodeIds: string[];
  distances: Map<string, Map<string, number>>;
  maxDepth: number;
}

// Functions
buildStoryGraph(nodes, edges): StoryAdjacency
computeLeafDistances(graph: StoryAdjacency): Map<string, Set<number>>
getRowNodes(leafDistances, k): string[]
topologicalOrder(rowNodeIds, graph: StoryAdjacency): string[]
computeGraphDistances(rowNodeIds, graph: StoryAdjacency): Map<string, Map<string, number>>
computeRowLayout(allNodes, allEdges, rowDepth): RowLayoutResult
```

### `src/hooks/useRowLayout.ts`

React hook wrapping the engine.

```ts
interface UseRowLayoutResult {
  nodes: StoryReactFlowNode[];
  edges: StoryReactFlowEdge[];
  maxDepth: number;
  centeredNodeId: string | null;
}

function useRowLayout(
  graph: TransformedGraph | null,
  rowDepth: number,
): UseRowLayoutResult
```

Internally:
- Calls `computeRowLayout` on graph/rowDepth change.
- Assigns fixed (x, y) positions to story and choice nodes.
- Listens to ReactFlow `onMove` for center detection.
- Computes `distanceFromCenter` for each node and injects it into `node.data`.
- Filters choice nodes to center ± 1 story nodes only.

---

## Changes to Existing Files

### `src/types/graph.types.ts`
- Add optional `distanceFromCenter?: number` to `ReactFlowNodeData`.

### `src/config/graph.config.ts`
- Add `rowMode` section:
  ```ts
  rowMode: {
    storyY: 100,
    choiceGap: 40,
    spacing: 400,          // horizontal distance between story node centers
    scaleFalloff: 0.3,
    opacityFalloff: 0.4,
  }
  ```

### `src/components/graph/StoryNode.tsx`
- When `data.distanceFromCenter` is defined, wrap the outer `<div>` with inline `transform` and `opacity` styles. No changes when undefined (tree mode).

### `src/components/graph/ChoiceNode.tsx`
- Same treatment as StoryNode.

### `src/components/graph/GraphView.tsx`
- Accept `mode: 'tree' | 'row'` and `rowDepth: number` props.
- In `GraphCanvasInner`: if mode is `'row'`, use `useRowLayout` instead of the ELK-computed nodes/edges. Apply row-mode ReactFlow config (locked vertical pan, no zoom, horizontal scroll).
- Conditionally render depth arrows (▲/▼) and depth label overlay when in row mode.
- Hide MiniMap when in row mode.

### `src/App.tsx`
- Add `mode` state (`'tree' | 'row'`, default `'tree'`).
- Add `rowDepth` state (`number`, default `0`).
- Render mode toggle button near the "Graph Visualization" heading.
- Pass `mode`, `rowDepth`, and depth change handlers to `GraphView`.
- In row mode, still pass `layoutGraph` (ELK output) as `graph` — `GraphView` will use it to feed `useRowLayout` with the transformed nodes/edges.

---

## Interaction Behaviour

| Action | Behaviour |
|---|---|
| Horizontal pan / scroll | Smoothly shifts the row; centered node updates dynamically. Scale/opacity animate via CSS transitions. |
| Click a story node | Opens the reading panel (same as tree mode). |
| Click a choice node | Selects it for editing/submission (same as tree mode). |
| Submit a choice | Triggers story generation. New story node appears in the leaf row. If currently viewing a non-leaf row, the new node won't appear until the user navigates down. |
| Press ▲ | Increment rowDepth. Row recomputes. Center snaps to most recent node in new row (or first node). |
| Press ▼ | Decrement rowDepth. Same centering logic. |
| Toggle Tree ↔ Row | Full layout swap. Row defaults to leaf row. Tree restores ELK layout. |

---

## Testing

- **Unit tests** for `rowLayoutEngine.ts`: row membership, topological ordering, graph distance computation. Use the S1/S2/S3/S4/S5 example tree from the design discussion.
- **Integration test**: verify `useRowLayout` produces correct node positions and updates `distanceFromCenter` on simulated viewport changes.
- **Behaviour tests** (Playwright): add to `app-behaviours.md`:
  - Toggle to Row Mode → verify horizontal row of leaf nodes.
  - Press ▲ → verify depth label changes and correct nodes appear.
  - Scroll horizontally → verify centered node scales up, neighbours scale down.
  - Click a choice node in Row Mode → verify story generation works.
  - Toggle back to Tree Mode → verify full tree is restored.

---

## Out of Scope

- Animated transitions between Tree and Row mode (future enhancement).
- Vertical Row Mode / different orientations.
- Persisting mode preference across sessions.
- Backend changes — this is purely a frontend feature.
