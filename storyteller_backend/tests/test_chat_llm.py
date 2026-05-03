"""Tests for the chat-model factory.

Pins the contract that thinking_budget is auto-applied for Gemini (so
gemini-2.5-flash doesn't consume the output budget on internal reasoning)
and not leaked to other providers.
"""

from unittest.mock import patch, MagicMock

from config.settings import settings, Provider
from services.llm import get_chat_llm


def test_gemini_gets_thinking_budget_zero(monkeypatch):
    monkeypatch.setattr(settings._config, "provider", Provider.GEMINI)
    captured = {}

    def fake_init(model, **kwargs):
        captured.update(kwargs)
        captured["model"] = model
        return MagicMock()

    with patch("services.llm.init_chat_model", side_effect=fake_init):
        get_chat_llm(temperature=0.9, max_tokens=1200)

    assert captured["thinking_budget"] == 0
    assert captured["temperature"] == 0.9
    assert captured["max_tokens"] == 1200
    assert captured["model"] == settings.chat_model


def test_openai_does_not_get_thinking_budget(monkeypatch):
    monkeypatch.setattr(settings._config, "provider", Provider.OPENAI)
    captured = {}

    def fake_init(model, **kwargs):
        captured.update(kwargs)
        return MagicMock()

    with patch("services.llm.init_chat_model", side_effect=fake_init):
        get_chat_llm(temperature=0.5)

    assert "thinking_budget" not in captured


def test_explicit_thinking_budget_override_is_preserved(monkeypatch):
    monkeypatch.setattr(settings._config, "provider", Provider.GEMINI)
    captured = {}

    def fake_init(model, **kwargs):
        captured.update(kwargs)
        return MagicMock()

    with patch("services.llm.init_chat_model", side_effect=fake_init):
        get_chat_llm(thinking_budget=2048)

    assert captured["thinking_budget"] == 2048
