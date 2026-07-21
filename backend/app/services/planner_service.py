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
the prompt_version tag (planner_v1 vs planner_v1_regenerate) keeps the
two call sites separable.
"""

from __future__ import annotations

import uuid

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.goal import Goal
from app.models.plan import Milestone, Plan
from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.planner.llm.base import LLMProvider, LLMProviderError
from app.planner.parser import PlannerOutputError, parse_planner_output
from app.planner.prompts import (
    PLANNER_V1_SYSTEM_PROMPT,
    PROMPT_VERSION,
    PROMPT_VERSION_REGENERATE,
    build_regenerate_user_prompt,
    build_user_prompt,
)
from app.schemas.planner import PlannerGenerateRequest, PlannerLLMOutput


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
) -> Plan:
    if goal.plan is not None:
        raise PlanAlreadyExistsError("This goal already has a plan. Use regenerate to update it.")

    settings = get_settings()
    user_prompt = build_user_prompt(
        goal_title=goal.title,
        goal_description=goal.description,
        timeline=data.timeline,
        availability=data.availability,
        constraints=data.constraints,
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
    return _save_plan(
        db,
        plan=plan,
        goal_id=goal.id,
        prompt_version=PROMPT_VERSION,
        model_used=settings.openai_model,
    )


def regenerate_plan(
    db: Session,
    *,
    plan: Plan,
    adjustment: str,
    llm_provider: LLMProvider,
) -> Plan:
    """Updates `plan` in place using its own goal, its current content,
    and the user's adjustment. On failure, `plan` is left completely
    untouched - the caller (and the UI) still has the last good plan,
    not a blank state."""
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
    user_prompt = build_regenerate_user_prompt(
        goal_title=goal.title,
        goal_description=goal.description,
        previous_plan=previous_plan,
        adjustment=adjustment,
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

    return _save_plan(
        db,
        plan=plan,
        goal_id=goal.id,
        prompt_version=PROMPT_VERSION_REGENERATE,
        model_used=settings.openai_model,
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
    return plan


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
        system_prompt=PLANNER_V1_SYSTEM_PROMPT, user_prompt=user_prompt
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
            system_prompt=PLANNER_V1_SYSTEM_PROMPT, user_prompt=corrected_prompt
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
