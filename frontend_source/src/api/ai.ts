import { apiRequest } from "@/api/client";
import type { ContactMetadataSuggestion, NextActionSuggestion } from "@/types/api";

export function suggestContactMetadata(payload: {
  notes: string;
  first_name?: string;
  company?: string;
  role?: string;
  source_where_met?: string;
  contact_id?: number;
}) {
  return apiRequest<ContactMetadataSuggestion>("/api/v1/ai/suggest-contact-metadata", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function suggestNextAction(payload: { notes: string; last_interaction_summary?: string; contact_id?: number }) {
  return apiRequest<NextActionSuggestion>("/api/v1/ai/suggest-next-action", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
