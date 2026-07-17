import type { LucideIcon } from "lucide-react";

interface PlaceholderSectionProps {
  icon: LucideIcon;
  title: string;
  comingIn: string;
}

/**
 * Shared placeholder for workspace sections that don't have real
 * functionality yet (Tasks, Planner, Knowledge, Timeline, Chat - see
 * docs/mvp_scope.md for when each lands). One component so every
 * "coming soon" screen looks and behaves identically rather than each
 * page inventing its own.
 */
export default function PlaceholderSection({
  icon: Icon,
  title,
  comingIn,
}: PlaceholderSectionProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 py-24 text-center">
      <div className="bg-surface flex h-12 w-12 items-center justify-center rounded-full">
        <Icon className="text-muted-foreground" size={22} />
      </div>
      <h2 className="text-foreground text-base font-semibold">{title}</h2>
      <p className="text-muted-foreground text-sm">{comingIn}</p>
    </div>
  );
}
