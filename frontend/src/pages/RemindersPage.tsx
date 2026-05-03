import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { listContacts } from "@/api/contacts";
import { createReminder, deleteReminder, listReminders, updateReminder } from "@/api/reminders";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { ReminderForm } from "@/features/reminders/ReminderForm";
import { formatDateTime } from "@/shared/lib/format";
import { getReminderStatusLabel, getReminderTypeLabel } from "@/shared/lib/labels";

const filterOptions = ["active", "overdue", "completed"] as const;

export function RemindersPage() {
  const [filter, setFilter] = useState<(typeof filterOptions)[number]>("active");
  const queryClient = useQueryClient();

  const contactsQuery = useQuery({
    queryKey: ["contacts", "reminder-options"],
    queryFn: () => listContacts({ sort_by: "name", sort_order: "asc" }),
  });
  const remindersQuery = useQuery({
    queryKey: ["reminders", filter],
    queryFn: () => listReminders(filter),
  });

  const createMutation = useMutation({
    mutationFn: createReminder,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["reminders"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
      ]);
    },
  });

  const completeMutation = useMutation({
    mutationFn: (reminderId: number) => updateReminder(reminderId, { status: "completed" }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["reminders"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
      ]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteReminder,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["reminders"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
      ]);
    },
  });

  if (contactsQuery.isLoading || remindersQuery.isLoading) {
    return <Spinner />;
  }
  if (contactsQuery.error || remindersQuery.error) {
    return <Alert>Не удалось загрузить напоминания.</Alert>;
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <ReminderForm
        contacts={contactsQuery.data?.items ?? []}
        onSubmit={async (payload) => createMutation.mutateAsync(payload)}
      />

      <div className="space-y-6">
        <Card className="flex flex-wrap gap-3">
          {filterOptions.map((option) => (
            <Button
              key={option}
              variant={filter === option ? "primary" : "secondary"}
              onClick={() => setFilter(option)}
            >
              {getReminderStatusLabel(option)}
            </Button>
          ))}
        </Card>

        <div className="space-y-4">
          {(remindersQuery.data ?? []).map((reminder) => (
            <Card key={reminder.id}>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-lg font-semibold text-white">{reminder.title}</p>
                    <Badge>{getReminderTypeLabel(reminder.reminder_type)}</Badge>
                  </div>
                  <p className="mt-2 text-sm text-slate-400">
                    {reminder.contact ? `${reminder.contact.first_name} ${reminder.contact.last_name ?? ""}` : "Без привязки к контакту"}
                  </p>
                  <p className="mt-3 text-sm text-slate-300">{reminder.description || "Без описания"}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-400">{formatDateTime(reminder.due_date)}</p>
                  <div className="mt-3 flex gap-2">
                    {reminder.status !== "completed" ? (
                      <Button variant="secondary" onClick={() => completeMutation.mutate(reminder.id)}>
                        Отметить выполненным
                      </Button>
                    ) : null}
                    <Button variant="ghost" onClick={() => deleteMutation.mutate(reminder.id)}>
                      Удалить
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
