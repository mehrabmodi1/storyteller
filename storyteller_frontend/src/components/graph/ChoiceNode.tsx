import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import type { ReactFlowNodeData } from '@/types/graph.types';
import { DEFAULT_THEME } from '@/context/AppContext';
import { GRAPH_VISUAL_CONFIG } from '@/config/graph.config';

interface ChoiceNodeProps extends NodeProps<ReactFlowNodeData> {
  onSelectChoice?: (nodeId: string) => void;
}

function getRingClass(themeRing?: string | null) {
  if (!themeRing) {
    return 'ring-sky-400';
  }
  return themeRing.replace('focus:', '');
}

export const ChoiceNode: React.FC<ChoiceNodeProps> = ({ id, data, selected, onSelectChoice }) => {
  const theme = data.theme ?? DEFAULT_THEME;
  const background = theme.input ?? 'bg-slate-900';
  const accent = theme.button ?? 'bg-sky-600';
  const ringClass = getRingClass(theme.ring);

  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} className="!bg-white/60" />
      <button
        type="button"
        onClick={() => onSelectChoice?.(id)}
        className={`text-left rounded-2xl border ${
          selected ? `ring-2 ${ringClass} border-transparent shadow-lg shadow-sky-500/30` : 'border-slate-700'
        } ${background} text-white p-4 flex flex-col gap-2 focus:outline-none transition-all`}
        style={{
          width: GRAPH_VISUAL_CONFIG.choiceNode.width,
          height: GRAPH_VISUAL_CONFIG.choiceNode.height,
        }}
      >
        <div className="flex items-center justify-between text-xs uppercase tracking-wide text-white/80">
          <span>Choice</span>
          {data.persona ? (
            <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${accent} text-white`}>
              {data.persona}
            </span>
          ) : null}
        </div>
        <div className="text-base font-semibold line-clamp-1">{data.label}</div>
        <div className="flex-1 overflow-y-auto text-sm text-white/80">
          {data.story ? data.story : <span className="italic text-white/50">Prompt only</span>}
        </div>
        <div className="text-xs text-white/60">
          {data.timestamp ? new Date(data.timestamp).toLocaleString() : 'Timestamp unknown'}
        </div>
        <div className="text-xs text-white/70">Press Enter to generate follow-up</div>
      </button>
      <Handle type="source" position={Position.Bottom} className="!bg-white/60" />
    </div>
  );
};



