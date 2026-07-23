"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Modal from "@/components/ui/Modal";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { WORKFLOW_STEPS } from "@/features/dashboard/workflowSteps";

/**
 * The destination behind the Hero's "Explore LifeOS" link - previously
 * that link just scrolled down to a compact "How LifeOS works" teaser
 * inline on the homepage. A dedicated page reads better for "learn more
 * before you commit": each step is tappable, and tapping one opens a
 * brief with more detail than a homepage teaser would have room for.
 *
 * The homepage briefly had its own copy of this same row (with the same
 * tap-to-reveal behavior added after users tried tapping it there too),
 * but that meant identical content living in two places - it was
 * removed in favor of this being the one place this content lives,
 * reached through one reliable link.
 */
export default function ExploreView() {
  const router = useRouter();
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const active = activeIndex !== null ? WORKFLOW_STEPS[activeIndex] : null;

  return (
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-14 px-8 py-16 sm:py-20">
      {/* Back to Home, not Goals - the "Explore LifeOS" tile that leads
          here now lives on the Home page (see features/home/HomeView.tsx),
          not the Goals page. */}
      <Link
        href="/"
        className="text-muted-foreground hover:text-foreground inline-flex w-fit items-center gap-1.5 text-sm font-medium transition-colors duration-200"
      >
        <ArrowLeft size={15} />
        Back to Home
      </Link>

      <div className="animate-fade-in-up flex flex-col items-center gap-3 text-center">
        <h1 className="text-foreground text-4xl font-semibold tracking-tight">How LifeOS works</h1>
        <p className="text-muted-foreground max-w-xl text-lg leading-relaxed">
          One loop, repeated for every goal you bring to it. Tap a step to see how it works.
        </p>
      </div>

      <div className="flex flex-col items-stretch gap-4 sm:grid sm:grid-cols-2 lg:grid-cols-5">
        {WORKFLOW_STEPS.map((step, i) => (
          <Card
            key={step.label}
            hoverable
            role="button"
            tabIndex={0}
            className={`${motion.animation.workflowReveal} focus-visible:ring-accent group flex cursor-pointer flex-col items-center gap-3 py-8 text-center focus-visible:ring-2 focus-visible:outline-none`}
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
            <span className="text-accent inline-flex items-center gap-1 text-xs font-medium opacity-0 transition-opacity duration-300 group-hover:opacity-100">
              Learn more
              <ArrowRight size={12} />
            </span>
          </Card>
        ))}
      </div>

      <div className="border-border flex flex-col items-center gap-4 border-t pt-12 text-center">
        <p className="text-muted-foreground text-sm">Ready to put it to work?</p>
        <Button onClick={() => router.push("/goals")}>
          Create Your First Goal
          <ArrowRight size={15} />
        </Button>
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
    </div>
  );
}
