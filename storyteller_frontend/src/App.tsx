import { AppProvider, useApp } from '@/context/AppContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { PersonaDropdown } from '@/components/dropdowns/PersonaDropdown'
import { CorpusDropdown } from '@/components/dropdowns/CorpusDropdown'
import { UsernameDropdown } from '@/components/dropdowns/UsernameDropdown'
import { JourneyDropdown } from '@/components/dropdowns/JourneyDropdown'

function AppContent() {
  const { username, corpus, persona, theme, personas, personasLoading } = useApp()

  return (
    <div className={`min-h-screen transition-colors ${theme?.background || 'bg-gray-900'} text-white`}>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4">
            Storyteller Frontend
          </h1>
          <p className="text-xl text-gray-300">
            Phase 2 - Components Testing
          </p>
        </div>

        {/* Status Card */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h2 className="text-2xl font-semibold text-green-400 mb-4">
              ✓ Components Ready to Test
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-300">
              <div>
                <h3 className="font-semibold mb-2">Infrastructure:</h3>
                <ul className="space-y-1 text-sm">
                  <li>✓ AppContext & Global State</li>
                  <li>✓ useLocalStorage Hook</li>
                  <li>✓ useSSE Hook</li>
                  <li>✓ API Client (11 endpoints)</li>
                  <li>✓ ErrorBoundary</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Components:</h3>
                <ul className="space-y-1 text-sm">
                  <li>✓ BaseDropdown (Generic)</li>
                  <li>✓ PersonaDropdown</li>
                  <li>✓ CorpusDropdown</li>
                  <li>✓ UsernameDropdown</li>
                  <li>✓ JourneyDropdown</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Dropdowns Demo */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-gray-800 rounded-lg shadow-lg p-8 border border-gray-700">
            <h2 className="text-2xl font-semibold mb-6">Interactive Components</h2>
            
            <div className="space-y-6">
              {/* Row 1: Username & Persona */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">
                    Username:
                  </label>
                  <UsernameDropdown />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">
                    Persona:
                  </label>
                  {personasLoading ? (
                    <div className="text-gray-400">Loading personas...</div>
                  ) : (
                    <PersonaDropdown />
                  )}
                </div>
              </div>

              {/* Row 2: Corpus & Journey */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">
                    Corpus:
                  </label>
                  <CorpusDropdown />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">
                    Load Journey:
                  </label>
                  <JourneyDropdown />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Current State Display */}
        <div className="max-w-4xl mx-auto mt-8">
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h3 className="text-xl font-semibold mb-4">Current State (from AppContext)</h3>
            <div className="space-y-2 text-sm font-mono">
              <div className="flex gap-4">
                <span className="text-gray-400">Username:</span>
                <span className="text-green-400">{username || '(none)'}</span>
              </div>
              <div className="flex gap-4">
                <span className="text-gray-400">Persona:</span>
                <span className="text-green-400">{persona}</span>
              </div>
              <div className="flex gap-4">
                <span className="text-gray-400">Corpus:</span>
                <span className="text-green-400">{corpus}</span>
              </div>
              <div className="flex gap-4">
                <span className="text-gray-400">Personas Loaded:</span>
                <span className="text-green-400">{personas.length}</span>
              </div>
              <div className="flex gap-4">
                <span className="text-gray-400">Theme Background:</span>
                <span className="text-green-400">{theme?.background || 'default'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="max-w-4xl mx-auto mt-8 text-center text-gray-400 text-sm">
          <p>
            Try selecting different options above. The page background will change based on your persona!
          </p>
          <p className="mt-2">
            Username selections are saved to localStorage. Journeys are loaded from the backend.
          </p>
        </div>
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

