import Card from "@/components/ui/Card";
import ProgressBar from "@/components/ui/ProgressBar";
import type { Progress } from "@/types/task";

/**
 * Progress UI for the Plan View - a bar plus "24/30 Tasks Completed",
 * per the Sprint 3 spec. `progress` is always a client-computed mirror
 * of PlanTask status (see lib/planTasks.ts:computeProgress), so this
 * updates the instant a checkbox is toggled rather than waiting on a
 * round trip to GET /plans/{id}/progress.
 */
export default function PlanProgress({ progress }: { progress: Progress }) {
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between gap-4">
        <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
          Progress
        </h2>
        <span className="text-foreground text-sm font-semibold">
          {progress.completed}/{progress.total} Tasks Completed
        </span>
      </div>
      <ProgressBar value={progress.percentage} />
    </Card>
  );
}
