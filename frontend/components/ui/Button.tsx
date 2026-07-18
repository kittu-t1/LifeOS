import type { ButtonHTMLAttributes, ReactNode } from "react";
import { gradients } from "@/design-system/gradients";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  children: ReactNode;
}

const variantClasses: Record<Variant, string> = {
  // Soft top-to-bottom gradient (light -> base) reads as a physical,
  // slightly domed surface rather than a flat color fill. The inset
  // top highlight is what sells the "tactile" material feel; the glow
  // shadow uses the primaryGlow color token so it stays in sync with
  // the design system instead of a one-off rgba value.
  primary: `${gradients.primaryButton} text-accent-foreground px-5 py-2.5 ${shadows.buttonPrimary} hover:${motion.transform.hoverLift} hover:${shadows.buttonPrimaryHover} hover:brightness-[1.04]`,
  secondary: `bg-surface text-foreground border border-border px-4 py-2 hover:${motion.transform.hoverLiftSm} hover:bg-surface-hover`,
  ghost: `text-muted-foreground px-4 py-2 hover:${motion.transform.hoverLiftSm} hover:bg-surface hover:text-foreground`,
};

/** Shared button primitive - every button in the app should use this
 * rather than one-off Tailwind classes, so visual style stays consistent
 * as the product grows. Primary carries the "tactile premium material"
 * treatment (gradient, inner highlight, glow, hover lift, press-down) -
 * secondary/ghost stay quieter since they're not the page's main action.
 * All colors, shadows, gradients, and motion come from the design
 * system (@/design-system) rather than being hardcoded here. */
export default function Button({
  variant = "primary",
  className = "",
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`focus-visible:ring-accent inline-flex items-center justify-center gap-2 ${radius.lg.class} text-sm font-medium ${motion.transition.buttonHover} ${motion.transform.buttonPress} focus-visible:ring-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0 disabled:hover:shadow-none disabled:active:scale-100 ${variantClasses[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
