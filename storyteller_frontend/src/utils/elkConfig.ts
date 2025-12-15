import type { ElkNode } from 'elkjs';
import type { TransformedGraph } from './graphTransform';
import { GRAPH_VISUAL_CONFIG } from '@/config/graph.config';

export const ELK_LAYOUT_OPTIONS = {
  'elk.algorithm': 'layered',
  'elk.direction': 'DOWN',
  'elk.layered.spacing.nodeNodeBetweenLayers': '120',
  'elk.layered.spacing.nodeNode': '80',
  'elk.spacing.nodeNode': '80',
  'elk.layered.thoroughness': '10',
  'elk.layered.crossingMinimization.semiInteractive': 'true',
  'elk.layered.nodePlacement.bk.fixedAlignment': 'BALANCED',
  'elk.padding': '[top=80,left=80,bottom=80,right=80]',
} as const;

export function buildElkGraph(graph: TransformedGraph): ElkNode {
  return {
    id: 'root',
    layoutOptions: ELK_LAYOUT_OPTIONS,
    children: graph.nodes.map((node) => ({
      id: node.id,
      width:
        node.type === 'storyNode'
          ? GRAPH_VISUAL_CONFIG.storyNode.width
          : GRAPH_VISUAL_CONFIG.choiceNode.width,
      height:
        node.type === 'storyNode'
          ? GRAPH_VISUAL_CONFIG.storyNode.height
          : GRAPH_VISUAL_CONFIG.choiceNode.height,
    })),
    edges: graph.edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };
}


