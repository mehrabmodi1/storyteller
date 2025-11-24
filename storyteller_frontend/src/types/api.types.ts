/**
 * TypeScript type definitions for API requests and responses.
 * These types mirror the Pydantic models in storyteller_backend/models/api_models.py
 */

/**
 * Request model for story generation
 */
export interface StoryRequest {
  prompt: string;
  choice_id?: string | null;
  new_journey?: boolean;
  story_length?: number;
  persona_name?: string | null;
  randomize_retrieval?: boolean;
  username?: string | null;
  corpus_name?: string;
}

/**
 * SSE event types for story streaming
 */
export type SSEEventType = 'chunk' | 'graph' | 'end' | 'error';

/**
 * SSE response structure
 */
export interface StoryResponse {
  event_type: SSEEventType;
  data: any;
}

/**
 * Information about a text corpus
 */
export interface CorpusInfo {
  name: string;
  display_name: string;
  description: string;
  is_active: boolean;
  chunk_count: number;
  last_processed?: string | null;
  needs_rebuild: boolean;
  missing_components: string[];
}

/**
 * Information about a storyteller persona
 */
export interface PersonaInfo {
  name: string;
  short_description: string;
  color_theme: ColorTheme;
  system_prompt?: string;
  type?: string;
  created_at?: string;
  temperature?: number;
}

/**
 * Color theme for UI styling
 */
export interface ColorTheme {
  background: string;
  button: string;
  button_hover: string;
  input: string;
  ring: string;
}

/**
 * Metadata about a saved story journey
 */
export interface JourneyMeta {
  graph_id: string;
  username: string;
  timestamp: string;
  initial_prompt: string;
  initial_snippet?: string;
  last_prompt: string;
  last_snippet?: string;
  persona: string;
  corpus_name: string;
  num_story_nodes: number;
  last_story_timestamp: string;
  corpus_available?: boolean;
  corpus_active?: boolean;
  corpus_display_name?: string | null;
}

/**
 * Response containing list of saved journeys
 */
export interface JourneyListResponse {
  journeys: JourneyMeta[];
}

/**
 * Request to load a saved graph
 */
export interface LoadGraphRequest {
  username: string;
  graph_id: string;
}

/**
 * Response after loading a graph
 */
export interface LoadGraphResponse {
  success: boolean;
  meta?: Record<string, any> | null;
  error?: string | null;
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: string;
  timestamp: string;
}

