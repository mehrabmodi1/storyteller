import networkx as nx
import pytest
from langchain_core.messages import HumanMessage


@pytest.fixture
def root_only_graph():
    """A graph with one story node and three choice nodes (no continuation yet)."""
    g = nx.DiGraph()
    g.add_node("story_root", type="story", story="Root story text", summary="Root summary.")
    g.add_node("choice_a", type="choice", label="Choice A")
    g.add_node("choice_b", type="choice", label="Choice B")
    g.add_node("choice_c", type="choice", label="Choice C")
    g.add_edge("story_root", "choice_a")
    g.add_edge("story_root", "choice_b")
    g.add_edge("story_root", "choice_c")
    return g


@pytest.fixture
def depth_2_graph(root_only_graph):
    """Extends root_only_graph with a second story node."""
    g = root_only_graph
    g.add_node("story_2", type="story", story="Second story text", summary="Second summary.")
    g.add_node("choice_d", type="choice", label="Choice D")
    g.add_edge("choice_a", "story_2")
    g.add_edge("story_2", "choice_d")
    return g


@pytest.fixture
def depth_3_graph(depth_2_graph):
    """Extends depth_2_graph with a third story node."""
    g = depth_2_graph
    g.add_node("story_3", type="story", story="Third story text", summary="Third summary.")
    g.add_node("choice_e", type="choice", label="Choice E")
    g.add_edge("choice_d", "story_3")
    g.add_edge("story_3", "choice_e")
    return g


def make_state(graph, choice_id=None, messages=None):
    """Build a minimal StorytellerState dict for testing node functions."""
    return {
        "messages": messages or [HumanMessage(content="test prompt")],
        "graph": graph,
        "current_choice_id": choice_id,
        "latest_story_node_id": None,
        "search_query": "",
        "retrieved_chunks": [],
        "paragraph_count": 4,
        "path_context": "",
        "guardrail_rejected": False,
        "story": "",
        "last_story": None,
        "choices": [],
        "persona_name": None,
        "randomize_retrieval": False,
        "username": "test_user",
        "initial_prompt": None,
        "corpus_name": "mahabharata",
        "image_url": None,
        "image_prompt": None,       # mirrors initial_state in stories.py
        "parent_image_prompt": None,
        "serializable_graph": None,
    }
