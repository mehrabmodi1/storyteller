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
import traceback

from models.state import StorytellerState
from models.api_models import StoryRequest
from services import get_story_agent, get_journey_manager
from embed_retrieve import get_registry
from api.dependencies import get_graph_state

router = APIRouter()


async def story_generation_events(
    prompt: str,
    choice_id: Optional[str] = None,
    new_journey: bool = False,
    paragraph_count: int = 4,
    persona_name: Optional[str] = None,
    randomize_retrieval: bool = False,
    username: Optional[str] = None,
    corpus_name: Optional[str] = None,
    graph_id: Optional[str] = None
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
    
    # Test error trigger: passing corpus_name "__test_error__" forces an error response
    if corpus_name == "__test_error__":
        yield {"event": "error", "data": "Test error triggered: simulated stream failure."}
        return

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

        # If continuing a journey (choice_id provided), ensure the graph is loaded
        if choice_id and choice_id not in current_graph:
            # In-memory graph doesn't have this node — load from disk
            if graph_id and username:
                try:
                    journey_manager = get_journey_manager()
                    current_graph, _meta = journey_manager.load_graph(username, graph_id)
                    await graph_state.set_graph(current_graph)
                    print(f"Loaded graph '{graph_id}' from disk for user '{username}'")
                except (FileNotFoundError, ValueError) as e:
                    print(f"Failed to load graph from disk: {e}")
                    yield {"event": "error", "data": f"Could not load saved journey: {e}"}
                    return

            # Still not found after disk load attempt
            if choice_id not in current_graph:
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
            "paragraph_count": paragraph_count,
            "path_context": "",
            "guardrail_rejected": False,
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
            
            # Detect guardrail rejection — emitted before any generation begins
            if event_type == "on_chain_end" and event_name == 'screen_prompt':
                node_output = event['data'].get('output', {})
                if node_output.get('guardrail_rejected'):
                    yield {
                        "event": "guardrail_reject",
                        "data": "The storyteller prefers a different path — would you like to rethink your prompt?"
                    }
                    return

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
        error_msg = f"ERROR during story generation: {e}"
        print(error_msg)
        print("Full traceback:")
        traceback.print_exc()
        yield {"event": "error", "data": str(e)}


@router.get("/stream_story")
async def stream_story(
    prompt: str = Query(..., description="User's story prompt"),
    choice_id: Optional[str] = Query(None, description="ID of selected choice node"),
    new_journey: bool = Query(False, description="Start a new journey"),
    paragraph_count: int = Query(4, ge=1, le=8, description="Number of paragraphs to generate (1-8)"),
    persona_name: Optional[str] = Query(None, description="Storyteller persona"),
    randomize_retrieval: bool = Query(False, description="Randomize retrieval results"),
    username: Optional[str] = Query(None, description="Username for saving"),
    corpus_name: Optional[str] = Query("mahabharata", description="Text corpus to use"),
    graph_id: Optional[str] = Query(None, description="Graph ID for loading persisted journey on continuation")
):
    """
    Stream story generation via Server-Sent Events (SSE).
    """
    return EventSourceResponse(
        story_generation_events(
            prompt=prompt,
            choice_id=choice_id,
            new_journey=new_journey,
            paragraph_count=paragraph_count,
            persona_name=persona_name,
            randomize_retrieval=randomize_retrieval,
            username=username,
            corpus_name=corpus_name,
            graph_id=graph_id
        )
    )

