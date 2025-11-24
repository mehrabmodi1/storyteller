/**
 * TypeScript type definitions for graph data structures.
 * These types mirror the backend graph models.
 */

/**
 * Node type in the story graph
 */
export type NodeType = 'story' | 'choice';

/**
 * A node in the story graph
 */
export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  story?: string | null;
  image_url?: string | null;
  timestamp?: string;
}

/**
 * An edge in the story graph
 */
export interface GraphEdge {
  source: string;
  target: string;
}

/**
 * Complete graph data structure
 */
export interface GraphData {
  nodes: GraphNode[];
  links: GraphEdge[];
}

/**
 * Response containing the loaded graph data
 */
export interface GetLoadedGraphResponse {
  graph: GraphData;
}

/**
 * Extended node type for ReactFlow (includes positioning)
 */
export interface ReactFlowNodeData {
  id: string;
  type: NodeType;
  label: string;
  story?: string | null;
  image_url?: string | null;
  timestamp?: string;
}

/**
 * ReactFlow node with position
 */
export interface ReactFlowNode {
  id: string;
  type: string; // 'storyNode' or 'choiceNode' for ReactFlow
  data: ReactFlowNodeData;
  position: { x: number; y: number };
}

/**
 * ReactFlow edge
 */
export interface ReactFlowEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  animated?: boolean;
}

