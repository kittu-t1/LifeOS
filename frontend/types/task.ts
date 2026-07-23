/**
 * Mirrors backend/app/schemas/task.py - keep these in sync manually
 * (same convention as types/planner.ts, types/goal.ts).
 */

export type PlanTaskStatus = "pending" | "completed";

export interface PlanTask {
  id: string;
  plan_id: string;
  milestone_id: string | null;
  week_number: number;
  day_number: number | null;
  title: string;
  description: string | null;
  estimated_minutes: number | null;
  display_order: number;
  status: PlanTaskStatus;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WeekTasksGroup {
  week_number: number;
  tasks: PlanTask[];
}

export interface PlanTasksResponse {
  weeks: WeekTasksGroup[];
}

export interface Progress {
  completed: number;
  total: number;
  remaining: number;
  percentage: number;
}
