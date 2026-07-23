import GoalsView from "@/features/goals/GoalsView";

/**
 * The sidebar's "Goals" destination - Create Goal, the Goal Showcase,
 * and the live "Your Goals" list. This is what used to live at "/"
 * before the sidebar architecture redesign split Home and Goals apart
 * (see features/home/HomeView.tsx and components/layout/navConfig.ts).
 */
export default function GoalsPage() {
  return <GoalsView />;
}
