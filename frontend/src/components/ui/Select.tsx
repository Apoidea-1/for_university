import { forwardRef, type SelectHTMLAttributes } from "react";

import { cn } from "@/shared/lib/cn";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(function Select(
  { className, ...props },
  ref,
) {
  return (
    <select
      ref={ref}
      {...props}
      className={cn(
        "w-full rounded-2xl border border-borderSoft bg-slate-950/50 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-accent",
        className,
      )}
    />
  );
});
