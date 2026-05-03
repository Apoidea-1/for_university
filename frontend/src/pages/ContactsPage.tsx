import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { listContacts, quickAddContact } from "@/api/contacts";
import { listCategories } from "@/api/lookups";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { ContactTable } from "@/features/contacts/ContactTable";
import { QuickContactForm } from "@/features/contacts/QuickContactForm";
import { importanceLabels } from "@/shared/lib/labels";

export function ContactsPage() {
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [importance, setImportance] = useState("");
  const [sortBy, setSortBy] = useState("last_interaction_date");
  const queryClient = useQueryClient();

  const categoriesQuery = useQuery({ queryKey: ["categories"], queryFn: listCategories });
  const contactsQuery = useQuery({
    queryKey: ["contacts", search, categoryId, importance, sortBy],
    queryFn: () =>
      listContacts({
        search,
        category_id: categoryId,
        importance_level: importance,
        sort_by: sortBy,
      }),
  });

  const quickAddMutation = useMutation({
    mutationFn: quickAddContact,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["contacts"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-categories"] }),
      ]);
    },
  });

  if (categoriesQuery.isLoading || contactsQuery.isLoading) {
    return <Spinner />;
  }
  if (categoriesQuery.error || contactsQuery.error) {
    return <Alert>Не удалось загрузить контакты.</Alert>;
  }

  return (
    <div className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="min-w-0 space-y-6">
        <Card className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-[minmax(0,1.5fr)_repeat(3,minmax(0,0.85fr))_auto]">
            <Input
              className="min-w-0 md:col-span-2 2xl:col-span-1"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Поиск по имени, компании, должности или тегу"
            />

            <Select className="min-w-0" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
              <option value="">Все категории</option>
              {(categoriesQuery.data ?? []).map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </Select>

            <Select className="min-w-0" value={importance} onChange={(event) => setImportance(event.target.value)}>
              <option value="">Любая важность</option>
              <option value="low">{importanceLabels.low}</option>
              <option value="medium">{importanceLabels.medium}</option>
              <option value="high">{importanceLabels.high}</option>
              <option value="strategic">{importanceLabels.strategic}</option>
            </Select>

            <Select className="min-w-0" value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
              <option value="last_interaction_date">Сначала по последнему взаимодействию</option>
              <option value="created_at">Сначала по дате добавления</option>
              <option value="name">По имени</option>
            </Select>

            <Button
              className="w-full 2xl:w-auto"
              variant="secondary"
              onClick={() => {
                setSearch("");
                setCategoryId("");
                setImportance("");
                setSortBy("last_interaction_date");
              }}
            >
              Сбросить
            </Button>
          </div>
        </Card>

        <ContactTable contacts={contactsQuery.data?.items ?? []} />
      </div>

      <div className="2xl:sticky 2xl:top-6 2xl:self-start">
        <QuickContactForm
          categories={categoriesQuery.data ?? []}
          onSubmit={async (payload) => {
            await quickAddMutation.mutateAsync(payload);
          }}
        />
      </div>
    </div>
  );
}
