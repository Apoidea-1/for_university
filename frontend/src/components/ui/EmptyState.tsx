import type { ReactNode } from "react";

import { Card } from "@/components/ui/Card";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <Card className="flex min-h-[220px] flex-col items-start justify-between gap-4">
      <div>
        <p className="text-lg font-semibold text-white">{title}</p>
        <p className="mt-2 max-w-md text-sm text-slate-400">{description}</p>
      </div>
      {action}
    </Card>
  );
}
