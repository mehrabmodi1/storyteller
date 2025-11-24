/**
 * API client for communicating with the storyteller backend.
 * Provides functions for all 11 API endpoints.
 */

import { API_CONFIG, buildURL } from '@/config/api.config';
import type {
  PersonaInfo,
  CorpusInfo,
  JourneyListResponse,
  LoadGraphRequest,
  LoadGraphResponse,
  GetLoadedGraphResponse,
  HealthResponse,
} from '@/types';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  // If endpoint is already a full URL (from buildURL), use it as-is
  // Otherwise, prepend the base URL
  const url = endpoint.startsWith('http') ? endpoint : `${API_CONFIG.baseURL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API request failed: ${url}`, error);
    throw error;
  }
}

// =============================================================================
// STORY GENERATION (SSE endpoint handled separately in useSSE hook)
// =============================================================================

/**
 * Build SSE URL for story streaming
 * Note: EventSource doesn't support POST, so we pass params via query string
 */
export function buildStreamStoryURL(params: {
  prompt: string;
  choice_id?: string;
  new_journey?: boolean;
  story_length?: number;
  persona_name?: string;
  randomize_retrieval?: boolean;
  username?: string;
  corpus_name?: string;
}): string {
  return buildURL(API_CONFIG.endpoints.streamStory, params as Record<string, string | number | boolean>);
}

// =============================================================================
// PERSONAS API (Full CRUD)
// =============================================================================

/**
 * GET /api/personas - List all personas
 */
export async function listPersonas(): Promise<PersonaInfo[]> {
  return apiFetch<PersonaInfo[]>(API_CONFIG.endpoints.personas);
}

/**
 * POST /api/personas - Create new persona
 */
export async function createPersona(persona: PersonaInfo): Promise<PersonaInfo> {
  return apiFetch<PersonaInfo>(API_CONFIG.endpoints.personas, {
    method: 'POST',
    body: JSON.stringify(persona),
  });
}

/**
 * PUT /api/personas/{name} - Update persona
 */
export async function updatePersona(name: string, persona: PersonaInfo): Promise<PersonaInfo> {
  return apiFetch<PersonaInfo>(API_CONFIG.endpoints.persona(name), {
    method: 'PUT',
    body: JSON.stringify(persona),
  });
}

/**
 * DELETE /api/personas/{name} - Delete persona
 */
export async function deletePersona(name: string): Promise<{ success: boolean; message: string }> {
  return apiFetch(API_CONFIG.endpoints.persona(name), {
    method: 'DELETE',
  });
}

// =============================================================================
// CORPUSES API (Full CRUD)
// =============================================================================

/**
 * GET /api/corpuses - List all corpuses with status
 */
export async function listCorpuses(): Promise<CorpusInfo[]> {
  return apiFetch<CorpusInfo[]>(API_CONFIG.endpoints.corpuses);
}

/**
 * POST /api/corpuses - Trigger corpus ingestion
 */
export async function createCorpus(corpusData: {
  name: string;
  display_name: string;
  description: string;
}): Promise<{ success: boolean; message: string; corpus?: CorpusInfo }> {
  return apiFetch(API_CONFIG.endpoints.corpuses, {
    method: 'POST',
    body: JSON.stringify(corpusData),
  });
}

/**
 * PUT /api/corpuses/{name} - Update corpus metadata
 */
export async function updateCorpus(
  name: string,
  updates: { display_name?: string; description?: string }
): Promise<CorpusInfo> {
  return apiFetch<CorpusInfo>(API_CONFIG.endpoints.corpus(name), {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

/**
 * DELETE /api/corpuses/{name} - Delete corpus
 */
export async function deleteCorpus(name: string): Promise<{ success: boolean; message: string }> {
  return apiFetch(API_CONFIG.endpoints.corpus(name), {
    method: 'DELETE',
  });
}

// =============================================================================
// JOURNEYS API
// =============================================================================

/**
 * GET /api/list_graphs - List user's saved journeys
 */
export async function listGraphs(username: string): Promise<JourneyListResponse> {
  const url = buildURL(API_CONFIG.endpoints.listGraphs, { username });
  return apiFetch<JourneyListResponse>(url);
}

/**
 * POST /api/load_graph - Load a saved journey
 */
export async function loadGraph(request: LoadGraphRequest): Promise<LoadGraphResponse> {
  return apiFetch<LoadGraphResponse>(API_CONFIG.endpoints.loadGraph, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * GET /api/get_loaded_graph - Get currently loaded graph
 */
export async function getLoadedGraph(): Promise<GetLoadedGraphResponse> {
  return apiFetch<GetLoadedGraphResponse>(API_CONFIG.endpoints.getLoadedGraph);
}

// =============================================================================
// HEALTH CHECK
// =============================================================================

/**
 * GET /health - Health check
 */
export async function healthCheck(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>(API_CONFIG.endpoints.health);
}

