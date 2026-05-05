import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { formatDateTime } from "@/shared/lib/format";
import { getInteractionTypeLabel } from "@/shared/lib/labels";
import type { Interaction } from "@/types/api";

export function InteractionList({
  items,
  onDelete,
}: {
  items: Interaction[];
  onDelete: (interactionId: number) => Promise<unknown>;
}) {
  return (
    <Card className="space-y-4">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Хронология</p>
        <h3 className="mt-2 text-xl font-bold text-white">История взаимодействий</h3>
      </div>
      <div className="space-y-3">
        {items.length ? (
          items.map((item) => (
            <div key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">{getInteractionTypeLabel(item.type)}</p>
                  <p className="mt-1 text-base font-semibold text-white">{item.title}</p>
                  <p className="mt-2 text-sm text-slate-300">{item.description || "Без описания"}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-400">{formatDateTime(item.interaction_date)}</p>
                  <Button className="mt-3" variant="ghost" onClick={() => onDelete(item.id)}>
                    Удалить
                  </Button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-borderSoft p-4 text-sm text-slate-400">
            Пока нет ни одного взаимодействия. Добавьте первое, чтобы история общения была под рукой.
          </div>
        )}
      </div>
    </Card>
  );
}
