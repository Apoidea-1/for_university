import { apiRequest } from "@/api/client";
import type { ContactMessage, ConversationSummary } from "@/types/api";

export function listConversations() {
  return apiRequest<ConversationSummary[]>("/api/v1/messages/conversations");
}

export function getConversation(pairKey: string) {
  return apiRequest<ContactMessage[]>(`/api/v1/messages/conversations/${pairKey}`);
}

export function createMessage(payload: {
  sender_contact_id: number;
  recipient_contact_id: number;
  body: string;
  message_type?: "chat" | "note" | "follow_up" | "meeting";
  sent_at?: string;
  metadata_json?: Record<string, unknown>;
  is_ai_draft?: boolean;
}) {
  return apiRequest<ContactMessage>("/api/v1/messages", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteMessage(messageId: string | number) {
  return apiRequest<void>(`/api/v1/messages/${messageId}`, {
    method: "DELETE",
  });
}
