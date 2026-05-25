const API_URL = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  headers.set("X-Requested-With", "XMLHttpRequest");
  if (init?.body) {
    headers.set("Content-Type", "application/json");
  }

  // We use credentials:'include' so the browser automatically sends
  // the Odoo session cookie (session_id) with every request.
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();

  // Guard against HTML responses (e.g. Odoo redirecting to its own login)
  if (text.trimStart().startsWith("<")) {
    throw new ApiError("Session expired", 401);
  }

  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new ApiError(data?.detail ?? "Ошибка запроса", response.status);
  }
  return data as T;
}
