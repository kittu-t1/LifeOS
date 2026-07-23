import HomeView from "@/features/home/HomeView";

/**
 * The sidebar's "Home" destination - a welcome message, not the goal
 * dashboard (that moved to /goals, see app/goals/page.tsx and the
 * sidebar architecture redesign). There's no login gate yet (see
 * app/core/deps.py on the backend - a single demo user is used until
 * real auth exists), so this is what every visitor lands on directly.
 */
export default function Home() {
  return <HomeView />;
}
