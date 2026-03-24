import pytest
import networkx as nx
from tests.conftest import make_state


# Import will fail until the function exists — that's expected
from services.story_agent import build_path_context


class TestBuildPathContextNewJourney:
    """No choice_id — root node, no path context needed."""

    def test_returns_empty_string_for_new_journey(self, root_only_graph):
        state = make_state(root_only_graph, choice_id=None)
        result = build_path_context(state)
        assert result["path_context"] == ""

    def test_does_not_raise_for_empty_graph(self):
        state = make_state(nx.DiGraph(), choice_id=None)
        result = build_path_context(state)
        assert result["path_context"] == ""


class TestBuildPathContextDepth2:
    """One ancestor story node (root only)."""

    def test_includes_root_summary(self, depth_2_graph):
        state = make_state(depth_2_graph, choice_id="choice_a")
        result = build_path_context(state)
        assert "Root summary." in result["path_context"]

    def test_numbered_list_format(self, depth_2_graph):
        state = make_state(depth_2_graph, choice_id="choice_a")
        result = build_path_context(state)
        assert result["path_context"].startswith("1.")

    def test_does_not_include_choice_node_labels(self, depth_2_graph):
        state = make_state(depth_2_graph, choice_id="choice_a")
        result = build_path_context(state)
        assert "Choice A" not in result["path_context"]
        assert "Choice B" not in result["path_context"]


class TestBuildPathContextDepth3:
    """Two ancestor story nodes (root and depth-2)."""

    def test_includes_both_summaries(self, depth_3_graph):
        state = make_state(depth_3_graph, choice_id="choice_d")
        result = build_path_context(state)
        assert "Root summary." in result["path_context"]
        assert "Second summary." in result["path_context"]

    def test_root_comes_first(self, depth_3_graph):
        state = make_state(depth_3_graph, choice_id="choice_d")
        result = build_path_context(state)
        root_pos = result["path_context"].index("Root summary.")
        second_pos = result["path_context"].index("Second summary.")
        assert root_pos < second_pos

    def test_two_numbered_entries(self, depth_3_graph):
        state = make_state(depth_3_graph, choice_id="choice_d")
        result = build_path_context(state)
        assert "1." in result["path_context"]
        assert "2." in result["path_context"]


class TestBuildPathContextMissingSummary:
    """Story node exists but has no summary field (legacy node)."""

    def test_skips_nodes_without_summary(self, depth_2_graph):
        # Remove summary from root
        depth_2_graph.nodes["story_root"].pop("summary", None)
        state = make_state(depth_2_graph, choice_id="choice_a")
        result = build_path_context(state)
        assert result["path_context"] == ""
