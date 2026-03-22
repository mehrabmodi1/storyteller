import React from 'react';

interface ReadingPanelProps {
  open: boolean;
  isStreaming: boolean;
  text: string;
  title?: string;
  themeInputClass?: string;
  onClose: () => void;
}

/**
 * Floating reader for live story tokens.
 * - Centered modal, nearly opaque.
 * - Non-blocking backdrop (clicks pass through outside the panel).
 * - Manual scroll; no auto-scroll to preserve reading position.
 */
export const ReadingPanel: React.FC<ReadingPanelProps> = ({
  open,
  isStreaming,
  text,
  title = 'Story',
  themeInputClass,
  onClose,
}) => {
  if (!open) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed inset-0 flex items-center justify-center z-50">
      <div
        className={`pointer-events-auto w-full max-w-3xl max-h-[70vh] rounded-2xl border border-white/10 shadow-2xl overflow-hidden ${
          themeInputClass || 'bg-slate-900'
        } bg-opacity-95`}
      >
        <div className={`flex items-center justify-between px-4 py-3 border-b border-white/10 ${themeInputClass || ''}`}>
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold">{title}</h3>
            <span
              className={`text-xs px-2 py-1 rounded-full ${
                isStreaming ? 'bg-green-500/20 text-green-200' : 'bg-white/10 text-white/80'
              }`}
            >
              {isStreaming ? 'Streaming…' : 'Complete'}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-white/70 hover:text-white text-sm px-3 py-1 rounded-lg border border-white/20 hover:border-white/40"
          >
            Close
          </button>
        </div>
        <div className="px-4 py-4 overflow-y-auto text-base leading-relaxed whitespace-pre-wrap max-h-[60vh]">
          {text || 'Awaiting story...'}
        </div>
      </div>
    </div>
  );
};
