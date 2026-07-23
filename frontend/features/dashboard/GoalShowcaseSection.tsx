import { Activity, ArrowUpRight, BrainCircuit, GraduationCap, Rocket } from "lucide-react";
import Card from "@/components/ui/Card";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";

const EXAMPLE_JOURNEYS = [
  {
    icon: BrainCircuit,
    title: "Learn Machine Learning",
    journey: "From curious beginner to confident builder.",
  },
  {
    icon: Rocket,
    title: "Build a Startup",
    journey: "From idea to something people use.",
  },
  {
    icon: Activity,
    title: "Improve Fitness",
    journey: "From first workout to lasting habit.",
  },
  {
    icon: GraduationCap,
    title: "Master a Skill",
    journey: "From practice to mastery.",
  },
];

/**
 * Not task cards - each example is framed as a journey (where someone
 * starts, where LifeOS takes them), matching the product's actual
 * shape: a goal becomes a workspace, not a checklist item. Clicking one
 * pre-fills CreateGoalModal via the same callback InspirationChips
 * uses, so the storytelling isn't just decoration - it's a real
 * shortcut into the product.
 *
 * No section heading here on purpose - "Every goal is a journey" was
 * removed, and the example cards below are self-explanatory (icon +
 * title + one line) without one.
 *
 * The "Explore LifeOS" tile that used to open this section (routes to
 * /explore - see features/explore/ExploreView.tsx) moved to the Home
 * page (features/home/HomeView.tsx) - Home is where people get oriented
 * on what LifeOS is; this page's job is narrower (actually creating a
 * goal), so a "learn how the loop works" link didn't belong here anymore.
 */
export default function GoalShowcaseSection({
  onSelectExample,
}: {
  onSelectExample: (title: string) => void;
}) {
  return (
    <section>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {EXAMPLE_JOURNEYS.map(({ icon: Icon, title, journey }, i) => (
          <Card
            key={title}
            hoverable
            role="button"
            tabIndex={0}
            className={`${motion.animation.workflowReveal} focus-visible:ring-accent group flex cursor-pointer flex-col gap-4 text-left focus-visible:ring-2 focus-visible:outline-none`}
            style={{ animationDelay: motion.staggerDelay(i) }}
            onClick={() => onSelectExample(title)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectExample(title);
              }
            }}
          >
            <div className="flex items-start justify-between">
              <div
                className={`bg-accent/10 flex h-11 w-11 items-center justify-center ${radius.full.class}`}
              >
                <Icon size={19} className="text-accent" strokeWidth={1.75} />
              </div>
              <ArrowUpRight
                size={16}
                className="text-muted-foreground/50 group-hover:text-accent transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <h3 className="text-foreground text-base font-semibold">{title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{journey}</p>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}
