# Graph Layout: Full Relayout with Smooth Transitions on Node Insert

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix overlapping choice nodes when a new story node is inserted by removing the position cache from `useELKLayout` and always using ELK's computed positions, with smooth CSS transitions after the first layout.

**Architecture:** Remove `positionsRef` from `useELKLayout.ts` — the cache that causes old nodes to ignore ELK's output when new nodes are added. Add an `initialLayoutDoneRef` flag so the first layout snaps into place without animation; subsequent layouts apply `transition: 'transform 0.4s ease'` to all nodes so the graph breathes open smoothly.

**Tech Stack:** TypeScript, React 18, ELK.js (`elkjs`), ReactFlow, Vitest, `@testing-library/react`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `storyteller_frontend/vite.config.ts` | Modify | Add `test` block for Vitest (jsdom environment) |
| `storyteller_frontend/package.json` | Modify | Add `test` script; add vitest/testing-library devDeps |
| `storyteller_frontend/src/hooks/__tests__/useELKLayout.test.ts` | Create | Unit tests for the new hook behaviour |
| `storyteller_frontend/src/hooks/useELKLayout.ts` | Modify | Remove position cache; add `initialLayoutDoneRef`; apply transition style |

---

### Task 1: Install Vitest and configure the test runner

**Files:**
- Modify: `storyteller_frontend/package.json`
- Modify: `storyteller_frontend/vite.config.ts`

The frontend has no test infrastructure. This task bootstraps Vitest so we can write hook tests in Task 2.

- [ ] **Step 1: Install test dependencies**

```bash
cd storyteller_frontend && npm install --save-dev vitest @testing-library/react jsdom
```

Expected: packages installed, `package.json` devDependencies updated.

- [ ] **Step 2: Add the `test` script to `package.json`**

In `storyteller_frontend/package.json`, add to the `"scripts"` block:

```json
"test": "vitest run --passWithNoTests",
"test:watch": "vitest"
```

- [ ] **Step 3: Configure Vitest in `vite.config.ts`**

Add a triple-slash reference and a `test` block. The final file should look like:

```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
  },
})
```

- [ ] **Step 4: Verify the runner works**

```bash
cd storyteller_frontend && npm test
```

Expected: `No test files found` (or 0 tests, 0 failures). The runner should exit 0.

- [ ] **Step 5: Commit**

```bash
git add storyteller_frontend/package.json storyteller_frontend/package-lock.json storyteller_frontend/vite.config.ts
git commit -m "chore: add vitest test runner to frontend"
```

---

### Task 2: Replace position cache with always-ELK layout + CSS transitions (TDD)

**Files:**
- Create: `storyteller_frontend/src/hooks/__tests__/useELKLayout.test.ts`
- Modify: `storyteller_frontend/src/hooks/useELKLayout.ts`

The core change: remove `positionsRef` and all `existing ?? suggested` merging. ELK's output is always used. A `initialLayoutDoneRef` flag controls whether a transition style is applied.

#### Background: how the hook works

`useELKLayout(graph)` takes a `TransformedGraph` (nodes + edges from the graph data), runs ELK's async `layout()` call, and returns `{ layout, isRunning }` where `layout` contains nodes with computed `position` values for ReactFlow.

`nodeKey` is a string derived from all node IDs and edges. The `useEffect` only re-runs when `nodeKey` changes — i.e. when graph *structure* changes (new nodes added), not when node data changes (story text streaming in). This behaviour is correct and must be preserved.

ELK's `layout()` returns `{ children: [{ id, x, y }, ...] }` — a position for every node.

#### The mock

ELK is an external async library. In tests, mock the entire module so `layout()` resolves synchronously with predictable `x` values:

```typescript
vi.mock('elkjs/lib/elk.bundled.js', () => ({
  default: class MockELK {
    async layout(graph: { children?: { id: string }[] }) {
      return {
        children: (graph.children ?? []).map((c, i) => ({
          id: c.id,
          x: i * 200,
          y: 0,
        })),
      };
    }
  },
}));
```

This places node 0 at `(0, 0)`, node 1 at `(200, 0)`, etc. — deterministic and easy to assert.

#### Helper

```typescript
import type { TransformedGraph } from '@/utils/graphTransform';
import type { StoryReactFlowNode } from '@/types/graph.types';

function makeGraph(ids: string[]): TransformedGraph {
  return {
    nodes: ids.map((id) => ({
      id,
      type: 'storyNode' as const,
      position: { x: 0, y: 0 },
      data: { id, type: 'story' as const, label: id },
    } as StoryReactFlowNode)),
    edges: [],
  };
}
```

- [ ] **Step 1: Write the failing tests**

Create `storyteller_frontend/src/hooks/__tests__/useELKLayout.test.ts`:

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useELKLayout } from '@/hooks/useELKLayout';
import type { TransformedGraph } from '@/utils/graphTransform';
import type { StoryReactFlowNode } from '@/types/graph.types';

vi.mock('elkjs/lib/elk.bundled.js', () => ({
  default: class MockELK {
    async layout(graph: { children?: { id: string }[] }) {
      return {
        children: (graph.children ?? []).map((c, i) => ({
          id: c.id,
          x: i * 200,
          y: 0,
        })),
      };
    }
  },
}));

function makeGraph(ids: string[]): TransformedGraph {
  return {
    nodes: ids.map((id) => ({
      id,
      type: 'storyNode' as const,
      position: { x: 0, y: 0 },
      data: { id, type: 'story' as const, label: id },
    } as StoryReactFlowNode)),
    edges: [],
  };
}

describe('useELKLayout', () => {
  it('uses ELK positions on first layout with no transition style', async () => {
    const { result } = renderHook(() => useELKLayout(makeGraph(['a', 'b'])));

    await waitFor(() => expect(result.current.layout).not.toBeNull());

    const nodes = result.current.layout!.nodes;
    expect(nodes[0].position).toEqual({ x: 0, y: 0 });
    expect(nodes[1].position).toEqual({ x: 200, y: 0 });
    expect(nodes[0].style?.transition).toBeUndefined();
    expect(nodes[1].style?.transition).toBeUndefined();
  });

  it('applies transition style on subsequent layouts when new nodes are added', async () => {
    const { result, rerender } = renderHook(
      ({ g }: { g: TransformedGraph }) => useELKLayout(g),
      { initialProps: { g: makeGraph(['a']) } },
    );

    await waitFor(() => expect(result.current.layout).not.toBeNull());

    // Add a second node — nodeKey changes, ELK re-runs
    rerender({ g: makeGraph(['a', 'b']) });

    await waitFor(() => expect(result.current.layout!.nodes).toHaveLength(2));

    const nodes = result.current.layout!.nodes;
    expect(nodes[0].position).toEqual({ x: 0, y: 0 });
    expect(nodes[1].position).toEqual({ x: 200, y: 0 });
    expect(nodes[0].style?.transition).toBe('transform 0.4s ease');
    expect(nodes[1].style?.transition).toBe('transform 0.4s ease');
  });

  it('resets transition state after graph is cleared then reloaded', async () => {
    const { result, rerender } = renderHook(
      ({ g }: { g: TransformedGraph | null }) => useELKLayout(g),
      { initialProps: { g: makeGraph(['a']) as TransformedGraph | null } },
    );

    await waitFor(() => expect(result.current.layout).not.toBeNull());

    // Trigger transition state
    rerender({ g: makeGraph(['a', 'b']) });
    await waitFor(() => expect(result.current.layout!.nodes).toHaveLength(2));

    // Clear graph (simulates loading a new journey)
    rerender({ g: null });
    await waitFor(() => expect(result.current.layout).toBeNull());

    // Reload — should be treated as a fresh first layout (no transition)
    rerender({ g: makeGraph(['x']) });
    await waitFor(() => expect(result.current.layout!.nodes).toHaveLength(1));

    expect(result.current.layout!.nodes[0].style?.transition).toBeUndefined();
  });
});
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd storyteller_frontend && npm test
```

Expected: 3 tests, all failing. The first test may pass by accident (existing code sometimes uses ELK positions for new nodes), but the second and third should fail because `positionsRef` preserves stale positions.

- [ ] **Step 3: Implement the new `useELKLayout`**

Replace the entire contents of `storyteller_frontend/src/hooks/useELKLayout.ts` with:

```typescript
import { useEffect, useMemo, useRef, useState } from 'react';
import ELK from 'elkjs/lib/elk.bundled.js';
import type { XYPosition } from 'reactflow';
import type { TransformedGraph } from '@/utils/graphTransform';
import type { StoryReactFlowNode, StoryReactFlowEdge } from '@/types/graph.types';
import { buildElkGraph } from '@/utils/elkConfig';

interface LayoutResult {
  nodes: StoryReactFlowNode[];
  edges: StoryReactFlowEdge[];
  latestStoryNodeId?: string;
  latestStoryTimestamp?: string;
}

const elk = new ELK();

export function useELKLayout(graph: TransformedGraph | null) {
  const [layout, setLayout] = useState<LayoutResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const initialLayoutDoneRef = useRef<boolean>(false);

  const nodeKey = useMemo(() => {
    if (!graph) return null;
    return `${graph.nodes.map((n) => n.id).join('|')}|${graph.edges
      .map((e) => `${e.source}->${e.target}`)
      .join('|')}`;
  }, [graph]);

  useEffect(() => {
    if (!graph || !graph.nodes.length) {
      setLayout(null);
      initialLayoutDoneRef.current = false;
      return;
    }

    const layoutTarget = graph;
    let cancelled = false;

    async function runLayout() {
      setIsRunning(true);
      try {
        const elkGraph = buildElkGraph(layoutTarget);
        const result = await elk.layout(elkGraph);

        if (cancelled) {
          return;
        }

        const childPositions = new Map<string, XYPosition>();
        result.children?.forEach((child) => {
          if (typeof child.x === 'number' && typeof child.y === 'number') {
            childPositions.set(child.id, { x: child.x, y: child.y });
          }
        });

        const isInitialLayout = !initialLayoutDoneRef.current;
        const transitionStyle = isInitialLayout ? {} : { transition: 'transform 0.4s ease' };

        const layoutedNodes = layoutTarget.nodes.map((node) => ({
          ...node,
          position: childPositions.get(node.id) ?? { x: 0, y: 0 },
          style: { ...node.style, ...transitionStyle },
        }));

        initialLayoutDoneRef.current = true;

        setLayout({
          nodes: layoutedNodes,
          edges: layoutTarget.edges,
          latestStoryNodeId: layoutTarget.latestStoryNodeId,
          latestStoryTimestamp: layoutTarget.latestStoryTimestamp,
        });
      } catch (error) {
        console.error('[useELKLayout] Failed to compute layout', error);
      } finally {
        if (!cancelled) {
          setIsRunning(false);
        }
      }
    }

    runLayout();

    return () => {
      cancelled = true;
    };
  }, [graph, nodeKey]);

  return {
    layout,
    isRunning,
  };
}
```

- [ ] **Step 4: Run tests and confirm all 3 pass**

```bash
cd storyteller_frontend && npm test
```

Expected: `3 passed`.

- [ ] **Step 5: Type-check and build**

```bash
cd storyteller_frontend && npm run type-check && npm run build
```

Expected: no TypeScript errors, build succeeds (a chunk-size warning is pre-existing and acceptable).

- [ ] **Step 6: Verify in the browser**

Start both servers if not running:
```bash
# terminal 1
cd storyteller_backend && poetry run python -m api.main

# terminal 2
cd storyteller_frontend && npm run dev
```

Open `http://localhost:3000`. Generate a journey, then continue it from a choice node. Verify:
1. New story node + its choice nodes appear in the correct positions — no overlaps.
2. Existing nodes animate smoothly (~0.4 s) to their new positions when the layout updates.
3. Load a saved journey — nodes appear immediately in correct positions without any animation from `(0, 0)`.

- [ ] **Step 7: Commit**

```bash
git add storyteller_frontend/src/hooks/useELKLayout.ts storyteller_frontend/src/hooks/__tests__/useELKLayout.test.ts
git commit -m "fix: remove ELK position cache; always use ELK output with CSS transitions"
```
