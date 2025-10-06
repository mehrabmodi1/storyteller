'use client';

import { useState, useRef, useEffect } from 'react';

interface ColorTheme {
  background: string;
  button: string;
  button_hover: string;
  input: string;
  ring: string;
}

interface Corpus {
  name: string;
  display_name: string;
  description: string;
  is_active: boolean;
  chunk_count: number;
  last_processed: string | null;
  needs_rebuild: boolean;
  missing_components: string[];
}

interface CorpusDropdownProps {
  corpuses: Corpus[];
  selectedCorpus: string;
  onCorpusChange: (corpusName: string) => void;
  disabled?: boolean;
  theme: ColorTheme | null;
}

export const CorpusDropdown = ({
  corpuses,
  selectedCorpus,
  onCorpusChange,
  disabled,
  theme,
}: CorpusDropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (corpusName: string) => {
    onCorpusChange(corpusName);
    setIsOpen(false);
  };

  const getSelectedCorpusDisplayName = () => {
    const corpus = corpuses.find(c => c.name === selectedCorpus);
    return corpus ? corpus.display_name : 'Select Corpus';
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return timestamp;
    }
  };

  const getStatusIndicator = (corpus: Corpus) => {
    if (!corpus.is_active) {
      return <span className="text-red-400">●</span>; // Red dot for inactive
    }
    if (corpus.needs_rebuild) {
      return <span className="text-yellow-400">●</span>; // Yellow dot for needs rebuild
    }
    return <span className="text-green-400">●</span>; // Green dot for active
  };

  return (
    <div className="relative w-48" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full border border-gray-700 rounded-md p-2 flex justify-between items-center focus:outline-none focus:ring-2 disabled:cursor-not-allowed text-sm ${
          theme ? `${theme.input} ${theme.ring}` : 'bg-gray-800 focus:ring-blue-500'
        }`}
      >
        <span className="truncate">{getSelectedCorpusDisplayName()}</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'transform rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>

      {isOpen && (
        <div
          className={`absolute z-20 w-full mt-1 border border-gray-700 rounded-md shadow-lg max-h-64 overflow-y-auto ${
            theme ? theme.input : 'bg-gray-800'
          }`}
        >
          <ul>
            {corpuses.map((corpus) => (
              <li key={corpus.name} className="group relative">
                <button
                  onClick={() => handleSelect(corpus.name)}
                  className={`w-full text-left px-4 py-2 text-sm ${
                    theme ? theme.button_hover : 'hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {getStatusIndicator(corpus)}
                    <span className="font-medium">{corpus.display_name}</span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {corpus.chunk_count} chunks • {formatTimestamp(corpus.last_processed)}
                  </div>
                </button>
                
                {/* Tooltip on hover */}
                <div
                  className={`absolute left-full top-0 ml-2 w-80 p-3 border border-gray-700 rounded-md text-sm text-gray-300 opacity-0 group-hover:opacity-100 invisible group-hover:visible transition-opacity pointer-events-none z-30 ${
                    theme ? theme.input : 'bg-gray-900'
                  }`}
                >
                  <div className="space-y-2">
                    <div>
                      <span className="font-bold">{corpus.display_name}</span>
                      <p className="text-xs mt-1">{corpus.description}</p>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span>Status: {corpus.is_active ? 'Active' : 'Inactive'}</span>
                      <span>Chunks: {corpus.chunk_count}</span>
                    </div>
                    {corpus.needs_rebuild && (
                      <div className="text-xs text-yellow-400">
                        Needs rebuild: {corpus.missing_components.join(', ')}
                      </div>
                    )}
                    <div className="text-xs text-gray-400">
                      Last processed: {formatTimestamp(corpus.last_processed)}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}; 