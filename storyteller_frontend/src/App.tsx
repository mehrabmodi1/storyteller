import { useMemo, useState } from 'react';
import { AppProvider, useApp, DEFAULT_THEME } from '@/context/AppContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { PersonaDropdown } from '@/components/dropdowns/PersonaDropdown';
import { CorpusDropdown } from '@/components/dropdowns/CorpusDropdown';
import { UsernameDropdown } from '@/components/dropdowns/UsernameDropdown';
import { JourneyDropdown } from '@/components/dropdowns/JourneyDropdown';
import { GraphDebugPanel } from '@/components/debug';
import { GraphView } from '@/components/graph/GraphView';
import type { ColorTheme, GraphData, JourneyMeta } from '@/types';
import { transformGraphData, TransformedGraph } from '@/utils/graphTransform';
import { useELKLayout } from '@/hooks/useELKLayout';

function AppContent() {
  const { persona, theme, personas, personasLoading } = useApp();
  const [rawGraph, setRawGraph] = useState<GraphData | null>(null);
  const [journeyPersona, setJourneyPersona] = useState<string | null>(null);
  const [promptInput, setPromptInput] = useState('');
  const [isStartingJourney, setIsStartingJourney] = useState(false);
  const [showDebug, setShowDebug] = useState(false);

  const journeyPersonaTheme = useMemo<ColorTheme>(() => {
    if (!journeyPersona) {
      return DEFAULT_THEME;
    }
    return (
      personas.find((p) => p.name === journeyPersona)?.color_theme ??
      DEFAULT_THEME
    );
  }, [journeyPersona, personas]);

  const transformedGraph = useMemo<TransformedGraph | null>(() => {
    if (!rawGraph) {
      return null;
    }
    return transformGraphData(rawGraph, {
      personaName: journeyPersona,
      personaTheme: journeyPersonaTheme,
    });
  }, [rawGraph, journeyPersona, journeyPersonaTheme]);
  const { layout: layoutGraph } = useELKLayout(transformedGraph);

  const handleJourneyLoad = (journey: JourneyMeta) => {
    setJourneyPersona(journey.persona);
  };

  const handleStartNewJourney = async () => {
    if (!promptInput.trim()) {
      return;
    }
    setIsStartingJourney(true);
    try {
      console.log('[StartJourney] TODO: trigger new story', {
        prompt: promptInput,
        persona,
        corpus: journeyPersona,
      });
    } finally {
      setIsStartingJourney(false);
    }
  };

  return (
    <div
      className={`min-h-screen transition-colors ${
        theme?.background || 'bg-gray-900'
      } text-white`}
    >
      <div className="container mx-auto px-4 py-8 space-y-8">
        <div className="space-y-4">
          <h1 className="text-3xl font-semibold text-white">Story Controls</h1>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-white/70 mb-1">Username</p>
                <UsernameDropdown />
              </div>
              <div>
                <p className="text-sm text-white/70 mb-1">Persona</p>
                {personasLoading ? (
                  <div className="text-gray-400">Loading personas...</div>
                ) : (
                  <PersonaDropdown />
                )}
              </div>
              <div>
                <p className="text-sm text-white/70 mb-1">Corpus</p>
                <CorpusDropdown />
              </div>
              <div>
                <p className="text-sm text-white/70 mb-1">Load Journey</p>
                <JourneyDropdown
                  onJourneyLoad={handleJourneyLoad}
                  onGraphLoaded={setRawGraph}
                />
              </div>
            </div>
            <div className="flex flex-col md:flex-row gap-4 items-stretch">
              <div className="flex-1">
                <p className="text-sm text-white/70 mb-1">Start a new journey</p>
                <input
                  type="text"
                  value={promptInput}
                  onChange={(e) => setPromptInput(e.target.value)}
                  placeholder="Enter an opening prompt..."
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
                />
              </div>
              <button
                type="button"
                onClick={handleStartNewJourney}
                disabled={!promptInput.trim() || isStartingJourney}
                className={`md:w-56 px-6 py-3 rounded-xl font-semibold transition flex items-center justify-center ${
                  !promptInput.trim() || isStartingJourney
                    ? 'bg-white/20 text-white/60 cursor-not-allowed'
                    : 'bg-white text-gray-900 hover:bg-gray-200'
                }`}
              >
                {isStartingJourney ? 'Starting…' : 'Start New Journey'}
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-3xl font-semibold">Graph Visualization</h2>
          <GraphView graph={layoutGraph} />
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => setShowDebug((prev) => !prev)}
              className="text-sm text-white/70 underline hover:text-white"
            >
              {showDebug ? 'Hide debug info' : 'Show debug info'}
            </button>
          </div>
        </div>

        {showDebug && (
          <div className="bg-black/30 rounded-2xl border border-white/10 p-4">
            <GraphDebugPanel
              rawGraph={rawGraph}
              transformed={transformedGraph}
              layoutGraph={layoutGraph}
            />
          </div>
        )}
      </div>
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </ErrorBoundary>
  )
}

export default App

