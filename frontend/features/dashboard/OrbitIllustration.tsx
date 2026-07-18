import { BookOpen, Sparkles, Target, TrendingUp, Trophy } from "lucide-react";
import { colors } from "@/design-system/colors";
import { gradients } from "@/design-system/gradients";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";

const ORBIT_NODES = [
  { icon: Target, style: { left: "10%", top: "42%" } },
  // Lower-left of the orb, between Target and the orb's bottom edge -
  // matches the same visual distance from the orb the other three
  // nodes have, rather than crowding its glow.
  { icon: BookOpen, style: { left: "26%", top: "88%" } },
  { icon: TrendingUp, style: { left: "68%", top: "10%" } },
  { icon: Trophy, style: { left: "82%", top: "64%" } },
];

/**
 * The hero's illustration - an abstract AI presence (center, a soft
 * two-tone glowing orb blending the deep-teal and pale-aqua accents)
 * held in orbit by the pieces of the LifeOS loop (Target/BookOpen/
 * TrendingUp/Trophy = Goal / Reflection / Progress / Achievement - the
 * same icon language as the WORKFLOW_STEPS data on /explore, so
 * BookOpen here is the same glyph as the "Reflection" step there, not
 * a one-off choice), on a quiet dashed path standing in for "AI plots
 * the route." Built from real icons and simple absolutely-positioned
 * circles rather than a bespoke hand-drawn SVG scene - reads as a
 * clean, custom illustration while staying consistent with the icon
 * language used everywhere else in the product, and easy to keep in
 * sync with the design system (colors/shadows/motion, not one-off
 * values).
 *
 * Glow hierarchy is deliberate: only the center orb glows continuously
 * (it's the one "this is alive, this is the AI" signal) - the four
 * orbiting nodes stay flat at rest and only pick up a glow on hover.
 * That's the same "calm by default, glow responds to interaction" rule
 * Button.tsx follows, so the whole page speaks one visual language
 * instead of some things glowing for no obvious reason.
 */
export default function OrbitIllustration() {
  return (
    <div
      aria-hidden
      className={`${motion.animation.floatSlow} relative mx-auto mt-6 h-80 w-full max-w-lg`}
    >
      {/* Dashed orbit path - an ellipse made from a circle flattened with scaleY. */}
      <div
        className="border-border absolute inset-x-7 top-1/2 h-44 -translate-y-1/2 rounded-full border border-dashed"
        style={{ transform: "translateY(-50%) scaleY(0.6)" }}
      />

      {/* Central node - the AI presence itself: a soft, breathing,
          two-tone (deep teal + pale aqua) glow behind a gradient orb,
          not just a flat colored circle. */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
        <div
          aria-hidden
          className={`${motion.animation.softPulse} absolute -inset-7 rounded-full blur-2xl`}
          style={{ background: colors.primaryGlow }}
        />
        <div
          aria-hidden
          className="absolute -inset-2 translate-x-2 translate-y-1 rounded-full blur-xl"
          style={{ background: colors.secondaryGlow }}
        />
        <div
          className={`relative flex h-24 w-24 items-center justify-center ${radius.full.class} ${gradients.primaryButton} ${shadows.buttonPrimary}`}
        >
          <Sparkles size={32} className="text-accent-foreground" strokeWidth={1.75} />
        </div>
      </div>

      {/* Orbiting nodes - Goal -> Reflection -> Progress -> Achievement.
          Flat at rest; `group` + `group-hover` reveal a soft glow and a
          tiny lift on hover, rather than glowing all the time like the
          center orb. */}
      {ORBIT_NODES.map(({ icon: Icon, style }, i) => (
        <div key={i} className="group absolute" style={style}>
          <div
            aria-hidden
            className={`pointer-events-none absolute -inset-2 rounded-full opacity-0 blur-lg ${motion.transition.buttonHover} group-hover:opacity-100`}
            style={{ background: colors.primaryGlow }}
          />
          <div
            className={`border-border bg-surface relative flex h-12 w-12 items-center justify-center ${radius.full.class} border ${shadows.floating} ${motion.transition.buttonHover} group-hover:${motion.transform.hoverLiftSm}`}
          >
            <Icon size={19} className="text-accent" strokeWidth={1.75} />
          </div>
        </div>
      ))}
    </div>
  );
}
