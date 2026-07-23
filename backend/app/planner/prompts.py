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

PROMPT_VERSION = "planner_v3"
# Tags PlannerRun rows produced by regenerate_plan (see
# app/services/planner_service.py) separately from fresh generate_plan
# runs - same system prompt/JSON contract, different user-turn (previous
# plan + adjustment instead of goal + timeline/availability), so quality
# between the two call sites can be evaluated independently.
PROMPT_VERSION_REGENERATE = "planner_v3_regenerate"

# Historical - no longer used to build any prompt (see PLANNER_V2_SYSTEM_PROMPT
# below), kept only so PlannerRun rows tagged prompt_version="planner_v1"
# still point at the exact text that produced them.
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

# Active prompt. Bumped from v1 because the JSON contract itself changed,
# not just wording: weekly_plan.tasks moved from plain strings to
# {title, description, estimated_minutes} objects, so the Execution
# Engine (app/models/plan_task.py) has real per-task duration/detail to
# persist instead of a bare label - Today's Focus and the task checklist
# both need that, and it has to come from the planner (content), not be
# invented by execution (status only).
PLANNER_V2_SYSTEM_PROMPT = """You are LifeOS Planning Agent.

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
3. A week-by-week execution plan - what to focus on each week, sized to the user's \
stated weekly availability. Each week's tasks must be concrete, individually \
completable actions (not vague themes) - each one needs its own short title, a \
one-sentence description of what doing it actually involves, and a realistic \
estimated_minutes for that single task alone (typically 20-180 minutes; never the \
whole week's worth of work in one task).
4. A timeline - a short ordered list of the plan's key phases or dates.

Rules:
- Be realistic. A goal that plainly cannot fit the stated timeline and availability \
should get a plan that says so implicitly through pacing (e.g. fewer milestones, an \
honest estimated_duration) rather than an inflated promise.
- Respect the user's constraints - do not schedule around something they said is \
unavailable.
- Do not pad the plan with filler. Every milestone, week, and task should do real work.
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
    {
      "week": 1,
      "focus": "string",
      "tasks": [
        {"title": "string", "description": "string", "estimated_minutes": 60}
      ]
    }
  ],
  "timeline": ["string", "string"]
}"""

# Active prompt. Bumped from v2 for the Recurring Task System sprint:
# the user turn can now include the user's existing recurring habits
# (see build_user_prompt's `existing_commitments` and
# app/services/habit_service.summarize_for_planner) as fixed context.
# The JSON contract itself is unchanged from v2 - only the system
# prompt's guidance changed (a new "Consider" bullet and a new rule), and
# per this file's own versioning convention that still counts as a
# meaningful prompt change worth its own version tag.
PLANNER_V3_SYSTEM_PROMPT = """You are LifeOS Planning Agent.

Your job is to transform a user's goal into a realistic, actionable execution plan.

Consider:
- The user's goal (title and any description)
- Their desired timeline
- Their available time per week
- Any constraints they've listed
- Any existing recurring commitments already on their schedule (if listed) - these are \
already happening and are not part of what you're planning

Generate:
1. A clear mission statement - one or two sentences framing what success looks like.
2. Major milestones - the big checkpoints between start and done, each with a title, \
a one-sentence description, and a rough duration.
3. A week-by-week execution plan - what to focus on each week, sized to the user's \
stated weekly availability. Each week's tasks must be concrete, individually \
completable actions (not vague themes) - each one needs its own short title, a \
one-sentence description of what doing it actually involves, and a realistic \
estimated_minutes for that single task alone (typically 20-180 minutes; never the \
whole week's worth of work in one task).
4. A timeline - a short ordered list of the plan's key phases or dates.

Rules:
- Be realistic. A goal that plainly cannot fit the stated timeline and availability \
should get a plan that says so implicitly through pacing (e.g. fewer milestones, an \
honest estimated_duration) rather than an inflated promise.
- Respect the user's constraints - do not schedule around something they said is \
unavailable.
- If existing recurring commitments are listed, treat them as fixed and already \
accounted for in the user's stated availability - never invent a weekly_plan task that \
duplicates one (e.g. don't add a "Workout" task if "Workout - every day" is already \
listed as a commitment), and don't assume time already claimed by them is also free for \
this plan's tasks.
- Do not pad the plan with filler. Every milestone, week, and task should do real work.
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
    {
      "week": 1,
      "focus": "string",
      "tasks": [
        {"title": "string", "description": "string", "estimated_minutes": 60}
      ]
    }
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
    existing_commitments: list[str] | None = None,
) -> str:
    """Builds the user-turn message for a fresh generate call. Kept as
    plain string formatting (not a template engine) - the prompt is
    short and static enough that a template engine would be one more
    dependency for no real benefit.

    `existing_commitments` is the user's active recurring habits (see
    app/services/habit_service.summarize_for_planner), passed as plain
    text lines rather than structured JSON - the model only needs to
    read and respect them (per PLANNER_V3_SYSTEM_PROMPT's rule), not
    parse or modify them, so prose is simpler than a nested object here."""
    lines = [f"Goal: {goal_title}"]
    if goal_description:
        lines.append(f"Goal details: {goal_description}")
    lines.append(f"Desired timeline: {timeline}")
    lines.append(f"Available time per week: {availability}")
    if constraints:
        lines.append("Constraints: " + "; ".join(constraints))
    else:
        lines.append("Constraints: none stated")
    if existing_commitments:
        lines.append("Existing recurring commitments (fixed, already scheduled):")
        lines.extend(f"- {commitment}" for commitment in existing_commitments)
    return "\n".join(lines)


def build_regenerate_user_prompt(
    *,
    goal_title: str,
    goal_description: str | None,
    previous_plan: dict[str, Any],
    adjustment: str,
    existing_commitments: list[str] | None = None,
) -> str:
    """Builds the user-turn message for a regenerate call - same
    PLANNER_V3_SYSTEM_PROMPT and JSON contract as a fresh generate, but
    the user turn gives the model the previous plan as context plus the
    user's requested adjustment, instead of goal/timeline/availability
    (regenerate_plan doesn't ask the user for those again - see
    app/services/planner_service.py). Passing the previous plan as
    literal JSON (not prose) keeps milestone/weekly-plan structure
    unambiguous for the model to revise rather than reinterpret.

    `existing_commitments` - see build_user_prompt - matters just as much
    here: a regenerate should never "solve" a tight schedule by
    reinventing a task that duplicates a habit the user already has
    running."""
    lines = [f"Goal: {goal_title}"]
    if goal_description:
        lines.append(f"Goal details: {goal_description}")
    lines.append("Here is the current plan:")
    lines.append(json.dumps(previous_plan))
    lines.append(f"Requested adjustment: {adjustment}")
    if existing_commitments:
        lines.append("Existing recurring commitments (fixed, already scheduled):")
        lines.extend(f"- {commitment}" for commitment in existing_commitments)
    lines.append(
        "Revise the plan to satisfy the requested adjustment, keeping it realistic and "
        "consistent with the goal. Return the full revised plan in the same JSON shape - "
        "not just the changed parts."
    )
    return "\n".join(lines)
