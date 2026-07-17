/**
 * Mirrors backend/app/schemas/goal.py - keep these in sync manually until
 * a shared schema-generation step exists.
 */

export type GoalStatus = "not_started" | "in_progress" | "completed";

export interface Goal {
  id: string;
  title: string;
  description: string | null;
  status: GoalStatus;
  progress: number;
  created_at: string;
  updated_at: string;
  workspace_id: string;
}

export interface CreateGoalInput {
  title: string;
  description?: string;
}
