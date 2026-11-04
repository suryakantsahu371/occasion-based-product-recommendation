import { AnimatePresence, LayoutGroup, MotionConfig, motion } from "framer-motion";
import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchOccasions } from "./api";
import { EmptyState } from "./components/EmptyState";
import { ErrorState } from "./components/ErrorState";
import { Footer } from "./components/Footer";
import { Header } from "./components/Header";
import { OccasionChips } from "./components/OccasionChips";
import { ProductCard } from "./components/ProductCard";
import { ProductSkeleton } from "./components/ProductSkeleton";
import { QuickViewModal } from "./components/QuickViewModal";
import { ResultsHeader } from "./components/ResultsHeader";
import { SearchBar } from "./components/SearchBar";
import { useRecommendations } from "./hooks/useRecommendations";
import { sortProducts } from "./lib/format";
import { useTheme } from "./lib/useTheme";
import type { Occasion, Product, SortKey } from "./types";

const SKELETON_COUNT = 8;
const GRID = "grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4";

export default function App() {
  const { dark, toggle } = useTheme();
  const { state, search, retry } = useRecommendations();
  const [occasions, setOccasions] = useState<Occasion[]>([]);
  const [query, setQuery] = useState("");
  const [searched, setSearched] = useState(false);
  const [sort, setSort] = useState<SortKey>("best");
  const [maxPrice, setMaxPrice] = useState<number | null>(null);
  const [selected, setSelected] = useState<Product | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    fetchOccasions(ctrl.signal)
      .then(setOccasions)
      .catch(() => undefined); // autocomplete is optional; the chips still work without it
    return () => ctrl.abort();
  }, []);

  const runSearch = useCallback(
    (occasion: string, price: number | null = maxPrice) => {
      setQuery(occasion);
      setSearched(true);
      void search({ occasion, max_price: price });
    },
    [maxPrice, search],
  );

  const changeMaxPrice = (value: number | null) => {
    setMaxPrice(value);
    if (query.trim()) runSearch(query.trim(), value);
  };

  const data = state.status === "success" ? state.data : null;
  const rankById = useMemo(
    () => new Map(data?.results.map((p, i) => [p.product_id, i]) ?? []),
    [data],
  );
  const sorted = useMemo(() => (data ? sortProducts(data.results, sort) : []), [data, sort]);
  const closeModal = useCallback(() => setSelected(null), []);

  return (
    <MotionConfig reducedMotion="user">
      <div className="flex min-h-screen flex-col">
        <Header dark={dark} onToggleTheme={toggle} />

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 sm:px-6">
          <LayoutGroup>
            <motion.section
              layout
              aria-labelledby="hero-title"
              className={`text-center ${searched ? "pb-6 pt-2" : "pb-10 pt-12 sm:pt-20"}`}
            >
              <motion.h1
                layout="position"
                id="hero-title"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className={`font-extrabold ${searched ? "mb-4 text-2xl sm:text-3xl" : "mb-3 text-4xl sm:text-6xl"}`}
              >
                Find the perfect gift for <span className="text-accent">every occasion</span>
              </motion.h1>
              <AnimatePresence>
                {!searched && (
                  <motion.p
                    key="subtitle"
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.4, ease: "easeOut", delay: 0.08 }}
                    className="mx-auto mb-8 max-w-xl text-base text-muted sm:text-lg"
                  >
                    Tell us the occasion, in any words you like, and we&apos;ll rank the catalog by
                    how well each gift fits.
                  </motion.p>
                )}
              </AnimatePresence>
              <motion.div
                layout="position"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: "easeOut", delay: 0.15 }}
              >
                <SearchBar
                  occasions={occasions}
                  value={query}
                  onChange={setQuery}
                  onSubmit={(q) => runSearch(q)}
                  loading={state.status === "loading"}
                />
              </motion.div>
              <motion.div layout="position">
                <OccasionChips active={query} onPick={(label) => runSearch(label)} />
              </motion.div>
            </motion.section>
          </LayoutGroup>

          <section aria-label="Recommendations" className="pb-8">
            {state.status === "loading" && (
              <>
                <ResultsHeader
                  query={null}
                  occasionTyped={state.occasion}
                  total={0}
                  latencyMs={null}
                  loading
                  sort={sort}
                  onSort={setSort}
                  maxPrice={maxPrice}
                  onMaxPrice={changeMaxPrice}
                />
                <ul className={GRID} aria-busy="true" aria-label="Loading recommendations">
                  {Array.from({ length: SKELETON_COUNT }, (_, i) => (
                    <ProductSkeleton key={i} />
                  ))}
                </ul>
              </>
            )}

            {state.status === "error" && <ErrorState message={state.message} onRetry={retry} />}

            {data && (
              <>
                <ResultsHeader
                  query={data.query}
                  occasionTyped={data.query.raw}
                  total={data.total}
                  latencyMs={data.latency_ms}
                  loading={false}
                  sort={sort}
                  onSort={setSort}
                  maxPrice={maxPrice}
                  onMaxPrice={changeMaxPrice}
                />
                {data.results.length === 0 ? (
                  <EmptyState query={data.query.raw} onPick={(label) => runSearch(label)} />
                ) : (
                  <motion.ul layout className={GRID} aria-label="Recommended products">
                    {sorted.map((p, i) => (
                      <ProductCard
                        key={p.product_id}
                        product={p}
                        rank={rankById.get(p.product_id) ?? i}
                        index={i}
                        onOpen={setSelected}
                      />
                    ))}
                  </motion.ul>
                )}
              </>
            )}
          </section>
        </main>

        <Footer />

        <AnimatePresence>
          {selected && (
            <QuickViewModal key={selected.product_id} product={selected} onClose={closeModal} />
          )}
        </AnimatePresence>
      </div>
    </MotionConfig>
  );
}
