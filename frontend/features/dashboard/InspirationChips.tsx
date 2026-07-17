import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";

const EXAMPLE_GOALS = [
  { icon: "🚀", label: "Build LifeOS MVP" },
  { icon: "💼", label: "Land Dream Job" },
  { icon: "🤖", label: "Launch AI Startup" },
  { icon: "✈️", label: "Europe Trip" },
  { icon: "🏋️", label: "Lose 10kg" },
  { icon: "📚", label: "Learn AI" },
];

/**
 * Clickable example goals shown in the empty dashboard state. Selecting
 * one pre-fills CreateGoalModal rather than creating the goal directly -
 * these are inspiration, not a shortcut that skips the user reviewing
 * what they're about to create. The icon is presentation only - the
 * clean label (without the emoji) is what gets passed to onSelect, so
 * it's what actually ends up as the goal's title.
 */
export default function InspirationChips({ onSelect }: { onSelect: (title: string) => void }) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2.5">
      {EXAMPLE_GOALS.map(({ icon, label }) => (
        <button
          key={label}
          type="button"
          onClick={() => onSelect(label)}
          className={`border-border bg-surface text-foreground hover:border-accent/30 hover:bg-surface-hover ${radius.pill.class} border px-4 py-2 text-sm ${motion.transition.chipHover} hover:${motion.transform.hoverLift} hover:scale-[1.02] hover:${shadows.chipGlowHover}`}
        >
          <span aria-hidden className="mr-1.5">
            {icon}
          </span>
          {label}
        </button>
      ))}
    </div>
  );
}
