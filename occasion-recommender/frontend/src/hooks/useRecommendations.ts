import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, recommend } from "../api";
import type { RecommendRequest, RecommendResponse } from "../types";

export type RecommendationState =
  | { status: "idle" }
  | { status: "loading"; occasion: string }
  | { status: "success"; data: RecommendResponse }
  | { status: "error"; message: string; occasion: string };

/** Runs searches, cancelling any in-flight request when a new one starts. */
export function useRecommendations() {
  const [state, setState] = useState<RecommendationState>({ status: "idle" });
  const controller = useRef<AbortController | null>(null);
  const lastRequest = useRef<RecommendRequest | null>(null);

  const search = useCallback(async (req: RecommendRequest) => {
    controller.current?.abort();
    const ctrl = new AbortController();
    controller.current = ctrl;
    lastRequest.current = req;
    setState({ status: "loading", occasion: req.occasion });
    try {
      const data = await recommend(req, ctrl.signal);
      setState({ status: "success", data });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return; // superseded by a newer search
      const message =
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setState({ status: "error", message, occasion: req.occasion });
    }
  }, []);

  const retry = useCallback(() => {
    if (lastRequest.current) void search(lastRequest.current);
  }, [search]);

  useEffect(() => () => controller.current?.abort(), []);

  return { state, search, retry };
}
