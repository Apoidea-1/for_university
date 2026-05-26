import { apiRequest } from "@/api/client";
import type { Reminder } from "@/types/api";

export function listReminders(status?: string) {
  const query = status ? `?status=${status}` : "";
  return apiRequest<Reminder[]>(`/api/v1/reminders${query}`);
}

export function createReminder(payload: {
  contact_id?: number | null;
  title: string;
  description?: string;
  due_date: string;
  status?: string;
  reminder_type: string;
}) {
  return apiRequest<Reminder>("/api/v1/reminders", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateReminder(reminderId: string | number, payload: Record<string, unknown>) {
  return apiRequest<Reminder>(`/api/v1/reminders/${reminderId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteReminder(reminderId: string | number) {
  return apiRequest<void>(`/api/v1/reminders/${reminderId}`, {
    method: "DELETE",
  });
}

export function suggestAIReminders() {
  return apiRequest<import("@/types/api").AiReminderSuggestion[]>("/api/v1/network/reminders/ai-suggest", {
    method: "GET",
  });
}
