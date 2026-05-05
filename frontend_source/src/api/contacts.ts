import { apiRequest } from "@/api/client";
import type { Contact, ContactListResponse, Interaction } from "@/types/api";

export interface ContactPayload {
  first_name: string;
  last_name?: string;
  company?: string;
  role?: string;
  source_where_met?: string;
  email?: string;
  phone?: string;
  telegram?: string;
  linkedin?: string;
  other_social?: string;
  category_id?: number | null;
  importance_level?: string;
  last_interaction_date?: string | null;
  notes?: string;
  tag_names?: string[];
}

export function listContacts(params: Record<string, string | number | undefined>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  return apiRequest<ContactListResponse>(`/api/v1/contacts?${searchParams.toString()}`);
}

export function getContact(contactId: string | number) {
  return apiRequest<Contact>(`/api/v1/contacts/${contactId}`);
}

export function createContact(payload: ContactPayload) {
  return apiRequest<Contact>("/api/v1/contacts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function quickAddContact(payload: {
  first_name: string;
  source_where_met?: string;
  category_id?: number | null;
  notes?: string;
}) {
  return apiRequest<Contact>("/api/v1/contacts/quick-add", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateContact(contactId: string | number, payload: Partial<ContactPayload>) {
  return apiRequest<Contact>(`/api/v1/contacts/${contactId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteContact(contactId: string | number) {
  return apiRequest<void>(`/api/v1/contacts/${contactId}`, {
    method: "DELETE",
  });
}

export function listInteractions(contactId: string | number) {
  return apiRequest<Interaction[]>(`/api/v1/contacts/${contactId}/interactions`);
}

export function createInteraction(
  contactId: string | number,
  payload: { type: string; title: string; description?: string; interaction_date: string },
) {
  return apiRequest<Interaction>(`/api/v1/contacts/${contactId}/interactions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteInteraction(interactionId: string | number) {
  return apiRequest<void>(`/api/v1/interactions/${interactionId}`, {
    method: "DELETE",
  });
}
