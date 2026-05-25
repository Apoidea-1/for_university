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

function buildPairKey(firstId: number, secondId: number) {
  return [firstId, secondId].sort((left, right) => left - right).join(":");
}

export function MessagesPage() {
  const queryClient = useQueryClient();
  const [selectedPairKey, setSelectedPairKey] = useState("");
  const [senderContactId, setSenderContactId] = useState("");
  const [recipientContactId, setRecipientContactId] = useState("");
  const [messageType, setMessageType] = useState<"chat" | "note" | "follow_up" | "meeting">("chat");
  const [body, setBody] = useState("");

  const contactsQuery = useQuery({
    queryKey: ["contacts", "message-options"],
    queryFn: () => listContacts({ sort_by: "name", sort_order: "asc", per_page: 200 }),
  });
  const conversationsQuery = useQuery({ queryKey: ["conversations"], queryFn: listConversations });
  const conversationQuery = useQuery({
    queryKey: ["conversation", selectedPairKey],
    queryFn: () => getConversation(selectedPairKey),
    enabled: Boolean(selectedPairKey),
  });

  useEffect(() => {
    if (!selectedPairKey && conversationsQuery.data?.[0]) {
      setSelectedPairKey(conversationsQuery.data[0].pair_key);
    }
  }, [conversationsQuery.data, selectedPairKey]);

  useEffect(() => {
    const selectedConversation = conversationsQuery.data?.find((item) => item.pair_key === selectedPairKey);
    if (selectedConversation) {
      setSenderContactId(String(selectedConversation.participants[0]?.id ?? ""));
      setRecipientContactId(String(selectedConversation.participants[1]?.id ?? ""));
    }
  }, [conversationsQuery.data, selectedPairKey]);

  const createMutation = useMutation({
    mutationFn: createMessage,
    onSuccess: async (message) => {
      setSelectedPairKey(message.pair_key);
      setBody("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["conversations"] }),
        queryClient.invalidateQueries({ queryKey: ["conversation", message.pair_key] }),
        queryClient.invalidateQueries({ queryKey: ["network-graph"] }),
        queryClient.invalidateQueries({ queryKey: ["relationships"] }),
      ]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteMessage,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["conversations"] }),
        queryClient.invalidateQueries({ queryKey: ["conversation", selectedPairKey] }),
      ]);
    },
  });

  const contacts = contactsQuery.data?.items ?? [];
  const selectedParticipants = useMemo(() => {
    if (senderContactId && recipientContactId) {
      const resolved = [
        contacts.find((contact) => contact.id === Number(senderContactId)),
        contacts.find((contact) => contact.id === Number(recipientContactId)),
      ];
      return resolved.filter((contact): contact is (typeof contacts)[number] => Boolean(contact));
    }
    return [];
  }, [contacts, recipientContactId, senderContactId]);

  if (contactsQuery.isLoading || conversationsQuery.isLoading) {
    return <Spinner />;
  }
  if (contactsQuery.error || conversationsQuery.error) {
    return <Alert>Не удалось загрузить чаты между контактами.</Alert>;
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <div className="space-y-6">
        <Card className="space-y-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Новый диалог</p>
            <h3 className="mt-2 text-xl font-bold text-white">Создайте поток общения между двумя контактами</h3>
          </div>

          <Select value={senderContactId} onChange={(event) => setSenderContactId(event.target.value)}>
            <option value="">Отправитель</option>
            {contacts.map((contact) => (
              <option key={contact.id} value={contact.id}>
                {contact.first_name} {contact.last_name ?? ""} {contact.company ? `• ${contact.company}` : ""}
              </option>
            ))}
          </Select>

          <Select value={recipientContactId} onChange={(event) => setRecipientContactId(event.target.value)}>
            <option value="">Получатель</option>
            {contacts.map((contact) => (
              <option key={contact.id} value={contact.id}>
                {contact.first_name} {contact.last_name ?? ""} {contact.company ? `• ${contact.company}` : ""}
              </option>
            ))}
          </Select>

          <Button
            className="w-full"
            variant="secondary"
            disabled={!senderContactId || !recipientContactId || senderContactId === recipientContactId}
            onClick={() => setSelectedPairKey(buildPairKey(Number(senderContactId), Number(recipientContactId)))}
          >
            Открыть диалог
          </Button>
        </Card>

        <Card className="space-y-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Потоки</p>
            <h3 className="mt-2 text-xl font-bold text-white">Последние диалоги</h3>
          </div>
          <div className="space-y-3">
            {(conversationsQuery.data ?? []).map((conversation) => (
              <button
                key={conversation.pair_key}
                className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                  selectedPairKey === conversation.pair_key
                    ? "border-accent bg-accent/10"
                    : "border-white/10 bg-white/5 hover:bg-white/10"
                }`}
                onClick={() => setSelectedPairKey(conversation.pair_key)}
              >
                <p className="font-semibold text-white">
                  {conversation.participants.map((participant) => participant.full_name).join(" ↔ ")}
                </p>
                <p className="mt-1 text-sm text-slate-400 line-clamp-2">{conversation.last_message.body}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                  {formatDateTime(conversation.last_message.sent_at)} • сообщений {conversation.message_count}
                </p>
              </button>
            ))}
          </div>
        </Card>
      </div>

      <div className="space-y-6">
        <Card className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Чат</p>
              <h3 className="mt-2 text-2xl font-bold text-white">
                {selectedParticipants.length
                  ? selectedParticipants.map((participant) => `${participant.first_name} ${participant.last_name ?? ""}`.trim()).join(" ↔ ")
                  : "Выберите пару контактов"}
              </h3>
            </div>
            {selectedPairKey ? (
              <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-400">{selectedPairKey}</span>
            ) : null}
          </div>

          {conversationQuery.isLoading ? <Spinner /> : null}
          {conversationQuery.error ? <Alert>Не удалось загрузить сообщения.</Alert> : null}

          <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
            {(conversationQuery.data ?? []).length ? (
              conversationQuery.data?.map((message) => (
                <div key={message.id} className="rounded-3xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-white">
                        {message.sender_contact.full_name} → {message.recipient_contact.full_name}
                      </p>
                      <p className="mt-1 text-sm leading-6 text-slate-300">{message.body}</p>
                    </div>
                    <Button variant="ghost" onClick={() => deleteMutation.mutate(message.id)}>
                      Удалить
                    </Button>
                  </div>
                  <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">
                    {message.message_type} • {formatDateTime(message.sent_at)}
                  </p>
                </div>
              ))
            ) : (
              <div className="rounded-3xl border border-dashed border-white/10 p-5 text-sm text-slate-400">
                Здесь пока пусто. Создайте первую запись общения между выбранными контактами.
              </div>
            )}
          </div>
        </Card>

        <Card className="space-y-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Новое сообщение</p>
            <h3 className="mt-2 text-xl font-bold text-white">Фиксация реального взаимодействия внутри сети</h3>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Select value={senderContactId} onChange={(event) => setSenderContactId(event.target.value)}>
              <option value="">Отправитель</option>
              {contacts.map((contact) => (
                <option key={contact.id} value={contact.id}>
                  {contact.first_name} {contact.last_name ?? ""}
                </option>
              ))}
            </Select>

            <Select value={recipientContactId} onChange={(event) => setRecipientContactId(event.target.value)}>
              <option value="">Получатель</option>
              {contacts.map((contact) => (
                <option key={contact.id} value={contact.id}>
                  {contact.first_name} {contact.last_name ?? ""}
                </option>
              ))}
            </Select>

            <Select value={messageType} onChange={(event) => setMessageType(event.target.value as typeof messageType)}>
              <option value="chat">Chat</option>
              <option value="note">Note</option>
              <option value="follow_up">Follow-up</option>
              <option value="meeting">Meeting</option>
            </Select>
          </div>

          <Textarea
            value={body}
            onChange={(event) => setBody(event.target.value)}
            placeholder="Сюда записывается содержание реального сообщения, созвона или договорённости между двумя контактами."
            className="min-h-[140px]"
          />

          <div className="flex flex-wrap gap-3">
            <Button
              loading={createMutation.isPending}
              disabled={!senderContactId || !recipientContactId || senderContactId === recipientContactId || !body.trim()}
              onClick={() =>
                createMutation.mutate({
                  sender_contact_id: Number(senderContactId),
                  recipient_contact_id: Number(recipientContactId),
                  body,
                  message_type: messageType,
                  sent_at: new Date().toISOString(),
                })
              }
            >
              Сохранить сообщение
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                const nextSender = recipientContactId;
                const nextRecipient = senderContactId;
                setSenderContactId(nextSender);
                setRecipientContactId(nextRecipient);
              }}
              disabled={!senderContactId || !recipientContactId}
            >
              Поменять направление
            </Button>
          </div>

          {createMutation.error ? (
            <Alert>{createMutation.error instanceof Error ? createMutation.error.message : "Не удалось сохранить сообщение."}</Alert>
          ) : null}
        </Card>
      </div>
    </div>
  );
}
