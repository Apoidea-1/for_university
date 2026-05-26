import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { suggestAIReminders, createReminder } from "@/api/reminders";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import type { AiReminderSuggestion, Contact } from "@/types/api";

export function AiRemindersGenerator({ contacts }: { contacts: Contact[] }) {
  const queryClient = useQueryClient();
  const [suggestions, setSuggestions] = useState<AiReminderSuggestion[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const suggestMutation = useMutation({
    mutationFn: suggestAIReminders,
    onSuccess: (data) => {
      setSuggestions(data);
      setError(null);
    },
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
        <Button 
          onClick={() => suggestMutation.mutate()} 
          loading={suggestMutation.isPending}
        >
          ✨ Сгенерировать
        </Button>
      </div>

      {error ? <Alert>{error}</Alert> : null}

      {suggestions && suggestions.length > 0 ? (
        <div className="mt-4 grid gap-3">
          {suggestions.map((suggestion, index) => {
            const contact = contacts.find((c) => c.id === suggestion.contact_id);
            const contactName = contact ? `${contact.first_name} ${contact.last_name || ""}`.trim() : "Неизвестный контакт";
            const isCreating = createMutation.isPending && createMutation.variables?.title === suggestion.title;
            
            return (
              <div key={index} className="rounded-xl border border-white/10 bg-white/5 p-4 flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
                <div>
                  <div className="flex flex-wrap gap-2 items-center">
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
