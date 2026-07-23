import Link from "next/link";
import ConnectionIndicator from "@/components/ConnectionIndicator";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";

/**
 * A minimal floating pill nav rather than a full-width sticky bar -
 * detached from the top edge with its own rounded border and soft
 * shadow, closer to a visionOS/macOS floating toolbar than a
 * traditional app header. Logo + connection status, plus Habits and
 * Memory links - both top-level nav destinations outside a Goal's
 * Workspace, since both are user-scoped rather than Goal-scoped (see
 * app/habits/page.tsx and app/memory/page.tsx).
 *
 * ConnectionIndicator only renders in development. It's a genuinely
 * useful "is the FastAPI backend actually running" signal while
 * building locally, but a real user has no context for what
 * "Connected" means or what it's connected to - showing internal
 * plumbing like that in a production build reads as unfinished, not
 * reassuring. `pnpm dev` still gets the signal; a production build
 * doesn't render it at all (not even hidden in the DOM).
 */
export default function AppHeader() {
  const isDev = process.env.NODE_ENV === "development";

  return (
    <header className="sticky top-4 z-40 flex justify-center px-4">
      <div
        className={`border-border bg-surface/90 mx-auto flex w-full max-w-[1100px] items-center justify-between ${radius.pill.class} border px-6 py-3 backdrop-blur-md ${shadows.floating}`}
      >
        <Link
          href="/"
          className="text-foreground flex items-center gap-2.5 text-[15px] font-semibold"
        >
          {/* Same icon as the browser tab favicon (app/favicon.ico, served
              at /favicon.ico) - kept in sync so the in-app logo and the
              tab icon are the same mark rather than two different ones.
              Rounded to radius.sm (6px) - the design-system scale doesn't
              have a 5px step, and the 1px difference is imperceptible at
              this size. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/favicon.ico" alt="" className={`h-5 w-5 ${radius.sm.class}`} />
          <span className="tracking-tight">LifeOS</span>
        </Link>
        <div className="flex items-center gap-4">
          <Link
            href="/habits"
            className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors"
          >
            Habits
          </Link>
          <Link
            href="/memory"
            className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors"
          >
            Memory
          </Link>
          {isDev && <ConnectionIndicator />}
        </div>
      </div>
    </header>
  );
}
