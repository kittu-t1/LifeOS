"use client";

import { AlertTriangle, ArrowRight, CalendarClock, Clock } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import { radius } from "@/design-system/radius";
import { formatDate } from "@/lib/format";
import type { ReplanProposal } from "@/types/replan";

interface ReplanModalProps {
  open: boolean;
  proposal: ReplanProposal | null;
  onDiscard: () => void;
  onAccept: () => void;
  accepting: boolean;
  error: string | null;
}

function formatEffort(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins}m`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}m`;
}

/**
 * Review step for the Adaptive Planning Engine (see services/replan.ts) -
 * shows what POST /replan proposed without having saved anything yet, so
 * the user can Accept or Discard rather than the plan silently rewriting
 * itself. Matches ImprovePlanModal's pattern of a plain Modal with
 * domain content instead of a form.
 */
export default function ReplanModal({
  open,
  proposal,
  onDiscard,
  onAccept,
  accepting,
  error,
}: ReplanModalProps) {
  if (!proposal) return null;
  const hasChanges = proposal.changes.length > 0;

  return (
    <Modal open={open} onClose={onDiscard}>
      <div className="mb-4">
        <h2 className="text-foreground text-lg font-semibold">Replan</h2>
        <p className="text-muted-foreground mt-1 text-sm">{proposal.reason}</p>
      </div>

      {hasChanges ? (
        <ul className={`bg-surface-hover ${radius.lg.class} mb-4 flex flex-col gap-1.5 p-3`}>
          {proposal.changes.map((change) => (
            <li key={change.task_id} className="flex items-center justify-between gap-3 text-sm">
              <span className="text-foreground truncate">{change.title}</span>
              <span className="text-muted-foreground flex shrink-0 items-center gap-1.5 text-xs">
                Week {change.previous_week}
                <ArrowRight size={11} />
                Week {change.new_week}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground mb-4 text-sm">Nothing needs to move.</p>
      )}

      <div className="flex flex-col gap-2 text-sm">
        <div className="flex items-center gap-2">
          <Clock size={14} className="text-muted-foreground" />
          <span className="text-muted-foreground">Remaining effort:</span>
          <span className="text-foreground font-medium">
            {formatEffort(proposal.remaining_effort_minutes)}
          </span>
        </div>
        {proposal.new_completion_estimate && (
          <div className="flex items-center gap-2">
            <CalendarClock size={14} className="text-muted-foreground" />
            <span className="text-muted-foreground">New completion estimate:</span>
            <span className="text-foreground font-medium">
              {formatDate(proposal.new_completion_estimate)}
            </span>
          </div>
        )}
        {proposal.deadline_at_risk && (
          <div className="mt-1 flex items-center gap-2">
            <Badge tone="warning">
              <span className="flex items-center gap-1">
                <AlertTriangle size={11} />
                Past your goal deadline
              </span>
            </Badge>
          </div>
        )}
      </div>

      {error && <p className="text-danger mt-4 text-sm">{error}</p>}

      <div className="mt-5 flex items-center justify-end gap-2">
        <Button type="button" variant="ghost" onClick={onDiscard} disabled={accepting}>
          Discard
        </Button>
        <Button type="button" onClick={onAccept} disabled={!hasChanges || accepting}>
          {accepting ? "Applying…" : "Accept Changes"}
        </Button>
      </div>
    </Modal>
  );
}
