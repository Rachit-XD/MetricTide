/**
 * Thin wrapper around `fetch` for talking to the MetricTide API.
 *
 * Scaffolding only: it resolves the correct base URL for the runtime
 * (server vs browser) and centralizes error handling. Feature-specific
 * calls will build on top of this.
 */
import { clientEnv } from "@/config/env";

function resolveBaseUrl(): string {
  // On the server we may reach the API via an internal hostname.
  if (typeof window === "undefined") {
    return process.env.API_INTERNAL_BASE_URL ?? clientEnv.NEXT_PUBLIC_API_BASE_URL;
  }
  return clientEnv.NEXT_PUBLIC_API_BASE_URL;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = resolveBaseUrl();
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(`Request to ${path} failed`, response.status);
  }

  return (await response.json()) as T;
}
