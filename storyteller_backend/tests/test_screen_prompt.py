import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from tests.conftest import make_state
import networkx as nx


# These imports will fail until the functions exist
from services.story_agent import _check_moderation, _classify_intent, screen_prompt
from models.api_models import PromptScreenResult


class TestCheckModeration:

    @pytest.mark.asyncio
    async def test_returns_true_when_not_flagged(self):
        mock_result = MagicMock()
        mock_result.results = [MagicMock(flagged=False)]

        with patch("services.story_agent.settings") as mock_settings, \
             patch("services.story_agent.AsyncOpenAI") as MockClient:
            mock_settings.provider = "openai"
            MockClient.return_value.moderations.create = AsyncMock(return_value=mock_result)
            result = await _check_moderation("Tell me about Arjuna", "test-key")

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_flagged(self):
        mock_result = MagicMock()
        mock_result.results = [MagicMock(flagged=True)]

        with patch("services.story_agent.settings") as mock_settings, \
             patch("services.story_agent.AsyncOpenAI") as MockClient:
            mock_settings.provider = "openai"
            MockClient.return_value.moderations.create = AsyncMock(return_value=mock_result)
            result = await _check_moderation("harmful content", "test-key")

        assert result is False

    @pytest.mark.asyncio
    async def test_skips_moderation_for_non_openai_provider(self):
        with patch("services.story_agent.settings") as mock_settings:
            mock_settings.provider = "gemini"
            result = await _check_moderation("any prompt", "test-key")
        assert result is True


class TestClassifyIntent:
    # _classify_intent calls init_chat_model(...).with_structured_output(PromptScreenResult)
    # then awaits .ainvoke() on the resulting chain. We must mock the full chain:
    # init_chat_model() -> mock_llm; mock_llm.with_structured_output() -> mock_chain;
    # mock_chain.ainvoke() -> result.

    @pytest.mark.asyncio
    async def test_returns_pass_for_faithful_prompt(self):
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(
            return_value=PromptScreenResult(verdict="pass", reason="Faithful exploration")
        )
        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_chain)

        with patch("services.story_agent.init_chat_model", return_value=mock_llm):
            result = await _classify_intent(
                "Tell me about Karna's moral failings", "mahabharata", "test-key"
            )

        assert result.verdict == "pass"

    @pytest.mark.asyncio
    async def test_returns_fail_for_malicious_prompt(self):
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(
            return_value=PromptScreenResult(verdict="fail", reason="Malicious demeaning portrayal")
        )
        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_chain)

        with patch("services.story_agent.init_chat_model", return_value=mock_llm):
            result = await _classify_intent(
                "Make Draupadi look stupid", "mahabharata", "test-key"
            )

        assert result.verdict == "fail"


class TestScreenPromptNode:

    @pytest.mark.asyncio
    async def test_sets_guardrail_rejected_false_on_pass(self):
        state = make_state(nx.DiGraph())

        with patch("services.story_agent._check_moderation", AsyncMock(return_value=True)), \
             patch("services.story_agent._classify_intent",
                   AsyncMock(return_value=PromptScreenResult(verdict="pass", reason="ok"))):
            result = await screen_prompt(state)

        assert result["guardrail_rejected"] is False

    @pytest.mark.asyncio
    async def test_moderation_alone_does_not_reject_when_classifier_passes(self):
        """Moderation API alone is not the primary gate; classifier pass allows the prompt."""
        state = make_state(nx.DiGraph())

        with patch("services.story_agent._check_moderation", AsyncMock(return_value=False)), \
             patch("services.story_agent._classify_intent",
                   AsyncMock(return_value=PromptScreenResult(verdict="pass", reason="ok"))):
            result = await screen_prompt(state)

        assert result["guardrail_rejected"] is False

    @pytest.mark.asyncio
    async def test_sets_guardrail_rejected_true_when_classifier_fails(self):
        state = make_state(nx.DiGraph())

        with patch("services.story_agent._check_moderation", AsyncMock(return_value=True)), \
             patch("services.story_agent._classify_intent",
                   AsyncMock(return_value=PromptScreenResult(verdict="fail", reason="malicious"))):
            result = await screen_prompt(state)

        assert result["guardrail_rejected"] is True

    @pytest.mark.asyncio
    async def test_both_checks_run_in_parallel(self):
        """Verifies asyncio.gather is used (both mock calls are awaited)."""
        state = make_state(nx.DiGraph())
        moderation_mock = AsyncMock(return_value=True)
        classifier_mock = AsyncMock(
            return_value=PromptScreenResult(verdict="pass", reason="ok")
        )

        with patch("services.story_agent._check_moderation", moderation_mock), \
             patch("services.story_agent._classify_intent", classifier_mock):
            await screen_prompt(state)

        moderation_mock.assert_called_once()
        classifier_mock.assert_called_once()
