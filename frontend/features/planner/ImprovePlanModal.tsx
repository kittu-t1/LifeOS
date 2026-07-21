"use client";

import { useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { radius } from "@/design-system/radius";

interface ImprovePlanModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (adjustment: string) => void;
  submitting: boolean;
  error: string | null;
}

const PRESETS = [
  {
    label: "More realistic",
    adjustment: "Make the plan more realistic and achievable, even if it takes longer.",
  },
  {
    label: "More aggressive",
    adjustment: "Make the plan more aggressive and fast-paced, even if it's more demanding.",
  },
  {
    label: "Shorter timeline",
    adjustment: "Compress the plan into a shorter timeline.",
  },
  {
    label: "Beginner friendly",
    adjustment: "Make the plan more beginner-friendly, with more foundational steps.",
  },
];

/**
 * "Improve Plan" (see PlanResultView) opens this instead of blindly
 * resubmitting the same inputs - four one-tap presets cover the common
 * asks, plus a free-text field for anything else. Either path calls the
 * same onSubmit(adjustment); the backend (planner_service.regenerate_plan)
 * doesn't care which one produced the string.
 */
export default function ImprovePlanModal({
  open,
  onClose,
  onSubmit,
  submitting,
  error,
}: ImprovePlanModalProps) {
  const [customAdjustment, setCustomAdjustment] = useState("");

  function handleCustomSubmit(e: FormEvent) {
    e.preventDefault();
    if (!customAdjustment.trim()) return;
    onSubmit(customAdjustment.trim());
  }

  return (
    <Modal open={open} onClose={onClose}>
      <div className="mb-4">
        <h2 className="text-foreground text-lg font-semibold">Improve Plan</h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Pick a direction, or describe what you&apos;d like changed. LifeOS will revise your plan,
          not start over.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            disabled={submitting}
            onClick={() => onSubmit(preset.adjustment)}
            className={`border-border bg-surface hover:bg-surface-hover hover:border-black/[0.12] ${radius.lg.class} border px-3 py-2.5 text-left text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50`}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <div className="text-muted-foreground my-4 flex items-center gap-3 text-xs">
        <span className="border-border h-px flex-1 border-t" />
        or describe it yourself
        <span className="border-border h-px flex-1 border-t" />
      </div>

      <form onSubmit={handleCustomSubmit} className="flex flex-col gap-3">
        <Input
          value={customAdjustment}
          onChange={(e) => setCustomAdjustment(e.target.value)}
          placeholder="e.g. focus more on portfolio projects"
          disabled={submitting}
        />

        {error && <p className="text-danger text-sm">{error}</p>}

        <div className="flex items-center justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={!customAdjustment.trim() || submitting}>
            {submitting ? "Improving…" : "Regenerate"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
