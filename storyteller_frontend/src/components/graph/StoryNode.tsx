import React from 'react';
import type { NodeProps } from 'reactflow';
import type { ReactFlowNodeData } from '@/types/graph.types';
import { DEFAULT_THEME } from '@/context/AppContext';

function getRingClass(themeRing?: string | null) {
  if (!themeRing) {
    return 'ring-amber-500';
  }
  return themeRing.replace('focus:', '');
}

export const StoryNode: React.FC<NodeProps<ReactFlowNodeData>> = ({ data, selected }) => {
  const theme = data.theme ?? DEFAULT_THEME;
  const background = theme.background ?? 'bg-slate-900';
  const accent = theme.button ?? 'bg-amber-600';
  const inputBg = theme.input ?? 'bg-slate-800';
  const ringClass = getRingClass(theme.ring);

  return (
    <div
      className={`w-[320px] rounded-2xl border ${
        selected ? `ring-2 ${ringClass} shadow-lg shadow-amber-500/30 border-transparent` : 'border-slate-700'
      } ${background} text-white p-4 space-y-3 transition-all`}
    >
      <div className="flex items-center justify-between text-xs uppercase tracking-wide text-white/80">
        <span>Story Chapter</span>
        {data.persona ? (
          <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${accent} text-white`}>
            {data.persona}
          </span>
        ) : null}
      </div>
      <div className="text-lg font-semibold">{data.label}</div>
      {data.story ? (
        <p className="text-sm text-white/80 whitespace-pre-line line-clamp-6">{data.story}</p>
      ) : (
        <p className="text-sm text-white/50 italic">Story content unavailable.</p>
      )}
      {data.image_url ? (
        <img
          src={data.image_url}
          alt={data.label}
          className={`w-full h-32 object-cover rounded-xl border ${inputBg.replace('bg-', 'border-')}`}
        />
      ) : null}
      <div className="text-xs text-white/60">
        {data.timestamp ? new Date(data.timestamp).toLocaleString() : 'Timestamp unknown'}
      </div>
    </div>
  );
};



