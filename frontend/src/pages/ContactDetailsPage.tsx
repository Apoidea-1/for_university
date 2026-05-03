import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import { suggestNextAction } from "@/api/ai";
import { createInteraction, deleteContact, deleteInteraction, getContact, listInteractions } from "@/api/contacts";
import { createReminder } from "@/api/reminders";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { InteractionForm } from "@/features/contacts/InteractionForm";
import { InteractionList } from "@/features/contacts/InteractionList";
import { ReminderForm } from "@/features/reminders/ReminderForm";
import { formatDate, relativeFromNow } from "@/shared/lib/format";
import { getImportanceLabel } from "@/shared/lib/labels";

export function ContactDetailsPage() {
  const { contactId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [aiError, setAiError] = useState<string | null>(null);

  const contactQuery = useQuery({
    queryKey: ["contact", contactId],
    queryFn: () => getContact(contactId as string),
  });
  const interactionsQuery = useQuery({
    queryKey: ["interactions", contactId],
    queryFn: () => listInteractions(contactId as string),
  });

  const interactionMutation = useMutation({
    mutationFn: (payload: { type: string; title: string; description?: string; interaction_date: string }) =>
      createInteraction(contactId as string, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["contact", contactId] }),
        queryClient.invalidateQueries({ queryKey: ["interactions", contactId] }),
        queryClient.invalidateQueries({ queryKey: ["contacts"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
      ]);
    },
  });

  const deleteInteractionMutation = useMutation({
    mutationFn: deleteInteraction,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["contact", contactId] }),
        queryClient.invalidateQueries({ queryKey: ["interactions", contactId] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
      ]);
    },
  });

  const reminderMutation = useMutation({
    mutationFn: createReminder,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["reminders"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
      ]);
    },
  });

  const nextActionMutation = useMutation({
    mutationFn: async () =>
      suggestNextAction({
        notes: contactQuery.data?.notes ?? "",
        last_interaction_summary: interactionsQuery.data?.[0]?.title,
        contact_id: contactQuery.data?.id,
      }),
    onError: (error) => {
      setAiError(error instanceof Error ? error.message : "Не удалось получить подсказку ИИ");
    },
  });

  const deleteContactMutation = useMutation({
    mutationFn: () => deleteContact(contactId as string),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["contacts"] });
      navigate("/contacts");
    },
  });

  if (contactQuery.isLoading || interactionsQuery.isLoading) {
    return <Spinner />;
  }
  if (contactQuery.error || interactionsQuery.error) {
    return <Alert>Не удалось загрузить карточку контакта.</Alert>;
  }

  const contact = contactQuery.data;
  if (!contact) {
    return <Alert>Контакт не найден.</Alert>;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Карточка контакта</p>
              <h1 className="mt-2 text-3xl font-bold text-white">
                {contact.first_name} {contact.last_name ?? ""}
              </h1>
              <p className="mt-2 text-slate-400">
                {contact.role || "Должность не указана"} {contact.company ? `• ${contact.company}` : ""}
              </p>
            </div>
            <div className="flex gap-3">
              <Link to={`/contacts/${contact.id}/edit`}>
                <Button variant="secondary">Редактировать</Button>
              </Link>
              <Button variant="danger" onClick={() => deleteContactMutation.mutate()}>
                Удалить
              </Button>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Категория</p>
              <p className="mt-2 font-semibold text-white">{contact.category?.name ?? "Без категории"}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Важность</p>
              <p className="mt-2 font-semibold text-white">{getImportanceLabel(contact.importance_level)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Где познакомились</p>
              <p className="mt-2 font-semibold text-white">{contact.source_where_met || "Не указано"}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Последнее взаимодействие</p>
              <p className="mt-2 font-semibold text-white">{relativeFromNow(contact.last_interaction_date)}</p>
            </div>
          </div>

          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Заметки</p>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-300">{contact.notes || "Пока без заметок."}</p>
          </div>

          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Теги</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {contact.tags.length ? (
                contact.tags.map((tag) => <Badge key={tag.id}>{tag.name}</Badge>)
              ) : (
                <span className="text-sm text-slate-400">Тегов пока нет.</span>
              )}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Создан</p>
              <p className="mt-2 font-semibold text-white">{formatDate(contact.created_at)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Почта</p>
              <p className="mt-2 font-semibold text-white">{contact.email || "Без почты"}</p>
            </div>
          </div>
        </Card>

        <div className="space-y-6">
          <Card className="space-y-4">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Следующий шаг от ИИ</p>
            <h3 className="text-xl font-bold text-white">Получить рекомендацию по следующему действию</h3>
            <p className="text-sm text-slate-400">
              Используйте тестовый ИИ-модуль, чтобы получить подсказку на основе заметок и последнего взаимодействия.
            </p>
            {aiError ? <Alert>{aiError}</Alert> : null}
            {nextActionMutation.data ? (
              <div className="rounded-2xl border border-accent/20 bg-accent/10 p-4">
                <p className="font-semibold text-white">{nextActionMutation.data.next_action}</p>
                <p className="mt-2 text-sm text-slate-300">{nextActionMutation.data.rationale}</p>
              </div>
            ) : null}
            <Button onClick={() => nextActionMutation.mutate()} loading={nextActionMutation.isPending}>
              Предложить следующий шаг
            </Button>
          </Card>

          <ReminderForm
            contacts={[contact]}
            defaultContactId={contact.id}
            onSubmit={async (payload) => reminderMutation.mutateAsync(payload)}
          />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <InteractionForm onSubmit={async (payload) => interactionMutation.mutateAsync(payload)} />
        <InteractionList
          items={interactionsQuery.data ?? []}
          onDelete={async (id) => deleteInteractionMutation.mutateAsync(id)}
        />
      </div>
    </div>
  );
}
