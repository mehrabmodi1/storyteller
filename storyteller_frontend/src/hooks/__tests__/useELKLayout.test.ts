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
