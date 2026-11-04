/** Typed mirror of the FastAPI response models (backend/app/schemas.py). */

export interface Occasion {
  key: string;
  label: string;
  icon: string;
}

export interface ScoreBreakdown {
  semantic: number;
  tag: number;
  keyword: number;
  name_boost: number;
  penalty: number;
}

export interface Product {
  product_id: string;
  title: string;
  category: string;
  description: string;
  description_snippet: string;
  image: string | null;
  shop: string;
  price: number | null;
  final_price: number | null;
  discount_pct: number;
  score: number;
  breakdown: ScoreBreakdown;
  reasons: string[];
}

export interface QueryInfo {
  raw: string;
  matched_occasion: string | null;
  matched_label: string | null;
  match_type: "exact" | "fuzzy" | "open_ended";
}

export interface RecommendResponse {
  query: QueryInfo;
  results: Product[];
  total: number;
  keyword_method: string;
  latency_ms: number;
}

export interface RecommendRequest {
  occasion: string;
  top_k?: number;
  max_price?: number | null;
}

export type SortKey = "best" | "price-asc" | "discount";
