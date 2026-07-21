"""LLM provider interface and the exceptions every adapter must raise."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProviderError(Exception):
    """Base class for anything that goes wrong calling the LLM. Caught at
    the service layer and turned into a clear HTTP error - callers of
    LLMProvider should never need to know which concrete provider is in
    use to handle failures correctly."""


class LLMTimeoutError(LLMProviderError):
    """The provider didn't respond within planner_llm_timeout_seconds."""


class LLMRequestError(LLMProviderError):
    """The provider responded with an error (auth, rate limit, bad
    request, network failure, etc.) - the original message is preserved
    in str(exc) for logs/PlannerRun.error_message, but callers should
    show the user a generic, non-leaky message instead of this text
    directly."""


class LLMProvider(ABC):
    """One method, one job: take a system+user prompt, return the model's
    raw text response. Structured-output parsing/validation happens one
    layer up (see app/planner/parser.py) - this interface doesn't know or
    care that the caller expects JSON."""

    @abstractmethod
    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Returns the model's raw text response.

        Raises:
            LLMTimeoutError: the request exceeded the configured timeout.
            LLMRequestError: any other provider-side failure.
        """
        raise NotImplementedError
