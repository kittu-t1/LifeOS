/**
 * Mirrors backend/app/schemas/planner.py - keep these in sync manually
 * until a shared schema-generation step exists (same convention as
 * types/goal.ts and types/workspace.ts).
 */

import type { MemoryCategory } from "@/types/memory";

export interface Milestone {
  id: string;
  title: string;
  description: string | null;
  duration: string | null;
  order: number;
  created_at: string;
}

export interface WeeklyPlanItem {
  week: number;
  focus: string;
  // As of the Execution Engine phase this is display/historical JSON
  // only - real, checkable tasks come from GET /plans/{id}/tasks (see
  // types/task.ts:PlanTask) instead. Left loosely typed since older
  // plans stored plain strings here and newer ones store
  // {title, description, estimated_minutes} objects - nothing in the
  // frontend reads this field's tasks anymore, only `focus`.
  tasks: unknown[];
}

// Mirrors backend/app/schemas/planner.py's SuggestedMemory - shaped
// identically to MemoryCreateInput (types/memory.ts) on purpose, so
// accepting a suggestion is just `createMemory(suggestion)` with no
// reshaping (see features/planner/MemorySuggestionCard.tsx).
export interface SuggestedMemory {
  category: MemoryCategory;
  key: string;
  value: string;
}

export interface Plan {
  id: string;
  goal_id: string;
  mission: string;
  estimated_duration: string;
  timeline: string[];
  weekly_plan: WeeklyPlanItem[];
  milestones: Milestone[];
  created_at: string;
  updated_at: string;
  // Set only on the response from POST .../generate or .../regenerate -
  // how many of the user's Memory entries were injected into that call's
  // prompt as "User Context" (see backend/app/schemas/planner.py's
  // PlanRead). null on a plain GET, since re-fetching an existing plan
  // doesn't re-run memory lookup. Drives the small "Personalized using N
  // memories" indicator in PlanResultView - absent/null/0 shows nothing.
  memories_used?: number | null;
  // Same "only set right after generate/regenerate" treatment as
  // memories_used - a preference-shaped sentence the Planner noticed in
  // what the user just typed (a constraint or an Improve Plan
  // adjustment), offered as an opt-in "remember this?" suggestion.
  // Nothing is saved until the user clicks Accept - see
  // MemorySuggestionCard. null/absent means nothing was detected, or a
  // matching memory already exists.
  suggested_memory?: SuggestedMemory | null;
}

export interface GeneratePlanInput {
  timeline: string;
  availability: string;
  constraints: string[];
}

export interface RegeneratePlanInput {
  adjustment: string;
}
