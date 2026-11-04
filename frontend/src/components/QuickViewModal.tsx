import { motion } from "framer-motion";
import { Check, Percent, Sparkles, Store, Tag, X } from "lucide-react";
import { useEffect, useId, useRef } from "react";
import { formatPrice, matchPercent } from "../lib/format";
import type { Product, ScoreBreakdown } from "../types";
import { PriceTag } from "./PriceTag";
import { ProductImage } from "./ProductImage";

interface Props {
  product: Product;
  onClose: () => void;
}

// Maximum contribution of each signal under the default weights (backend/app/config.py),
// used only to scale the bars.
const ROWS: { key: keyof ScoreBreakdown; label: string; max: number; hint: string }[] = [
  {
    key: "semantic",
    label: "Semantic similarity",
    max: 0.45,
    hint: "Embedding match to the occasion",
  },
  { key: "tag", label: "Occasion tag", max: 0.35, hint: "Offline occasion-fit score" },
  { key: "keyword", label: "Keyword match", max: 0.2, hint: "BM25 / TF-IDF text overlap" },
  { key: "name_boost", label: "Name boost", max: 0.3, hint: "Occasion appears in the title" },
];

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

// Radius / circumference of the circular match gauge.
const GAUGE_R = 26;
const GAUGE_C = 2 * Math.PI * GAUGE_R;

export function QuickViewModal({ product, onClose }: Props) {
  const titleId = useId();
  const panel = useRef<HTMLDivElement>(null);
  const closeBtn = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    closeBtn.current?.focus();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "Tab" && panel.current) {
        // Keep keyboard focus inside the dialog.
        const items = Array.from(panel.current.querySelectorAll<HTMLElement>(FOCUSABLE));
        if (items.length === 0) return;
        const first = items[0];
        const last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      previouslyFocused?.focus();
    };
  }, [onClose]);

  const { breakdown } = product;
  const pct = matchPercent(product.score);
  const saving =
    product.price != null && product.final_price != null ? product.price - product.final_price : 0;

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <motion.div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 24, scale: 0.97 }}
        transition={{ type: "spring", stiffness: 380, damping: 32 }}
        className="relative flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-t-3xl bg-surface shadow-float sm:rounded-3xl md:max-h-[88vh] md:flex-row"
      >
        <button
          ref={closeBtn}
          type="button"
          onClick={onClose}
          aria-label="Close details"
          className="absolute right-3 top-3 z-20 rounded-full bg-surface/90 p-2 text-ink shadow-card transition-colors hover:bg-sunken focus-visible:outline-none focus-visible:shadow-glow"
        >
          <X className="h-5 w-5" aria-hidden="true" />
        </button>

        {/* Media column */}
        <div className="relative shrink-0 bg-sunken md:w-[46%]">
          <ProductImage
            src={product.image}
            alt={product.title}
            eager
            className="aspect-[4/3] md:aspect-auto md:h-full md:min-h-[32rem]"
          />
          <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-black/35 to-transparent" />
          <div className="absolute left-4 top-4 flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-surface/95 px-3 py-1 text-xs font-semibold text-accent shadow-card">
              <Tag className="h-3 w-3" aria-hidden="true" />
              {product.category}
            </span>
            {product.discount_pct > 0 && (
              <span className="inline-flex items-center gap-1 rounded-full bg-deal px-3 py-1 text-xs font-bold text-white shadow-card">
                <Percent className="h-3 w-3" aria-hidden="true" />
                {Math.round(product.discount_pct)}% off
              </span>
            )}
          </div>
        </div>

        {/* Details column */}
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="flex-1 space-y-6 overflow-y-auto p-6 md:p-8">
            <header className="flex items-start justify-between gap-4 pr-10">
              <div className="min-w-0">
                <h2 id={titleId} className="text-2xl font-extrabold leading-tight tracking-heading">
                  {product.title}
                </h2>
                <p className="mt-1.5 inline-flex items-center gap-1.5 text-sm text-muted">
                  <Store className="h-4 w-4" aria-hidden="true" />
                  Sold by <span className="font-semibold text-ink">{product.shop}</span>
                </p>
              </div>
            </header>

            <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-sunken p-4">
              <div>
                <PriceTag product={product} large />
                {saving > 0 && (
                  <p className="mt-1 text-sm font-semibold text-deal">
                    You save {formatPrice(saving)}
                  </p>
                )}
              </div>
              <div
                className="flex items-center gap-3"
                role="img"
                aria-label={`${pct}% match with the occasion`}
                title="How well this product matches the occasion"
              >
                <div className="relative h-14 w-14">
                  <svg viewBox="0 0 64 64" className="h-14 w-14 -rotate-90" aria-hidden="true">
                    <circle
                      cx="32"
                      cy="32"
                      r={GAUGE_R}
                      fill="none"
                      strokeWidth="6"
                      className="stroke-surface"
                    />
                    <motion.circle
                      cx="32"
                      cy="32"
                      r={GAUGE_R}
                      fill="none"
                      strokeWidth="6"
                      strokeLinecap="round"
                      className="stroke-accent"
                      strokeDasharray={GAUGE_C}
                      initial={{ strokeDashoffset: GAUGE_C }}
                      animate={{ strokeDashoffset: GAUGE_C * (1 - pct / 100) }}
                      transition={{ duration: 0.7, ease: "easeOut", delay: 0.1 }}
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-sm font-extrabold tabular-nums">
                    {pct}%
                  </span>
                </div>
                <span className="text-xs font-semibold leading-tight text-muted">
                  Occasion
                  <br />
                  match
                </span>
              </div>
            </div>

            <section aria-label="About this product">
              <h3 className="mb-2 text-sm font-bold">About this product</h3>
              <p className="text-sm leading-relaxed text-muted">{product.description}</p>
            </section>

            {product.reasons.length > 0 && (
              <section aria-label="Why recommended">
                <h3 className="mb-2 flex items-center gap-1.5 text-sm font-bold">
                  <Sparkles className="h-4 w-4 text-accent" aria-hidden="true" />
                  Why recommended
                </h3>
                <ul className="flex flex-wrap gap-2">
                  {product.reasons.map((r) => (
                    <li
                      key={r}
                      className="inline-flex items-center gap-1.5 rounded-full bg-accent-soft px-3 py-1 text-xs font-semibold text-accent"
                    >
                      <Check className="h-3 w-3" aria-hidden="true" />
                      {r}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <section aria-label="Score breakdown" className="rounded-2xl bg-sunken p-4">
              <h3 className="mb-3 text-sm font-bold">
                Score breakdown{" "}
                <span className="font-medium text-muted">· total {product.score.toFixed(2)}</span>
              </h3>
              <dl className="space-y-2.5">
                {ROWS.map(({ key, label, max, hint }) => (
                  <div key={key} title={hint}>
                    <div className="flex justify-between text-xs">
                      <dt className="font-medium text-muted">{label}</dt>
                      <dd className="font-semibold tabular-nums">+{breakdown[key].toFixed(2)}</dd>
                    </div>
                    <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface">
                      <motion.div
                        className="h-full w-full origin-left rounded-full bg-accent"
                        initial={{ scaleX: 0 }}
                        animate={{ scaleX: Math.min(1, breakdown[key] / max) }}
                        transition={{ duration: 0.45, ease: "easeOut", delay: 0.1 }}
                      />
                    </div>
                  </div>
                ))}
                {breakdown.penalty > 0 && (
                  <div className="flex justify-between text-xs">
                    <dt className="font-medium text-danger">
                      Penalty (sibling occasion / data quality)
                    </dt>
                    <dd className="font-semibold tabular-nums text-danger">
                      −{breakdown.penalty.toFixed(2)}
                    </dd>
                  </div>
                )}
              </dl>
              <p className="mt-3 text-xs text-muted">
                score = 0.45·semantic + 0.35·tag + 0.20·keyword + name boost − penalties
              </p>
            </section>
          </div>

          <footer className="flex items-center justify-between gap-3 border-t border-sunken bg-surface p-4 md:px-8">
            <span className="hidden text-xs text-muted sm:block">
              Press{" "}
              <kbd className="rounded border border-sunken bg-sunken px-1.5 py-0.5 font-sans">
                Esc
              </kbd>{" "}
              to close
            </span>
            <button
              type="button"
              onClick={onClose}
              className="w-full rounded-xl bg-accent px-6 py-2.5 text-sm font-bold text-accent-ink shadow-card transition-transform hover:-translate-y-0.5 focus-visible:outline-none focus-visible:shadow-glow sm:w-auto"
            >
              Back to results
            </button>
          </footer>
        </div>
      </motion.div>
    </motion.div>
  );
}
