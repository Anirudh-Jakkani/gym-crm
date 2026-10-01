import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

export type Schemas = components["schemas"];

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

type ErrorBody = { detail?: string | { msg: string; loc?: (string | number)[] }[] };

function messageFrom(body: unknown, status: number): string {
  const detail = (body as ErrorBody | undefined)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    const field = first.loc?.filter((p) => p !== "body").join(".");
    return field ? `${field}: ${first.msg}` : first.msg;
  }
  return status >= 500 ? "Something went wrong. Please try again." : "Request failed";
}

let refreshing: Promise<boolean> | null = null;

/** One refresh at a time, shared by every request that got a 401 meanwhile. */
function refreshSession(): Promise<boolean> {
  refreshing ??= fetch("/api/auth/refresh", { method: "POST", credentials: "include" })
    .then((res) => res.ok)
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

const NO_RETRY = ["/api/auth/login", "/api/auth/signup", "/api/auth/refresh", "/api/auth/logout"];

async function fetchWithRefresh(input: Request): Promise<Response> {
  const retry = input.clone();
  const res = await fetch(input);
  const path = new URL(input.url).pathname;
  if (res.status !== 401 || NO_RETRY.some((p) => path.startsWith(p))) return res;
  if (await refreshSession()) return fetch(retry);
  if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
  }
  return res;
}

export const api = createClient<paths>({
  baseUrl: typeof window === "undefined" ? process.env.BACKEND_URL : "",
  credentials: "include",
  fetch: fetchWithRefresh,
});

/** Turns an openapi-fetch result into data-or-throw, for use with TanStack Query. */
export async function unwrap<T>(
  promise: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await promise;
  if (!response.ok) throw new ApiError(messageFrom(error, response.status), response.status);
  return data as T;
}
