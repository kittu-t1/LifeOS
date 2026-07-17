"use client";

import { useEffect, useState } from "react";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";
import { getHealth } from "@/lib/api";

type Status = "loading" | "connected" | "error";

/**
 * Small, unobtrusive backend connectivity indicator - a compact successor
 * to Day 1's full-card BackendStatus. Kept because it's genuinely useful
 * for local development (instantly shows if the FastAPI server isn't
 * running), but demoted to a header pill so it doesn't compete with real
 * product UI for attention.
 */
export default function ConnectionIndicator() {
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    getHealth()
      .then(() => setStatus("connected"))
      .catch(() => setStatus("error"));
  }, []);

  const label = status === "connected" ? "Connected" : status === "error" ? "Offline" : "Checking…";
  const dotClass =
    status === "connected"
      ? `bg-success ${shadows.statusRingSuccess}`
      : status === "error"
        ? "bg-danger"
        : "animate-pulse bg-warning";

  return (
    <div
      className={`bg-surface/60 text-muted-foreground flex items-center gap-2 ${radius.pill.class} px-3 py-1.5 text-[11px] font-medium tracking-wide uppercase`}
      title={status === "error" ? "Backend unreachable - is uvicorn running?" : undefined}
    >
      <span className={`h-1.5 w-1.5 ${radius.pill.class} ${dotClass}`} />
      {label}
    </div>
  );
}
