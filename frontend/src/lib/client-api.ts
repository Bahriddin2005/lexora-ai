// Browser-side calls go to /api/v1 on the same origin (rewritten to the backend by next.config.ts).
import { toApiError } from "./api-error";

export { ApiError } from "./api-error";

let refreshing: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  refreshing ??= fetch("/api/v1/auth/refresh", { method: "POST", credentials: "same-origin" })
    .then((r) => r.ok)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

export async function apiFetch(path: string, init: RequestInit = {}, retry = true): Promise<Response> {
  const res = await fetch(`/api/v1${path}`, {
    ...init,
    credentials: "same-origin",
    headers: { "content-type": "application/json", ...(init.headers ?? {}) },
  });
  if (res.status === 401 && retry && !path.startsWith("/auth/") && (await refreshSession())) {
    return apiFetch(path, init, false);
  }
  return res;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await apiFetch(path, init);
  if (!res.ok) throw await toApiError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
export const put = <T>(path: string, body: unknown) => api<T>(path, { method: "PUT", body: JSON.stringify(body) });
export const patch = <T>(path: string, body: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
export const del = (path: string) => api<void>(path, { method: "DELETE" });
