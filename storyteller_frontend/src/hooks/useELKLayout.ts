import { useEffect, useMemo, useRef, useState } from 'react';
import ELK from 'elkjs/lib/elk.bundled.js';
import type { XYPosition } from 'reactflow';
import type { TransformedGraph } from '@/utils/graphTransform';
import type { StoryReactFlowNode, StoryReactFlowEdge } from '@/types/graph.types';
import { buildElkGraph } from '@/utils/elkConfig';

interface LayoutResult {
  nodes: StoryReactFlowNode[];
  edges: StoryReactFlowEdge[];
  latestStoryNodeId?: string;
  latestStoryTimestamp?: string;
}

const elk = new ELK();

export function useELKLayout(graph: TransformedGraph | null) {
  const [layout, setLayout] = useState<LayoutResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const positionsRef = useRef<Map<string, XYPosition>>(new Map());

  const nodeKey = useMemo(() => {
    if (!graph) return null;
    return `${graph.nodes.map((n) => n.id).join('|')}|${graph.edges
      .map((e) => `${e.source}->${e.target}`)
      .join('|')}`;
  }, [graph]);

  useEffect(() => {
    if (!graph || !graph.nodes.length) {
      setLayout(null);
      positionsRef.current.clear();
      return;
    }

    const layoutTarget = graph;
    let cancelled = false;

    async function runLayout() {
      setIsRunning(true);
      try {
        const elkGraph = buildElkGraph(layoutTarget);
        const result = await elk.layout(elkGraph);

        if (cancelled) {
          return;
        }

        const childPositions = new Map<string, XYPosition>();
        result.children?.forEach((child) => {
          if (typeof child.x === 'number' && typeof child.y === 'number') {
            childPositions.set(child.id, { x: child.x, y: child.y });
          }
        });

        const updatedPositions = new Map(positionsRef.current);

        // Remove cached positions for nodes that no longer exist
        Array.from(updatedPositions.keys()).forEach((nodeId) => {
          if (!layoutTarget.nodes.find((node) => node.id === nodeId)) {
            updatedPositions.delete(nodeId);
          }
        });

        const layoutedNodes = layoutTarget.nodes.map((node) => {
          const existing = updatedPositions.get(node.id);
          const suggested = childPositions.get(node.id);

          const finalPosition: XYPosition =
            existing ??
            suggested ?? {
              x: 0,
              y: 0,
            };

          // Cache the position for future layouts
          updatedPositions.set(node.id, finalPosition);

          return {
            ...node,
            position: finalPosition,
          };
        });

        positionsRef.current = updatedPositions;

        setLayout({
          nodes: layoutedNodes,
          edges: layoutTarget.edges,
          latestStoryNodeId: layoutTarget.latestStoryNodeId,
          latestStoryTimestamp: layoutTarget.latestStoryTimestamp,
        });
      } catch (error) {
        console.error('[useELKLayout] Failed to compute layout', error);
      } finally {
        if (!cancelled) {
          setIsRunning(false);
        }
      }
    }

    runLayout();

    return () => {
      cancelled = true;
    };
  }, [graph, nodeKey]);

  return {
    layout,
    isRunning,
  };
}


