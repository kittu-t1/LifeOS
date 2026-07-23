import type { Habit } from "@/types/habit";

/**
 * Mirrors backend/app/services/habit_service.py::_describe_recurrence
 * word-for-word - keep these in sync manually (same convention as
 * lib/goal-status.ts). Used anywhere a Habit's cadence needs to read as
 * a short human sentence instead of raw recurrence_type/recurrence_config.
 */
export function describeRecurrence(
  habit: Pick<Habit, "recurrence_type" | "recurrence_config" | "start_date">,
): string {
  const names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  switch (habit.recurrence_type) {
    case "daily":
      return "every day";
    case "weekdays":
      return "every weekday";
    case "weekly": {
      const days = [...(habit.recurrence_config.days_of_week ?? [])]
        .filter((d) => d >= 0 && d <= 6)
        .sort((a, b) => a - b);
      return days.length > 0 ? `every ${days.map((d) => names[d]).join(", ")}` : "weekly";
    }
    case "monthly": {
      const day = habit.recurrence_config.day_of_month ?? new Date(habit.start_date).getDate();
      return `monthly on day ${day}`;
    }
    case "custom_interval": {
      const interval = habit.recurrence_config.interval_days ?? 1;
      return `every ${interval} day(s)`;
    }
    default:
      return "recurring";
  }
}

/** Local YYYY-MM-DD for "today", matching what a date input expects and
 * what the backend's occurrence_date fields already are. */
export function todayIso(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset();
  return new Date(now.getTime() - offset * 60_000).toISOString().slice(0, 10);
}
