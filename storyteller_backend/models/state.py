"""
LangGraph state definition for the storyteller agent.

This state is passed between all nodes in the LangGraph pipeline.
Migrated from src/agent/state.py with backward compatibility.
"""

from typing import List, TypedDict, Optional
from langchain_core.messages import BaseMessage
import networkx as nx


class StorytellerState(TypedDict):
    """
    Represents the state of our storyteller agent.
    
    This is the "memory" that gets passed between each step of the agent's process.
    Each field tracks a different aspect of the story generation pipeline.
    """
    
    # ============================================
    # Conversation History
    # ============================================
    messages: List[BaseMessage]
    """The history of messages in the conversation."""
    
    # ============================================
    # Graph Structure
    # ============================================
    graph: nx.DiGraph
    """The graph that stores the entire story structure (nodes and edges)."""
    
    current_choice_id: Optional[str]
    """The ID of the choice node that triggered the current story generation."""
    
    latest_story_node_id: Optional[str]
    """The ID of the most recently created story node."""
    
    # ============================================
    # Retrieval Pipeline
    # ============================================
    search_query: str
    """The search query generated from the user's prompt."""
    
    retrieved_chunks: List[str]
    """The chunks retrieved from the database based on the search query."""
    
    randomize_retrieval: Optional[bool]
    """Whether to randomize retrieval results (for exploration mode)."""
    
    corpus_name: Optional[str]
    """The name of the corpus being used for this story generation."""
    
    # ============================================
    # Story Generation
    # ============================================
    story: str
    """The most recently generated story text."""
    
    story_length: int
    """The desired length of the story in tokens."""
    
    last_story: Optional[str]
    """The story from the previous turn, to be used as context."""
    
    persona_name: Optional[str]
    """The name of the selected storyteller persona."""
    
    # ============================================
    # Choice Generation
    # ============================================
    choices: List[str]
    """The list of generated follow-up prompts for the user."""
    
    # ============================================
    # Image Generation
    # ============================================
    image_url: Optional[str]
    """The URL of the image generated for the latest story chapter."""
    
    # ============================================
    # Persistence
    # ============================================
    username: Optional[str]
    """The username for saving user-specific graphs."""
    
    initial_prompt: Optional[str]
    """The initial prompt for saving graph metadata."""
    
    serializable_graph: Optional[dict]
    """The final, serialized graph to be sent to the frontend."""

