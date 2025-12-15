import React from 'react';
import type { NodeProps } from 'reactflow';
import type { ReactFlowNodeData } from '@/types/graph.types';
import { DEFAULT_THEME } from '@/context/AppContext';

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
    <button
      type="button"
      onClick={() => onSelectChoice?.(id)}
      className={`w-[260px] text-left rounded-2xl border ${
        selected ? `ring-2 ${ringClass} border-transparent shadow-lg shadow-sky-500/30` : 'border-slate-700'
      } ${background} text-white p-4 space-y-2 focus:outline-none transition-all`}
    >
      <div className="flex items-center justify-between text-xs uppercase tracking-wide text-white/80">
        <span>Choice</span>
        {data.persona ? (
          <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${accent} text-white`}>
            {data.persona}
          </span>
        ) : null}
      </div>
      <div className="text-base font-semibold">{data.label}</div>
      {data.story ? (
        <p className="text-sm text-white/80 line-clamp-4">{data.story}</p>
      ) : (
        <p className="text-sm text-white/50 italic">Prompt only</p>
      )}
      <div className="text-xs text-white/60">
        {data.timestamp ? new Date(data.timestamp).toLocaleString() : 'Timestamp unknown'}
      </div>
      <div className="text-xs text-white/70">Press Enter to generate follow-up</div>
    </button>
  );
};



