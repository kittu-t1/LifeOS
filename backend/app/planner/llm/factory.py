"""
Returns the configured LLMProvider.

A function, not a global singleton - constructing a fresh OpenAIProvider
per call is cheap (no connection pooling to preserve) and means tests can
swap in a fake provider via FastAPI dependency overrides without any
module-level state to reset between tests.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.planner.llm.base import LLMProvider
from app.planner.llm.openai_provider import OpenAIProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    return OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        timeout_seconds=settings.planner_llm_timeout_seconds,
    )
