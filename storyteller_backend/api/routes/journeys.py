"""
Journeys API Routes

Endpoints for managing story journeys:
- GET /api/list_graphs - List user's saved journeys
- POST /api/load_graph - Load a saved journey
- GET /api/get_loaded_graph - Get currently loaded graph
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List
import networkx as nx

from models.api_models import (
    JourneyListResponse,
    LoadGraphRequest,
    LoadGraphResponse,
    GetLoadedGraphResponse,
    GraphData
)
from services import get_journey_manager
from api.dependencies import get_graph_state

router = APIRouter()


@router.get("/list_graphs", response_model=JourneyListResponse)
async def list_graphs(username: str = Query(..., description="Username to list journeys for")):
    """
    List all saved journeys for a user.
    
    Args:
        username: Username to list journeys for
    
    Returns:
        List of journey metadata sorted by most recent first
    """
    journey_manager = get_journey_manager()
    
    try:
        journeys = journey_manager.list_journeys(username)
        return JourneyListResponse(journeys=journeys)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list journeys: {str(e)}"
        )


@router.post("/load_graph", response_model=LoadGraphResponse)
async def load_graph(request: LoadGraphRequest):
    """
    Load a saved journey into memory.
    
    This sets the journey as the current active graph that will be
    continued when the user generates new stories.
    
    Args:
        request: Username and graph_id to load
    
    Returns:
        Success status and journey metadata
    """
    journey_manager = get_journey_manager()
    graph_state = get_graph_state()
    
    try:
        # Load graph from file
        graph, meta = journey_manager.load_graph(request.username, request.graph_id)
        
        # Set as current graph
        await graph_state.set_graph(graph)
        
        return LoadGraphResponse(
            success=True,
            meta=meta
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey '{request.graph_id}' not found for user '{request.username}'"
        )
    except ValueError as e:
        # Corpus validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load journey: {str(e)}"
        )


@router.get("/get_loaded_graph", response_model=GetLoadedGraphResponse)
async def get_loaded_graph():
    """
    Get the currently loaded graph data.
    
    Returns the graph in NetworkX node-link format, ready for
    visualization in the frontend.
    
    Returns:
        Graph data with nodes and links
    """
    graph_state = get_graph_state()
    
    try:
        # Get current graph
        graph = await graph_state.get_graph()
        
        # Convert to node-link format
        serializable_graph = nx.node_link_data(graph)
        
        # Convert to our GraphData model
        graph_data = GraphData(
            nodes=serializable_graph.get("nodes", []),
            links=serializable_graph.get("links", [])
        )
        
        return GetLoadedGraphResponse(graph=graph_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get loaded graph: {str(e)}"
        )

