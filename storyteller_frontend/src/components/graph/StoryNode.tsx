import React from 'react';
import type { NodeProps } from 'reactflow';
import type { ReactFlowNodeData } from '@/types/graph.types';
import { DEFAULT_THEME } from '@/context/AppContext';
import { GRAPH_VISUAL_CONFIG } from '@/config/graph.config';

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
      className={`rounded-2xl border ${
        selected ? `ring-2 ${ringClass} shadow-lg shadow-amber-500/30 border-transparent` : 'border-slate-700'
      } ${background} text-white p-4 flex flex-col gap-3 transition-all`}
      style={{
        width: GRAPH_VISUAL_CONFIG.storyNode.width,
        height: GRAPH_VISUAL_CONFIG.storyNode.height,
      }}
    >
      <div className="flex items-center justify-between text-xs uppercase tracking-wide text-white/80">
        <span>Story Chapter</span>
        {data.persona ? (
          <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${accent} text-white`}>
            {data.persona}
          </span>
        ) : null}
      </div>
      <div className="text-lg font-semibold line-clamp-1">{data.label}</div>
      <div className="flex-1 flex flex-col gap-2 min-h-0">
        <div className="flex-1 overflow-y-auto text-sm text-white/80 whitespace-pre-line pr-1">
          {data.story ? (
            data.story
          ) : (
            <span className="italic text-white/50">Story content unavailable.</span>
          )}
        </div>
        <div
          className={`h-24 rounded-xl border ${inputBg.replace('bg-', 'border-')} overflow-hidden`}
        >
          {data.image_url ? (
            <img
              src={data.image_url}
              alt={data.label}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-xs uppercase tracking-widest text-white/40 bg-white/5 border border-dashed border-white/20 rounded-xl">
              No image
            </div>
          )}
        </div>
      </div>
      <div className="text-xs text-white/60">
        {data.timestamp ? new Date(data.timestamp).toLocaleString() : 'Timestamp unknown'}
      </div>
    </div>
  );
};



