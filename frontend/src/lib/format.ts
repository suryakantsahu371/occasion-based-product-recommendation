import type { Product, SortKey } from "../types";

const inr = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export const formatPrice = (value: number | null): string =>
  value == null ? "" : inr.format(value);

/** Match percentage shown on cards: the hybrid score clamped to 0-100. */
export const matchPercent = (score: number): number =>
  Math.max(0, Math.min(100, Math.round(score * 100)));

/** Client-side sorting; "best" keeps the server's relevance order. Ties fall back to relevance. */
export function sortProducts(products: Product[], sort: SortKey): Product[] {
  const byRelevance = (a: Product, b: Product) => b.score - a.score;
  const copy = [...products];
  if (sort === "price-asc") {
    return copy.sort(
      (a, b) => (a.final_price ?? Infinity) - (b.final_price ?? Infinity) || byRelevance(a, b),
    );
  }
  if (sort === "discount")
    return copy.sort((a, b) => b.discount_pct - a.discount_pct || byRelevance(a, b));
  return copy.sort(byRelevance);
}
