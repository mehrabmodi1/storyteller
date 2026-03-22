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

// ── Task 4: dfsOrder ──────────────────────────────────────────────────────────

/**
 * Returns the subset of rowNodeIds in DFS pre-order starting from the graph roots.
 * Only emits nodes that appear in rowNodeIds; duplicates are suppressed.
 */
export function dfsOrder(
  rowNodeIds: string[],
  graph: StoryAdjacency,
): string[] {
  if (rowNodeIds.length === 0) return [];

  const rowSet = new Set(rowNodeIds);
  const visited = new Set<string>();
  const order: string[] = [];

  function dfs(nodeId: string): void {
    if (visited.has(nodeId)) return;
    visited.add(nodeId);

    if (rowSet.has(nodeId)) {
      order.push(nodeId);
    }

    for (const childId of graph.children.get(nodeId) ?? []) {
      dfs(childId);
    }
  }

  for (const root of graph.roots) {
    dfs(root);
  }

  return order;
}

// ── Task 5: computeGraphDistances + computeRowLayout ─────────────────────────

/**
 * BFS through the undirected story graph from each row node.
 * Returns pairwise distances between row nodes only.
 */
export function computeGraphDistances(
  rowNodeIds: string[],
  graph: StoryAdjacency,
): Map<string, Map<string, number>> {
  const rowSet = new Set(rowNodeIds);

  // Build undirected adjacency from the directed children map
  const undirected = new Map<string, string[]>();
  for (const [nodeId, childIds] of graph.children) {
    if (!undirected.has(nodeId)) undirected.set(nodeId, []);
    for (const childId of childIds) {
      undirected.get(nodeId)!.push(childId);
      if (!undirected.has(childId)) undirected.set(childId, []);
      undirected.get(childId)!.push(nodeId);
    }
  }

  const result = new Map<string, Map<string, number>>();

  for (const startId of rowNodeIds) {
    const distMap = new Map<string, number>();
    result.set(startId, distMap);

    // BFS from startId through the undirected graph
    const visited = new Map<string, number>();
    visited.set(startId, 0);
    const queue: string[] = [startId];

    while (queue.length > 0) {
      const current = queue.shift()!;
      const currentDist = visited.get(current)!;

      for (const neighbour of undirected.get(current) ?? []) {
        if (!visited.has(neighbour)) {
          visited.set(neighbour, currentDist + 1);
          queue.push(neighbour);
        }
      }
    }

    // Record distances to row nodes only
    for (const [nodeId, d] of visited) {
      if (rowSet.has(nodeId)) {
        distMap.set(nodeId, d);
      }
    }
  }

  return result;
}

/**
 * Orchestrates the full row layout for a given depth in the story graph.
 *
 * @param graph  Pre-built StoryAdjacency (output of buildStoryGraph)
 * @param depth  Row depth where 0 = leaf row, 1 = leaf-1 row, etc.
 */
export function computeRowLayout(
  graph: StoryAdjacency,
  depth: number,
): RowLayout {
  const leafDistances = computeLeafDistances(graph);

  let maxDepth = 0;
  for (const distances of leafDistances.values()) {
    for (const d of distances) {
      if (d > maxDepth) maxDepth = d;
    }
  }

  const rowNodeIds = getRowNodes(leafDistances, depth);
  const orderedNodeIds = dfsOrder(rowNodeIds, graph);
  const distances = computeGraphDistances(orderedNodeIds, graph);

  return { orderedNodeIds, distances, maxDepth };
}
