import type { Goal } from "@/types/goal";

/** Mirrors backend/app/schemas/workspace.py. */
export interface Workspace {
  id: string;
  created_at: string;
  goal: Goal;
}
