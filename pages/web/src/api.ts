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

export interface SourceSummary {
  slug: string;
  title: string;
  /** Which typesetting this is: "JEP, 2018". Page numbers belong to it. */
  edition: string;
  filename: string;
  sha256: string;
  pages: number | null;
  characters: number;
  units: number;
  embedded_units: number;
  language: string;
  extractor: string;
  pipeline_version: string;
  ingested_at: string;
}

export interface SourcesResponse {
  sources: SourceSummary[];
  provider_configured: boolean;
}

/** A verbatim run of the document, with the anchor that locates it. */
export interface Citation {
  unit_id: number;
  path: string;
  page_start: number | null;
  page_end: number | null;
  start_offset: number;
  end_offset: number;
  text: string;
}

export interface Claim {
  statement: string;
  /** "quotation" restates one extract; "interpretation" reads across them. */
  kind: "quotation" | "interpretation";
  supported: boolean;
  citations: Citation[];
}

export interface RetrievedUnit {
  unit_id: number;
  path: string;
  page_start: number | null;
  page_end: number | null;
  start_offset: number;
  end_offset: number;
  kind: string;
  heading: string;
  preview: string;
}

/** The document an answer came out of, carried by the answer itself. */
export interface AnswerSource {
  slug: string;
  title: string;
  edition: string;
  sha256: string;
  pages: number | null;
}

export interface Answer {
  source: AnswerSource;
  question: string;
  abstained: boolean;
  abstention_reason: string | null;
  claims: Claim[];
  retrieved: RetrievedUnit[];
  notes: string[];
  model: string | null;
  usage: { input_tokens: number | null; output_tokens: number | null } | null;
}

async function getJSON<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    signal,
    headers: { Accept: "application/json" },
  });
  return (await response.json()) as T;
}

export function fetchHealth(signal?: AbortSignal): Promise<Health> {
  return getJSON<Health>("/health", signal);
}

export function fetchSources(signal?: AbortSignal): Promise<SourcesResponse> {
  return getJSON<SourcesResponse>("/sources", signal);
}

export async function ask(
  slug: string,
  question: string,
  signal?: AbortSignal,
): Promise<Answer> {
  const response = await fetch(`${BASE_URL}/sources/${slug}/ask`, {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ question }),
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body?.error ?? `The API answered ${response.status}`);
  }
  return body as Answer;
}
