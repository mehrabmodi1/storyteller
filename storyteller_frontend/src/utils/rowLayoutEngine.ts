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

// ── Task 3: computeLeafDistances + getRowNodes ────────────────────────────────

/**
 * For each story node, computes the set of hop-distances to descendant leaves.
 * Leaves (nodes with no children) have distance 0 to themselves.
 * A node's distances are { childDistance + 1 for each child's distance }.
 */
export function computeLeafDistances(
  graph: StoryAdjacency,
): Map<string, Set<number>> {
  const result = new Map<string, Set<number>>();

  function dfs(nodeId: string): Set<number> {
    if (result.has(nodeId)) return result.get(nodeId)!;

    const childIds = graph.children.get(nodeId) ?? [];
    if (childIds.length === 0) {
      const s = new Set<number>([0]);
      result.set(nodeId, s);
      return s;
    }

    const distances = new Set<number>();
    for (const childId of childIds) {
      const childDistances = dfs(childId);
      for (const d of childDistances) {
        distances.add(d + 1);
      }
    }
    result.set(nodeId, distances);
    return distances;
  }

  for (const root of graph.roots) {
    dfs(root);
  }

  return result;
}

/**
 * Returns the ids of nodes whose leaf-distance set contains k.
 */
export function getRowNodes(
  leafDistances: Map<string, Set<number>>,
  k: number,
): string[] {
  const result: string[] = [];
  for (const [nodeId, distances] of leafDistances) {
    if (distances.has(k)) {
      result.push(nodeId);
    }
  }
  return result;
}
