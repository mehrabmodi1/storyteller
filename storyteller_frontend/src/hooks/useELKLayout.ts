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
  const initialLayoutDoneRef = useRef<boolean>(false);

  const nodeKey = useMemo(() => {
    if (!graph) return null;
    return `${graph.nodes.length}:${graph.edges.length}:${graph.latestStoryNodeId ?? ''}`;
  }, [graph?.nodes.length, graph?.edges.length, graph?.latestStoryNodeId]);

  useEffect(() => {
    if (!graph || !graph.nodes.length) {
      setLayout(null);
      initialLayoutDoneRef.current = false;
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

        const isInitialLayout = !initialLayoutDoneRef.current;

        const layoutedNodes = layoutTarget.nodes.map((node) => ({
          ...node,
          position: childPositions.get(node.id) ?? { x: 0, y: 0 },
          style: isInitialLayout ? node.style : { ...node.style, transition: 'transform 0.4s ease' },
        }));

        initialLayoutDoneRef.current = true;

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
  }, [nodeKey]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    layout,
    isRunning,
  };
}
