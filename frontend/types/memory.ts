/**
 * Mirrors backend/app/memory/schemas/memory.py and
 * backend/app/memory/models/memory.py - keep these in sync manually
 * (same convention as types/habit.ts, types/task.ts).
 */

export type MemoryCategory =
  "preference" | "planning_context" | "habit_insight" | "learned_pattern" | "note";

export type MemorySource = "manual" | "system";

export interface Memory {
  id: string;
  category: MemoryCategory;
  key: string;
  value: string;
  source: MemorySource;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface MemoryCreateInput {
  category: MemoryCategory;
  key: string;
  value: string;
}

export interface MemoryUpdateInput {
  category?: MemoryCategory;
  key?: string;
  value?: string;
}
