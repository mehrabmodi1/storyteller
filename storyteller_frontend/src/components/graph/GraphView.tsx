import { MouseEvent, useCallback, useEffect, useMemo, useRef } from 'react';
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  NodeTypes,
  useReactFlow,
  FitViewOptions,
  ReactFlowProvider,
  DefaultEdgeOptions,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import type { TransformedGraph } from '@/utils/graphTransform';
import type {
  StoryReactFlowNode,
  StoryReactFlowEdge,
} from '@/types/graph.types';
import { GRAPH_VISUAL_CONFIG } from '@/config/graph.config';
import { StoryNode } from './StoryNode';
import { ChoiceNode } from './ChoiceNode';

const nodeTypes: NodeTypes = {
  storyNode: StoryNode,
  choiceNode: ChoiceNode,
};

const fitViewOptions: FitViewOptions = {
  padding: 0.2,
  duration: 800,
};

const defaultEdgeOptions: DefaultEdgeOptions = {
  animated: GRAPH_VISUAL_CONFIG.edge.animated,
  style: {
    stroke: GRAPH_VISUAL_CONFIG.edge.color,
    strokeWidth: GRAPH_VISUAL_CONFIG.edge.width,
  },
  markerEnd: {
    type: MarkerType.ArrowClosed,
    color: GRAPH_VISUAL_CONFIG.edge.color,
  },
};

interface GraphCanvasProps {
  graph: TransformedGraph | null;
  onSelectChoice?: (nodeId: string) => void;
}

function GraphCanvasInner({ graph, onSelectChoice }: GraphCanvasProps) {
  const reactFlowInstance = useReactFlow();
  const prevLatestNodeRef = useRef<string | undefined>();

  const nodes = useMemo<StoryReactFlowNode[]>(() => graph?.nodes ?? [], [graph?.nodes]);
  const edges = useMemo<StoryReactFlowEdge[]>(() => graph?.edges ?? [], [graph?.edges]);

  const handleNodeClick = useCallback(
    (_event: MouseEvent, node: StoryReactFlowNode) => {
      if (node.type === 'choiceNode') {
        onSelectChoice?.(node.id);
      }
    },
    [onSelectChoice],
  );

  useEffect(() => {
    console.log('[GraphView] nodes/edges', {
      nodes: nodes.length,
      edges: edges.length,
      sampleEdges: edges.slice(0, 3),
    });
  }, [nodes, edges]);

  useEffect(() => {
    if (!graph || !graph.latestStoryNodeId || !nodes.length) {
      return;
    }

    const hasChanged = prevLatestNodeRef.current !== graph.latestStoryNodeId;
    if (!hasChanged) {
      return;
    }

    prevLatestNodeRef.current = graph.latestStoryNodeId;

    const latestNode = nodes.find((node) => node.id === graph.latestStoryNodeId);
    if (!latestNode) {
      return;
    }

    requestAnimationFrame(() => {
      reactFlowInstance.setCenter(latestNode.position.x, latestNode.position.y, {
        zoom: 0.8,
        duration: 800,
      });
    });
  }, [graph, nodes, reactFlowInstance]);

  return (
    <div className="h-[720px] rounded-3xl border border-slate-800 overflow-hidden bg-slate-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={handleNodeClick}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        fitViewOptions={fitViewOptions}
        proOptions={{ hideAttribution: true }}
        minZoom={0.1}
        maxZoom={1.8}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#374151" />
        <MiniMap
          nodeColor={(node) => (node.type === 'storyNode' ? '#f59e0b' : '#22d3ee')}
          nodeStrokeWidth={2}
          zoomable
          pannable
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

export function GraphView(props: GraphCanvasProps) {
  return (
    <ReactFlowProvider>
      <GraphCanvasInner {...props} />
    </ReactFlowProvider>
  );
}


