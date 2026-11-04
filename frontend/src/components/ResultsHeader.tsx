import type { QueryInfo, SortKey } from "../types";

interface Props {
  query: QueryInfo | null;
  occasionTyped: string;
  total: number;
  latencyMs: number | null;
  loading: boolean;
  sort: SortKey;
  onSort: (sort: SortKey) => void;
  maxPrice: number | null;
  onMaxPrice: (value: number | null) => void;
}

const PRICE_OPTIONS = [1000, 2500, 5000];

const selectClass =
  "rounded-control border border-line bg-surface px-3 py-2 text-sm font-medium text-ink transition-colors hover:border-accent";

/** "Top picks for Diwali · 12 results · 38 ms" plus sort and max-price controls. */
export function ResultsHeader({
  query,
  occasionTyped,
  total,
  latencyMs,
  loading,
  sort,
  onSort,
  maxPrice,
  onMaxPrice,
}: Props) {
  const label = query?.matched_label ?? query?.raw ?? occasionTyped;
  const interpreted =
    query &&
    query.match_type !== "open_ended" &&
    query.raw.trim().toLowerCase() !== label.toLowerCase();

  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div aria-live="polite" aria-atomic="true">
        <h2 className="text-2xl font-extrabold sm:text-3xl">
          {loading ? "Finding gifts for " : "Top picks for "}
          <span className="text-accent">{label}</span>
        </h2>
        <p className="mt-1 text-sm text-muted">
          {loading ? (
            "Searching the catalog…"
          ) : (
            <>
              {total} {total === 1 ? "result" : "results"}
              {latencyMs != null && ` · ${Math.round(latencyMs)} ms`}
              {interpreted && ` · interpreted “${query?.raw}” as ${label}`}
            </>
          )}
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <label className="flex flex-col gap-1 text-xs font-semibold text-muted">
          Sort by
          <select
            value={sort}
            onChange={(e) => onSort(e.target.value as SortKey)}
            className={selectClass}
          >
            <option value="best">Best match</option>
            <option value="price-asc">Price: low to high</option>
            <option value="discount">Biggest discount</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs font-semibold text-muted">
          Max price
          <select
            value={maxPrice ?? ""}
            onChange={(e) => onMaxPrice(e.target.value ? Number(e.target.value) : null)}
            className={selectClass}
          >
            <option value="">Any price</option>
            {PRICE_OPTIONS.map((p) => (
              <option key={p} value={p}>
                Up to ₹{p.toLocaleString("en-IN")}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
