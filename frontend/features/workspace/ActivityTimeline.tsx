import { History } from "lucide-react";
import Card from "@/components/ui/Card";

/**
 * Reserved for the real, chronological event history of a Workspace:
 * goal creation, task completion, daily check-ins, planner updates,
 * knowledge updates, and execution history. None of those events are
 * tracked yet, so this intentionally shows an honest empty state rather
 * than synthesizing fake entries - distinct from the curated "Recent
 * Activity" summary card in OverviewSection, which surfaces what we
 * genuinely know happened (goal/workspace creation) plus what's coming.
 */
export default function ActivityTimeline() {
  return (
    <Card>
      <div className="mb-3 flex items-center gap-2">
        <History size={14} className="text-muted-foreground" />
        <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
          Activity Timeline
        </h2>
      </div>
      <p className="text-muted-foreground text-sm">No activity yet.</p>
    </Card>
  );
}
