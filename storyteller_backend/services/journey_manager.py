"""
Journey Manager Service

Handles persistence and management of story journey graphs:
- Save graphs to disk
- Load graphs from disk
- List user journeys with metadata
- Validate corpus availability

Migrated from src/agent/graph.py (save/load functions)
"""

import os
import json
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional
import networkx as nx

from config.settings import settings
from models.api_models import JourneyMeta
from embed_retrieve import get_registry


class JourneyManager:
    """
    Manages story journey persistence and retrieval.
    
    Journeys are stored as JSON files containing graph data and metadata,
    organized by username.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the journey manager.
        
        Args:
            base_dir: Base directory for saved graphs. If None, uses settings.
        """
        if base_dir is None:
            self.base_dir = settings.saved_graphs_path
        else:
            self.base_dir = base_dir
    
    def _ensure_user_dir(self, username: str) -> str:
        """
        Ensure the user's directory exists and return its path.
        
        Args:
            username: Username for the directory
        
        Returns:
            Path to the user's directory
        """
        dir_path = self.base_dir / username
        dir_path.mkdir(parents=True, exist_ok=True)
        return str(dir_path)
    
    def save_graph(
        self,
        graph: nx.DiGraph,
        username: str,
        initial_prompt: str,
        last_prompt: str,
        persona: Optional[str] = None,
        corpus_name: Optional[str] = None
    ) -> str:
        """
        Save a story graph to disk.
        
        Args:
            graph: The NetworkX graph to save
            username: Username who owns this journey
            initial_prompt: The first prompt that started the journey
            last_prompt: The most recent prompt
            persona: The storyteller persona used
            corpus_name: The corpus used for story generation
        
        Returns:
            The graph filename (graph_id)
        """
        dir_path = self._ensure_user_dir(username)
        
        # Retrieve or generate graph_name
        meta = getattr(graph, 'graph', {})
        graph_name = meta.get('graph_name')
        
        if not graph_name:
            # Generate new graph name from timestamp and initial prompt
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            initial_snippet = (initial_prompt or '')[:25].replace(' ', '_').replace('/', '_')
            graph_name = f"{timestamp}_{initial_snippet}.json"
            
            # Store in graph metadata
            if not hasattr(graph, 'graph'):
                graph.graph = {}
            graph.graph['graph_name'] = graph_name
        
        file_path = os.path.join(dir_path, graph_name)
        
        # Find the latest story node timestamp
        story_timestamps = [
            d.get('timestamp')
            for _, d in graph.nodes(data=True)
            if d.get('type') == 'story' and d.get('timestamp')
        ]
        last_story_timestamp = max(story_timestamps) if story_timestamps else None
        
        # Count story nodes
        num_story_nodes = sum(
            1 for _, d in graph.nodes(data=True)
            if d.get('type') == 'story'
        )
        
        # Prepare data structure
        data = {
            'meta': {
                'username': username,
                'graph_name': graph_name,
                'timestamp': datetime.now().isoformat(),
                'initial_prompt': initial_prompt,
                'initial_snippet': (initial_prompt or '')[:50],  # Longer snippet for display
                'last_prompt': last_prompt,
                'last_snippet': (last_prompt or '')[:50],
                'persona': persona,
                'corpus_name': corpus_name,
                'num_story_nodes': num_story_nodes,
                'last_story_timestamp': last_story_timestamp,
            },
            'graph': nx.node_link_data(graph)
        }
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return graph_name
    
    def list_journeys(self, username: str) -> List[JourneyMeta]:
        """
        List all saved journeys for a user, with metadata.
        
        Args:
            username: Username to list journeys for
        
        Returns:
            List of journey metadata, sorted by most recent first
        """
        dir_path = self._ensure_user_dir(username)
        journeys = []
        registry = get_registry()
        
        for fname in os.listdir(dir_path):
            if fname.endswith('.json'):
                file_path = os.path.join(dir_path, fname)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    meta = data.get('meta', {})
                    graph_data = data.get('graph', {})
                    
                    # Extract prompts from graph if missing from metadata
                    initial_prompt = meta.get('initial_prompt')
                    last_prompt = meta.get('last_prompt')
                    
                    if not initial_prompt or not last_prompt:
                        # Extract from graph nodes
                        nodes = graph_data.get('nodes', [])
                        choice_nodes = [
                            n for n in nodes 
                            if n.get('type') == 'choice'
                        ]
                        
                        if choice_nodes and not initial_prompt:
                            # Find the first choice node by timestamp
                            # Filter out nodes without timestamps and sort by timestamp
                            timestamped_nodes = [n for n in choice_nodes if n.get('timestamp')]
                            if timestamped_nodes:
                                first_node = min(timestamped_nodes, key=lambda n: n.get('timestamp', ''))
                                initial_prompt = first_node.get('label', 'Unknown prompt')
                            else:
                                # Fallback: use first node by ID if no timestamps
                                initial_prompt = choice_nodes[0].get('label', 'Unknown prompt')
                        
                        if choice_nodes and not last_prompt:
                            # Find the last choice node by timestamp
                            timestamped_nodes = [n for n in choice_nodes if n.get('timestamp')]
                            if timestamped_nodes:
                                last_node = max(timestamped_nodes, key=lambda n: n.get('timestamp', ''))
                                last_prompt = last_node.get('label', 'Unknown prompt')
                            else:
                                # Fallback: use last node by ID if no timestamps
                                last_prompt = choice_nodes[-1].get('label', 'Unknown prompt')
                    
                    # Fallbacks if still None
                    initial_prompt = initial_prompt or 'Legacy journey'
                    last_prompt = last_prompt or 'Unknown'
                    
                    # Add corpus validation status
                    corpus_name = meta.get('corpus_name')
                    corpus_available = True
                    corpus_active = True
                    corpus_display_name = None
                    
                    if corpus_name:
                        corpus_config = registry.get_corpus(corpus_name)
                        corpus_available = corpus_config is not None
                        corpus_active = corpus_config.is_active if corpus_config else False
                        corpus_display_name = corpus_config.display_name if corpus_config else corpus_name
                    else:
                        # Legacy graphs without corpus info - assume mahabharata
                        corpus_display_name = "The Mahabharata"
                    
                    # Create JourneyMeta object
                    journey = JourneyMeta(
                        graph_id=fname,
                        username=meta.get('username') or username,
                        timestamp=meta.get('timestamp') or '',
                        initial_prompt=initial_prompt,
                        initial_snippet=initial_prompt[:50] if initial_prompt else '',
                        last_prompt=last_prompt,
                        last_snippet=last_prompt[:50] if last_prompt else '',
                        persona=meta.get('persona') or 'default',
                        corpus_name=corpus_name or 'mahabharata',
                        num_story_nodes=meta.get('num_story_nodes') or 0,
                        last_story_timestamp=meta.get('last_story_timestamp') or '',
                        corpus_available=corpus_available,
                        corpus_active=corpus_active,
                        corpus_display_name=corpus_display_name
                    )
                    
                    journeys.append(journey)
                    
                except Exception as e:
                    print(f"Error loading journey {fname}: {e}")
                    continue
        
        # Sort by timestamp descending (most recent first)
        journeys.sort(key=lambda j: j.timestamp, reverse=True)
        return journeys
    
    def load_graph(self, username: str, graph_id: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """
        Load a saved graph from disk.
        
        Args:
            username: Username who owns the graph
            graph_id: The graph filename (e.g., "20250101_120000_story.json")
        
        Returns:
            Tuple of (graph, metadata_dict)
        
        Raises:
            FileNotFoundError: If the graph file doesn't exist
            ValueError: If the graph's corpus is unavailable or inactive
        """
        dir_path = self._ensure_user_dir(username)
        file_path = os.path.join(dir_path, graph_id)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Graph {graph_id} not found for user {username}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Validate corpus availability
        meta = data.get('meta', {})
        graph_corpus = meta.get('corpus_name')
        
        if graph_corpus:
            registry = get_registry()
            corpus_config = registry.get_corpus(graph_corpus)
            
            if not corpus_config:
                raise ValueError(
                    f"Graph was created with corpus '{graph_corpus}' which is no longer available."
                )
            
            if not corpus_config.is_active:
                raise ValueError(
                    f"Graph was created with corpus '{graph_corpus}' which is no longer active."
                )
        
        # Reconstruct graph from node-link data
        graph = nx.node_link_graph(data['graph'])
        
        return graph, meta
    
    def delete_graph(self, username: str, graph_id: str) -> bool:
        """
        Delete a saved graph.
        
        Args:
            username: Username who owns the graph
            graph_id: The graph filename to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        dir_path = self._ensure_user_dir(username)
        file_path = os.path.join(dir_path, graph_id)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting graph {graph_id}: {e}")
            return False


# Global instance for convenience
_journey_manager: Optional[JourneyManager] = None


def get_journey_manager() -> JourneyManager:
    """
    Get the global journey manager instance.
    
    Returns:
        JourneyManager instance
    """
    global _journey_manager
    if _journey_manager is None:
        _journey_manager = JourneyManager()
    return _journey_manager

