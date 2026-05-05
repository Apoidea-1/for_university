import { apiRequest } from "@/api/client";
import type { AuthResponse, User } from "@/types/api";

export function register(payload: { full_name: string; email: string; password: string }) {
  return apiRequest<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function login(payload: { email: string; password: string }) {
  return apiRequest<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCurrentUser() {
  return apiRequest<User>("/api/v1/auth/me");
}
