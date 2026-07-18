import { BookOpen, ListChecks, Sparkles, Target, Trophy } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface WorkflowStep {
  icon: LucideIcon;
  label: string;
  /** One line - the tile's always-visible summary on the /explore page. */
  description: string;
  /** A few sentences - shown in the tap-to-reveal detail modal on /explore. */
  brief: string;
}

/**
 * The product's whole loop, told as five beats. Single source of truth
 * for the /explore page (features/explore/ExploreView.tsx). This used
 * to also back a compact inline teaser on the homepage
 * (HowItWorksSection.tsx), but that duplicated /explore for no real
 * benefit once the Hero's "Explore LifeOS" link reliably took people to
 * the full version, so it was removed - this file is now /explore's
 * only consumer.
 */
export const WORKFLOW_STEPS: WorkflowStep[] = [
  {
    icon: Target,
    label: "Goal",
    description: "State what you want to achieve, in plain language.",
    brief:
      'Every journey in LifeOS starts with a single sentence - no forms, no rigid templates. Tell LifeOS what you\'re trying to achieve, whether it\'s "learn machine learning" or "get in better shape," and the AI takes it from there. The goal you state here becomes the anchor for everything that follows: the roadmap, the daily tasks, and the milestones that mark your progress.',
  },
  {
    icon: Sparkles,
    label: "AI Planning",
    description: "LifeOS turns it into a concrete roadmap.",
    brief:
      "LifeOS breaks your goal down into a concrete, sequenced roadmap - the milestones, skills, or steps that actually get you there, tailored to where you're starting from. Instead of staring at a blank page wondering what to do first, you get a plan you can act on immediately, and it adapts as your circumstances change.",
  },
  {
    icon: ListChecks,
    label: "Daily Execution",
    description: "Work the plan, one day at a time.",
    brief:
      "Big goals are won in small daily sessions, not single bursts of motivation. LifeOS turns your roadmap into a day-by-day rhythm, so you always know exactly what today's next action is - no re-planning required every morning. Along the way, it tracks where you're ahead and where you're stuck, and nudges you at the right moment rather than on a fixed schedule.",
  },
  {
    icon: BookOpen,
    label: "Reflection",
    description: "Review what happened, adjust what's next.",
    brief:
      "Progress isn't just moving forward - it's understanding what worked and what didn't. LifeOS prompts you to reflect on completed work, surfaces patterns in your habits, and helps you adjust the plan based on how things are actually going, not just how they were supposed to go.",
  },
  {
    icon: Trophy,
    label: "Achievement",
    description: "Intentions become outcomes you can see.",
    brief:
      "Every completed step compounds. LifeOS tracks how far you've come from your original goal and marks the milestones along the way, so progress isn't just something you feel - it's something you can point to.",
  },
];
