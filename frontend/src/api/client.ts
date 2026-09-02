/** Thin fetch wrapper. No client-side state, no caching, no interceptors. */

import type {
  ChatResponse,
  ConversationMessage,
  CorpusResponse,
  OnboardingConfig,
  Profile,
  SourceResponse,
} from "./types";

const BASE_URL = String(import.meta.env.VITE_API_BASE_URL ?? "");

export class ApiRequestError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiRequestError(
      "DemocraSeek could not be reached. Check your connection and try again.",
      0,
      "network_error",
    );
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}.`;
    let code = "http_error";
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
      if (typeof body?.error === "string") code = body.error;
    } catch {
      /* a non-JSON error body is not worth surfacing to the user */
    }
    throw new ApiRequestError(detail, response.status, code);
  }

  // A non-JSON success usually means a proxy returned the SPA fallback.
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("json")) {
    throw new ApiRequestError(
      `Expected JSON from ${path} but received "${contentType || "an unknown type"}". ` +
        "The request is probably not reaching the DemocraSeek API - check that the " +
        "backend is running and that the dev server proxy or VITE_API_BASE_URL is correct.",
      response.status,
      "unexpected_content_type",
    );
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiRequestError(
      `The response from ${path} was not valid JSON.`,
      response.status,
      "invalid_json",
    );
  }
}

export function fetchOnboardingConfig(): Promise<OnboardingConfig> {
  return request<OnboardingConfig>("/api/onboarding/config");
}

export function sendQuestion(
  question: string,
  profile: Profile,
  history: ConversationMessage[],
): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ question, profile, history }),
  });
}

export function fetchSource(sourceUrl: string): Promise<SourceResponse> {
  return request<SourceResponse>(sourceUrl);
}

export function fetchCorpus(): Promise<CorpusResponse> {
  return request<CorpusResponse>("/api/corpus");
}

export function absoluteUrl(path: string): string {
  return `${BASE_URL}${path}`;
}
