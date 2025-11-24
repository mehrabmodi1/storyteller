/**
 * Corpus selector dropdown
 * Uses BaseDropdown to eliminate code duplication
 */

import React, { useEffect, useState } from 'react';
import { BaseDropdown } from './BaseDropdown';
import { useApp } from '@/context/AppContext';
import { listCorpuses } from '@/services/api';
import type { CorpusInfo } from '@/types';

export function CorpusDropdown() {
  const { corpus, setCorpus, theme } = useApp();
  const [corpuses, setCorpuses] = useState<CorpusInfo[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    async function loadCorpuses() {
      try {
        const data = await listCorpuses();
        setCorpuses(data.filter((c) => c.is_active));
      } catch (error) {
        console.error('Failed to load corpuses:', error);
      } finally {
        setLoading(false);
      }
    }
    loadCorpuses();
  }, []);
  
  const selectedCorpus = corpuses.find((c) => c.name === corpus) || null;
  
  if (loading) {
    return (
      <div className={`w-48 border border-gray-700 rounded-md p-2 ${theme?.input || 'bg-gray-800'}`}>
        <span className="text-gray-400">Loading...</span>
      </div>
    );
  }
  
  return (
    <BaseDropdown<CorpusInfo>
      items={corpuses}
      selectedItem={selectedCorpus}
      onSelect={(item) => setCorpus(item.name)}
      getLabel={(item) => item.display_name}
      getKey={(item) => item.name}
      renderTooltip={(item) => (
        <div>
          <p className="font-semibold mb-1">{item.display_name}</p>
          <p className="text-gray-300 text-xs mb-2">{item.description}</p>
          <p className="text-gray-400 text-xs">{item.chunk_count.toLocaleString()} chunks</p>
        </div>
      )}
      theme={theme}
      placeholder="Select Corpus"
      width="w-48"
    />
  );
}

