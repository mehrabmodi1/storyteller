from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage
from typing import Optional, Any, Dict, List
import asyncio
import json
import networkx as nx
from datetime import datetime

# Import the compiled agent from our graph file
from .graph import story_agent,  list_saved_graphs, load_graph_from_file
from .state import StorytellerState

app = FastAPI()

# --- CORS Middleware ---
# This is crucial for allowing the front-end (running on a different port)
# to communicate with this server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# In-memory storage for our single, evolving graph.
# This is a simple solution for this example. In a real application,
# you would persist this graph in a database.
STORY_GRAPH = nx.DiGraph()
GRAPH_LOCK = asyncio.Lock()

# Load personas from the JSON file at startup
with open("src/agent/personas.json", "r") as f:
    PERSONAS = json.load(f)

@app.get("/api/personas")
async def get_personas():
    """
    An endpoint to fetch the list of available storyteller personas.
    """
    # We only need to send the name and short description to the frontend
    # to populate the dropdown menu.
    persona_list = [
        {
            "name": p["name"],
            "short_description": p["short_description"],
            "color_theme": p["color_theme"],
        }
        for p in PERSONAS
    ]
    return persona_list

@app.get("/api/corpuses")
async def get_corpuses():
    """
    An endpoint to fetch the list of available corpuses with their metadata and status.
    """
    from ..embed_retrieve.corpus_registry import get_registry
    registry = get_registry()
    
    # Get status for all corpuses
    corpus_statuses = registry.get_all_corpus_statuses()
    
    # Format the response
    corpus_list = []
    for status in corpus_statuses:
        corpus_config = registry.get_corpus(status.name)
        corpus_list.append({
            "name": status.name,
            "display_name": status.display_name,
            "description": corpus_config.description if corpus_config else "",
            "is_active": status.chunks_exist and status.chroma_exists and status.bm25_exists,
            "chunk_count": status.chunk_count,
            "last_processed": status.last_processed,
            "needs_rebuild": status.needs_rebuild,
            "missing_components": status.missing_components
        })
    
    return corpus_list

async def story_events(prompt: str, choice_id: Optional[str] = None, new_journey: bool = False, story_length: int = 1500, persona_name: Optional[str] = None, randomize_retrieval: bool = False, username: Optional[str] = None, corpus_name: Optional[str] = None):
    """
    Runs the storyteller agent and streams back intermediate story tokens
    and the final, updated graph.
    """
    global STORY_GRAPH
    
    # Validate corpus if specified
    if corpus_name:
        from ..embed_retrieve.corpus_registry import get_registry
        registry = get_registry()
        corpus_config = registry.get_corpus(corpus_name)
        if not corpus_config:
            yield {"event": "error", "data": f"Corpus '{corpus_name}' not found. Available corpuses: {list(registry.corpuses.keys())}"}
            return
        if not corpus_config.is_active:
            yield {"event": "error", "data": f"Corpus '{corpus_name}' is not active."}
            return
    else:
        # Default to mahabharata for backward compatibility
        corpus_name = "mahabharata"
    
    # Acquire a lock to ensure that only one request modifies the graph at a time.
    await GRAPH_LOCK.acquire()
    try:
        # If this is a new journey, clear the graph before proceeding.
        if new_journey:
            STORY_GRAPH = nx.DiGraph()
        
        # If a choice was selected, it must exist in the graph.
        if choice_id and choice_id not in STORY_GRAPH:
            print(f"ERROR: Client requested choice_id '{choice_id}' which does not exist in the server's graph.")
            print(f"Available nodes: {list(STORY_GRAPH.nodes())}")
            yield {"event": "error", "data": "Client and server are out of sync. Please start a new journey."}
            return

        # If a choice was selected, update its label in the graph to persist edits
        if choice_id and choice_id in STORY_GRAPH:
            STORY_GRAPH.nodes[choice_id]['label'] = prompt

        # The input to the agent is the initial state.
        initial_state: StorytellerState = {
            "messages": [HumanMessage(content=prompt)],
            "graph": STORY_GRAPH.copy(), # Work on a copy
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
            "corpus_name": corpus_name,  # Add corpus_name to state
        }

        # The agent will now yield events directly, including our custom story_chunk
        is_generating_story = False
        async for event in story_agent.astream_events(initial_state, version="v1"):
            # print(f"--- Server received event: {event['event']} for node {event.get('name')} @ {datetime.now()} ---")
            event_type = event['event']
            event_name = event.get('name')

            if event_type == 'on_chain_start' and event_name == 'generate_story':
                is_generating_story = True
            elif event_type == 'on_chain_end' and event_name == 'generate_story':
                is_generating_story = False

            # If we're in the story generation phase, look for streaming chunks from the LLM
            if is_generating_story and event_type == "on_chat_model_stream":
                # The actual token is an AIMessageChunk with a 'content' attribute
                token = event['data']['chunk'].content
                if token:
                    yield {"event": "story_chunk", "data": token}

            # At the end of the graph, get the final state and the updated graph
            elif event_type == "on_chain_end" and event_name == 'update_graph_with_choices':
                node_output = event['data'].get('output')
                if node_output and 'serializable_graph' in node_output:
                    # Update the global graph state
                    STORY_GRAPH = node_output['graph']
                    # Send the final message
                    yield {"event": "message", "data": json.dumps(node_output['serializable_graph'])}

        # Signal that the stream is complete
        print(f"[{datetime.now()}] Ending SSE stream.")
        yield {"event": "end", "data": "Stream ended."}
    finally:
        # Always release the lock when the stream is finished or if an error occurs.
        GRAPH_LOCK.release()


@app.get("/api/story")
async def stream_story(prompt: str, choice_id: Optional[str] = None, new_journey: bool = False, story_length: int = 1500, persona_name: Optional[str] = None, randomize_retrieval: Optional[bool] = False, username: Optional[str] = None, corpus_name: Optional[str] = None):
    """
    The main endpoint to start or continue a story generation stream.
    - 'prompt': The user's initial prompt or their chosen follow-up.
    - 'choice_id': The unique ID of the choice node that was clicked.
    - 'new_journey': If true, clears the existing graph and starts a new one.
    - 'story_length': The desired length of the story in tokens.
    - 'persona_name': The name of the selected storyteller persona.
    - 'randomize_retrieval': If true, randomizes similarity scores of retrieved chunks (for suggestion box stories).
    - 'username': The username for saving user-specific graphs.
    """
    print(f"[{datetime.now()}] Received new request. Prompt: {prompt[:50]}..., Persona: {persona_name}, Username: {username}, Randomize: {randomize_retrieval}")
    if not prompt:
        return {"error": "Prompt not provided"}, 400
    
    return EventSourceResponse(story_events(prompt, choice_id, new_journey, story_length, persona_name, randomize_retrieval, username, corpus_name))

@app.get("/api/list_graphs")
async def list_graphs(username: str):
    """
    Returns a list of saved graphs for the given username, with metadata for each.
    """
    graphs = list_saved_graphs(username)
    
    # Add corpus validation status to each graph
    from ..embed_retrieve.corpus_registry import get_registry
    registry = get_registry()
    
    for graph in graphs:
        corpus_name = graph.get('corpus_name')
        if corpus_name:
            corpus_config = registry.get_corpus(corpus_name)
            graph['corpus_available'] = corpus_config is not None
            graph['corpus_active'] = corpus_config.is_active if corpus_config else False
            graph['corpus_display_name'] = corpus_config.display_name if corpus_config else corpus_name
        else:
            # Legacy graphs without corpus info
            graph['corpus_available'] = True  # Assume mahabharata is available
            graph['corpus_active'] = True
            graph['corpus_display_name'] = "The Mahabharata"
    
    return graphs

@app.post("/api/load_graph")
async def load_graph(payload: dict):
    """
    Loads a graph for the user, given {username, graph_id}, and sets it as the current STORY_GRAPH.
    """
    global STORY_GRAPH
    username = payload.get('username')
    graph_id = payload.get('graph_id')
    if not username or not graph_id:
        return {"error": "username and graph_id are required"}, 400
    
    graph, meta = load_graph_from_file(username, graph_id)
    
    # Validate that the graph's corpus is available and active
    graph_corpus = meta.get('corpus_name')
    if graph_corpus:
        from ..embed_retrieve.corpus_registry import get_registry
        registry = get_registry()
        corpus_config = registry.get_corpus(graph_corpus)
        if not corpus_config:
            return {"error": f"Graph was created with corpus '{graph_corpus}' which is no longer available."}, 400
        if not corpus_config.is_active:
            return {"error": f"Graph was created with corpus '{graph_corpus}' which is no longer active."}, 400
    
    STORY_GRAPH = graph
    return {"success": True, "meta": meta}

@app.post("/api/get_loaded_graph")
async def get_loaded_graph():
    """
    Returns the currently loaded graph data in the format expected by the frontend.
    """
    global STORY_GRAPH
    # Convert the graph to the format expected by the frontend
    serializable_graph = nx.node_link_data(STORY_GRAPH)
    return {"graph": serializable_graph}

if __name__ == "__main__":
    import uvicorn
    # This allows running the server directly for testing
    # uvicorn src.agent.server:app --reload
    uvicorn.run("src.agent.server:app", host="0.0.0.0", port=8000, reload=True) 