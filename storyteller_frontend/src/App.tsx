import React from 'react'

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Storyteller Frontend
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Phase 2 - Foundation Ready
        </p>
        <div className="bg-white rounded-lg shadow-md p-6 max-w-md mx-auto">
          <h2 className="text-2xl font-semibold text-green-600 mb-2">
            ✓ Setup Complete
          </h2>
          <ul className="text-left text-gray-700 space-y-2">
            <li>✓ Vite + React + TypeScript</li>
            <li>✓ Tailwind CSS configured</li>
            <li>✓ Project structure created</li>
            <li>✓ API proxy configured (port 8000)</li>
            <li>✓ Ready for components</li>
          </ul>
        </div>
        <p className="text-sm text-gray-500 mt-6">
          Run <code className="bg-gray-100 px-2 py-1 rounded">npm install</code> and <code className="bg-gray-100 px-2 py-1 rounded">npm run dev</code> to start
        </p>
      </div>
    </div>
  )
}

export default App

