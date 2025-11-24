/**
 * API configuration
 * Base URL is loaded from environment variables
 */

export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  endpoints: {
    // Story generation
    streamStory: '/api/stream_story',
    
    // Personas
    personas: '/api/personas',
    persona: (name: string) => `/api/personas/${encodeURIComponent(name)}`,
    
    // Corpuses
    corpuses: '/api/corpuses',
    corpus: (name: string) => `/api/corpuses/${encodeURIComponent(name)}`,
    
    // Journeys
    listGraphs: '/api/list_graphs',
    loadGraph: '/api/load_graph',
    getLoadedGraph: '/api/get_loaded_graph',
    
    // Health
    health: '/health',
  },
} as const;

/**
 * Helper to build full URL
 */
export function buildURL(endpoint: string, params?: Record<string, string | number | boolean>): string {
  const url = new URL(endpoint, API_CONFIG.baseURL);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, String(value));
    });
  }
  
  return url.toString();
}

