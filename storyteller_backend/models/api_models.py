"""
Pydantic models for API request/response validation.

These models define the data contracts for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class StoryRequest(BaseModel):
    """Request model for story generation."""
    
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User's story prompt or choice"
    )
    choice_id: Optional[str] = Field(
        default=None,
        description="ID of the choice node that was selected"
    )
    new_journey: bool = Field(
        default=False,
        description="Whether to start a new story journey"
    )
    story_length: int = Field(
        default=1500,
        ge=500,
        le=3000,
        description="Desired story length in tokens"
    )
    persona_name: Optional[str] = Field(
        default=None,
        description="Name of the storyteller persona to use"
    )
    randomize_retrieval: bool = Field(
        default=False,
        description="Whether to randomize retrieval results (for exploration)"
    )
    username: Optional[str] = Field(
        default=None,
        description="Username for saving the journey"
    )
    corpus_name: str = Field(
        default="mahabharata",
        description="Name of the corpus to use for story generation"
    )


class StoryResponse(BaseModel):
    """Response model for story generation (sent via SSE)."""
    
    event_type: str = Field(
        ...,
        description="Type of event: 'chunk', 'graph', 'end', 'error'"
    )
    data: Any = Field(
        ...,
        description="Event data (story chunk, graph data, error message, etc.)"
    )


class CorpusInfo(BaseModel):
    """Information about a text corpus."""
    
    name: str = Field(..., description="Internal corpus name")
    display_name: str = Field(..., description="Human-readable corpus name")
    description: str = Field(..., description="Corpus description")
    is_active: bool = Field(..., description="Whether corpus is active and ready")
    chunk_count: int = Field(..., description="Number of text chunks in corpus")
    last_processed: Optional[str] = Field(
        default=None,
        description="Timestamp of last processing"
    )
    needs_rebuild: bool = Field(
        ...,
        description="Whether corpus needs rebuilding"
    )
    missing_components: List[str] = Field(
        default_factory=list,
        description="List of missing components (chunks, chroma, bm25)"
    )


class PersonaInfo(BaseModel):
    """Information about a storyteller persona."""
    
    name: str = Field(..., description="Persona name")
    short_description: str = Field(..., description="Brief persona description")
    color_theme: Dict[str, str] = Field(
        ...,
        description="Color theme for UI (background, button, input, ring, etc.)"
    )


class ColorTheme(BaseModel):
    """Color theme for a persona."""
    
    background: str = Field(..., description="Background color class")
    button: str = Field(..., description="Button color class")
    button_hover: str = Field(..., description="Button hover color class")
    input: str = Field(..., description="Input field color class")
    ring: str = Field(..., description="Focus ring color class")


class JourneyMeta(BaseModel):
    """Metadata about a saved story journey."""
    
    graph_id: str = Field(..., description="Unique journey ID (timestamp-based)")
    username: str = Field(..., description="Username who created the journey")
    timestamp: str = Field(..., description="Creation timestamp")
    initial_prompt: str = Field(..., description="First prompt that started the journey")
    initial_snippet: str = Field(
        default="",
        description="Snippet from initial story"
    )
    last_prompt: str = Field(..., description="Most recent prompt")
    last_snippet: str = Field(
        default="",
        description="Snippet from most recent story"
    )
    persona: str = Field(..., description="Persona used for this journey")
    corpus_name: str = Field(
        default="mahabharata",
        description="Corpus used for this journey"
    )
    num_story_nodes: int = Field(..., description="Number of story chapters")
    last_story_timestamp: str = Field(..., description="Timestamp of last story")
    corpus_available: Optional[bool] = Field(
        default=True,
        description="Whether the corpus is still available"
    )
    corpus_active: Optional[bool] = Field(
        default=True,
        description="Whether the corpus is still active"
    )
    corpus_display_name: Optional[str] = Field(
        default=None,
        description="Display name of the corpus"
    )


class JourneyListResponse(BaseModel):
    """Response containing list of saved journeys."""
    
    journeys: List[JourneyMeta] = Field(
        default_factory=list,
        description="List of journey metadata"
    )


class GraphNode(BaseModel):
    """A node in the story graph."""
    
    id: str = Field(..., description="Unique node ID")
    type: str = Field(..., description="Node type: 'story' or 'choice'")
    label: str = Field(..., description="Node label (choice text or story title)")
    story: Optional[str] = Field(
        default=None,
        description="Story content (for story nodes)"
    )
    image_url: Optional[str] = Field(
        default=None,
        description="URL of generated image (for story nodes)"
    )


class GraphEdge(BaseModel):
    """An edge in the story graph."""
    
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")


class GraphData(BaseModel):
    """Complete graph data structure."""
    
    nodes: List[GraphNode] = Field(
        default_factory=list,
        description="List of graph nodes"
    )
    links: List[GraphEdge] = Field(
        default_factory=list,
        description="List of graph edges"
    )


class LoadGraphRequest(BaseModel):
    """Request to load a saved graph."""
    
    username: str = Field(..., description="Username who owns the graph")
    graph_id: str = Field(..., description="ID of the graph to load")


class LoadGraphResponse(BaseModel):
    """Response after loading a graph."""
    
    success: bool = Field(..., description="Whether load was successful")
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Graph metadata"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if load failed"
    )


class GetLoadedGraphResponse(BaseModel):
    """Response containing the loaded graph data."""
    
    graph: GraphData = Field(..., description="The graph data")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(default="healthy", description="Service status")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Current timestamp"
    )

