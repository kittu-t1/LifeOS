"""
Turns an LLM's raw text response into a validated PlannerLLMOutput.

This is the "Validate structured output" step from the architecture
diagram (Planner Service -> LLM Provider Adapter -> Structured Planner
Output -> Database). Two things can go wrong between "the model replied"
and "we have a usable plan": the text isn't valid JSON at all (stray
prose, markdown fences), or it's valid JSON that doesn't match the
schema (missing a field, empty milestones list, wrong types). Both are
raised as the same PlannerOutputError so planner_service can handle them
identically - a partially-shaped plan is exactly as unusable as no plan.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.schemas.planner import PlannerLLMOutput


class PlannerOutputError(Exception):
    """The model's response couldn't be turned into a valid plan."""


def parse_planner_output(raw_text: str) -> PlannerLLMOutput:
    cleaned = _strip_code_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise PlannerOutputError(f"Model response was not valid JSON: {exc}") from exc

    try:
        return PlannerLLMOutput.model_validate(data)
    except ValidationError as exc:
        raise PlannerOutputError(
            f"Model response didn't match the expected plan structure: {exc}"
        ) from exc


def _strip_code_fences(text: str) -> str:
    """OpenAI's json_object response_format shouldn't produce these, but
    other providers (or a future prompt tweak) might wrap the JSON in a
    ```json ... ``` block - stripping it here keeps that concern local to
    parsing instead of leaking into every provider adapter."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()
