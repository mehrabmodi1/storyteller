"""
Stories API Routes

Endpoints for story generation:
- POST /api/stream_story - Generate story with SSE streaming
"""

from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage
from typing import Optional
import networkx as nx
import json
from datetime import datetime

from models.state import StorytellerState
from models.api_models import StoryRequest
from services import get_story_agent
from embed_retrieve import get_registry
from api.dependencies import get_graph_state

router = APIRouter()


async def story_generation_events(
    prompt: str,
    choice_id: Optional[str] = None,
    new_journey: bool = False,
    story_length: int = 1500,
    persona_name: Optional[str] = None,
    randomize_retrieval: bool = False,
    username: Optional[str] = None,
    corpus_name: Optional[str] = None
):
    """
    Generate story events via SSE streaming.
    
    Streams:
    - story_chunk: Individual tokens as the story is generated
    - message: Final graph data when complete
    - end: Stream completion signal
    - error: Error messages
    """
    graph_state = get_graph_state()
    
    # Validate corpus if specified
    if corpus_name:
        registry = get_registry()
        corpus_config = registry.get_corpus(corpus_name)
        if not corpus_config:
            yield {
                "event": "error",
                "data": f"Corpus '{corpus_name}' not found. Available corpuses: {list(registry.corpuses.keys())}"
            }
            return
        if not corpus_config.is_active:
            yield {"event": "error", "data": f"Corpus '{corpus_name}' is not active."}
            return
    else:
        # Default to mahabharata for backward compatibility
        corpus_name = "mahabharata"
    
    try:
        # Get current graph
        current_graph = await graph_state.get_graph()
        
        # If this is a new journey, clear the graph
        if new_journey:
            current_graph = nx.DiGraph()
            await graph_state.clear_graph()
        
        # If a choice was selected, it must exist in the graph
        if choice_id and choice_id not in current_graph:
            print(f"ERROR: Client requested choice_id '{choice_id}' which does not exist in the server's graph.")
            print(f"Available nodes: {list(current_graph.nodes())}")
            yield {"event": "error", "data": "Client and server are out of sync. Please start a new journey."}
            return
        
        # If a choice was selected, update its label in the graph to persist edits
        if choice_id and choice_id in current_graph:
            current_graph.nodes[choice_id]['label'] = prompt
        
        # Prepare initial state for the agent
        initial_state: StorytellerState = {
            "messages": [HumanMessage(content=prompt)],
            "graph": current_graph.copy(),  # Work on a copy
            "current_choice_id": choice_id,
            "latest_story_node_id": None,
            "search_query": "",
            "retrieved_chunks": [],
            "story": "",
            "choices": [],
            "story_length": story_length,
            "last_story": None,
            "serializable_graph": None,
            "persona_name": persona_name,
            "randomize_retrieval": randomize_retrieval,
            "username": username,
            "initial_prompt": prompt if new_journey else None,
            "corpus_name": corpus_name,
            "image_url": None,
            "image_prompt": None,
            "parent_image_prompt": None,
        }
        
        # Get the story agent
        story_agent = get_story_agent()
        
        # Stream events from the agent
        is_generating_story = False
        async for event in story_agent.astream_events(initial_state, version="v1"):
            event_type = event['event']
            event_name = event.get('name')
            
            # Track when we're in story generation phase
            if event_type == 'on_chain_start' and event_name == 'generate_story':
                is_generating_story = True
            elif event_type == 'on_chain_end' and event_name == 'generate_story':
                is_generating_story = False
            
            # Stream story tokens as they're generated
            if is_generating_story and event_type == "on_chat_model_stream":
                token = event['data']['chunk'].content
                if token:
                    yield {"event": "story_chunk", "data": token}
            
            # At the end, get the final state and updated graph
            elif event_type == "on_chain_end" and event_name == 'update_graph_with_choices':
                node_output = event['data'].get('output')
                if node_output and 'serializable_graph' in node_output:
                    # Update the global graph state
                    await graph_state.set_graph(node_output['graph'])
                    # Send the final graph
                    yield {"event": "message", "data": json.dumps(node_output['serializable_graph'])}
        
        # Signal completion
        print(f"[{datetime.now()}] Ending SSE stream.")
        yield {"event": "end", "data": "Stream ended."}
    
    except Exception as e:
        print(f"ERROR during story generation: {e}")
        yield {"event": "error", "data": str(e)}


@router.get("/stream_story")
async def stream_story(
    prompt: str = Query(..., description="User's story prompt"),
    choice_id: Optional[str] = Query(None, description="ID of selected choice node"),
    new_journey: bool = Query(False, description="Start a new journey"),
    story_length: int = Query(1500, ge=500, le=3000, description="Desired story length"),
    persona_name: Optional[str] = Query(None, description="Storyteller persona"),
    randomize_retrieval: bool = Query(False, description="Randomize retrieval results"),
    username: Optional[str] = Query(None, description="Username for saving"),
    corpus_name: Optional[str] = Query("mahabharata", description="Text corpus to use")
):
    """
    Stream story generation via Server-Sent Events (SSE).
    
    This endpoint generates a story based on the user's prompt and streams
    the result token by token for real-time display in the UI.
    
    Event Types:
    - story_chunk: Individual story tokens
    - message: Final graph data (JSON)
    - end: Stream completion
    - error: Error messages
    
    Args:
        prompt: User's story prompt or chosen follow-up
        choice_id: If continuing a story, the ID of the selected choice
        new_journey: If True, starts a new story (clears current graph)
        story_length: Desired story length in tokens (500-3000)
        persona_name: Name of the storyteller persona to use
        randomize_retrieval: If True, randomizes retrieval for exploration
        username: Username for saving the journey
        corpus_name: Name of the corpus to use for generation
    
    Returns:
        Server-Sent Events stream
    """
    return EventSourceResponse(
        story_generation_events(
            prompt=prompt,
            choice_id=choice_id,
            new_journey=new_journey,
            story_length=story_length,
            persona_name=persona_name,
            randomize_retrieval=randomize_retrieval,
            username=username,
            corpus_name=corpus_name
        )
    )

