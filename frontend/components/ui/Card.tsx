import type { HTMLAttributes, ReactNode } from "react";
import { gradients } from "@/design-system/gradients";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hoverable?: boolean;
}

/**
 * Floating-material card (Apple-style redesign pass). A soft radial
 * highlight in the top-left corner plus a light inset top edge give it
 * a sense of being its own physical surface, without heavy
 * glassmorphism - no strong backdrop blur, no busy saturation, just a
 * hairline border and quiet lighting (closer to visionOS materials than
 * frosted glass). `hoverable` adds a gentle lift and a touch more
 * presence on hover, used for clickable cards like GoalCard. The
 * decorative highlight is `absolute`, so it drops out of flex flow and
 * never interferes with a `className` like "flex flex-col gap-4" passed
 * in by a caller.
 *
 * Colors, shadows, and motion all come from the design system
 * (@/design-system) - `hover:border-white/[0.14]` is the one exception,
 * left as Tailwind's own color+opacity syntax (equivalent to
 * `colors.borderStrong`) since a raw rgba string with spaces can't be
 * safely interpolated into a Tailwind arbitrary-value class.
 */
export default function Card({ children, hoverable = false, className = "", ...rest }: CardProps) {
  return (
    <div
      className={`border-border bg-surface relative overflow-hidden ${radius.lg.class} border p-5 ${shadows.floating} ${motion.transition.cardHover} ${hoverable ? `hover:bg-surface-hover hover:${motion.transform.hoverLift} hover:border-white/[0.14] hover:${shadows.floatingHover}` : ""} ${className}`}
      {...rest}
    >
      <div
        aria-hidden
        className={`pointer-events-none absolute inset-0 ${gradients.cardSurface}`}
      />
      {children}
    </div>
  );
}
