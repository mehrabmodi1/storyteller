'use client';

import { useState, useRef, useEffect } from 'react';

interface ColorTheme {
  background: string;
  button: string;
  button_hover: string;
  input: string;
  ring: string;
}

interface JourneyMeta {
  graph_id: string;
  username: string;
  timestamp: string;
  initial_prompt: string;
  initial_snippet: string;
  last_prompt: string;
  last_snippet: string;
  persona: string;
  num_story_nodes: number;
  last_story_timestamp: string;
}

interface JourneyDropdownProps {
  username: string;
  onJourneySelect: (graphId: string) => void;
  disabled?: boolean;
  theme: ColorTheme | null;
}

export const JourneyDropdown = ({
  username,
  onJourneySelect,
  disabled,
  theme,
}: JourneyDropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [journeys, setJourneys] = useState<JourneyMeta[]>([]);
  const [isLoading, setIsLoading] = useState(false);
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

  // Fetch journeys when username changes
  useEffect(() => {
    if (username) {
      fetchJourneys();
    }
  }, [username]);

  // Fetch journeys when dropdown opens (to allow manual refresh)
  useEffect(() => {
    if (isOpen && username) {
      fetchJourneys();
    }
  }, [isOpen, username]);

  const fetchJourneys = async () => {
    if (!username) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/list_graphs?username=${encodeURIComponent(username)}`);
      if (response.ok) {
        const data = await response.json();
        setJourneys(data);
      } else {
        console.error('Failed to fetch journeys');
        setJourneys([]);
      }
    } catch (error) {
      console.error('Error fetching journeys:', error);
      setJourneys([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelect = (graphId: string) => {
    onJourneySelect(graphId);
    setIsOpen(false);
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp.replace(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6'));
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return timestamp;
    }
  };

  const getDisplayText = (journey: JourneyMeta) => {
    let snippet = '';
    if (journey.last_snippet && journey.last_snippet.length > 0) {
      snippet = journey.last_snippet;
    } else if (journey.last_prompt && journey.last_prompt.length > 0) {
      snippet = journey.last_prompt;
    } else if (journey.initial_prompt) {
      snippet = journey.initial_prompt;
    } else {
      return '(No prompt)';
    }
    // Replace underscores with spaces and trim
    snippet = snippet.replace(/_/g, ' ').trim();
    // Truncate to 25 chars and always append '...'
    return snippet.length > 25 ? snippet.substring(0, 25) + '...' : snippet + '...';
  };

  return (
    <div className="relative w-48" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || !username}
        className={`w-full border border-gray-700 rounded-md p-2 flex justify-between items-center focus:outline-none focus:ring-2 disabled:cursor-not-allowed text-sm ${
          theme ? `${theme.input} ${theme.ring}` : 'bg-gray-800 focus:ring-blue-500'
        }`}
      >
        <span className="truncate">
          {!username ? 'Select User First' : journeys.length === 0 ? 'No Journeys' : `${journeys.length} Journeys`}
        </span>
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
          {isLoading ? (
            <div className="p-4 text-center text-sm text-gray-400">
              Loading journeys...
            </div>
          ) : journeys.length === 0 ? (
            <div className="p-4 text-center text-sm text-gray-400">
              No journeys found for {username}
            </div>
          ) : (
            <ul>
              {journeys.map((journey) => (
                <li key={journey.graph_id} className="group relative">
                  <button
                    onClick={() => handleSelect(journey.graph_id)}
                    className={`w-full text-left px-4 py-2 text-sm ${
                      theme ? theme.button_hover : 'hover:bg-gray-700'
                    }`}
                  >
                    <div className="font-medium">{getDisplayText(journey)}</div>
                    <div className="text-xs text-gray-400">
                      {formatTimestamp(journey.timestamp)} • {journey.num_story_nodes} chapters
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
                        <span className="font-bold">Initial Prompt:</span>
                        <p className="text-xs mt-1">{journey.initial_prompt}</p>
                      </div>
                      <div>
                        <span className="font-bold">Last Prompt:</span>
                        <p className="text-xs mt-1">{journey.last_prompt}</p>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span>Persona: {journey.persona}</span>
                        <span>Nodes: {journey.num_story_nodes}</span>
                      </div>
                      <div className="text-xs text-gray-400">
                        Created: {formatTimestamp(journey.timestamp)}
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}; 