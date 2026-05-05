import type { HTMLAttributes } from "react";

import { cn } from "@/shared/lib/cn";

export function Alert({
  className,
  variant = "error",
  ...props
}: HTMLAttributes<HTMLDivElement> & { variant?: "error" | "success" | "info" }) {
  return (
    <div
      className={cn(
        "rounded-2xl border px-4 py-3 text-sm",
        variant === "error" && "border-rose-500/30 bg-rose-500/10 text-rose-100",
        variant === "success" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-100",
        variant === "info" && "border-sky-500/30 bg-sky-500/10 text-sky-100",
        className,
      )}
      {...props}
    />
  );
}
