"use client";

import { useEffect, type ReactNode } from "react";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

/** Minimal, dependency-free modal. Closes on Escape or backdrop click.
 *  Radius and shadow come from the design system - `shadows.xl` maps to
 *  Tailwind's own `shadow-2xl`, so it renders identically to before. */
export default function Modal({ open, onClose, children }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-[15vh] backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className={`border-border bg-surface-elevated w-full max-w-lg ${radius["2xl"].class} border p-6 ${shadows.xl}`}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}
