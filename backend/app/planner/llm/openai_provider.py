"""OpenAI adapter - the one concrete LLMProvider this MVP ships with."""

from __future__ import annotations

import openai
from openai import OpenAI

from app.planner.llm.base import LLMProvider, LLMRequestError, LLMTimeoutError


class OpenAIProvider(LLMProvider):
    def __init__(self, *, api_key: str | None, model: str, timeout_seconds: int) -> None:
        # Checked here (not left to the SDK) so a missing key fails with a
        # message that actually says what to do about it, the first time
        # anyone tries to generate a plan without having set one - this is
        # the expected state right after this feature ships, until a real
        # key is pasted into backend/.env.
        if not api_key:
            raise LLMRequestError(
                "OPENAI_API_KEY is not set. Add one to backend/.env "
                "(get a key at platform.openai.com) and restart the backend."
            )
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._client = OpenAI(api_key=api_key, timeout=timeout_seconds)

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                # Forces the API to only ever return a syntactically valid
                # JSON object - eliminates the most common failure mode
                # (markdown code fences, leading/trailing commentary)
                # before app/planner/parser.py even has to deal with it.
                response_format={"type": "json_object"},
                temperature=0.4,
            )
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError(
                f"OpenAI request timed out after {self._timeout_seconds}s"
            ) from exc
        except openai.OpenAIError as exc:
            raise LLMRequestError(f"OpenAI request failed: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMRequestError("OpenAI returned an empty response")
        return content
