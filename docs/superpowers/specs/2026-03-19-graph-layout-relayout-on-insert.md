# Graph Layout: Full Relayout with Smooth Transitions on Node Insert

## Problem

When a new story node is inserted into an existing graph (e.g. the user continues a journey and a new story node plus its child choice nodes are added), the choice nodes at the same hierarchical depth collide and overlap each other.

Reloading the journey from disk produces a correct layout. This asymmetry reveals the root cause.

## Root Cause

`useELKLayout.ts` maintains a `positionsRef` cache of every node's last known position. When new nodes are added:

1. ELK runs a full layout and computes correct positions for **all** nodes.
2. Existing nodes **ignore** ELK's output and use their cached positions.
3. New nodes use ELK's positions, which were computed assuming all nodes are at ELK's suggested coordinates — not the cached ones.
4. The two coordinate spaces disagree → collisions.

On a fresh load the cache is empty, so ELK's positions are used for everything → no collisions.

## Design

### Approach

Remove the position cache entirely. Always use ELK's computed positions as the single source of truth. Add CSS transitions so that when ELK re-lays out an existing graph (because new nodes were added), existing nodes animate smoothly to their new positions rather than snapping.

### First-Layout Guard

Nodes must not animate from `(0, 0)` when a graph is first rendered. A `initialLayoutDoneRef: MutableRefObject<boolean>` tracks whether the first ELK run for the current graph has completed:

- Resets to `false` when the graph goes `null` / empty (new journey loaded or graph cleared).
- Set to `true` after the first successful ELK run.
- While `false`: nodes receive no `transition` style — they appear at their ELK positions immediately.
- Once `true`: every node gets `style: { transition: 'transform 0.4s ease' }` merged in, so subsequent relayouts animate.

### Transition Mechanics

ReactFlow positions nodes via CSS `transform: translate(x, y)` on the node wrapper `div`. Merging `{ transition: 'transform 0.4s ease' }` into each node's `style` prop is sufficient — the browser handles interpolation automatically when ELK emits updated `x`/`y` values.

### Trigger Conditions

ELK already only re-runs when `nodeKey` changes. `nodeKey` is derived from the set of node IDs and edges, so it changes only on structural updates (new nodes or edges added/removed). Data-only updates (story text streaming in) do not retrigger ELK. This remains unchanged.

## File Changes

| File | Change |
|------|--------|
| `storyteller_frontend/src/hooks/useELKLayout.ts` | Remove `positionsRef` and all `existing ?? suggested` merging logic. Add `initialLayoutDoneRef`. Apply transition style after first layout. |

## Implementation Notes

**`useEffect` dependency array:** The current hook depends on `[graph, nodeKey]`. `nodeKey` is derived from `graph` via `useMemo`, so a change to `graph` that doesn't change structure (e.g. story text streaming in) correctly does not retrigger ELK because `nodeKey` is stable. Do not remove `graph` from the dependency array without verifying this invariant holds.

**`initialLayoutDoneRef` reset location:** Reset `initialLayoutDoneRef.current = false` in the same early-return branch that currently calls `positionsRef.current.clear()` — i.e. `if (!graph || !graph.nodes.length)`. This ensures a newly loaded journey always snaps in without animation.

No other files change.

## Edge Cases

| Scenario | Behaviour |
|----------|-----------|
| User loads a saved journey | Graph goes `null` → `initialLayoutDoneRef` resets → nodes appear at ELK positions without animation |
| ELK throws an error | `catch` block logs and bails; layout stays `null`; graph shows empty (same as today) |
| Streaming updates node data without adding nodes | `nodeKey` unchanged → ELK does not re-run → positions stable |
| Two story nodes at the same depth | ELK lays out all nodes in one pass → correct horizontal spacing → choice subtrees don't collide |

## Acceptance Criteria

1. After generating a continuation that adds a new story node, all nodes in the graph are correctly spaced — no overlaps.
2. Existing nodes animate smoothly to their new positions (approx. 0.4 s ease).
3. On initial graph load (new or saved journey), nodes appear in their correct positions without any animation from `(0, 0)`.
4. Reloading a journey that previously showed overlapping nodes now shows a clean layout.
