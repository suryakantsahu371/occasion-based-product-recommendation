import { motion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect, useId, useRef } from "react";
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
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.96 }}
        transition={{ type: "spring", stiffness: 380, damping: 32 }}
        className="relative max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-t-3xl bg-surface shadow-float sm:rounded-3xl md:grid md:grid-cols-2"
      >
        <button
          ref={closeBtn}
          type="button"
          onClick={onClose}
          aria-label="Close details"
          className="absolute right-3 top-3 z-10 rounded-full bg-surface/90 p-2 text-ink shadow-card transition-colors hover:bg-sunken"
        >
          <X className="h-5 w-5" aria-hidden="true" />
        </button>

        <ProductImage
          src={product.image}
          alt={product.title}
          eager
          className="md:aspect-auto md:h-full md:min-h-[24rem]"
        />

        <div className="flex flex-col gap-5 p-6">
          <div>
            <span className="rounded-full bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent">
              {product.category}
            </span>
            <h2 id={titleId} className="mt-3 text-2xl font-extrabold leading-tight">
              {product.title}
            </h2>
            <p className="mt-1 text-sm text-muted">Sold by {product.shop}</p>
          </div>

          <PriceTag product={product} large />
          <p className="text-sm leading-relaxed text-muted">{product.description}</p>

          <section aria-label="Why recommended">
            <h3 className="mb-2 text-sm font-bold">Why recommended</h3>
            <ul className="flex flex-wrap gap-1.5">
              {product.reasons.map((r) => (
                <li
                  key={r}
                  className="rounded-md bg-sunken px-2 py-1 text-xs font-medium text-muted"
                >
                  {r}
                </li>
              ))}
            </ul>
          </section>

          <section aria-label="Score breakdown">
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
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-sunken">
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
      </motion.div>
    </motion.div>
  );
}
