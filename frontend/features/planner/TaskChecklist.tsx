"use client";

import { CheckCircle2, Circle, Clock } from "lucide-react";
import { radius } from "@/design-system/radius";
import type { PlanTask, WeekTasksGroup } from "@/types/task";

interface TaskChecklistProps {
  weeks: WeekTasksGroup[];
  weekFocus: Record<number, string>;
  onToggle: (task: PlanTask) => void;
}

/**
 * Replaces the old static "read the AI's JSON out loud" weekly plan
 * rendering with real, checkable PlanTask rows (see types/task.ts and
 * services/tasks.ts) - the same visual shape (Week N badge + focus text
 * + a list) as the section it replaces in PlanResultView, but every item
 * is now a persisted, toggleable task instead of a plain string.
 * `weekFocus` comes from Plan.weekly_plan (still the only place `focus`
 * text lives - see types/planner.ts), keyed by week number since that's
 * the only link between the two right now.
 */
export default function TaskChecklist({ weeks, weekFocus, onToggle }: TaskChecklistProps) {
  return (
    <div className="flex flex-col gap-3">
      {weeks.map((week) => (
        <div
          key={week.week_number}
          className={`bg-surface-hover ${radius.xl.class} border-border border p-4`}
        >
          <div className="mb-2 flex items-baseline gap-2">
            <span className="text-accent text-xs font-semibold tracking-wide uppercase">
              Week {week.week_number}
            </span>
            {weekFocus[week.week_number] && (
              <span className="text-foreground text-sm font-medium">
                {weekFocus[week.week_number]}
              </span>
            )}
          </div>
          <ul className="flex flex-col gap-1">
            {week.tasks.map((task) => (
              <TaskRow key={task.id} task={task} onToggle={onToggle} />
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export function TaskRow({
  task,
  onToggle,
}: {
  task: PlanTask;
  onToggle: (task: PlanTask) => void;
}) {
  const done = task.status === "completed";
  return (
    <li>
      <button
        type="button"
        onClick={() => onToggle(task)}
        className="group flex w-full items-start gap-2.5 rounded-lg px-1 py-1.5 text-left text-sm transition-colors hover:bg-black/[0.03]"
      >
        {done ? (
          <CheckCircle2 size={16} className="text-success mt-0.5 shrink-0" />
        ) : (
          <Circle
            size={16}
            className="text-muted-foreground/40 group-hover:text-accent mt-0.5 shrink-0 transition-colors"
          />
        )}
        <span className="flex-1">
          <span className={done ? "text-muted-foreground line-through" : "text-foreground"}>
            {task.title}
          </span>
          {task.estimated_minutes !== null && (
            <span className="text-muted-foreground/70 ml-2 inline-flex items-center gap-1 text-xs">
              <Clock size={11} />
              {task.estimated_minutes}m
            </span>
          )}
          {/* The AI writes a one-sentence description for every task (see
              PLANNER_V5_SYSTEM_PROMPT's "Generate" section) but until now
              nothing ever displayed it - shown here, shared by both
              TaskChecklist and TodaysFocus since both render rows through
              this one component. */}
          {task.description && (
            <span className="text-muted-foreground mt-0.5 block text-xs leading-relaxed">
              {task.description}
            </span>
          )}
        </span>
      </button>
    </li>
  );
}
