import type { ColorTheme } from '@/types';
import {
  GraphData,
  GraphNode,
  GraphEdge,
  StoryReactFlowNode,
  StoryReactFlowEdge,
} from '@/types/graph.types';
import { DEFAULT_THEME } from '@/context/AppContext';
import { GRAPH_VISUAL_CONFIG } from '@/config/graph.config';

export interface TransformOptions {
  personaName?: string | null;
  personaTheme?: ColorTheme | null;
}

export interface TransformedGraph {
  nodes: StoryReactFlowNode[];
  edges: StoryReactFlowEdge[];
  latestStoryNodeId?: string;
  latestStoryTimestamp?: string;
}

const DEFAULT_POSITION = { x: 0, y: 0 };
const STORY_NODE_COMPONENT = 'storyNode';
const CHOICE_NODE_COMPONENT = 'choiceNode';
const EDGE_TYPE = 'smoothstep';

function parseTimestamp(value?: string | null): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? undefined : parsed;
}

function resolveTheme(
  node: GraphNode,
  options: TransformOptions,
): ColorTheme {
  if (node.persona && node.theme) {
    return node.theme;
  }
  if (node.theme) {
    return node.theme;
  }
  if (options.personaTheme) {
    return options.personaTheme;
  }
  return DEFAULT_THEME;
}

function transformNode(
  node: GraphNode,
  index: number,
  options: TransformOptions,
): StoryReactFlowNode {
  const isStory = node.type === 'story';

  const dimensions = isStory ? GRAPH_VISUAL_CONFIG.storyNode : GRAPH_VISUAL_CONFIG.choiceNode;

  return {
    id: node.id || `node-${index}`,
    type: isStory ? STORY_NODE_COMPONENT : CHOICE_NODE_COMPONENT,
    position: DEFAULT_POSITION,
    width: dimensions.width,
    height: dimensions.height,
    data: {
      id: node.id,
      type: node.type,
      label: node.label,
      story: node.story ?? null,
      image_url: node.image_url ?? null,
      timestamp: node.timestamp,
      persona: node.persona ?? options.personaName ?? null,
      theme: resolveTheme(node, options),
    },
  };
}

function transformEdge(edge: GraphEdge, index: number): StoryReactFlowEdge {
  const edgeId = `${edge.source}-${edge.target}-${index}`;
  return {
    id: edgeId,
    source: edge.source,
    target: edge.target,
    type: EDGE_TYPE,
    animated: false,
  };
}

export function transformGraphData(
  graph: GraphData | null | undefined,
  options: TransformOptions = {},
): TransformedGraph {
  if (!graph) {
    return { nodes: [], edges: [] };
  }

  const nodes = graph.nodes.map((node, idx) => transformNode(node, idx, options));
  const edges = graph.links.map(transformEdge);

  const storyNodes = nodes.filter(
    (node) => node.data?.type === 'story' && node.data?.timestamp,
  );

  const latestStoryNode = storyNodes
    .map((node) => ({
      node,
      timestampValue: parseTimestamp(node.data.timestamp),
    }))
    .filter((entry) => typeof entry.timestampValue === 'number')
    .sort((a, b) => (a.timestampValue! > b.timestampValue! ? -1 : 1))[0];

  return {
    nodes,
    edges,
    latestStoryNodeId: latestStoryNode?.node.id,
    latestStoryTimestamp: latestStoryNode?.node.data.timestamp,
  };
}

