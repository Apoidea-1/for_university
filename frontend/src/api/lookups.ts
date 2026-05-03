import { apiRequest } from "@/api/client";
import type { Category, Tag } from "@/types/api";

export function listCategories() {
  return apiRequest<Category[]>("/api/v1/categories");
}

export function listTags() {
  return apiRequest<Tag[]>("/api/v1/tags");
}

export function createCategory(payload: { name: string; color: string }) {
  return apiRequest<Category>("/api/v1/categories", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createTag(payload: { name: string }) {
  return apiRequest<Tag>("/api/v1/tags", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
