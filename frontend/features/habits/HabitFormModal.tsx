"use client";

import { useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { radius } from "@/design-system/radius";
import { todayIso } from "@/lib/habits";
import type { Habit, HabitCreateInput, RecurrenceType } from "@/types/habit";

interface HabitFormModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: HabitCreateInput) => void;
  submitting: boolean;
  error: string | null;
  /** Present when editing an existing habit - prefills the form and
   * changes the submit copy. Absent means "create new". */
  editingHabit?: Habit | null;
}

const RECURRENCE_OPTIONS: { value: RecurrenceType; label: string }[] = [
  { value: "daily", label: "Daily" },
  { value: "weekdays", label: "Weekdays (Mon-Fri)" },
  { value: "weekly", label: "Weekly (choose days)" },
  { value: "monthly", label: "Monthly (choose day)" },
  { value: "custom_interval", label: "Every N days" },
];

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

/**
 * Create/edit form for a Habit (see backend/app/schemas/habit.py). The
 * only field whose shape actually varies is recurrence_config - what it
 * needs depends entirely on recurrence_type (see
 * backend/app/services/recurrence.py), so this renders one of three
 * small sub-controls (day-of-week toggles / day-of-month number /
 * interval-days number) instead of a generic JSON field. Daily and
 * Weekdays need no config at all.
 */
export default function HabitFormModal({
  open,
  onClose,
  onSubmit,
  submitting,
  error,
  editingHabit,
}: HabitFormModalProps) {
  const isEditing = Boolean(editingHabit);

  const [title, setTitle] = useState(editingHabit?.title ?? "");
  const [description, setDescription] = useState(editingHabit?.description ?? "");
  const [recurrenceType, setRecurrenceType] = useState<RecurrenceType>(
    editingHabit?.recurrence_type ?? "daily",
  );
  const [daysOfWeek, setDaysOfWeek] = useState<number[]>(
    editingHabit?.recurrence_config.days_of_week ?? [],
  );
  const [dayOfMonth, setDayOfMonth] = useState(
    editingHabit?.recurrence_config.day_of_month?.toString() ?? "1",
  );
  const [intervalDays, setIntervalDays] = useState(
    editingHabit?.recurrence_config.interval_days?.toString() ?? "2",
  );
  const [estimatedMinutes, setEstimatedMinutes] = useState(
    editingHabit?.estimated_minutes?.toString() ?? "",
  );
  const [startDate, setStartDate] = useState(editingHabit?.start_date ?? todayIso());
  const [endDate, setEndDate] = useState(editingHabit?.end_date ?? "");

  const needsWeekdayPicker = recurrenceType === "weekly";
  const canSubmit =
    title.trim().length > 0 &&
    startDate.length > 0 &&
    (!needsWeekdayPicker || daysOfWeek.length > 0);

  function toggleDay(day: number) {
    setDaysOfWeek((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort((a, b) => a - b),
    );
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    let recurrence_config = {};
    if (recurrenceType === "weekly") recurrence_config = { days_of_week: daysOfWeek };
    if (recurrenceType === "monthly") recurrence_config = { day_of_month: Number(dayOfMonth) || 1 };
    if (recurrenceType === "custom_interval")
      recurrence_config = { interval_days: Number(intervalDays) || 1 };

    onSubmit({
      title: title.trim(),
      description: description.trim() || null,
      recurrence_type: recurrenceType,
      recurrence_config,
      estimated_minutes: estimatedMinutes ? Number(estimatedMinutes) : null,
      start_date: startDate,
      end_date: endDate || null,
    });
  }

  return (
    <Modal open={open} onClose={onClose}>
      <div className="mb-4">
        <h2 className="text-foreground text-lg font-semibold">
          {isEditing ? "Edit Habit" : "New Habit"}
        </h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Recurring commitments show up in your schedule automatically, and the Planner works around
          them.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
            Title
          </label>
          <Input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Morning workout"
          />
        </div>

        <div>
          <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
            Description <span className="normal-case">(optional)</span>
          </label>
          <Input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. 30 min cardio + stretching"
          />
        </div>

        <div>
          <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
            Repeats
          </label>
          <select
            value={recurrenceType}
            onChange={(e) => setRecurrenceType(e.target.value as RecurrenceType)}
            className={`border-border bg-background text-foreground focus:border-accent focus:ring-accent w-full ${radius.lg.class} border px-3.5 py-2.5 text-sm focus:ring-1 focus:outline-none`}
          >
            {RECURRENCE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {recurrenceType === "weekly" && (
          <div className="flex flex-wrap gap-1.5">
            {DAY_LABELS.map((label, day) => (
              <button
                key={label}
                type="button"
                onClick={() => toggleDay(day)}
                className={`${radius.lg.class} border px-3 py-1.5 text-xs font-medium transition-colors ${
                  daysOfWeek.includes(day)
                    ? "border-accent bg-accent/15 text-accent"
                    : "border-border bg-surface text-muted-foreground hover:bg-surface-hover"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        )}

        {recurrenceType === "monthly" && (
          <div>
            <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
              Day of month
            </label>
            <Input
              type="number"
              min={1}
              max={31}
              value={dayOfMonth}
              onChange={(e) => setDayOfMonth(e.target.value)}
            />
          </div>
        )}

        {recurrenceType === "custom_interval" && (
          <div>
            <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
              Repeat every N days
            </label>
            <Input
              type="number"
              min={1}
              value={intervalDays}
              onChange={(e) => setIntervalDays(e.target.value)}
            />
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
              Start date
            </label>
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div>
            <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
              End date <span className="normal-case">(optional)</span>
            </label>
            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
        </div>

        <div>
          <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
            Estimated time <span className="normal-case">(optional, minutes)</span>
          </label>
          <Input
            type="number"
            min={1}
            value={estimatedMinutes}
            onChange={(e) => setEstimatedMinutes(e.target.value)}
            placeholder="e.g. 45"
          />
        </div>

        {error && <p className="text-danger text-sm">{error}</p>}

        <div className="flex items-center justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={!canSubmit || submitting}>
            {submitting ? "Saving…" : isEditing ? "Save changes" : "Create habit"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
