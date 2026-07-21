/**
 * Mirrors backend/app/schemas/planner.py - keep these in sync manually
 * until a shared schema-generation step exists (same convention as
 * types/goal.ts and types/workspace.ts).
 */

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
  tasks: string[];
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
}

export interface GeneratePlanInput {
  timeline: string;
  availability: string;
  constraints: string[];
}

export interface RegeneratePlanInput {
  adjustment: string;
}
