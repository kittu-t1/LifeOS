import { ArrowRight } from "lucide-react";
import Button from "@/components/ui/Button";
import { typography } from "@/design-system/typography";
import OrbitIllustration from "@/features/dashboard/OrbitIllustration";

/**
 * The homepage's opening statement (see the "Homepage redesign" spec:
 * a storytelling landing experience, not a bare CRUD screen). Centered,
 * generous whitespace, one idea per element - the headline states what
 * the product is for, one sentence explains how, and a single confident
 * CTA (Create Your First Goal) rather than two competing actions.
 * "Explore LifeOS" (the dedicated page at /explore with tap-to-reveal
 * detail on each step - see features/explore/ExploreView.tsx) lives as
 * the CTA for the Goal Showcase section further down instead of sitting
 * next to this button.
 *
 * No "LifeOS" eyebrow badge here on purpose - the floating nav
 * (AppHeader.tsx) already shows the logo and wordmark a few inches
 * above this, so repeating it here was redundant branding rather than
 * a real piece of content. The headline is now the first thing you see
 * under the nav.
 */
export default function HeroSection({ onCreateGoal }: { onCreateGoal: () => void }) {
  return (
    <section className="animate-fade-in-up flex flex-col items-center gap-10 text-center">
      <div className="flex flex-col items-center gap-6">
        <h1
          className={`text-foreground max-w-3xl text-[${typography.displayXL.fontSize}] leading-[${typography.displayXL.lineHeight}] font-semibold tracking-tight sm:text-[${typography.displayXL.responsive.fontSize}] sm:leading-[${typography.displayXL.responsive.lineHeight}]`}
        >
          Your AI Life Navigator
        </h1>
        <p className="text-muted-foreground max-w-xl text-lg leading-relaxed">
          Plan your goals, organize your days, and let AI help you move forward.
        </p>
      </div>

      <Button onClick={onCreateGoal} className="group">
        Create Your First Goal
        <ArrowRight
          size={15}
          className="transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:translate-x-0.5"
        />
      </Button>

      <OrbitIllustration />
    </section>
  );
}
