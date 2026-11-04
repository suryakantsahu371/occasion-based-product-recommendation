import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import type { Product } from "../types";
import { MatchBar } from "./MatchBar";
import { PriceTag } from "./PriceTag";
import { ProductImage } from "./ProductImage";

interface Props {
  product: Product;
  /** Position by relevance (0 = best); the top 3 get a "Best match" badge. */
  rank: number;
  /** Position in the current (possibly re-sorted) grid; drives the entrance stagger. */
  index: number;
  onOpen: (product: Product) => void;
}

const MAX_REASONS_ON_CARD = 3;

export function ProductCard({ product, rank, index, onOpen }: Props) {
  const delay = Math.min(index, 12) * 0.05;
  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      whileHover={{ y: -4 }}
      transition={{
        default: { duration: 0.3, ease: "easeOut", delay },
        layout: { type: "spring", stiffness: 320, damping: 32 },
      }}
      className="group relative flex flex-col overflow-hidden rounded-card border border-line bg-surface shadow-card transition-shadow duration-200 hover:shadow-card-hover"
    >
      <div className="relative">
        <ProductImage src={product.image} alt={product.title} />
        <div className="pointer-events-none absolute inset-x-3 top-3 flex items-start justify-between gap-2">
          {rank < 3 ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-accent px-2.5 py-1 text-xs font-bold text-accent-ink shadow-card">
              <Sparkles className="h-3 w-3" aria-hidden="true" />
              Best match
            </span>
          ) : (
            <span />
          )}
          {product.discount_pct > 0 && (
            <span className="rounded-full bg-surface px-2.5 py-1 text-xs font-bold text-deal shadow-card">
              −{Math.round(product.discount_pct)}%
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <span className="w-fit rounded-full bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent">
          {product.category}
        </span>
        <div>
          <h3 className="clamp-2 text-base font-bold leading-snug">
            <button
              type="button"
              onClick={() => onOpen(product)}
              className="text-left after:absolute after:inset-0 after:content-[''] focus-visible:ring-offset-0"
              aria-label={`${product.title}: view details`}
            >
              {product.title}
            </button>
          </h3>
          <p className="clamp-2 mt-1 text-sm text-muted">{product.description_snippet}</p>
        </div>

        <ul className="flex flex-wrap gap-1.5" aria-label="Why recommended">
          {product.reasons.slice(0, MAX_REASONS_ON_CARD).map((reason) => (
            <li
              key={reason}
              className="rounded-md bg-sunken px-2 py-1 text-xs font-medium text-muted"
            >
              {reason}
            </li>
          ))}
        </ul>

        <div className="mt-auto space-y-3 pt-1">
          <MatchBar score={product.score} delay={delay} />
          <PriceTag product={product} />
        </div>
      </div>
    </motion.li>
  );
}
