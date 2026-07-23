"""
Planner service.

The orchestration layer from the AI Planner architecture: Planner API ->
Planner Service (here) -> LLM Provider Adapter (app/planner/llm/) ->
Structured Planner Output (app/planner/parser.py) -> Database.

Two entry points, matching the Planner Productization phase's model:
Plan is a strict one-to-one with Goal (see app/models/plan.py).
  - generate_plan: first-time creation. Rejects (PlanAlreadyExistsError)
    if the goal already has a Plan - regenerate_plan is how you change
    an existing one, not a second call to generate.
  - regenerate_plan: updates the existing Plan in place using the
    original goal + the current plan + a user-supplied adjustment,
    instead of asking for timeline/availability again.

Every attempt from either entry point is recorded as a PlannerRun,
success or failure, before the function returns or raises - see
_record_run. That's what makes PlannerRun useful for evaluating AI
quality later: the failure history is as visible as the successes, and
the prompt_version tag (planner_v5 vs planner_v5_regenerate) keeps the
two call sites separable.

As of the Execution Engine phase, both entry points also build PlanTask
rows from the LLM output (see _build_tasks) alongside Milestones - this
module still only generates them, never touches their status. Completing/
reopening a task is app/services/task_service.py's job, and calculating
progress from them is app/services/progress_service.py's - see those
modules for why the split matters (planner_service regenerating a plan
wholesale-replaces tasks the same way it already did milestones, so it
owns creation, but never owns "is this done").
"""

from __future__ import annotations

import logging
import uuid
from typing import NamedTuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.memory.models.memory import Memory, MemoryCategory
from app.memory.repositories.memory_repository import SqlAlchemyMemoryRepository
from app.memory.services.memory_service import MemoryService
from app.models.goal import Goal
from app.models.plan import Milestone, Plan
from app.models.plan_task import PlanTask, PlanTaskStatus
from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.planner.llm.base import LLMProvider, LLMProviderError
from app.planner.parser import PlannerOutputError, parse_planner_output
from app.planner.preference_detection import detect_preference_statement
from app.planner.prompts import (
    PLANNER_V5_SYSTEM_PROMPT,
    PROMPT_VERSION,
    PROMPT_VERSION_REGENERATE,
    build_regenerate_user_prompt,
    build_user_prompt,
)
from app.schemas.planner import PlannerGenerateRequest, PlannerLLMOutput, SuggestedMemory
from app.services import habit_service

logger = logging.getLogger(__name__)

# Fixed, generic key for every Planner-suggested memory (see
# _suggest_memory) - "short, machine-ish identifier" per the Memory
# model's own docstring, not a unique constraint, so multiple accepted
# suggestions over time simply share this key like any other memories
# that happen to share one.
_SUGGESTED_MEMORY_KEY = "planner_detected_preference"


class PlanGenerationResult(NamedTuple):
    """What generate_plan/regenerate_plan hand back to the API layer -
    the persisted Plan itself, plus two ephemeral, request-scoped facts
    about *this* call that are useful to show the user but don't belong
    as permanent columns on Plan: how many memories personalized the
    prompt (memories_used) and whether a new preference was noticed in
    what they typed (suggested_memory). See PlanRead for how these reach
    the frontend."""

    plan: Plan
    memories_used: int
    suggested_memory: SuggestedMemory | None


class PlanAlreadyExistsError(Exception):
    """generate_plan was called for a goal that already has a Plan -
    regenerate_plan is the correct call for an existing one."""


class PlanPersistenceError(Exception):
    """The LLM call succeeded and produced a valid plan, but saving it to
    the database failed (connection dropped, constraint violation,
    etc.)."""


def generate_plan(
    db: Session,
    *,
    goal: Goal,
    data: PlannerGenerateRequest,
    llm_provider: LLMProvider,
) -> PlanGenerationResult:
    """See PlanGenerationResult for what the two extra fields mean beyond
    the Plan itself."""
    if goal.plan is not None:
        raise PlanAlreadyExistsError("This goal already has a plan. Use regenerate to update it.")

    settings = get_settings()
    active_habits = habit_service.list_active_habits(db, user_id=goal.user_id)
    memory_context, memories_used = _build_memory_context(
        db, user_id=goal.user_id, context="generate_plan"
    )
    user_prompt = build_user_prompt(
        goal_title=goal.title,
        goal_description=goal.description,
        timeline=data.timeline,
        availability=data.availability,
        constraints=data.constraints,
        existing_commitments=habit_service.summarize_for_planner(active_habits),
        memory_context=memory_context,
    )

    try:
        output = _generate_with_retry(llm_provider, user_prompt)
    except (LLMProviderError, PlannerOutputError) as exc:
        _record_run(
            db,
            goal_id=goal.id,
            plan_id=None,
            prompt_version=PROMPT_VERSION,
            model_used=settings.openai_model,
            status=PlannerRunStatus.FAILED,
            error_message=str(exc),
        )
        db.commit()
        raise

    plan = _build_plan(goal_id=goal.id, output=output)
    saved = _save_plan(
        db,
        plan=plan,
        goal_id=goal.id,
        prompt_version=PROMPT_VERSION,
        model_used=settings.openai_model,
    )
    suggested_memory = _suggest_memory(db, user_id=goal.user_id, candidate_texts=data.constraints)
    return PlanGenerationResult(
        plan=saved, memories_used=memories_used, suggested_memory=suggested_memory
    )


def regenerate_plan(
    db: Session,
    *,
    plan: Plan,
    adjustment: str,
    llm_provider: LLMProvider,
) -> PlanGenerationResult:
    """Updates `plan` in place using its own goal, its current content,
    and the user's adjustment. On failure, `plan` is left completely
    untouched - the caller (and the UI) still has the last good plan,
    not a blank state. See PlanGenerationResult for the return shape."""
    goal = plan.goal
    settings = get_settings()
    previous_plan = {
        "mission": plan.mission,
        "estimated_duration": plan.estimated_duration,
        "milestones": [
            {
                "title": milestone.title,
                "description": milestone.description or "",
                "duration": milestone.duration or "",
            }
            for milestone in plan.milestones
        ],
        "weekly_plan": plan.weekly_plan,
        "timeline": plan.timeline,
    }
    active_habits = habit_service.list_active_habits(db, user_id=goal.user_id)
    memory_context, memories_used = _build_memory_context(
        db, user_id=goal.user_id, context="regenerate_plan"
    )
    user_prompt = build_regenerate_user_prompt(
        goal_title=goal.title,
        goal_description=goal.description,
        previous_plan=previous_plan,
        adjustment=adjustment,
        existing_commitments=habit_service.summarize_for_planner(active_habits),
        memory_context=memory_context,
    )

    try:
        output = _generate_with_retry(llm_provider, user_prompt)
    except (LLMProviderError, PlannerOutputError) as exc:
        _record_run(
            db,
            goal_id=goal.id,
            plan_id=plan.id,
            prompt_version=PROMPT_VERSION_REGENERATE,
            model_used=settings.openai_model,
            status=PlannerRunStatus.FAILED,
            error_message=str(exc),
        )
        db.commit()
        raise

    plan.mission = output.mission
    plan.estimated_duration = output.estimated_duration
    plan.timeline = output.timeline
    plan.weekly_plan = [week.model_dump() for week in output.weekly_plan]
    plan.milestones = [
        Milestone(
            title=milestone.title,
            description=milestone.description,
            duration=milestone.duration,
            order=index,
        )
        for index, milestone in enumerate(output.milestones)
    ]
    # Same "AI output is a full new draft, not a patch" treatment as
    # milestones - every task from the previous plan is replaced, so a
    # completed task's checkmark doesn't survive a regenerate under a
    # since-changed task list pretending to be the same one.
    plan.tasks = _build_tasks(output)

    saved = _save_plan(
        db,
        plan=plan,
        goal_id=goal.id,
        prompt_version=PROMPT_VERSION_REGENERATE,
        model_used=settings.openai_model,
    )
    suggested_memory = _suggest_memory(db, user_id=goal.user_id, candidate_texts=[adjustment])
    return PlanGenerationResult(
        plan=saved, memories_used=memories_used, suggested_memory=suggested_memory
    )


def get_plan_for_goal(db: Session, *, goal_id: uuid.UUID) -> Plan | None:
    return db.query(Plan).filter(Plan.goal_id == goal_id).first()


def get_owned_plan(db: Session, *, user_id: uuid.UUID, plan_id: uuid.UUID) -> Plan | None:
    """Fetches a Plan by its own id, scoped to the requesting user via a
    join on its Goal - same not-fetched-then-checked idiom as
    goal_service.get_goal, so a plan belonging to another user 404s
    instead of leaking whether the id exists."""
    return (
        db.query(Plan)
        .join(Goal, Plan.goal_id == Goal.id)
        .filter(Plan.id == plan_id, Goal.user_id == user_id)
        .first()
    )


def _build_plan(*, goal_id: uuid.UUID, output: PlannerLLMOutput) -> Plan:
    plan = Plan(
        goal_id=goal_id,
        mission=output.mission,
        estimated_duration=output.estimated_duration,
        timeline=output.timeline,
        weekly_plan=[week.model_dump() for week in output.weekly_plan],
    )
    plan.milestones = [
        Milestone(
            title=milestone.title,
            description=milestone.description,
            duration=milestone.duration,
            order=index,
        )
        for index, milestone in enumerate(output.milestones)
    ]
    plan.tasks = _build_tasks(output)
    return plan


def _build_tasks(output: PlannerLLMOutput) -> list[PlanTask]:
    """Flattens weekly_plan into PlanTask rows - the Execution Engine's
    entry point (see app/models/plan_task.py). display_order runs across
    the whole plan (not reset per week) so the checklist has one stable
    ordering. milestone_id is left unset - see the model's docstring for
    why linking tasks to milestones isn't part of this phase."""
    tasks: list[PlanTask] = []
    display_order = 0
    for week in output.weekly_plan:
        for task in week.tasks:
            tasks.append(
                PlanTask(
                    week_number=week.week,
                    title=task.title,
                    description=task.description or None,
                    estimated_minutes=task.estimated_minutes,
                    display_order=display_order,
                    status=PlanTaskStatus.PENDING,
                )
            )
            display_order += 1
    return tasks


def _save_plan(
    db: Session, *, plan: Plan, goal_id: uuid.UUID, prompt_version: str, model_used: str
) -> Plan:
    """Shared persistence tail for both a fresh Plan (generate_plan) and
    an updated one (regenerate_plan) - `db.add` on an already-persistent
    object is a harmless no-op, so the same flush/record/commit/refresh
    sequence covers both call sites."""
    try:
        db.add(plan)
        db.flush()  # assigns/confirms plan.id for the PlannerRun row below
        _record_run(
            db,
            goal_id=goal_id,
            plan_id=plan.id,
            prompt_version=prompt_version,
            model_used=model_used,
            status=PlannerRunStatus.SUCCESS,
            error_message=None,
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanPersistenceError("Couldn't save your plan. Please try again.") from exc

    db.refresh(plan)
    return plan


# Human-readable section headings for _format_memory_context, in the
# same order as MemoryService's _CATEGORY_PRIORITY - so whichever
# categories a user actually has memories in, the most important group
# (per that ranking) always reads first in the prompt, not just whatever
# order they happened to be created in.
_MEMORY_CATEGORY_HEADINGS: dict[MemoryCategory, str] = {
    MemoryCategory.PREFERENCE: "Preferences",
    MemoryCategory.PLANNING_CONTEXT: "Planning Context",
    MemoryCategory.LEARNED_PATTERN: "Patterns",
    MemoryCategory.NOTE: "Notes",
    MemoryCategory.HABIT_INSIGHT: "Habit Insights",
}


def _build_memory_context(
    db: Session, *, user_id: uuid.UUID, context: str
) -> tuple[str | None, int]:
    """Memory Engine integration point (see app/memory/). Retrieves this
    user's ranked, relevant memories (see MemoryService.
    get_relevant_memories - deterministic: category priority, recency,
    confidence; no embeddings) and formats them into the "User Context"
    block PLANNER_V5_SYSTEM_PROMPT expects (see _format_memory_context).
    Returns `(None, 0)` when the user has no memories yet, so
    build_user_prompt/build_regenerate_user_prompt can skip the section
    entirely instead of emitting an empty header.

    Also returns the memory count alongside the formatted text - not just
    for the log line, but so generate_plan/regenerate_plan can surface
    "personalized using N memories" back to the API response (see
    PlanRead.memories_used) without the frontend having to re-derive it
    or guess from log output.

    Uses MemoryService directly (not the HTTP API) since this runs
    inside the same request/process - importing app.memory.services is
    the one-way dependency the Memory Engine's design explicitly allows
    (see memory_service.py's docstring): Planner depends on Memory,
    never the reverse."""
    memory_service = MemoryService(SqlAlchemyMemoryRepository(db))
    relevant = memory_service.get_relevant_memories(user_id=user_id)
    logger.info(
        "planner.%s: injecting %d memories into prompt as user context: %s",
        context,
        len(relevant),
        [f"{m.category.value}:{m.key}" for m in relevant],
    )
    return _format_memory_context(relevant), len(relevant)


def _format_memory_context(memories: list[Memory]) -> str | None:
    """Formats already-ranked memories into the structured, prose "User
    Context" block the prompts append - grouped by category with a
    readable heading and one line per memory, e.g.:

        Preferences
        - Prefers evening work sessions

    Never raw JSON (per the sprint spec's explicit "keep prompts clean
    and readable") - the model only needs to read this, not parse it.
    Returns None for an empty list rather than an empty string, so the
    caller can tell "no context" apart from "context, but it's blank"."""
    if not memories:
        return None

    grouped: dict[MemoryCategory, list[Memory]] = {}
    for memory in memories:
        grouped.setdefault(memory.category, []).append(memory)

    blocks: list[str] = []
    for category, heading in _MEMORY_CATEGORY_HEADINGS.items():
        items = grouped.get(category)
        if not items:
            continue
        block_lines = [heading]
        block_lines.extend(f"- {item.value}" for item in items)
        blocks.append("\n".join(block_lines))
    return "\n\n".join(blocks)


def _suggest_memory(
    db: Session, *, user_id: uuid.UUID, candidate_texts: list[str]
) -> SuggestedMemory | None:
    """Looks for a preference statement in what the user just typed into
    the Planner (goal constraints on generate, the adjustment text on
    regenerate/Improve Plan) and, if it finds one worth asking about,
    returns it as an unsaved SuggestedMemory - never writes anything to
    the database itself (see app/planner/preference_detection.py's
    module docstring for why this stays "detect and suggest," not
    "detect and save").

    Two reasons this can return None: detect_preference_statement found
    nothing that reads like a first-person preference, or it did but this
    user already has an identical memory (case/whitespace-insensitive
    comparison) - re-suggesting something they already said yes to (or
    already have saved some other way) isn't "keeping the user in
    control," it's nagging them.

    Uses MemoryService.list_memories (not get_relevant_memories) for the
    dedupe check - this needs every memory the user has, not the ranked/
    capped subset the prompt gets, so a low-priority-category duplicate
    still suppresses the suggestion."""
    candidate = detect_preference_statement(*candidate_texts)
    if candidate is None:
        return None

    memory_service = MemoryService(SqlAlchemyMemoryRepository(db))
    existing = memory_service.list_memories(user_id=user_id)
    normalized = candidate.strip().lower()
    if any(memory.value.strip().lower() == normalized for memory in existing):
        return None

    return SuggestedMemory(
        category=MemoryCategory.PREFERENCE.value,
        key=_SUGGESTED_MEMORY_KEY,
        value=candidate,
    )


def _generate_with_retry(llm_provider: LLMProvider, user_prompt: str) -> PlannerLLMOutput:
    """Calls the LLM and validates its output. If the response isn't
    parseable/valid JSON, retries exactly once with an added corrective
    instruction - LLMs occasionally wrap JSON in commentary despite
    instructions not to, and one retry recovers most of those cases
    without masking a genuinely broken provider or prompt.

    Provider-level failures (timeout, auth, rate limit - LLMProviderError)
    are NOT retried here: those are usually not transient in a way an
    immediate retry fixes, and silently doubling the request on, say, an
    invalid API key just doubles the wait before the same clear error."""
    raw_text = llm_provider.generate(
        system_prompt=PLANNER_V5_SYSTEM_PROMPT, user_prompt=user_prompt
    )
    try:
        return parse_planner_output(raw_text)
    except PlannerOutputError:
        corrected_prompt = (
            f"{user_prompt}\n\n"
            "Your previous response could not be parsed. Return ONLY a valid JSON "
            "object matching the exact schema given - no markdown, no commentary, "
            "no code fences."
        )
        raw_text = llm_provider.generate(
            system_prompt=PLANNER_V5_SYSTEM_PROMPT, user_prompt=corrected_prompt
        )
        return parse_planner_output(raw_text)  # let a second failure propagate


def _record_run(
    db: Session,
    *,
    goal_id: uuid.UUID,
    plan_id: uuid.UUID | None,
    prompt_version: str,
    model_used: str,
    status: PlannerRunStatus,
    error_message: str | None,
) -> None:
    db.add(
        PlannerRun(
            goal_id=goal_id,
            plan_id=plan_id,
            prompt_version=prompt_version,
            model_used=model_used,
            status=status,
            error_message=error_message,
        )
    )
