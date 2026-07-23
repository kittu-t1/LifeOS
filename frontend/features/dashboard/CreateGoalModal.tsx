"use client";

import { useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { createGoal } from "@/services/goals";
import type { Goal } from "@/types/goal";

interface CreateGoalModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (goal: Goal) => void;
  /** Pre-fills the title field - used when the user clicks an
   * InspirationChips example rather than typing their own goal. */
  initialTitle?: string;
}

// One example per goal category the Planner should feel natural for
// (see the Goal Intake UX Refinement sprint's audit categories:
// learning, project, travel, finance, fitness, personal-life) - not
// just project/career goals, so the placeholder itself signals that
// LifeOS isn't only for that one kind of goal.
const EXAMPLES = [
  "Learn React",
  "Build LifeOS MVP",
  "Plan a Trip to Hyderabad",
  "Save $10,000",
  "Run a Marathon",
  "Organize a Wedding",
];

/**
 * Creating a goal immediately creates its Workspace on the backend (see
 * goal_service.create_goal). Once created, we hand the goal straight back
 * to the caller, which navigates into the new Workspace - the user never
 * has to think about "workspace creation" as a separate step, matching
 * the product philosophy: users manage Goals, LifeOS manages the rest.
 */
export default function CreateGoalModal({
  open,
  onClose,
  onCreated,
  initialTitle = "",
}: CreateGoalModalProps) {
  const [title, setTitle] = useState(initialTitle);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Lazy initializer runs exactly once on mount rather than on every
  // render, which is what makes calling Math.random() here safe under
  // React's purity rules (a plain call during render is not allowed).
  const [placeholder] = useState(() => EXAMPLES[Math.floor(Math.random() * EXAMPLES.length)]);

  // Sync the field to whatever example (if any) was just clicked each
  // time the modal opens - CreateGoalModal itself never unmounts (only
  // the inner <Modal> conditionally renders), so this can't rely on
  // initial state alone. Adjusted during render rather than in a
  // useEffect, per React's guidance for "resetting state when a prop
  // changes" - this bails out after one extra render instead of the
  // effect-then-second-render round trip an effect would cause.
  const [wasOpen, setWasOpen] = useState(open);
  if (open !== wasOpen) {
    setWasOpen(open);
    if (open) setTitle(initialTitle);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const goal = await createGoal({ title: title.trim() });
      setTitle("");
      onCreated(goal);
    } catch {
      setError("Couldn't create that goal. Is the backend running?");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <h2 className="text-foreground text-lg font-semibold">
            What are you trying to accomplish?
          </h2>
          <p className="text-muted-foreground mt-1 text-sm">
            State your goal in plain language. LifeOS will create a dedicated Workspace for it.
          </p>
        </div>

        <Input
          autoFocus
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={placeholder}
        />

        {error && <p className="text-danger text-sm">{error}</p>}

        <div className="flex items-center justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={!title.trim() || submitting}>
            {submitting ? "Creating…" : "Create Goal"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
