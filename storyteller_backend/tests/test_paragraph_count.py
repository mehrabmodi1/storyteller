import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

BASE_PARAMS = {
    "prompt": "Tell me about the Pandavas",
    "new_journey": True,
    "corpus_name": "mahabharata",
    "username": "test_user",
}


class TestParagraphCountValidation:
    """Tests that only validate query parameter parsing — no real LLM calls.

    Out-of-range values must return 422 before any agent code runs.
    In-range values reach the agent but we mock it to avoid real API calls.
    """

    def test_paragraph_count_above_max_returns_422(self):
        resp = client.get("/api/stream_story", params={**BASE_PARAMS, "paragraph_count": 20})
        assert resp.status_code == 422

    def test_paragraph_count_zero_returns_422(self):
        resp = client.get("/api/stream_story", params={**BASE_PARAMS, "paragraph_count": 0})
        assert resp.status_code == 422

    def test_paragraph_count_negative_returns_422(self):
        resp = client.get("/api/stream_story", params={**BASE_PARAMS, "paragraph_count": -1})
        assert resp.status_code == 422

    def test_paragraph_count_at_min_accepted(self):
        # Mock the story agent so we don't make real API calls.
        # We only care that the endpoint accepts paragraph_count=1 (no 422).
        mock_agent = MagicMock()
        mock_agent.astream_events = AsyncMock(return_value=aiter([]))

        with patch("api.routes.stories.get_story_agent", return_value=mock_agent):
            resp = client.get("/api/stream_story", params={**BASE_PARAMS, "paragraph_count": 1})

        assert resp.status_code != 422

    def test_paragraph_count_at_max_accepted(self):
        mock_agent = MagicMock()
        mock_agent.astream_events = AsyncMock(return_value=aiter([]))

        with patch("api.routes.stories.get_story_agent", return_value=mock_agent):
            resp = client.get("/api/stream_story", params={**BASE_PARAMS, "paragraph_count": 8})

        assert resp.status_code != 422

    def test_no_paragraph_count_uses_default(self):
        # No paragraph_count param — should default to 4, not raise 422
        mock_agent = MagicMock()
        mock_agent.astream_events = AsyncMock(return_value=aiter([]))

        with patch("api.routes.stories.get_story_agent", return_value=mock_agent):
            resp = client.get("/api/stream_story", params=BASE_PARAMS)

        assert resp.status_code != 422


def aiter(items):
    """Helper: async iterable from a list."""
    async def _gen():
        for item in items:
            yield item
    return _gen()
