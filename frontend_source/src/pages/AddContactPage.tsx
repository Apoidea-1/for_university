import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";

import { createContact, getContact, updateContact } from "@/api/contacts";
import { listCategories } from "@/api/lookups";
import { Alert } from "@/components/ui/Alert";
import { Spinner } from "@/components/ui/Spinner";
import { ContactForm, type ContactFormPayload } from "@/features/contacts/ContactForm";

export function AddContactPage() {
  const { contactId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = Boolean(contactId);

  const categoriesQuery = useQuery({ queryKey: ["categories"], queryFn: listCategories });
  const contactQuery = useQuery({
    queryKey: ["contact", contactId],
    queryFn: () => getContact(contactId as string),
    enabled: isEditing,
  });

  const mutation = useMutation({
    mutationFn: async (payload: ContactFormPayload) => {
      if (isEditing) {
        return updateContact(contactId as string, payload);
      }
      return createContact(payload);
    },
    onSuccess: async (contact) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["contacts"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-categories"] }),
      ]);
      navigate(`/contacts/${contact.id}`);
    },
  });

  if (categoriesQuery.isLoading || contactQuery.isLoading) {
    return <Spinner />;
  }
  if (categoriesQuery.error || contactQuery.error) {
    return <Alert>Не удалось загрузить форму контакта.</Alert>;
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">
          {isEditing ? "Редактирование" : "Новый контакт"}
        </p>
        <h1 className="mt-2 text-3xl font-bold text-white">
          {isEditing ? "Обновите данные контакта" : "Создайте подробную карточку контакта"}
        </h1>
      </div>

      <ContactForm
        categories={categoriesQuery.data ?? []}
        defaultContact={contactQuery.data}
        submitLabel={isEditing ? "Сохранить изменения" : "Создать контакт"}
        submitting={mutation.isPending}
        onSubmit={async (payload) => mutation.mutateAsync(payload)}
      />
    </div>
  );
}
