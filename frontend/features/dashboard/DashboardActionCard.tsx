import { ArrowRight, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { gradients } from "@/design-system/gradients";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";

interface DashboardActionCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel: string;
  /** Navigates via Next's router - use for entry points that go to an
   * existing route (e.g. Habits -> /habits). Mutually exclusive with
   * `onAction`; exactly one should be passed. */
  href?: string;
  /** Runs a callback instead of navigating - use for entry points that
   * open an existing flow in place (e.g. Goal -> CreateGoalModal). */
  onAction?: () => void;
}

// Shared look for both the card and its "button" - one string used by
// whichever root element (Link or button) actually renders, so the two
// stay pixel-identical without duplicating the class list. Modeled on
// Card.tsx's floating-material style, but written out directly rather
// than importing Card - Card always renders a <div>, and this needs to
// be a single real <Link>/<button> (the whole tile is the click target,
// per the "clicking the card or button" requirement), which would mean
// nesting a second interactive element otherwise.
const cardClasses = `border-border bg-surface group relative flex flex-col items-start gap-5 overflow-hidden text-left ${radius["2xl"].class} border p-8 ${shadows.floating} ${motion.transition.cardHover} hover:bg-surface-hover hover:${motion.transform.hoverLift} hover:border-black/[0.12] hover:${shadows.floatingHover} focus-visible:ring-accent focus-visible:ring-2 focus-visible:outline-none`;

/**
 * The dashboard's primary action card (see DashboardActions.tsx - today
 * that's just Create Goal; Habits/Memory/future modules live in the
 * sidebar instead, see components/layout/navConfig.ts). Deliberately
 * generic - icon, title, description, action label, and either a `href`
 * or an `onAction` - kept reusable rather than Create-Goal-specific in
 * case a second genuinely goal-related dashboard action shows up later.
 */
export default function DashboardActionCard({
  icon: Icon,
  title,
  description,
  actionLabel,
  href,
  onAction,
}: DashboardActionCardProps) {
  const content = (
    <>
      <div
        className={`bg-accent/10 flex h-14 w-14 items-center justify-center ${radius.full.class}`}
      >
        <Icon size={24} className="text-accent" strokeWidth={1.75} />
      </div>

      <div className="flex flex-col gap-1.5">
        <h3 className="text-foreground text-xl font-semibold tracking-tight">{title}</h3>
        <p className="text-muted-foreground text-sm leading-relaxed">{description}</p>
      </div>

      <span
        className={`mt-1 inline-flex items-center gap-2 ${radius.lg.class} ${gradients.primaryButton} text-accent-foreground px-5 py-2.5 text-sm font-medium ${shadows.buttonPrimary} ${motion.transition.buttonHover} group-hover:brightness-[1.04]`}
      >
        {actionLabel}
        <ArrowRight
          size={15}
          className="transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:translate-x-0.5"
        />
      </span>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={cardClasses}>
        {content}
      </Link>
    );
  }

  return (
    <button type="button" onClick={onAction} className={`w-full ${cardClasses}`}>
      {content}
    </button>
  );
}
