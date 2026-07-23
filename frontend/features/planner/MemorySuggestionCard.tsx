"use client";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import type { SuggestedMemory } from "@/types/planner";

interface MemorySuggestionCardProps {
  suggestion: SuggestedMemory;
  onAccept: () => void;
  onDecline: () => void;
  saving: boolean;
  error: string | null;
}

/**
 * The "Would you like LifeOS to remember this preference?" prompt (see
 * the Memory Personalization sprint's follow-up spec). Appears only when
 * PlanRead.suggested_memory came back non-null on the response from
 * generate/regenerate - see types/planner.ts's Plan.suggested_memory and
 * PlannerView's handleGenerate/handleImprove.
 *
 * Deliberately opt-in, not automatic: nothing is written to Memory until
 * the user clicks Accept (see PlannerView.handleAcceptMemorySuggestion,
 * which calls the existing createMemory - the same endpoint the Memory
 * page's "New Memory" form uses, not a new one). Decline just dismisses
 * the card - no API call at all, "do nothing" per the spec. Either way
 * the card never reappears for this same generate/regenerate response,
 * and since suggested_memory isn't persisted on the Plan, a page reload
 * naturally clears it too rather than needing its own "already asked"
 * tracking.
 */
export default function MemorySuggestionCard({
  suggestion,
  onAccept,
  onDecline,
  saving,
  error,
}: MemorySuggestionCardProps) {
  return (
    <Card>
      <p className="text-muted-foreground mb-2 text-sm">
        Would you like LifeOS to remember this preference?
      </p>
      <p className="text-foreground mb-4 text-sm font-medium">&ldquo;{suggestion.value}&rdquo;</p>
      <div className="flex items-center gap-3">
        <Button variant="secondary" onClick={onAccept} disabled={saving}>
          {saving ? "Saving…" : "Remember this"}
        </Button>
        <Button variant="ghost" onClick={onDecline} disabled={saving}>
          Not now
        </Button>
      </div>
      {error && <p className="text-danger mt-2 text-sm">{error}</p>}
    </Card>
  );
}
