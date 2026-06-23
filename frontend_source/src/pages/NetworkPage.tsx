import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useNavigate } from "react-router-dom";

import { listContacts } from "@/api/contacts";
import { createRelationship, deleteRelationship, getNetworkGraph, listRelationships } from "@/api/network";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { MetricCard } from "@/components/ui/MetricCard";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { Textarea } from "@/components/ui/Textarea";
import { NetworkGraph } from "@/features/network/NetworkGraph";
import { formatDateTime } from "@/shared/lib/format";

const relationshipOptions = [
  { value: "professional", label: "Профессиональная связь" },
  { value: "mentor", label: "Менторская связь" },
  { value: "peer", label: "Равный контакт" },
  { value: "friend", label: "Личное знакомство" },
  { value: "client", label: "Клиентская связь" },
  { value: "community", label: "Комьюнити" },
  { value: "broker", label: "Bridge / connector" },
  { value: "other", label: "Другое" },
];

export function NetworkPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [sourceContactId, setSourceContactId] = useState("");
  const [targetContactId, setTargetContactId] = useState("");
  const [relationshipType, setRelationshipType] = useState("professional");
  const [strength, setStrength] = useState("1.5");
  const [sharedContext, setSharedContext] = useState("");
  const [notes, setNotes] = useState("");

  const contactsQuery = useQuery({
    queryKey: ["contacts", "network-options"],
    queryFn: () => listContacts({ sort_by: "name", sort_order: "asc", per_page: 200 }),
  });
  const graphQuery = useQuery({ queryKey: ["network-graph"], queryFn: getNetworkGraph });
  const relationshipsQuery = useQuery({ queryKey: ["relationships"], queryFn: listRelationships });

  const createMutation = useMutation({
    mutationFn: createRelationship,
    onSuccess: async () => {
      setSharedContext("");
      setNotes("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["network-graph"] }),
        queryClient.invalidateQueries({ queryKey: ["relationships"] }),
      ]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteRelationship,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["network-graph"] }),
        queryClient.invalidateQueries({ queryKey: ["relationships"] }),
      ]);
    },
  });

  if (contactsQuery.isLoading || graphQuery.isLoading || relationshipsQuery.isLoading) {
    return <Spinner />;
  }
  if (contactsQuery.error || graphQuery.error || relationshipsQuery.error) {
    return <Alert>Не удалось загрузить граф сети.</Alert>;
  }

  const contacts = contactsQuery.data?.items ?? [];
  const graph = graphQuery.data;
  const relationships = relationshipsQuery.data ?? [];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Контакты в графе" value={graph?.summary.total_contacts ?? 0} detail="Все узлы вашей персональной сети." />
        <MetricCard label="Связи между контактами" value={graph?.summary.total_relationships ?? 0} detail="Рёбра, которые вы явно описали или породили чатами." />
        <MetricCard label="Bridge-контакты" value={graph?.summary.bridge_contacts ?? 0} detail="Контакты с повышенной центральностью." />
        <MetricCard label="Целевые точки роста" value={graph?.summary.target_contacts ?? 0} detail="Приоритетные контакты, к которым стоит вернуться." />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <Card>
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Граф связей</p>
              <h3 className="mt-2 text-2xl font-bold text-white">Сеть контактов и их роль в вашем нетворке</h3>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-slate-400">
              {graph?.summary.bridge_names.map((name) => (
                <span key={name} className="rounded-full border border-white/10 px-3 py-1">
                  {name}
                </span>
              ))}
            </div>
          </div>
          {graph ? (
            <NetworkGraph
              data={graph}
              onContactClick={(id) => navigate(`/contacts/${id}`)}
            />
          ) : null}
        </Card>

        <Card className="space-y-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Новая связь</p>
            <h3 className="mt-2 text-xl font-bold text-white">Свяжите два контакта внутри сети</h3>
          </div>

          <Select value={sourceContactId} onChange={(event) => setSourceContactId(event.target.value)}>
            <option value="">Контакт A</option>
            {contacts.map((contact) => (
              <option key={contact.id} value={contact.id}>
                {contact.first_name} {contact.last_name ?? ""} {contact.company ? `• ${contact.company}` : ""}
              </option>
            ))}
          </Select>

          <Select value={targetContactId} onChange={(event) => setTargetContactId(event.target.value)}>
            <option value="">Контакт B</option>
            {contacts.map((contact) => (
              <option key={contact.id} value={contact.id}>
                {contact.first_name} {contact.last_name ?? ""} {contact.company ? `• ${contact.company}` : ""}
              </option>
            ))}
          </Select>

          <Select value={relationshipType} onChange={(event) => setRelationshipType(event.target.value)}>
            {relationshipOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>

          <Input value={strength} onChange={(event) => setStrength(event.target.value)} type="number" min="0.5" max="5" step="0.1" placeholder="Сила связи" />
          <Input value={sharedContext} onChange={(event) => setSharedContext(event.target.value)} placeholder="Общий контекст, проект или среда" />
          <Textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Почему эта связь важна, кто кому помогает, где есть потенциал." />

          <Button
            className="w-full"
            loading={createMutation.isPending}
            onClick={() =>
              createMutation.mutate({
                source_contact_id: Number(sourceContactId),
                target_contact_id: Number(targetContactId),
                relationship_type: relationshipType,
                strength: Number(strength) || 1.0,
                shared_context: sharedContext,
                notes,
                is_bridge: relationshipType === "broker",
              })
            }
            disabled={!sourceContactId || !targetContactId}
          >
            Сохранить связь
          </Button>

          {createMutation.error ? (
            <Alert>{createMutation.error instanceof Error ? createMutation.error.message : "Не удалось создать связь."}</Alert>
          ) : null}
        </Card>
      </section>

      <section>
        <div className="mb-4">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Рёбра графа</p>
          <h3 className="mt-2 text-2xl font-bold text-white">Последние связи между контактами</h3>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          {relationships.map((relationship) => (
            <Card key={relationship.id} className="space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-lg font-semibold text-white">
                    {relationship.source_contact.full_name} ↔ {relationship.target_contact.full_name}
                  </p>
                  <p className="mt-1 text-sm text-slate-400">
                    {relationship.relationship_type} • сила {relationship.strength.toFixed(1)} • сообщений {relationship.message_count}
                  </p>
                </div>
                <Button variant="ghost" onClick={() => deleteMutation.mutate(relationship.id)}>
                  Удалить
                </Button>
              </div>
              <p className="text-sm text-slate-300">{relationship.shared_context || relationship.notes || "Контекст пока не заполнен."}</p>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                Последняя активность: {formatDateTime(relationship.last_active_at)}
              </p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
