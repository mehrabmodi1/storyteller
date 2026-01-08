import { useEffect, useMemo, useState } from 'react';
import { AppProvider, useApp, DEFAULT_THEME } from '@/context/AppContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { PersonaDropdown } from '@/components/dropdowns/PersonaDropdown';
import { CorpusDropdown } from '@/components/dropdowns/CorpusDropdown';
import { UsernameDropdown } from '@/components/dropdowns/UsernameDropdown';
import { JourneyDropdown } from '@/components/dropdowns/JourneyDropdown';
import { GraphDebugPanel } from '@/components/debug';
import { GraphView } from '@/components/graph/GraphView';
import { ReadingPanel } from '@/components/ReadingPanel';
import type { ColorTheme, GraphData, JourneyMeta } from '@/types';
import { transformGraphData, TransformedGraph } from '@/utils/graphTransform';
import { useELKLayout } from '@/hooks/useELKLayout';
import { buildStreamStoryURL } from '@/services/api';
import { useSSE } from '@/hooks';

function AppContent() {
  const { persona, theme, personas, personasLoading, username, corpus, setCorpus } = useApp();
  const [rawGraph, setRawGraph] = useState<GraphData | null>(null);
  const [journeyPersona, setJourneyPersona] = useState<string | null>(null);
  const [promptInput, setPromptInput] = useState('');
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [showDebug, setShowDebug] = useState(false);
  const [showReadingPanel, setShowReadingPanel] = useState(false);
  const [currentStoryTitle, setCurrentStoryTitle] = useState<string>('Story');
  const [journeyError, setJourneyError] = useState<string | null>(null);
  const { graphData: streamingGraph, isStreaming, error: streamError, closeStream, streamingText } = useSSE(streamUrl);

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
    setCorpus(journey.corpus_name);
  };

  const handleStartNewJourney = () => {
    const trimmedPrompt = promptInput.trim();
    if (!trimmedPrompt) {
      return;
    }
    setJourneyError(null);
    setJourneyPersona(persona);
    setCurrentStoryTitle(trimmedPrompt);
    const sseUrl = buildStreamStoryURL({
      prompt: trimmedPrompt,
      new_journey: true,
      persona_name: persona,
      username,
      corpus_name: corpus,
    });
    setStreamUrl(sseUrl);
  };

  useEffect(() => {
    if (isStreaming) {
      setShowReadingPanel(true);
    }
  }, [isStreaming]);

  useEffect(() => {
    if (streamingGraph) {
      setRawGraph(streamingGraph);
      setPromptInput('');
      setStreamUrl(null);
      setJourneyError(null);
    }
  }, [streamingGraph]);

  useEffect(() => {
    if (streamError) {
      setJourneyError(streamError.message);
      setStreamUrl(null);
    }
  }, [streamError]);

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
                disabled={!promptInput.trim() || isStreaming}
                className={`md:w-56 px-6 py-3 rounded-xl font-semibold transition flex items-center justify-center ${
                  !promptInput.trim() || isStreaming
                    ? 'bg-white/20 text-white/60 cursor-not-allowed'
                    : 'bg-white text-gray-900 hover:bg-gray-200'
                }`}
              >
                {isStreaming ? 'Starting…' : 'Start New Journey'}
              </button>
            </div>
            {journeyError ? (
              <p className="text-sm text-red-400">
                Failed to start journey: {journeyError}
                {streamError ? (
                  <button
                    type="button"
                    onClick={closeStream}
                    className="ml-3 underline text-red-200 hover:text-red-100"
                  >
                    Dismiss
                  </button>
                ) : null}
              </p>
            ) : null}
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
              isStreaming={isStreaming}
              streamError={streamError}
              streamingText={streamingText}
            />
          </div>
        )}
        <ReadingPanel
          open={showReadingPanel && (isStreaming || !!streamingText)}
          isStreaming={isStreaming}
          text={streamingText}
          title={currentStoryTitle}
          themeInputClass={journeyPersonaTheme?.input}
          onClose={() => setShowReadingPanel(false)}
        />
      </div>
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <AppProvider>ßß
        <AppContent />
      </AppProvider>
    </ErrorBoundary>
  )
}

export default App

