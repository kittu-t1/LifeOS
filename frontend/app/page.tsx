import DashboardView from "@/features/dashboard/DashboardView";

/**
 * The Dashboard is the app's home screen (see docs/vision.md and Sprint 1
 * Day 3). There's no login gate yet (see app/core/deps.py on the backend -
 * a single demo user is used until real auth exists), so this is what
 * every visitor lands on directly.
 */
export default function Home() {
  return <DashboardView />;
}
