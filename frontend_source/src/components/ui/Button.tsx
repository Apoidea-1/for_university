import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/shared/lib/cn";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({ className, children, variant = "primary", loading, icon, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
        variant === "primary" && "bg-accent text-slate-950 hover:bg-[#2dd4bf]",
        variant === "secondary" && "border border-borderSoft bg-panelSoft text-slate-100 hover:bg-slate-800",
        variant === "ghost" && "text-slate-300 hover:bg-white/5",
        variant === "danger" && "bg-rose-500 text-white hover:bg-rose-400",
        className,
      )}
      {...props}
    >
      {loading ? "Подождите..." : icon}
      {loading ? null : children}
      {loading ? children : null}
    </button>
  );
}
