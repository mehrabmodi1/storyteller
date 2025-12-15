import { MouseEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
  type: 'smoothstep',
  style: {
    stroke: GRAPH_VISUAL_CONFIG.edge.color,
    strokeWidth: GRAPH_VISUAL_CONFIG.edge.width,
  },
  markerEnd: {
    type: MarkerType.ArrowClosed,
    color: GRAPH_VISUAL_CONFIG.edge.color,
    width: 20,
    height: 15,
  },
};

interface GraphCanvasProps {
  graph: TransformedGraph | null;
  onSelectChoice?: (nodeId: string) => void;
}

function GraphCanvasInner({ graph, onSelectChoice }: GraphCanvasProps) {
  const reactFlowInstance = useReactFlow();
  const prevLatestNodeRef = useRef<string | undefined>();
  const [edgeDiagnostics, setEdgeDiagnostics] = useState({
    propCount: 0,
    storeCount: 0,
  });

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
    const storeEdges = reactFlowInstance.getEdges?.() ?? [];
    setEdgeDiagnostics({
      propCount: edges.length,
      storeCount: storeEdges.length,
    });
    console.log('[GraphView] edge diagnostics', {
      propEdges: edges.length,
      storeEdges,
    });
    if (edges.length && storeEdges.length === 0) {
      console.warn('[GraphView] Edges provided but ReactFlow store is empty', {
        edges,
        storeEdges,
      });
    }
  }, [edges, reactFlowInstance]);

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

  const showEdgeWarning = edgeDiagnostics.propCount > 0 && edgeDiagnostics.storeCount === 0;

  return (
    <div className="relative h-[720px] rounded-3xl border border-slate-800 overflow-hidden bg-slate-950">
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
      <div className="absolute bottom-3 right-4 text-xs text-white/70 bg-black/40 backdrop-blur px-3 py-1 rounded-full">
        Edges: props {edgeDiagnostics.propCount} · store {edgeDiagnostics.storeCount}
      </div>
      {showEdgeWarning && (
        <div className="absolute bottom-16 right-4 text-xs text-red-300 bg-red-900/60 border border-red-500/60 rounded-lg px-3 py-2 max-w-xs">
          Warning: edges are present in transformed data but missing from the ReactFlow store.
          Check console logs for diagnostics.
        </div>
      )}
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


