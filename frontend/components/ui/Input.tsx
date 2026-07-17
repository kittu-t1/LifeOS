import type { InputHTMLAttributes } from "react";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";

export default function Input({ className = "", ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`border-border bg-background text-foreground placeholder:text-muted-foreground focus:border-accent focus:ring-accent w-full ${radius.lg.class} border px-3.5 py-2.5 text-sm ${motion.transition.fade} focus:ring-1 focus:outline-none ${className}`}
      {...rest}
    />
  );
}
