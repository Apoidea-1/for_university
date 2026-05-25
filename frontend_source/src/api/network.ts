import { apiRequest } from "@/api/client";
import type { ContactRelationship, NetworkGraphData } from "@/types/api";

export function getNetworkGraph() {
  return apiRequest<NetworkGraphData>("/api/v1/network/graph");
}

export function listRelationships() {
  return apiRequest<ContactRelationship[]>("/api/v1/network/relationships");
}

export function createRelationship(payload: {
  source_contact_id: number;
  target_contact_id: number;
  relationship_type: string;
  strength: number;
  shared_context?: string;
  notes?: string;
  is_bridge?: boolean;
}) {
  return apiRequest<ContactRelationship>("/api/v1/network/relationships", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateRelationship(
  relationshipId: string | number,
  payload: Partial<{
    relationship_type: string;
    strength: number;
    shared_context: string;
    notes: string;
    is_bridge: boolean;
    last_active_at: string;
  }>,
) {
  return apiRequest<ContactRelationship>(`/api/v1/network/relationships/${relationshipId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteRelationship(relationshipId: string | number) {
  return apiRequest<void>(`/api/v1/network/relationships/${relationshipId}`, {
    method: "DELETE",
  });
}
