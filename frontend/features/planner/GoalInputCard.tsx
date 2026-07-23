"use client";

import { useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import type { GeneratePlanInput } from "@/types/planner";

interface GoalInputCardProps {
  goalTitle: string;
  onGenerate: (input: GeneratePlanInput) => void;
  submitting: boolean;
  error: string | null;
}

/**
 * The Planner tab's starting state - one form, three fields, matching
 * the AI Planner MVP spec's user flow (goal is already known from the
 * Workspace this tab lives in; the form only asks for what the goal
 * itself can't tell us: timeline, availability, constraints).
 * Constraints are entered as a single comma-separated field rather than
 * a dynamic "add another" list - keeps the form to three visible fields
 * for a goal most people will only fill out once or twice per plan.
 *
 * All three fields are plain free text on the backend (see
 * app/schemas/planner.py's PlannerGenerateRequest - no unit is enforced,
 * no schema/API/prompt change made here - see the Goal Intake UX
 * Refinement sprint's "Preserve Existing Backend" requirement), but
 * wording that only reads naturally for one goal shape ("Available time
 * per week", "e.g. 10 hours/week") quietly tells everyone else - travel,
 * finance, fitness, personal-life goals - that they're using the form
 * "wrong." FIELD_COPY below is written so a recurring skill-building
 * goal ("Learn React"), a one-time project ("Build LifeOS MVP"), a
 * dated trip ("Plan a trip to Hyderabad"), a savings target ("Save
 * $10,000"), a fitness goal ("Run a marathon"), and a personal-life goal
 * ("Organize a wedding") each have an obvious, natural answer, without
 * introducing any goal-type-specific branching or new fields.
 *
 * FIELD_COPY is a plain object, not inlined into the JSX below, on
 * purpose: a future Goal Classification system (out of scope for this
 * sprint - see the sprint's "Keep Future Compatibility" requirement)
 * could pick a different copy set per detected goal type later by
 * swapping what's passed to each field, without restructuring this
 * component or touching the layout/validation around it.
 */
const FIELD_COPY = {
  timeline: {
    label: "Timeline",
    placeholder: 'e.g. 3 months, or "by December 15"',
    helper: 'Also works: "trip starts in 2 weeks", "before my interview"',
  },
  availability: {
    label: "Time You Can Dedicate",
    placeholder: 'e.g. 10 hours/week, or "evenings after work"',
    helper: 'Also works: "weekends only", "a few hours before departure"',
  },
  constraints: {
    label: "Constraints",
    placeholder: "e.g. no weekends, budget under $500",
    helper: "Optional - separate multiple constraints with commas.",
  },
} as const;

export default function GoalInputCard({
  goalTitle,
  onGenerate,
  submitting,
  error,
}: GoalInputCardProps) {
  const [timeline, setTimeline] = useState("");
  const [availability, setAvailability] = useState("");
  const [constraintsText, setConstraintsText] = useState("");

  const canSubmit = timeline.trim().length > 0 && availability.trim().length > 0;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    const constraints = constraintsText
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);

    onGenerate({ timeline: timeline.trim(), availability: availability.trim(), constraints });
  }

  return (
    <Card className="mx-auto max-w-xl">
      <div className="mb-5">
        <h2 className="text-foreground text-lg font-semibold">
          Let&apos;s plan &quot;{goalTitle}&quot;
        </h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Tell LifeOS your timeline and how much time you can dedicate, and it will generate a
          realistic execution plan - mission, milestones, and a step-by-step schedule.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label
            htmlFor="planner-timeline"
            className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase"
          >
            {FIELD_COPY.timeline.label}
          </label>
          <Input
            id="planner-timeline"
            autoFocus
            value={timeline}
            onChange={(e) => setTimeline(e.target.value)}
            placeholder={FIELD_COPY.timeline.placeholder}
          />
          <p className="text-muted-foreground mt-1.5 text-xs">{FIELD_COPY.timeline.helper}</p>
        </div>

        <div>
          <label
            htmlFor="planner-availability"
            className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase"
          >
            {FIELD_COPY.availability.label}
          </label>
          <Input
            id="planner-availability"
            value={availability}
            onChange={(e) => setAvailability(e.target.value)}
            placeholder={FIELD_COPY.availability.placeholder}
          />
          <p className="text-muted-foreground mt-1.5 text-xs">{FIELD_COPY.availability.helper}</p>
        </div>

        <div>
          <label
            htmlFor="planner-constraints"
            className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase"
          >
            {FIELD_COPY.constraints.label}
          </label>
          <Input
            id="planner-constraints"
            value={constraintsText}
            onChange={(e) => setConstraintsText(e.target.value)}
            placeholder={FIELD_COPY.constraints.placeholder}
          />
          <p className="text-muted-foreground mt-1.5 text-xs">{FIELD_COPY.constraints.helper}</p>
        </div>

        {error && <p className="text-danger text-sm">{error}</p>}

        <Button type="submit" disabled={!canSubmit || submitting} className="mt-1">
          {submitting ? "Generating your plan…" : "Generate Plan"}
        </Button>
      </form>
    </Card>
  );
}
