import Link from "next/link";
import ConnectionIndicator from "@/components/ConnectionIndicator";
import { radius } from "@/design-system/radius";

export default function AppHeader() {
  return (
    <header className="border-border bg-background/80 sticky top-0 z-40 border-b backdrop-blur-sm">
      <div className="mx-auto flex w-full max-w-[1100px] items-center justify-between px-8 py-5">
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
        <ConnectionIndicator />
      </div>
    </header>
  );
}
