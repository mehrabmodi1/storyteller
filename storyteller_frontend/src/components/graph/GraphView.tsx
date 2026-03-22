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
  PanOnScrollMode,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useRowLayout } from '@/hooks/useRowLayout';

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
  onSelectStoryNode?: (nodeId: string) => void;
  activeChoiceId?: string | null;
  editablePrompt?: string;
  onChangePrompt?: (value: string) => void;
  onSubmitPrompt?: (text?: string) => void;
  onCancelEdit?: () => void;
  mode?: 'tree' | 'row';
  rowDepth?: number;
  onRowDepthChange?: (depth: number) => void;
  transformedGraph?: TransformedGraph | null;
}

function GraphCanvasInner(props: GraphCanvasProps) {
  const { graph, onSelectChoice: _onSelectChoice, onSelectStoryNode, onCancelEdit } = props;
  const reactFlowInstance = useReactFlow();
  const prevLatestNodeRef = useRef<string | undefined>();
  const [edgeDiagnostics, setEdgeDiagnostics] = useState({
    propCount: 0,
    storeCount: 0,
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(800);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const isRowMode = props.mode === 'row';
  const rowLayout = useRowLayout(
    isRowMode ? props.transformedGraph ?? null : null,
    props.rowDepth ?? 0,
    containerWidth,
  );

  const nodes = useMemo<StoryReactFlowNode[]>(() => {
    if (isRowMode) return rowLayout.nodes;
    return graph?.nodes ?? [];
  }, [isRowMode, rowLayout.nodes, graph?.nodes]);

  const edges = useMemo<StoryReactFlowEdge[]>(() => {
    if (isRowMode) return rowLayout.edges;
    return graph?.edges ?? [];
  }, [isRowMode, rowLayout.edges, graph?.edges]);

  // Inject choiceProps into choice nodes — needed for both tree and row mode
  const nodesWithChoiceProps = useMemo<StoryReactFlowNode[]>(() => {
    if (!nodes.length) return nodes;
    return nodes.map((node) => {
      if (node.type !== 'choiceNode') return node;
      const isActive = node.id === props.activeChoiceId;
      return {
        ...node,
        data: {
          ...node.data,
          choiceProps: {
            isActive,
            editablePrompt: props.editablePrompt,
            onChangePrompt: props.onChangePrompt,
            onSubmitPrompt: props.onSubmitPrompt,
            onCancel: props.onCancelEdit,
            onSelectChoice: props.onSelectChoice,
          },
        },
      } as StoryReactFlowNode;
    });
  }, [nodes, props.activeChoiceId, props.editablePrompt, props.onChangePrompt, props.onSubmitPrompt, props.onCancelEdit, props.onSelectChoice]);

  const handleNodeClick = useCallback(
    (_event: MouseEvent, node: StoryReactFlowNode) => {
      if (node.type === 'storyNode') {
        onSelectStoryNode?.(node.id);
      }
      // choiceNode clicks are handled by ChoiceNode's own onClick
    },
    [onSelectStoryNode],
  );

  const handlePaneClick = useCallback(() => {
    onCancelEdit?.();
  }, [onCancelEdit]);

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
    if (props.mode === 'row') return;
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

  const ROW_CONFIG = GRAPH_VISUAL_CONFIG.rowMode;
  const ROW_CHOICE_Y = ROW_CONFIG.storyY + GRAPH_VISUAL_CONFIG.storyNode.height + ROW_CONFIG.choiceGap;

  const rowFlowProps = isRowMode
    ? {
        translateExtent: [
          [-Infinity, ROW_CONFIG.storyY - 100],
          [Infinity, ROW_CHOICE_Y + GRAPH_VISUAL_CONFIG.choiceNode.height + 100],
        ] as [[number, number], [number, number]],
        zoomOnScroll: false,
        zoomOnPinch: false,
        panOnScroll: true,
        panOnScrollMode: PanOnScrollMode.Horizontal,
        fitView: false,
        minZoom: 1,
        maxZoom: 1,
      }
    : {};

  return (
    <div ref={containerRef} className="relative h-[720px] rounded-3xl border border-slate-800 overflow-hidden bg-slate-950">
      <ReactFlow
        nodes={nodesWithChoiceProps}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        fitViewOptions={fitViewOptions}
        proOptions={{ hideAttribution: true }}
        minZoom={0.1}
        maxZoom={1.8}
        onlyRenderVisibleElements={false}
        onMove={isRowMode ? (_event, viewport) => rowLayout.onViewportChange(viewport) : undefined}
        {...rowFlowProps}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#374151" />
        {!isRowMode && (
          <MiniMap
            nodeColor={(node) => (node.type === 'storyNode' ? '#f59e0b' : '#22d3ee')}
            nodeStrokeWidth={2}
            zoomable
            pannable
          />
        )}
        <Controls showInteractive={false} />
      </ReactFlow>
      {isRowMode && (
        <div className="absolute left-4 top-1/2 -translate-y-1/2 flex flex-col items-center gap-2 z-10">
          <button
            type="button"
            onClick={() => props.onRowDepthChange?.((props.rowDepth ?? 0) + 1)}
            disabled={(props.rowDepth ?? 0) >= rowLayout.maxDepth}
            className="bg-slate-800 border border-slate-600 text-slate-300 rounded-lg px-3 py-2 text-sm disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-700"
          >
            ▲
          </button>
          <div className="bg-slate-700 text-slate-300 text-[10px] text-center px-2 py-1 rounded tracking-wide">
            {(props.rowDepth ?? 0) === 0 ? 'LEAF' : `LEAF-${props.rowDepth}`}
          </div>
          <button
            type="button"
            onClick={() => props.onRowDepthChange?.(Math.max(0, (props.rowDepth ?? 0) - 1))}
            disabled={(props.rowDepth ?? 0) === 0}
            className="bg-slate-800 border border-slate-600 text-slate-300 rounded-lg px-3 py-2 text-sm disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-700"
          >
            ▼
          </button>
        </div>
      )}
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
  const { graph, activeChoiceId, editablePrompt, onChangePrompt, onSubmitPrompt, onCancelEdit, onSelectChoice } = props;

  const nodesWithChoiceProps = useMemo(() => {
    if (!graph?.nodes?.length) return graph?.nodes ?? [];
    return graph.nodes.map((node) => {
      if (node.type !== 'choiceNode') return node;
      const isActive = node.id === activeChoiceId;
      return {
        ...node,
        data: {
          ...node.data,
          choiceProps: {
            isActive,
            editablePrompt,
            onChangePrompt,
            onSubmitPrompt,
            onCancel: onCancelEdit,
            onSelectChoice,
          },
        },
      } as StoryReactFlowNode;
    });
  }, [graph?.nodes, activeChoiceId, onChangePrompt, onSubmitPrompt, onCancelEdit, onSelectChoice]);

  return (
    <ReactFlowProvider>
      <GraphCanvasInner
        {...props}
        graph={graph ? { ...graph, nodes: nodesWithChoiceProps } : graph}
        onCancelEdit={onCancelEdit}
      />
    </ReactFlowProvider>
  );
}


