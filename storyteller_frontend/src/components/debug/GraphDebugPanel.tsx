import React from 'react';
import { GraphData } from '../../types';
import { TransformedGraph } from '../../utils/graphTransform';

interface GraphDebugPanelProps {
  rawGraph: GraphData | null;
  transformed: TransformedGraph | null;
  layoutGraph?: TransformedGraph | null;
}

const sectionClasses =
  'bg-slate-900/70 rounded-xl border border-slate-800 p-4 space-y-2 text-sm';

export const GraphDebugPanel: React.FC<GraphDebugPanelProps> = ({
  rawGraph,
  transformed,
  layoutGraph,
}) => {
  if (!rawGraph && !transformed && !layoutGraph) {
    return null;
  }

  return (
    <div className="space-y-4 mt-8" data-testid="graph-debug-panel">
      <h3 className="text-2xl font-semibold text-white">Graph Debug Panel</h3>

      <div className={sectionClasses}>
        <div className="text-xs uppercase tracking-wide text-slate-400">
          Raw Backend Graph
        </div>
        <pre className="overflow-auto text-slate-200 text-xs max-h-64">
          {JSON.stringify(rawGraph, null, 2)}
        </pre>
      </div>

      {layoutGraph ? (
        <div className={sectionClasses}>
          <div className="text-xs uppercase tracking-wide text-slate-400">
            Layout Result (ELK + Frozen Positions)
          </div>
          <pre className="overflow-auto text-slate-200 text-xs max-h-64">
            {JSON.stringify(layoutGraph, null, 2)}
          </pre>
        </div>
      ) : null}

      <div className={sectionClasses}>
        <div className="text-xs uppercase tracking-wide text-slate-400">
          ReactFlow Transformed Graph
        </div>
        <pre className="overflow-auto text-slate-200 text-xs max-h-64">
          {JSON.stringify(transformed, null, 2)}
        </pre>
      </div>

      {transformed?.latestStoryNodeId ? (
        <div className={sectionClasses}>
          <div className="text-xs uppercase tracking-wide text-slate-400">
            Latest Story Node
          </div>
          <div className="text-slate-200">
            <div>
              <span className="text-slate-400">Node ID:</span>{' '}
              {transformed.latestStoryNodeId}
            </div>
            <div>
              <span className="text-slate-400">Timestamp:</span>{' '}
              {transformed.latestStoryTimestamp ?? 'unknown'}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default GraphDebugPanel;


