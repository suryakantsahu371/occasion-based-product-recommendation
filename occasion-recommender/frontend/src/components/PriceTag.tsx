import { formatPrice } from "../lib/format";
import type { Product } from "../types";

/** Final price with the original struck through when discounted. */
export function PriceTag({ product, large = false }: { product: Product; large?: boolean }) {
  const discounted =
    product.discount_pct > 0 && product.price != null && product.final_price != null;
  return (
    <p className="flex items-baseline gap-2">
      <span
        className={`font-extrabold tracking-heading text-ink ${large ? "text-2xl" : "text-lg"}`}
      >
        {formatPrice(product.final_price)}
      </span>
      {discounted && (
        <>
          <s className="text-sm text-muted">
            <span className="sr-only">Original price </span>
            {formatPrice(product.price)}
          </s>
          <span className="rounded-md bg-deal-soft px-1.5 py-0.5 text-xs font-bold text-deal">
            {Math.round(product.discount_pct)}% off
          </span>
        </>
      )}
    </p>
  );
}
