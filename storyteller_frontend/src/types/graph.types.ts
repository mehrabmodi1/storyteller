import type { Node, Edge } from 'reactflow';
import type { ColorTheme } from './api.types';

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
  persona?: string | null;
  theme?: ColorTheme;
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
  graph?: { graph_name?: string; [key: string]: unknown };
}

/**
 * Response containing the loaded graph data
 */
export interface GetLoadedGraphResponse {
  graph: GraphData;
}

/**
 * Extended node type for ReactFlow (includes persona/theme metadata)
 */
export interface ReactFlowNodeData {
  id: string;
  type: NodeType;
  label: string;
  story?: string | null;
  image_url?: string | null;
  timestamp?: string;
  persona?: string | null;
  theme?: ColorTheme;
}

export type StoryReactFlowNode = Node<ReactFlowNodeData>;
export type StoryReactFlowEdge = Edge;

