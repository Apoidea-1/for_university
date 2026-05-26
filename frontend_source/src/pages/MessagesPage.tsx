import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { listContacts } from "@/api/contacts";
import { createMessage, deleteMessage, getConversation, listConversations } from "@/api/messages";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { Textarea } from "@/components/ui/Textarea";
import { formatDateTime } from "@/shared/lib/format";

export function MessagesPage() {
  const queryClient = useQueryClient();
  const [selectedContactId, setSelectedContactId] = useState("");
  const [messageType, setMessageType] = useState<"chat" | "note" | "follow_up" | "meeting">("chat");
  const [messageDirection, setMessageDirection] = useState<"outbound" | "inbound">("outbound");
  const [body, setBody] = useState("");

  const contactsQuery = useQuery({
    queryKey: ["contacts", "message-options"],
    queryFn: () => listContacts({ sort_by: "name", sort_order: "asc", per_page: 200 }),
  });
  
  const conversationsQuery = useQuery({ queryKey: ["conversations"], queryFn: listConversations });
  
  const pairKey = selectedContactId ? `0:${selectedContactId}` : "";
  const conversationQuery = useQuery({
    queryKey: ["conversation", pairKey],
    queryFn: () => getConversation(pairKey),
    enabled: Boolean(pairKey),
  });

  const createMutation = useMutation({
    mutationFn: createMessage,
    onSuccess: async () => {
      setBody("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["conversations"] }),
        queryClient.invalidateQueries({ queryKey: ["conversation", pairKey] }),
      ]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteMessage,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["conversations"] }),
        queryClient.invalidateQueries({ queryKey: ["conversation", pairKey] }),
      ]);
    },
  });

  const contacts = contactsQuery.data?.items ?? [];
  const selectedContact = useMemo(() => {
    return contacts.find((c) => c.id === Number(selectedContactId));
  }, [contacts, selectedContactId]);

  if (contactsQuery.isLoading || conversationsQuery.isLoading) {
    return <Spinner />;
  }
  if (contactsQuery.error || conversationsQuery.error) {
    return <Alert>Не удалось загрузить чаты.</Alert>;
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <div className="space-y-6">
        <Card className="space-y-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Контакты</p>
            <h3 className="mt-2 text-xl font-bold text-white">Выберите контакт для общения</h3>
          </div>

          <Select value={selectedContactId} onChange={(event) => setSelectedContactId(event.target.value)}>
            <option value="">Выберите контакт</option>
            {contacts.map((contact) => (
              <option key={contact.id} value={contact.id}>
                {contact.first_name} {contact.last_name ?? ""} {contact.company ? `• ${contact.company}` : ""}
              </option>
            ))}
          </Select>
        </Card>

        <Card className="space-y-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">История</p>
            <h3 className="mt-2 text-xl font-bold text-white">Активные диалоги</h3>
          </div>
          <div className="space-y-3">
            {(conversationsQuery.data ?? [])
              .filter(conv => conv.pair_key.startsWith("0:"))
              .map((conversation) => {
              const otherParticipant = conversation.participants.find(p => p !== null);
              if (!otherParticipant) return null;
              
              return (
                <button
                  key={conversation.pair_key}
                  className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                    pairKey === conversation.pair_key
                      ? "border-accent bg-accent/10"
                      : "border-white/10 bg-white/5 hover:bg-white/10"
                  }`}
                  onClick={() => setSelectedContactId(String(otherParticipant.id))}
                >
                  <p className="font-semibold text-white">
                    {otherParticipant.full_name}
                  </p>
                  <p className="mt-1 text-sm text-slate-400 line-clamp-2">{conversation.last_message.body}</p>
                  <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                    {formatDateTime(conversation.last_message.sent_at)} • сообщений {conversation.message_count}
                  </p>
                </button>
              );
            })}
          </div>
        </Card>
      </div>

      <div className="space-y-6">
        <Card className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Чат</p>
              <h3 className="mt-2 text-2xl font-bold text-white">
                {selectedContact ? `${selectedContact.first_name} ${selectedContact.last_name ?? ""}`.trim() : "Выберите контакт"}
              </h3>
            </div>
          </div>

          {conversationQuery.isLoading ? <Spinner /> : null}
          {conversationQuery.error ? <Alert>Не удалось загрузить сообщения.</Alert> : null}

          <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
            {selectedContactId ? (
              (conversationQuery.data ?? []).length ? (
                conversationQuery.data?.map((message) => {
                  const isFromUser = !message.sender_contact;
                  return (
                    <div key={message.id} className={`flex ${isFromUser ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[80%] rounded-3xl p-4 ${isFromUser ? "bg-accent/20 border border-accent/30 text-right" : "bg-white/5 border border-white/10 text-left"}`}>
                        <p className="text-sm leading-6 text-slate-200">{message.body}</p>
                        <div className={`mt-2 flex items-center gap-3 text-xs uppercase tracking-[0.18em] text-slate-500 ${isFromUser ? "justify-end" : "justify-start"}`}>
                          <span>{message.message_type}</span>
                          <span>•</span>
                          <span>{formatDateTime(message.sent_at)}</span>
                          <button className="text-slate-500 hover:text-rose-400" onClick={() => deleteMutation.mutate(message.id)}>
                            ×
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="rounded-3xl border border-dashed border-white/10 p-5 text-sm text-slate-400">
                  Здесь пока пусто. Напишите первое сообщение или оставьте заметку о звонке.
                </div>
              )
            ) : (
              <div className="rounded-3xl border border-dashed border-white/10 p-5 text-sm text-slate-400">
                Выберите контакт слева, чтобы увидеть историю общения.
              </div>
            )}
          </div>
        </Card>

        {selectedContactId ? (
          <Card className="space-y-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Новая запись</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Select value={messageDirection} onChange={(event) => setMessageDirection(event.target.value as "outbound" | "inbound")}>
                <option value="outbound">Я написал(а)</option>
                <option value="inbound">Контакт написал</option>
              </Select>

              <Select value={messageType} onChange={(event) => setMessageType(event.target.value as typeof messageType)}>
                <option value="chat">Чат / Сообщение</option>
                <option value="note">Заметка</option>
                <option value="meeting">Встреча / Звонок</option>
              </Select>
            </div>

            <Textarea
              value={body}
              onChange={(event) => setBody(event.target.value)}
              placeholder="Сюда записывается содержание сообщения, звонка или важная деталь..."
              className="min-h-[100px]"
            />

            <div className="flex flex-wrap gap-3">
              <Button
                loading={createMutation.isPending}
                disabled={!body.trim()}
                onClick={() =>
                  createMutation.mutate({
                    sender_contact_id: messageDirection === "inbound" ? Number(selectedContactId) : undefined,
                    recipient_contact_id: messageDirection === "outbound" ? Number(selectedContactId) : undefined,
                    body,
                    message_type: messageType,
                    sent_at: new Date().toISOString(),
                  })
                }
              >
                Сохранить
              </Button>
            </div>

            {createMutation.error ? (
              <Alert>{createMutation.error instanceof Error ? createMutation.error.message : "Не удалось сохранить."}</Alert>
            ) : null}
          </Card>
        ) : null}
      </div>
    </div>
  );
}
