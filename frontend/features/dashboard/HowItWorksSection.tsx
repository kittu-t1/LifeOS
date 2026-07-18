"use client";

import { useState } from "react";
import { ChevronRight } from "lucide-react";
import Card from "@/components/ui/Card";
import Modal from "@/components/ui/Modal";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { WORKFLOW_STEPS } from "@/features/dashboard/workflowSteps";

/**
 * The product's whole loop, told as five short beats rather than one
 * paragraph - each card is one idea (icon, name, one line), and the
 * row itself is the explanation: this is a cycle a goal moves through,
 * not five unrelated features.
 *
 * Tapping a card opens the same brief-detail Modal as the /explore page
 * (features/explore/ExploreView.tsx) - both read from the same
 * WORKFLOW_STEPS data, and both are independently clickable rather than
 * this row being a "look but don't touch" preview. A card that looks
 * and hovers like every other clickable card in the app but silently
 * does nothing on tap is a worse experience than a little duplicated
 * modal wiring.
 */
export default function HowItWorksSection() {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const active = activeIndex !== null ? WORKFLOW_STEPS[activeIndex] : null;

  return (
    <section>
      <div className="mx-auto flex max-w-xl flex-col items-center gap-3 text-center">
        <h2 className="text-foreground text-3xl font-semibold tracking-tight">How LifeOS works</h2>
        <p className="text-muted-foreground text-base leading-relaxed">
          One loop, repeated for every goal you bring to it.
        </p>
      </div>

      <div className="mt-12 flex flex-col items-stretch gap-3 lg:flex-row lg:items-center">
        {WORKFLOW_STEPS.map((step, i) => (
          <div key={step.label} className="flex items-center gap-3 lg:flex-1">
            <Card
              hoverable
              role="button"
              tabIndex={0}
              className={`${motion.animation.workflowReveal} focus-visible:ring-accent flex flex-1 cursor-pointer flex-col items-center gap-3 py-8 text-center focus-visible:ring-2 focus-visible:outline-none`}
              style={{ animationDelay: motion.staggerDelay(i) }}
              onClick={() => setActiveIndex(i)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setActiveIndex(i);
                }
              }}
            >
              <div className="bg-accent/10 flex h-11 w-11 items-center justify-center rounded-full">
                <step.icon size={19} className="text-accent" strokeWidth={1.75} />
              </div>
              <div className="flex flex-col gap-1">
                <h3 className="text-foreground text-sm font-semibold">{step.label}</h3>
                <p className="text-muted-foreground text-xs leading-relaxed">{step.description}</p>
              </div>
            </Card>
            {i < WORKFLOW_STEPS.length - 1 && (
              <ChevronRight
                size={16}
                className="text-muted-foreground/40 hidden shrink-0 lg:block"
              />
            )}
          </div>
        ))}
      </div>

      <Modal open={active !== null} onClose={() => setActiveIndex(null)}>
        {active && (
          <div className="flex flex-col gap-4">
            <div
              className={`bg-accent/10 flex h-12 w-12 items-center justify-center ${radius.full.class}`}
            >
              <active.icon size={22} className="text-accent" strokeWidth={1.75} />
            </div>
            <h2 className="text-foreground text-xl font-semibold">{active.label}</h2>
            <p className="text-muted-foreground text-sm leading-relaxed">{active.brief}</p>
            <button
              type="button"
              onClick={() => setActiveIndex(null)}
              className="text-muted-foreground hover:text-foreground self-start text-sm font-medium transition-colors duration-200"
            >
              Close
            </button>
          </div>
        )}
      </Modal>
    </section>
  );
}
