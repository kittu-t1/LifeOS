"use client";

import { CheckCircle2, ChevronDown, Circle, Clock, Pause, Pencil, Play } from "lucide-react";
import { useEffect, useState } from "react";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import { radius } from "@/design-system/radius";
import { describeRecurrence, todayIso } from "@/lib/habits";
import { listOccurrences, updateOccurrenceStatus } from "@/services/habits";
import type { Habit, HabitOccurrence } from "@/types/habit";

interface HabitCardProps {
  habit: Habit;
  onEdit: () => void;
  onTogglePause: () => void;
  pauseToggling: boolean;
}

/**
 * One Habit's card - cadence + status at a glance, today's occurrence as
 * a one-click complete action (the spec's "completing today's occurrence
 * while the recurring schedule stays active"), and the rest of the
 * generated window collapsed behind "Upcoming" since most days nobody
 * needs to look past today. Occurrences are fetched per-card (not lifted
 * to HabitsView) since GET .../occurrences is what actually triggers the
 * backend's sync_occurrences top-up (see app/api/v1/habits.py) - each
 * card is responsible for keeping its own habit's window fresh.
 */
export default function HabitCard({ habit, onEdit, onTogglePause, pauseToggling }: HabitCardProps) {
  const [occurrences, setOccurrences] = useState<HabitOccurrence[] | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listOccurrences(habit.id)
      .then((rows) => {
        if (!cancelled) setOccurrences(rows);
      })
      .catch(() => {
        if (!cancelled) setOccurrences([]);
      });
    return () => {
      cancelled = true;
    };
  }, [habit.id]);

  async function handleToggleOccurrence(occurrence: HabitOccurrence) {
    if (!occurrences) return;
    const nextStatus = occurrence.status === "completed" ? "pending" : "completed";
    const previous = occurrences;
    setTogglingId(occurrence.id);
    setOccurrences(
      occurrences.map((o) =>
        o.id === occurrence.id
          ? {
              ...o,
              status: nextStatus,
              completed_at: nextStatus === "completed" ? new Date().toISOString() : null,
            }
          : o,
      ),
    );
    try {
      await updateOccurrenceStatus(occurrence.id, nextStatus);
    } catch {
      setOccurrences(previous);
    } finally {
      setTogglingId(null);
    }
  }

  const today = todayIso();
  const todayOccurrence = occurrences?.find((o) => o.occurrence_date === today) ?? null;
  const upcoming = (occurrences ?? []).filter((o) => o.occurrence_date > today);

  return (
    <Card>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-foreground text-base font-semibold">{habit.title}</h3>
            <Badge tone={habit.status === "active" ? "accent" : "neutral"}>
              {habit.status === "active" ? "Active" : "Paused"}
            </Badge>
          </div>
          {habit.description && (
            <p className="text-muted-foreground mt-0.5 text-sm">{habit.description}</p>
          )}
          <div className="text-muted-foreground mt-2 flex flex-wrap items-center gap-3 text-xs">
            <span>{describeRecurrence(habit)}</span>
            {habit.estimated_minutes !== null && (
              <span className="inline-flex items-center gap-1">
                <Clock size={11} />
                {habit.estimated_minutes}m
              </span>
            )}
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={onEdit}
            aria-label="Edit habit"
            className={`text-muted-foreground hover:bg-surface-hover hover:text-foreground flex h-8 w-8 items-center justify-center ${radius.lg.class} transition-colors`}
          >
            <Pencil size={15} />
          </button>
          <button
            type="button"
            onClick={onTogglePause}
            disabled={pauseToggling}
            aria-label={habit.status === "active" ? "Pause habit" : "Resume habit"}
            className={`text-muted-foreground hover:bg-surface-hover hover:text-foreground flex h-8 w-8 items-center justify-center ${radius.lg.class} transition-colors disabled:opacity-50`}
          >
            {habit.status === "active" ? <Pause size={15} /> : <Play size={15} />}
          </button>
        </div>
      </div>

      {habit.status === "active" && (
        <div className="border-border mt-4 border-t pt-3">
          {todayOccurrence ? (
            <OccurrenceRow
              occurrence={todayOccurrence}
              label="Today"
              onToggle={handleToggleOccurrence}
              toggling={togglingId === todayOccurrence.id}
            />
          ) : (
            <p className="text-muted-foreground text-xs">No occurrence scheduled today.</p>
          )}

          {upcoming.length > 0 && (
            <div className="mt-2">
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="text-muted-foreground hover:text-foreground flex items-center gap-1 text-xs font-medium transition-colors"
              >
                <ChevronDown
                  size={13}
                  className={`transition-transform ${expanded ? "rotate-180" : ""}`}
                />
                {expanded ? "Hide upcoming" : `View upcoming (${upcoming.length})`}
              </button>
              {expanded && (
                <ul className="mt-2 flex flex-col gap-0.5">
                  {upcoming.map((occurrence) => (
                    <OccurrenceRow
                      key={occurrence.id}
                      occurrence={occurrence}
                      label={formatShortDate(occurrence.occurrence_date)}
                      onToggle={handleToggleOccurrence}
                      toggling={togglingId === occurrence.id}
                    />
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function OccurrenceRow({
  occurrence,
  label,
  onToggle,
  toggling,
}: {
  occurrence: HabitOccurrence;
  label: string;
  onToggle: (occurrence: HabitOccurrence) => void;
  toggling: boolean;
}) {
  const done = occurrence.status === "completed";
  return (
    <li>
      <button
        type="button"
        disabled={toggling}
        onClick={() => onToggle(occurrence)}
        className="group flex w-full items-center gap-2.5 rounded-lg px-1 py-1.5 text-left text-sm transition-colors hover:bg-black/[0.03] disabled:opacity-50"
      >
        {done ? (
          <CheckCircle2 size={16} className="text-success shrink-0" />
        ) : (
          <Circle
            size={16}
            className="text-muted-foreground/40 group-hover:text-accent shrink-0 transition-colors"
          />
        )}
        <span className={done ? "text-muted-foreground line-through" : "text-foreground"}>
          {label}
        </span>
      </button>
    </li>
  );
}

function formatShortDate(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}
