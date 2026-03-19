import React from 'react';

interface ParagraphCountSliderProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

const WORD_TARGETS: Record<number, number> = {
  1: 200, 2: 400, 3: 600, 4: 800,
  5: 1000, 6: 1200, 7: 1400, 8: 1600,
};

export const ParagraphCountSlider: React.FC<ParagraphCountSliderProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <input
          type="range"
          min={1}
          max={8}
          step={1}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          disabled={disabled}
          className="w-full accent-white cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
        />
      </div>
      <p className="text-xs text-white/60">
        {value} paragraph{value !== 1 ? 's' : ''} (~{WORD_TARGETS[value]} words)
      </p>
    </div>
  );
};

export default ParagraphCountSlider;
