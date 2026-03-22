import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useReactFlow, type Viewport } from 'reactflow';
import type { TransformedGraph } from '@/utils/graphTransform';
import type { StoryReactFlowNode, StoryReactFlowEdge } from '@/types/graph.types';
import { GRAPH_VISUAL_CONFIG } from '@/config/graph.config';
import { buildStoryGraph, computeRowLayout } from '@/utils/rowLayoutEngine';

const ROW = GRAPH_VISUAL_CONFIG.rowMode;
const CHOICE_Y = ROW.storyY + GRAPH_VISUAL_CONFIG.storyNode.height + ROW.choiceGap;

export interface UseRowLayoutResult {
  nodes: StoryReactFlowNode[];
  edges: StoryReactFlowEdge[];
  maxDepth: number;
  centeredNodeId: string | null;
  onViewportChange: (viewport: Viewport) => void;
}

export function useRowLayout(
  graph: TransformedGraph | null,
  rowDepth: number,
  containerWidth: number,
): UseRowLayoutResult {
  const reactFlow = useReactFlow();

  // Compute row layout from engine
  const engineResult = useMemo(() => {
    if (!graph || !graph.nodes.length) return null;
    const storyGraph = buildStoryGraph(graph.nodes, graph.edges);
    return computeRowLayout(storyGraph, rowDepth);
  }, [graph, rowDepth]);

  // Build position map for story nodes
  const storyPositions = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    if (!engineResult) return map;
    engineResult.orderedNodeIds.forEach((id, index) => {
      map.set(id, { x: index * ROW.spacing, y: ROW.storyY });
    });
    return map;
  }, [engineResult]);

  // Center detection — initialize synchronously to avoid empty-content flash
  const initialCenteredId = useMemo(() => {
    if (!engineResult || !engineResult.orderedNodeIds.length) return null;
    const rowSet = new Set(engineResult.orderedNodeIds);
    if (graph?.latestStoryNodeId && rowSet.has(graph.latestStoryNodeId)) {
      return graph.latestStoryNodeId;
    }
    return engineResult.orderedNodeIds[0];
  }, [engineResult, graph?.latestStoryNodeId]);

  const [centeredNodeId, setCenteredNodeId] = useState<string | null>(initialCenteredId);
  const centeredRef = useRef<string | null>(initialCenteredId);

  // Snap viewport when initial centered node changes (depth or graph change)
  useEffect(() => {
    if (!initialCenteredId) return;
    setCenteredNodeId(initialCenteredId);
    centeredRef.current = initialCenteredId;

    const pos = storyPositions.get(initialCenteredId);
    if (pos) {
      requestAnimationFrame(() => {
        reactFlow.setCenter(pos.x, ROW.storyY, { zoom: 1, duration: 300 });
      });
    }
  }, [initialCenteredId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Viewport change handler — detect new centered node
  const onViewportChange = useCallback(
    (viewport: Viewport) => {
      if (!engineResult || !engineResult.orderedNodeIds.length) return;

      const centerX = (-viewport.x + containerWidth / 2) / viewport.zoom;
      let closestId = engineResult.orderedNodeIds[0];
      let closestDist = Infinity;

      for (const id of engineResult.orderedNodeIds) {
        const pos = storyPositions.get(id);
        if (!pos) continue;
        const dist = Math.abs(pos.x - centerX);
        if (dist < closestDist) {
          closestDist = dist;
          closestId = id;
        }
      }

      if (closestId !== centeredRef.current) {
        centeredRef.current = closestId;
        setCenteredNodeId(closestId);
      }
    },
    [engineResult, storyPositions, containerWidth],
  );

  // Build final nodes and edges
  const { nodes, edges } = useMemo(() => {
    if (!graph || !engineResult || !centeredNodeId) {
      return { nodes: [] as StoryReactFlowNode[], edges: [] as StoryReactFlowEdge[] };
    }

    const orderedIds = engineResult.orderedNodeIds;
    const centerIdx = orderedIds.indexOf(centeredNodeId);
    if (centerIdx === -1) {
      return { nodes: [] as StoryReactFlowNode[], edges: [] as StoryReactFlowEdge[] };
    }

    // Visible story window: center ± 2 (5 nodes)
    const visibleStart = Math.max(0, centerIdx - 2);
    const visibleEnd = Math.min(orderedIds.length - 1, centerIdx + 2);
    const visibleStoryIds = orderedIds.slice(visibleStart, visibleEnd + 1);

    // Choice window: center ± 1 (3 nodes show choices)
    const choiceStart = Math.max(0, centerIdx - 1);
    const choiceEnd = Math.min(orderedIds.length - 1, centerIdx + 1);
    const choiceStoryIds = new Set(orderedIds.slice(choiceStart, choiceEnd + 1));

    // Distances from centered node
    const distMap = engineResult.distances.get(centeredNodeId);

    const originalNodeMap = new Map(graph.nodes.map((n) => [n.id, n]));
    const resultNodes: StoryReactFlowNode[] = [];
    const resultEdges: StoryReactFlowEdge[] = [];

    for (const storyId of visibleStoryIds) {
      const original = originalNodeMap.get(storyId);
      if (!original) continue;
      const pos = storyPositions.get(storyId)!;
      const graphDist = distMap?.get(storyId) ?? 0;

      resultNodes.push({
        ...original,
        position: pos,
        data: { ...original.data, distanceFromCenter: graphDist },
      });

      // Add choice nodes if this story is in the choice window
      if (choiceStoryIds.has(storyId)) {
        const choiceEdges = graph.edges.filter((e) => e.source === storyId);
        const choiceIds = choiceEdges.map((e) => e.target);
        const validChoices = choiceIds.filter((id) => {
          const node = originalNodeMap.get(id);
          return node && node.data.type === 'choice';
        });

        const choiceCount = validChoices.length;
        const choiceWidth = GRAPH_VISUAL_CONFIG.choiceNode.width;
        const choiceGap = 20;
        const totalWidth = choiceCount * choiceWidth + (choiceCount - 1) * choiceGap;
        const storyCenter = pos.x + GRAPH_VISUAL_CONFIG.storyNode.width / 2;
        const startX = storyCenter - totalWidth / 2;

        validChoices.forEach((choiceId, i) => {
          const choiceOriginal = originalNodeMap.get(choiceId)!;
          const choiceX = startX + i * (choiceWidth + choiceGap);

          resultNodes.push({
            ...choiceOriginal,
            position: { x: choiceX, y: CHOICE_Y },
            data: { ...choiceOriginal.data, distanceFromCenter: graphDist },
          });

          resultEdges.push({
            id: `row-${storyId}-${choiceId}`,
            source: storyId,
            target: choiceId,
            type: 'smoothstep',
          });
        });
      }
    }

    return { nodes: resultNodes, edges: resultEdges };
  }, [graph, engineResult, centeredNodeId, storyPositions]);

  return {
    nodes,
    edges,
    maxDepth: engineResult?.maxDepth ?? 0,
    centeredNodeId,
    onViewportChange,
  };
}
