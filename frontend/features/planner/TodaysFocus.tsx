"use client";

import { Flame } from "lucide-react";
import Card from "@/components/ui/Card";
import { flattenTasks } from "@/lib/planTasks";
import type { PlanTask, WeekTasksGroup } from "@/types/task";
import { TaskRow } from "@/features/planner/TaskChecklist";

interface TodaysFocusProps {
  goalTitle: string;
  weeks: WeekTasksGroup[];
  onToggle: (task: PlanTask) => void;
}

/**
 * Reusable "what should I work on right now" summary - Goal, Current
 * Week, Today's Tasks (see Sprint 3 spec). LifeOS has no calendar or
 * plan-start-date concept yet (explicitly out of scope), so "current
 * week" isn't calendar-derived: it's the earliest week that still has a
 * pending task, i.e. wherever the user actually left off - and falls
 * forward to the plan's last week once everything is done, so the card
 * still shows *a* week instead of going blank.
 *
 * "Today's tasks" prefers day_number-tagged tasks within the current
 * week (day_number exists on PlanTask for exactly this - see
 * app/models/plan_task.py - but the planner doesn't assign it yet, so
 * this branch is forward-compatible rather than currently reachable) and
 * otherwise falls back to that week's remaining pending tasks, per spec.
 */
export default function TodaysFocus({ goalTitle, weeks, onToggle }: TodaysFocusProps) {
  const allTasks = flattenTasks(weeks);
  if (allTasks.length === 0) return null;

  const currentWeek =
    weeks.find((week) => week.tasks.some((task) => task.status === "pending")) ??
    weeks[weeks.length - 1];

  const dayTagged = currentWeek.tasks.filter(
    (task) => task.day_number !== null && task.status === "pending",
  );
  const todaysTasks =
    dayTagged.length > 0
      ? dayTagged
      : currentWeek.tasks.filter((task) => task.status === "pending");

  return (
    <Card className="border-accent/20">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-muted-foreground mb-1 text-xs font-medium tracking-wide uppercase">
            Today&apos;s Focus
          </h2>
          <p className="text-foreground text-sm font-semibold">{goalTitle}</p>
        </div>
        <span className="text-accent bg-accent/10 flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold">
          <Flame size={13} />
          Week {currentWeek.week_number}
        </span>
      </div>

      {todaysTasks.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Nothing left this week — nice work. Check the full plan below for what&apos;s next.
        </p>
      ) : (
        <ul className="flex flex-col gap-1">
          {todaysTasks.map((task) => (
            <TaskRow key={task.id} task={task} onToggle={onToggle} />
          ))}
        </ul>
      )}
    </Card>
  );
}
