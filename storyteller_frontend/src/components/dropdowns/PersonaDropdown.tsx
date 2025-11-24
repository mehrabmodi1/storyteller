/**
 * Persona selector dropdown
 * Uses BaseDropdown to eliminate code duplication
 */

import React from 'react';
import { BaseDropdown } from './BaseDropdown';
import { useApp } from '@/context/AppContext';
import type { PersonaInfo } from '@/types';

export function PersonaDropdown() {
  const { persona, setPersona, personas, theme } = useApp();
  
  const selectedPersona = personas.find((p) => p.name === persona) || null;
  
  return (
    <BaseDropdown<PersonaInfo>
      items={personas}
      selectedItem={selectedPersona}
      onSelect={(item) => setPersona(item.name)}
      getLabel={(item) => item.name}
      getKey={(item) => item.name}
      renderTooltip={(item) => (
        <div>
          <p className="font-semibold mb-1">{item.name}</p>
          <p className="text-gray-300 text-xs">{item.short_description}</p>
        </div>
      )}
      theme={theme}
      placeholder="Select Persona"
      width="w-48"
    />
  );
}

