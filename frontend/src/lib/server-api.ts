// Server-side calls to the FastAPI backend: forwards the visitor's cookies and IP.
import { cookies, headers } from "next/headers";

import { ApiError, toApiError } from "./api-error";
import type { User } from "./types";

export const BACKEND_URL = process.env.BACKEND_URL ?? "";

export async function apiServer<T>(path: string, init: RequestInit = {}): Promise<T> {
  const cookieStore = await cookies();
  const incoming = await headers();
  const host = incoming.get("x-forwarded-host") ?? incoming.get("host") ?? "localhost:3000";
  const proto = incoming.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  const apiOrigin = BACKEND_URL || `${proto}://${host}`;
  const forwardedFor = incoming.get("x-forwarded-for") ?? incoming.get("x-real-ip");
  const res = await fetch(`${apiOrigin}/api/v1${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      cookie: cookieStore.getAll().map((c) => `${c.name}=${c.value}`).join("; "),
      ...(forwardedFor ? { "x-forwarded-for": forwardedFor } : {}),
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) throw await toApiError(res);
  return (await res.json()) as T;
}

/** Like apiServer, but returns null for 401/403/404 instead of throwing. */
export async function apiServerOrNull<T>(path: string): Promise<T | null> {
  try {
    return await apiServer<T>(path);
  } catch (err) {
    if (err instanceof ApiError && [401, 403, 404].includes(err.status)) return null;
    throw err;
  }
}

export async function currentUser(): Promise<User | null> {
  const cookieStore = await cookies();
  if (!cookieStore.has("lx_access")) return null;
  return apiServerOrNull<User>("/auth/me");
}
