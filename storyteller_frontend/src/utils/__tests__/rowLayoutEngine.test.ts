import { describe, it, expect } from 'vitest';
import {
  buildStoryGraph,
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
