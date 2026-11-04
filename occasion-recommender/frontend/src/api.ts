import type { Occasion, RecommendRequest, RecommendResponse } from "./types";

// Empty by default: in dev Vite proxies /api, in Docker nginx does. Override for a remote API.
const BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, init);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Can't reach the recommendation service. Check your connection and retry.");
  }
  if (!res.ok) {
    const hint =
      res.status === 422 ? "Please enter a valid occasion (1–100 characters)." : undefined;
    throw new ApiError(hint ?? `The service returned an error (${res.status}).`, res.status);
  }
  return (await res.json()) as T;
}

export const fetchOccasions = (signal?: AbortSignal) =>
  request<Occasion[]>("/api/occasions", { signal });

export const recommend = (body: RecommendRequest, signal?: AbortSignal) =>
  request<RecommendResponse>("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
