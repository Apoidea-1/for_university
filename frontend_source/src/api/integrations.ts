import { apiRequest } from "@/api/client";
import type { Integration } from "@/types/api";

export function listIntegrations() {
  return apiRequest<Integration[]>("/api/v1/integrations");
}

export function connectMockIntegration(provider: string) {
  return apiRequest<{ provider: string; status: string; message: string }>(
    `/api/v1/integrations/${provider}/connect-mock`,
    {
      method: "POST",
    },
  );
}
