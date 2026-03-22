import type { StoryReactFlowNode, StoryReactFlowEdge } from '@/types/graph.types';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface StoryAdjacency {
  children: Map<string, string[]>;
  parents: Map<string, string>;
  roots: string[];
}

export interface RowLayout {
  orderedNodeIds: string[];
  distances: Map<string, Map<string, number>>;
  maxDepth: number;
}

// ── Task 2: buildStoryGraph ───────────────────────────────────────────────────

/**
 * Builds a story-only adjacency graph from a ReactFlow graph that contains
 * both story and choice nodes connected via story→choice→story edges.
 *
 * For each story node, its direct story children are those reachable by
 * traversing through one choice intermediary.
 */
export function buildStoryGraph(
  nodes: StoryReactFlowNode[],
  edges: StoryReactFlowEdge[],
): StoryAdjacency {
  const children = new Map<string, string[]>();
  const parents = new Map<string, string>();

  const nodeById = new Map<string, StoryReactFlowNode>();
  for (const node of nodes) {
    nodeById.set(node.id, node);
  }

  const outEdges = new Map<string, string[]>();
  for (const node of nodes) {
    outEdges.set(node.id, []);
  }
  for (const e of edges) {
    outEdges.get(e.source)?.push(e.target);
  }

  for (const node of nodes) {
    if (node.data.type === 'story') {
      children.set(node.id, []);
    }
  }

  for (const node of nodes) {
    if (node.data.type !== 'story') continue;
    const storyId = node.id;
    const choiceNeighbours = outEdges.get(storyId) ?? [];

    for (const choiceId of choiceNeighbours) {
      const choiceNode = nodeById.get(choiceId);
      if (!choiceNode || choiceNode.data.type !== 'choice') continue;

      const storyNeighbours = outEdges.get(choiceId) ?? [];
      for (const childStoryId of storyNeighbours) {
        const childNode = nodeById.get(childStoryId);
        if (!childNode || childNode.data.type !== 'story') continue;

        children.get(storyId)!.push(childStoryId);
        parents.set(childStoryId, storyId);
      }
    }
  }

  const roots: string[] = [];
  for (const node of nodes) {
    if (node.data.type === 'story' && !parents.has(node.id)) {
      roots.push(node.id);
    }
  }

  return { children, parents, roots };
}
