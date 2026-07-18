import { BellRing, BookOpen, Map, TrendingUp } from "lucide-react";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";

const CAPABILITIES = [
  {
    icon: Map,
    title: "Roadmap generation",
    description: "Turns a goal into a step-by-step plan tailored to you.",
  },
  {
    icon: TrendingUp,
    title: "Progress insights",
    description: "Understands where you're ahead, and where you're stuck.",
  },
  {
    icon: BellRing,
    title: "Smart reminders",
    description: "Nudges you at the right moment, not just on a schedule.",
  },
  {
    icon: BookOpen,
    title: "Personal reflection",
    description: "Helps you look back and see how far you've come.",
  },
];

/**
 * The one section that explains *why* LifeOS is more than a task list -
 * kept to a single sentence of explanation plus four concrete
 * capabilities, in a softly-tinted panel that visually sets the AI
 * layer apart from the rest of the page without turning the accent
 * color into the whole interface.
 */
export default function AIIntelligenceSection() {
  return (
    <section className="bg-accent/[0.04] border-border rounded-3xl border px-6 py-16 sm:px-12 sm:py-20">
      <div className="mx-auto flex max-w-2xl flex-col items-center gap-3 text-center">
        <h2 className="text-foreground text-3xl font-semibold tracking-tight">
          The intelligence behind LifeOS
        </h2>
        <p className="text-muted-foreground text-base leading-relaxed">
          LifeOS understands your goals and helps transform them into actionable plans.
        </p>
      </div>

      <div className="mx-auto mt-12 grid max-w-3xl grid-cols-1 gap-x-8 gap-y-10 sm:grid-cols-2">
        {CAPABILITIES.map(({ icon: Icon, title, description }, i) => (
          <div
            key={title}
            className={`${motion.animation.workflowReveal} flex items-start gap-4`}
            style={{ animationDelay: motion.staggerDelay(i) }}
          >
            <div
              className={`bg-surface flex h-11 w-11 shrink-0 items-center justify-center ${radius.full.class} ${shadows.floating}`}
            >
              <Icon
                size={18}
                className={`text-accent ${shadows.iconGlowAccent}`}
                strokeWidth={1.75}
              />
            </div>
            <div className="flex flex-col gap-1">
              <h3 className="text-foreground text-sm font-semibold">{title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
