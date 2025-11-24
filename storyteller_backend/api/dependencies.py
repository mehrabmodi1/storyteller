"""
API Dependencies

Shared dependencies for API routes including:
- Global graph state management
- Thread-safe access with async locks
"""

import asyncio
import networkx as nx
from typing import Optional


# ============================================
# Global State Management
# ============================================

class GraphState:
    """
    Thread-safe container for the current story graph.
    
    Maintains a single active graph across requests, with
    async lock for concurrent access.
    """
    
    def __init__(self):
        self._graph: nx.DiGraph = nx.DiGraph()
        self._lock = asyncio.Lock()
    
    async def get_graph(self) -> nx.DiGraph:
        """Get a copy of the current graph."""
        async with self._lock:
            return self._graph.copy()
    
    async def set_graph(self, graph: nx.DiGraph) -> None:
        """Set the current graph (replaces existing)."""
        async with self._lock:
            self._graph = graph.copy()
    
    async def clear_graph(self) -> None:
        """Clear the current graph."""
        async with self._lock:
            self._graph = nx.DiGraph()
    
    async def is_empty(self) -> bool:
        """Check if the current graph is empty."""
        async with self._lock:
            return len(self._graph.nodes) == 0


# Global graph state instance
_graph_state: Optional[GraphState] = None


def get_graph_state() -> GraphState:
    """
    Get the global graph state instance.
    
    Returns:
        GraphState instance
    """
    global _graph_state
    if _graph_state is None:
        _graph_state = GraphState()
    return _graph_state

