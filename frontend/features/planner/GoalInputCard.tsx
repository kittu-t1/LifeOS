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
 */
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
          Tell LifeOS your timeline and availability, and it will generate a realistic execution
          plan - mission, milestones, and a week-by-week schedule.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label
            htmlFor="planner-timeline"
            className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase"
          >
            Desired timeline
          </label>
          <Input
            id="planner-timeline"
            autoFocus
            value={timeline}
            onChange={(e) => setTimeline(e.target.value)}
            placeholder="e.g. 90 days"
          />
        </div>

        <div>
          <label
            htmlFor="planner-availability"
            className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase"
          >
            Available time per week
          </label>
          <Input
            id="planner-availability"
            value={availability}
            onChange={(e) => setAvailability(e.target.value)}
            placeholder="e.g. 10 hours/week"
          />
        </div>

        <div>
          <label
            htmlFor="planner-constraints"
            className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase"
          >
            Constraints <span className="normal-case">(optional)</span>
          </label>
          <Input
            id="planner-constraints"
            value={constraintsText}
            onChange={(e) => setConstraintsText(e.target.value)}
            placeholder="e.g. no weekends, budget under $500"
          />
          <p className="text-muted-foreground mt-1.5 text-xs">
            Separate multiple constraints with commas.
          </p>
        </div>

        {error && <p className="text-danger text-sm">{error}</p>}

        <Button type="submit" disabled={!canSubmit || submitting} className="mt-1">
          {submitting ? "Generating your plan…" : "Generate Plan"}
        </Button>
      </form>
    </Card>
  );
}
