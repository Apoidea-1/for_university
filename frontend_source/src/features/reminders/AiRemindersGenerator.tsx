import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { suggestAIReminders, createReminder } from "@/api/reminders";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { usePushNotifications } from "@/hooks/usePushNotifications";
import type { AiReminderSuggestion, Contact } from "@/types/api";

function BellIcon({ on }: { on: boolean }) {
  return on ? (
    <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
      fill="currentColor" stroke="currentColor" strokeWidth="0">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
  ) : (
    <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
  );
}

export function AiRemindersGenerator({ contacts }: { contacts: Contact[] }) {
  const queryClient = useQueryClient();
  const [suggestions, setSuggestions] = useState<AiReminderSuggestion[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { state: pushState, isLoading: pushLoading, subscribe, unsubscribe } = usePushNotifications();

  const suggestMutation = useMutation({
    mutationFn: suggestAIReminders,
    onSuccess: (data) => { setSuggestions(data); setError(null); },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Не удалось сгенерировать напоминания.");
    },
  });

  const createMutation = useMutation({
    mutationFn: createReminder,
    onSuccess: async (_, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["reminders"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
      ]);
      setSuggestions((prev) =>
        prev ? prev.filter((s) => s.contact_id !== variables.contact_id || s.title !== variables.title) : null
      );
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Ошибка при создании напоминания.");
    },
  });

  const pushLabel =
    pushState === "unsupported" ? "Не поддерживается"
    : pushState === "denied"     ? "Заблокировано браузером"
    : pushState === "subscribed" ? "Push включён"
    : "Включить push";

  const canTogglePush = pushState !== "unsupported" && pushState !== "denied";

  return (
    <Card className="space-y-4 border-accent/20 bg-accent/5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">AI-помощник</p>
          <h3 className="mt-2 text-xl font-bold text-white">Умные напоминания</h3>
          <p className="mt-2 text-sm text-slate-400">
            ИИ проанализирует ваши контакты и предложит, с кем стоит связаться в первую очередь.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {/* Push toggle */}
          <button
            onClick={pushState === "subscribed" ? unsubscribe : subscribe}
            disabled={!canTogglePush || pushLoading}
            title={pushLabel}
            className={[
              "flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-semibold transition",
              pushState === "subscribed"
                ? "border-accent/40 bg-accent/10 text-accent hover:bg-accent/20"
                : pushState === "denied" || pushState === "unsupported"
                  ? "cursor-not-allowed border-white/10 text-slate-500 opacity-60"
                  : "border-white/10 text-slate-400 hover:border-accent/30 hover:text-accent",
            ].join(" ")}
          >
            <BellIcon on={pushState === "subscribed"} />
            {pushLoading ? "…" : pushLabel}
          </button>

          <Button onClick={() => suggestMutation.mutate()} loading={suggestMutation.isPending}>
            ✨ Сгенерировать
          </Button>
        </div>
      </div>

      {pushState === "subscribed" && (
        <p className="rounded-xl border border-accent/20 bg-accent/5 px-4 py-2.5 text-xs text-accent">
          🔔 Push-уведомления активны — напомним за несколько минут до дедлайна, даже если вкладка закрыта.
        </p>
      )}

      {pushState === "denied" && (
        <p className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-slate-500">
          Push-уведомления заблокированы в настройках браузера. Разрешите их вручную в адресной строке.
        </p>
      )}

      {error ? <Alert>{error}</Alert> : null}

      {suggestions && suggestions.length > 0 ? (
        <div className="mt-4 grid gap-3">
          {suggestions.map((suggestion, index) => {
            const contact = contacts.find((c) => c.id === suggestion.contact_id);
            const contactName = contact
              ? `${contact.first_name} ${contact.last_name || ""}`.trim()
              : "Неизвестный контакт";
            const isCreating =
              createMutation.isPending && createMutation.variables?.title === suggestion.title;

            return (
              <div
                key={index}
                className="flex flex-col items-start justify-between gap-4 rounded-xl border border-white/10 bg-white/5 p-4 sm:flex-row sm:items-center"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-white">{contactName}</p>
                    <Badge>{suggestion.priority === "high" ? "Высокий приоритет" : "Обычный"}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-slate-300">{suggestion.title}</p>
                  <p className="mt-1 text-xs text-slate-500">Через дней: {suggestion.due_in_days}</p>
                </div>
                <Button
                  variant="secondary"
                  loading={isCreating}
                  onClick={() => {
                    const due = new Date();
                    due.setDate(due.getDate() + suggestion.due_in_days);
                    createMutation.mutate({
                      contact_id: suggestion.contact_id,
                      title: suggestion.title,
                      due_date: due.toISOString(),
                      reminder_type: suggestion.reminder_type,
                      status: "active",
                    });
                  }}
                >
                  Создать
                </Button>
              </div>
            );
          })}
        </div>
      ) : suggestions !== null ? (
        <p className="text-sm text-slate-400">Нет новых предложений для связи.</p>
      ) : null}
    </Card>
  );
}
