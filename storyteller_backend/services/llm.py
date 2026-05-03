"""Chat-model factory.

Single entry point for constructing langchain chat models against the active
provider. Centralises provider-specific kwargs that must not leak across
providers (most importantly `thinking_budget=0` for Gemini, which prevents
gemini-2.5-flash from spending the entire output token budget on internal
reasoning before producing visible output).
"""

from typing import Any, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from config.settings import settings, Provider


def get_chat_llm(
    *,
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
    streaming: bool = False,
    api_key: Optional[str] = None,
    **extra: Any,
) -> BaseChatModel:
    """Construct a chat model for the active provider.

    For Gemini, `thinking_budget` from the provider profile is applied
    automatically (currently 0 = thinking disabled). Pass `thinking_budget=N`
    explicitly to override.
    """
    kwargs: dict[str, Any] = {
        "temperature": temperature,
        "api_key": settings.resolve_api_key(api_key),
        "streaming": streaming,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if settings.provider is Provider.GEMINI and settings.thinking_budget is not None:
        kwargs.setdefault("thinking_budget", settings.thinking_budget)

    kwargs.update(extra)

    return init_chat_model(
        settings.chat_model,
        model_provider=settings.langchain_chat_provider,
        **kwargs,
    )
