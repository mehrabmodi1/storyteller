import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import type { ReactFlowNodeData } from '@/types/graph.types';
import { DEFAULT_THEME } from '@/context/AppContext';
import { GRAPH_VISUAL_CONFIG } from '@/config/graph.config';

type ChoiceNodeData = ReactFlowNodeData & {
  choiceProps?: {
    isActive?: boolean;
    editablePrompt?: string;
    onChangePrompt?: (value: string) => void;
    onSubmitPrompt?: (text?: string) => void;
    onCancel?: () => void;
    onSelectChoice?: (nodeId: string) => void;
  };
};

function getRingClass(themeRing?: string | null) {
  if (!themeRing) {
    return 'ring-sky-400';
  }
  return themeRing.replace('focus:', '');
}

export const ChoiceNode: React.FC<NodeProps<ChoiceNodeData>> = ({ id, data, selected }) => {
  const {
    isActive = false,
    editablePrompt,
    onChangePrompt: _onChangePrompt,
    onSubmitPrompt,
    onCancel,
    onSelectChoice,
  } = data.choiceProps || {};

  const theme = data.theme ?? DEFAULT_THEME;
  const background = theme.input ?? 'bg-slate-900';
  const accent = theme.button ?? 'bg-sky-600';
  const ringClass = getRingClass(theme.ring);

  // Local state for textarea to avoid re-render cascade from parent useMemo
  const [localPrompt, setLocalPrompt] = useState(editablePrompt ?? data.label);
  const localPromptRef = useRef(localPrompt);
  localPromptRef.current = localPrompt;
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Re-initialize local state when the node becomes active
  useEffect(() => {
    if (isActive) {
      setLocalPrompt(editablePrompt ?? data.label);
    }
  }, [isActive]);

  // Move cursor to end of textarea when it becomes active
  useEffect(() => {
    if (isActive && textareaRef.current) {
      const len = textareaRef.current.value.length;
      textareaRef.current.setSelectionRange(len, len);
    }
  }, [isActive]);

  const handleLocalChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setLocalPrompt(e.target.value);
  }, []);

  const handleLocalSubmit = useCallback(() => {
    // Pass the current local text directly to submit, bypassing stale parent state
    onSubmitPrompt?.(localPromptRef.current);
  }, [onSubmitPrompt]);

  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    // Stop all keystrokes from bubbling to the parent <button>, which would
    // otherwise treat Space/Enter as a button click and re-trigger onSelectChoice.
    e.stopPropagation();
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleLocalSubmit();
    }
  };

  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} className="!bg-white/60" />
      <button
        type="button"
        onClick={() => onSelectChoice?.(id)}
        className={`text-left rounded-2xl border ${
          selected ? `ring-2 ${ringClass} border-transparent shadow-lg shadow-sky-500/30` : 'border-slate-700'
        } ${background} text-white p-4 flex flex-col gap-3 focus:outline-none transition-all`}
        style={{
          width: GRAPH_VISUAL_CONFIG.choiceNode.width,
          height: isActive ? GRAPH_VISUAL_CONFIG.choiceNode.height * 1.4 : GRAPH_VISUAL_CONFIG.choiceNode.height,
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

        {isActive ? (
          <>
            <div className="flex-1">
              <textarea
                ref={textareaRef}
                id={`choice-prompt-${id}`}
                name={`choice-prompt-${id}`}
                value={localPrompt}
                onChange={handleLocalChange}
                onKeyDown={handleKeyDown}
                className="w-full rounded-xl bg-white/10 border border-white/20 px-3 py-2 text-sm text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/40 resize-none"
                rows={4}
                placeholder="Edit or write your follow-up prompt..."
                autoFocus
              />
            </div>
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onCancel?.(); }}
                className="text-xs text-white/70 hover:text-white underline"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); handleLocalSubmit(); }}
                className="text-sm px-3 py-2 rounded-lg font-semibold bg-white text-gray-900 hover:bg-gray-200"
              >
                Continue Journey
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto text-sm text-white/80">
              {data.story ? data.story : <span className="italic text-white/50">Prompt only</span>}
            </div>
            <div className="text-xs text-white/60">
              {data.timestamp ? new Date(data.timestamp).toLocaleString() : 'Timestamp unknown'}
            </div>
            <div className="text-xs text-white/70">Press Enter to generate follow-up</div>
          </>
        )}
      </button>
      <Handle type="source" position={Position.Bottom} className="!bg-white/60" />
    </div>
  );
};



