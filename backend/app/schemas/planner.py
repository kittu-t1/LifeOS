"""
Request/response schemas for the AI Planner.

PlannerLLMOutput is the important one to read first: it's the structured
JSON contract the LLM is instructed to return (see
app/planner/prompts.py) and the validation gate everything else depends
on - app/planner/parser.py parses the model's raw text into this schema
and raises immediately if it doesn't match, so a malformed or
hallucinated response can never reach the database.

Field naming follows this codebase's existing schema convention (`id`,
not `plan_id`/`goal_id` inside a resource's own schema - see
GoalRead/WorkspaceRead) rather than the AI Planner MVP spec's literal
`"plan_id"` response key. The frontend reads `plan.id`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MilestoneItem(BaseModel):
    """One milestone as the LLM returns it, before it has a DB id."""

    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    duration: str = ""


class WeeklyPlanItem(BaseModel):
    week: int = Field(ge=1)
    focus: str = Field(min_length=1)
    tasks: list[str] = Field(default_factory=list)


class PlannerLLMOutput(BaseModel):
    """The exact structured JSON contract planner_v1 asks the model for.
    Anything the model returns that doesn't fit this shape is treated as
    an invalid response (see app/planner/parser.py), not silently
    coerced - a plan with a missing mission or zero milestones isn't a
    usable "wow moment," it's a bug we want to see immediately."""

    mission: str = Field(min_length=1)
    estimated_duration: str = Field(min_length=1)
    milestones: list[MilestoneItem] = Field(min_length=1)
    weekly_plan: list[WeeklyPlanItem] = Field(min_length=1)
    timeline: list[str] = Field(min_length=1)


class PlannerGenerateRequest(BaseModel):
    """`goal_id` replaces the MVP spec's free-text `goal` field - see the
    module docstring in app/planner/__init__.py and
    app/services/planner_service.py for why: this app already requires a
    Goal (and its Workspace) to exist before you can reach the Planner
    tab, so accepting a second, disconnected "goal" string here would
    create two sources of truth for the same idea."""

    timeline: str = Field(min_length=1, max_length=200, examples=["90 days"])
    availability: str = Field(min_length=1, max_length=200, examples=["10 hours/week"])
    constraints: list[str] = Field(default_factory=list)


class RegeneratePlanRequest(BaseModel):
    """No goal_id/timeline/availability here on purpose - regenerate acts
    on an existing Plan (identified by the URL's plan_id) and pulls the
    goal and previous plan itself (see planner_service.regenerate_plan);
    the only new information the caller provides is what to change."""

    adjustment: str = Field(min_length=1, max_length=500, examples=["Make it more realistic"])


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    duration: str | None
    order: int
    created_at: datetime


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    goal_id: uuid.UUID
    mission: str
    estimated_duration: str
    timeline: list[str]
    weekly_plan: list[WeeklyPlanItem]
    milestones: list[MilestoneRead]
    created_at: datetime
    updated_at: datetime
