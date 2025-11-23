/**
 * Journey (saved graph) selector dropdown
 * Uses BaseDropdown to eliminate code duplication
 */

import { useEffect, useState } from 'react';
import { BaseDropdown } from './BaseDropdown';
import { useApp } from '@/context/AppContext';
import { listGraphs, loadGraph } from '@/services/api';
import type { JourneyMeta } from '@/types';

interface JourneyDropdownProps {
  onJourneyLoad?: (journey: JourneyMeta) => void;
}

export function JourneyDropdown({ onJourneyLoad }: JourneyDropdownProps) {
  const { username, theme } = useApp();
  const [journeys, setJourneys] = useState<JourneyMeta[]>([]);
  const [selectedJourney, setSelectedJourney] = useState<JourneyMeta | null>(null);
  const [loading, setLoading] = useState(false);
  
  console.log('[JourneyDropdown] Rendering with username:', username, 'journeys:', journeys.length);
  
  // Load journeys when username changes
  useEffect(() => {
    async function loadJourneys() {
      console.log('[JourneyDropdown] Username changed:', username);
      
      if (!username) {
        console.log('[JourneyDropdown] No username, clearing journeys');
        setJourneys([]);
        return;
      }
      
      try {
        console.log('[JourneyDropdown] Loading journeys for:', username);
        setLoading(true);
        const response = await listGraphs(username);
        console.log('[JourneyDropdown] Received journeys:', response.journeys.length);
        setJourneys(response.journeys);
      } catch (error) {
        console.error('[JourneyDropdown] Failed to load journeys:', error);
      } finally {
        setLoading(false);
      }
    }
    
    loadJourneys();
    setSelectedJourney(null);
  }, [username]);
  
  const handleSelect = async (journey: JourneyMeta) => {
    try {
      const response = await loadGraph({
        username: journey.username,
        graph_id: journey.graph_id,
      });
      
      if (response.success) {
        setSelectedJourney(journey);
        onJourneyLoad?.(journey);
      } else {
        console.error('Failed to load journey:', response.error);
        alert(`Failed to load journey: ${response.error}`);
      }
    } catch (error) {
      console.error('Error loading journey:', error);
      alert('Failed to load journey');
    }
  };
  
  if (!username) {
    return (
      <div className={`w-64 border border-gray-700 rounded-md p-2 ${theme?.input || 'bg-gray-800'}`}>
        <span className="text-gray-500">Select username first</span>
      </div>
    );
  }
  
  if (loading) {
    return (
      <div className={`w-64 border border-gray-700 rounded-md p-2 ${theme?.input || 'bg-gray-800'}`}>
        <span className="text-gray-400">Loading journeys...</span>
      </div>
    );
  }
  
  if (journeys.length === 0) {
    return (
      <div className={`w-64 border border-gray-700 rounded-md p-2 ${theme?.input || 'bg-gray-800'}`}>
        <span className="text-gray-500">No saved journeys</span>
      </div>
    );
  }
  
  return (
    <BaseDropdown<JourneyMeta>
      items={journeys}
      selectedItem={selectedJourney}
      onSelect={handleSelect}
      getLabel={(item) => item.initial_prompt.slice(0, 40) + (item.initial_prompt.length > 40 ? '...' : '')}
      getKey={(item) => item.graph_id}
      renderTooltip={(item) => (
        <div>
          <p className="font-semibold mb-1 text-xs text-gray-400">
            {new Date(item.timestamp).toLocaleString()}
          </p>
          <p className="text-sm mb-2">{item.initial_prompt}</p>
          <div className="text-xs text-gray-400 space-y-1">
            <p>Persona: {item.persona}</p>
            <p>Corpus: {item.corpus_display_name || item.corpus_name}</p>
            <p>Chapters: {item.num_story_nodes}</p>
          </div>
        </div>
      )}
      theme={theme}
      placeholder="Load Journey"
      width="w-64"
    />
  );
}

