/**
 * Global application context
 * Provides shared state for username, corpus, persona, and theme
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useLocalStorage } from '@/hooks/useLocalStorage';
import { listPersonas } from '@/services/api';
import type { PersonaInfo, ColorTheme } from '@/types';

interface AppContextType {
  // User state
  username: string;
  setUsername: (username: string) => void;
  
  // Corpus state
  corpus: string;
  setCorpus: (corpus: string) => void;
  
  // Persona state
  persona: string;
  setPersona: (persona: string) => void;
  personas: PersonaInfo[];
  personasLoading: boolean;
  personasError: string | null;
  
  // Theme (derived from selected persona)
  theme: ColorTheme | null;
}

const defaultTheme: ColorTheme = {
  background: 'bg-gray-900',
  button: 'bg-blue-600',
  button_hover: 'hover:bg-blue-500',
  input: 'bg-gray-800',
  ring: 'focus:ring-blue-500',
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  // Persistent state via localStorage
  const [username, setUsername] = useLocalStorage<string>('storyteller_username', '');
  const [corpus, setCorpus] = useLocalStorage<string>('storyteller_corpus', 'mahabharata');
  
  // Debug: Log username changes
  useEffect(() => {
    console.log('[AppContext] Username changed to:', username);
  }, [username]);
  
  // Persona state (not persisted - user can select each session)
  const [persona, setPersona] = useState<string>('Grandmother');
  const [personas, setPersonas] = useState<PersonaInfo[]>([]);
  const [personasLoading, setPersonasLoading] = useState<boolean>(true);
  const [personasError, setPersonasError] = useState<string | null>(null);
  
  // Load personas from API on mount
  useEffect(() => {
    async function loadPersonas() {
      try {
        setPersonasLoading(true);
        setPersonasError(null);
        const data = await listPersonas();
        setPersonas(data);
        
        // If current persona doesn't exist, default to first persona
        if (data.length > 0 && !data.find((p) => p.name === persona)) {
          setPersona(data[0].name);
        }
      } catch (error) {
        console.error('Failed to load personas:', error);
        setPersonasError('Failed to load personas');
      } finally {
        setPersonasLoading(false);
      }
    }
    
    loadPersonas();
  }, []); // Only run on mount
  
  // Compute theme from selected persona
  const theme = personas.find((p) => p.name === persona)?.color_theme || defaultTheme;
  
  const value: AppContextType = {
    username,
    setUsername,
    corpus,
    setCorpus,
    persona,
    setPersona,
    personas,
    personasLoading,
    personasError,
    theme,
  };
  
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

/**
 * Hook to use the app context
 */
export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

