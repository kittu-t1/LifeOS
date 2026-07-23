/**
 * Mirrors backend/app/schemas/habit.py and app/models/habit.py - keep
 * these in sync manually (same convention as types/task.ts, types/replan.ts).
 */

export type RecurrenceType = "daily" | "weekdays" | "weekly" | "monthly" | "custom_interval";

export type HabitStatus = "active" | "paused";

export type HabitOccurrenceStatus = "pending" | "completed";

/**
 * Shape depends on recurrence_type - see backend/app/services/recurrence.py:
 *   daily / weekdays:  {} (nothing to configure)
 *   weekly:            { days_of_week: [0, 2, 4] }  (0=Monday..6=Sunday)
 *   monthly:           { day_of_month: 15 }
 *   custom_interval:   { interval_days: 3 }
 */
export interface RecurrenceConfig {
  days_of_week?: number[];
  day_of_month?: number;
  interval_days?: number;
}

export interface Habit {
  id: string;
  title: string;
  description: string | null;
  recurrence_type: RecurrenceType;
  recurrence_config: RecurrenceConfig;
  estimated_minutes: number | null;
  start_date: string;
  end_date: string | null;
  status: HabitStatus;
  created_at: string;
  updated_at: string;
}

export interface HabitOccurrence {
  id: string;
  habit_id: string;
  occurrence_date: string;
  status: HabitOccurrenceStatus;
  completed_at: string | null;
  created_at: string;
}

export interface HabitCreateInput {
  title: string;
  description?: string | null;
  recurrence_type: RecurrenceType;
  recurrence_config?: RecurrenceConfig;
  estimated_minutes?: number | null;
  start_date: string;
  end_date?: string | null;
}

export interface HabitUpdateInput {
  title?: string;
  description?: string | null;
  recurrence_type?: RecurrenceType;
  recurrence_config?: RecurrenceConfig;
  estimated_minutes?: number | null;
  start_date?: string;
  end_date?: string | null;
}
