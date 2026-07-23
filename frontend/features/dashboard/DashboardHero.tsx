import { typography } from "@/design-system/typography";

// Single-demo-user placeholder (see backend/app/core/deps.py -
// DEMO_USER_EMAIL resolves to a hardcoded User(name="Krishna") until real
// auth/login exists). Mirroring that same hardcoded name here rather than
// adding a GET /users/me round trip for a value that can't currently
// differ - swap this for a real fetched user name once auth ships.
const USER_NAME = "Krishna";

function timeOfDayGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

/**
 * The dashboard's new opening statement (see the "Goals + Habits as
 * equal entry points" IA spec) - replaces the old marketing-style Hero
 * (headline + orbit illustration + single CTA, see git history for
 * HeroSection.tsx/OrbitIllustration.tsx) with a personalized greeting
 * that immediately frames LifeOS as a home screen, not a landing page.
 *
 * Greeting is read directly during render (same convention the old
 * DashboardView used for its "{greeting}, welcome back" line) rather
 * than behind a client-only useEffect - this is a single local user in
 * one timezone, not a server serving visitors worldwide, so there's no
 * real hydration-mismatch risk worth the extra state/effect.
 */
export default function DashboardHero() {
  return (
    <section className="animate-fade-in-up flex flex-col items-center gap-4 text-center">
      <p className="text-muted-foreground text-base">
        {timeOfDayGreeting()}, {USER_NAME} 👋
      </p>

      <h1
        className={`text-foreground max-w-2xl text-[${typography.displayXL.fontSize}] leading-[${typography.displayXL.lineHeight}] font-semibold tracking-tight sm:text-[${typography.displayXL.responsive.fontSize}] sm:leading-[${typography.displayXL.responsive.lineHeight}]`}
      >
        What do you want to improve today?
      </h1>

      <p className="text-muted-foreground max-w-md text-lg leading-relaxed">
        Build meaningful goals and consistent habits.
      </p>
    </section>
  );
}
