// The only place the page knows where the API lives.
//
// Default is a same-origin path so that the dev server (and, later, a real
// reverse proxy) can forward it. A statically hosted build on its own
// origin sets VITE_API_BASE_URL to the backend's absolute origin instead —
// at which point the API needs CORS, which does not exist yet.
const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "/api").replace(/\/$/, "");

export interface Check {
  status: "ok" | "error";
  [key: string]: unknown;
}

export interface Health {
  status: "ok" | "error";
  service: string;
  checks: Record<string, Check>;
}

export async function fetchHealth(signal?: AbortSignal): Promise<Health> {
  const response = await fetch(`${BASE_URL}/health`, {
    signal,
    headers: { Accept: "application/json" },
  });
  // A failing check answers 503 with the same shape, so the body is worth
  // reading either way; only a non-JSON answer is a transport failure.
  const body = (await response.json()) as Health;
  return body;
}
