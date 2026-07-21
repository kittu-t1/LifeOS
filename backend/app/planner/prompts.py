"""
Versioned planner prompts.

`PROMPT_VERSION` is stored on every PlannerRun row (see
app/models/planner_run.py) precisely so prompt quality can be evaluated
and compared over time - bump it (planner_v1 -> planner_v2) any time the
prompt text changes meaningfully, rather than editing planner_v1's text
in place. Keep old versions around even if unused, so historical
PlannerRun rows stay meaningful.
"""

from __future__ import annotations

import json
from typing import Any

PROMPT_VERSION = "planner_v1"
# Tags PlannerRun rows produced by regenerate_plan (see
# app/services/planner_service.py) separately from fresh generate_plan
# runs - same system prompt/JSON contract, different user-turn (previous
# plan + adjustment instead of goal + timeline/availability), so quality
# between the two call sites can be evaluated independently.
PROMPT_VERSION_REGENERATE = "planner_v1_regenerate"

PLANNER_V1_SYSTEM_PROMPT = """You are LifeOS Planning Agent.

Your job is to transform a user's goal into a realistic, actionable execution plan.

Consider:
- The user's goal (title and any description)
- Their desired timeline
- Their available time per week
- Any constraints they've listed

Generate:
1. A clear mission statement - one or two sentences framing what success looks like.
2. Major milestones - the big checkpoints between start and done, each with a title, \
a one-sentence description, and a rough duration.
3. A week-by-week execution plan - what to focus on and do each week, sized to the \
user's stated weekly availability.
4. A timeline - a short ordered list of the plan's key phases or dates.

Rules:
- Be realistic. A goal that plainly cannot fit the stated timeline and availability \
should get a plan that says so implicitly through pacing (e.g. fewer milestones, an \
honest estimated_duration) rather than an inflated promise.
- Respect the user's constraints - do not schedule around something they said is \
unavailable.
- Do not pad the plan with filler. Every milestone and week should do real work.
- Return structured JSON only - no markdown, no commentary, no code fences, just the \
JSON object.

Return exactly this JSON shape:
{
  "mission": "string",
  "estimated_duration": "string",
  "milestones": [
    {"title": "string", "description": "string", "duration": "string"}
  ],
  "weekly_plan": [
    {"week": 1, "focus": "string", "tasks": ["string", "string"]}
  ],
  "timeline": ["string", "string"]
}"""


def build_user_prompt(
    *,
    goal_title: str,
    goal_description: str | None,
    timeline: str,
    availability: str,
    constraints: list[str],
) -> str:
    """Builds the user-turn message for planner_v1. Kept as plain string
    formatting (not a template engine) - the prompt is short and static
    enough that a template engine would be one more dependency for no
    real benefit."""
    lines = [f"Goal: {goal_title}"]
    if goal_description:
        lines.append(f"Goal details: {goal_description}")
    lines.append(f"Desired timeline: {timeline}")
    lines.append(f"Available time per week: {availability}")
    if constraints:
        lines.append("Constraints: " + "; ".join(constraints))
    else:
        lines.append("Constraints: none stated")
    return "\n".join(lines)


def build_regenerate_user_prompt(
    *,
    goal_title: str,
    goal_description: str | None,
    previous_plan: dict[str, Any],
    adjustment: str,
) -> str:
    """Builds the user-turn message for a regenerate call - same
    PLANNER_V1_SYSTEM_PROMPT and JSON contract as a fresh generate, but
    the user turn gives the model the previous plan as context plus the
    user's requested adjustment, instead of goal/timeline/availability
    (regenerate_plan doesn't ask the user for those again - see
    app/services/planner_service.py). Passing the previous plan as
    literal JSON (not prose) keeps milestone/weekly-plan structure
    unambiguous for the model to revise rather than reinterpret."""
    lines = [f"Goal: {goal_title}"]
    if goal_description:
        lines.append(f"Goal details: {goal_description}")
    lines.append("Here is the current plan:")
    lines.append(json.dumps(previous_plan))
    lines.append(f"Requested adjustment: {adjustment}")
    lines.append(
        "Revise the plan to satisfy the requested adjustment, keeping it realistic and "
        "consistent with the goal. Return the full revised plan in the same JSON shape - "
        "not just the changed parts."
    )
    return "\n".join(lines)
