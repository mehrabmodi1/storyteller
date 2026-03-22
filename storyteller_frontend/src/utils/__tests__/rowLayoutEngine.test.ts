import { describe, it, expect } from 'vitest';
import {
  buildStoryGraph,
  computeLeafDistances,
  getRowNodes,
  dfsOrder,
} from '../rowLayoutEngine';
import type { StoryReactFlowNode, StoryReactFlowEdge } from '@/types/graph.types';

// ── Test helpers ──────────────────────────────────────────────────────────────

function storyNode(id: string): StoryReactFlowNode {
  return {
    id,
    type: 'storyNode',
    position: { x: 0, y: 0 },
    data: { id, type: 'story', label: id },
  } as StoryReactFlowNode;
}

function choiceNode(id: string): StoryReactFlowNode {
  return {
    id,
    type: 'choiceNode',
    position: { x: 0, y: 0 },
    data: { id, type: 'choice', label: id },
  } as StoryReactFlowNode;
}

function edge(source: string, target: string): StoryReactFlowEdge {
  return { id: `${source}-${target}`, source, target, type: 'smoothstep' };
}

/*
  Test tree:
  S1 → C1a → S2 → C2a → S4
                 → C2b → S5
     → C1b → S3

  Story-only graph:
  S1 → S2 → S4
          → S5
     → S3
*/
const nodes: StoryReactFlowNode[] = [
  storyNode('S1'), choiceNode('C1a'), choiceNode('C1b'),
  storyNode('S2'), choiceNode('C2a'), choiceNode('C2b'),
  storyNode('S3'), storyNode('S4'), storyNode('S5'),
];

const edges: StoryReactFlowEdge[] = [
  edge('S1', 'C1a'), edge('S1', 'C1b'),
  edge('C1a', 'S2'), edge('C1b', 'S3'),
  edge('S2', 'C2a'), edge('S2', 'C2b'),
  edge('C2a', 'S4'), edge('C2b', 'S5'),
];

// ── Task 2: buildStoryGraph ───────────────────────────────────────────────────

describe('buildStoryGraph', () => {
  it('extracts story-only parent-child relationships', () => {
    const graph = buildStoryGraph(nodes, edges);
    expect(graph.children.get('S1')?.sort()).toEqual(['S2', 'S3'].sort());
    expect(graph.children.get('S2')?.sort()).toEqual(['S4', 'S5'].sort());
    expect(graph.children.get('S3')).toEqual([]);
    expect(graph.children.get('S4')).toEqual([]);
    expect(graph.children.get('S5')).toEqual([]);
  });

  it('computes roots and parents correctly', () => {
    const graph = buildStoryGraph(nodes, edges);
    expect(graph.roots).toEqual(['S1']);
    expect(graph.parents.get('S2')).toBe('S1');
    expect(graph.parents.get('S3')).toBe('S1');
    expect(graph.parents.get('S4')).toBe('S2');
    expect(graph.parents.get('S5')).toBe('S2');
    expect(graph.parents.has('S1')).toBe(false);
  });

  it('returns empty result for empty graph', () => {
    const graph = buildStoryGraph([], []);
    expect(graph.children.size).toBe(0);
    expect(graph.parents.size).toBe(0);
    expect(graph.roots).toEqual([]);
  });

  it('handles single story node', () => {
    const graph = buildStoryGraph([storyNode('S1')], []);
    expect(graph.roots).toEqual(['S1']);
    expect(graph.children.get('S1')).toEqual([]);
    expect(graph.parents.size).toBe(0);
  });
});

// ── Task 3: computeLeafDistances + getRowNodes ────────────────────────────────

describe('computeLeafDistances', () => {
  it('leaves have distance set containing 0', () => {
    const graph = buildStoryGraph(nodes, edges);
    const ld = computeLeafDistances(graph);
    expect(ld.get('S3')).toEqual(new Set([0]));
    expect(ld.get('S4')).toEqual(new Set([0]));
    expect(ld.get('S5')).toEqual(new Set([0]));
  });

  it('S2 is 1 hop from a leaf', () => {
    const graph = buildStoryGraph(nodes, edges);
    const ld = computeLeafDistances(graph);
    expect(ld.get('S2')).toEqual(new Set([1]));
  });

  it('S1 has distances 1 and 2', () => {
    const graph = buildStoryGraph(nodes, edges);
    const ld = computeLeafDistances(graph);
    expect(ld.get('S1')).toEqual(new Set([1, 2]));
  });
});

describe('getRowNodes', () => {
  it('k=0 returns leaves', () => {
    const graph = buildStoryGraph(nodes, edges);
    const ld = computeLeafDistances(graph);
    expect(getRowNodes(ld, 0).sort()).toEqual(['S3', 'S4', 'S5'].sort());
  });

  it('k=1 returns S1 and S2', () => {
    const graph = buildStoryGraph(nodes, edges);
    const ld = computeLeafDistances(graph);
    expect(getRowNodes(ld, 1).sort()).toEqual(['S1', 'S2'].sort());
  });

  it('k=2 returns S1 only', () => {
    const graph = buildStoryGraph(nodes, edges);
    const ld = computeLeafDistances(graph);
    expect(getRowNodes(ld, 2).sort()).toEqual(['S1']);
  });

  it('k=3 returns empty', () => {
    const graph = buildStoryGraph(nodes, edges);
    const ld = computeLeafDistances(graph);
    expect(getRowNodes(ld, 3)).toEqual([]);
  });
});

// ── Task 4: dfsOrder ──────────────────────────────────────────────────────────

describe('dfsOrder', () => {
  it('leaf row visits S4, S5, then S3 (DFS pre-order)', () => {
    const graph = buildStoryGraph(nodes, edges);
    const ld = computeLeafDistances(graph);
    const rowNodes = getRowNodes(ld, 0);
    expect(dfsOrder(rowNodes, graph)).toEqual(['S4', 'S5', 'S3']);
  });

  it('leaf-1 row visits S1, S2', () => {
    const graph = buildStoryGraph(nodes, edges);
    const ld = computeLeafDistances(graph);
    const rowNodes = getRowNodes(ld, 1);
    expect(dfsOrder(rowNodes, graph)).toEqual(['S1', 'S2']);
  });

  it('single node returns that node', () => {
    const graph = buildStoryGraph([storyNode('S1')], []);
    expect(dfsOrder(['S1'], graph)).toEqual(['S1']);
  });

  it('empty set returns empty', () => {
    const graph = buildStoryGraph(nodes, edges);
    expect(dfsOrder([], graph)).toEqual([]);
  });
});
