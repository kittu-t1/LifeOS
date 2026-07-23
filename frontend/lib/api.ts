/**
 * Thin client for talking to the LifeOS backend.
 *
 * The backend URL is read from an environment variable so it is never
 * hardcoded - this lets the same build work against local, staging, and
 * production backends just by changing NEXT_PUBLIC_API_URL.
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  timestamp: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/health`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Health check failed with status ${res.status}`);
  }

  return res.json() as Promise<HealthResponse>;
}

/**
 * Shared fetch wrapper for the /api/v1 surface - used by services/*.ts.
 * Centralizes base URL, JSON headers, and error handling so individual
 * services stay thin.
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(
      `Request to ${path} failed with status ${res.status}${body ? `: ${body}` : ""}`,
    );
  }

  // A 204 (e.g. DELETE /memories/{id} - see services/memory.ts) has no
  // body at all; res.json() would throw on the empty string. Every
  // other route in this app returns JSON, so this is the one exception,
  // not a general "maybe there's a body" check.
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
