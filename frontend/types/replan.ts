/**
 * Mirrors backend/app/schemas/replan.py - keep these in sync manually
 * (same convention as types/planner.ts, types/task.ts).
 */

export interface TaskAssignment {
  task_id: string;
  week_number: number;
  day_number: number | null;
}

export interface TaskReschedule {
  task_id: string;
  title: string;
  estimated_minutes: number | null;
  previous_week: number;
  new_week: number;
}

export interface ReplanProposal {
  plan_id: string;
  reason: string;
  changes: TaskReschedule[];
  remaining_effort_minutes: number;
  // "YYYY-MM-DD" or null (a plan with nothing left has no estimate)
  new_completion_estimate: string | null;
  deadline_at_risk: boolean;
  task_assignments: TaskAssignment[];
}

export interface ReplanEvent {
  id: string;
  plan_id: string;
  reason: string;
  summary: Record<string, unknown>;
  created_at: string;
}
