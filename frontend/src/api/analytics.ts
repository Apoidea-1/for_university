import { apiRequest } from "@/api/client";
import type { AnalyticsOverview, CategoryAnalyticsItem, StaleContact } from "@/types/api";

export function getAnalyticsOverview() {
  return apiRequest<AnalyticsOverview>("/api/v1/analytics/overview");
}

export function getCategoryAnalytics() {
  return apiRequest<CategoryAnalyticsItem[]>("/api/v1/analytics/categories");
}

export function getStaleContacts(days = 21) {
  return apiRequest<StaleContact[]>(`/api/v1/analytics/stale-contacts?days=${days}`);
}
