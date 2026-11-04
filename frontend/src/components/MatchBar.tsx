import { motion } from "framer-motion";
import { matchPercent } from "../lib/format";

/** Slim relevance bar that animates from 0 to the product's match percentage. */
export function MatchBar({ score, delay = 0 }: { score: number; delay?: number }) {
  const pct = matchPercent(score);
  return (
    <div className="flex items-center gap-2" title="How well this product matches the occasion">
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        aria-label="Match score"
        className="h-1.5 flex-1 overflow-hidden rounded-full bg-sunken"
      >
        <motion.div
          className="h-full w-full origin-left rounded-full bg-accent"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: pct / 100 }}
          transition={{ delay: delay + 0.15, duration: 0.5, ease: "easeOut" }}
        />
      </div>
      <span className="whitespace-nowrap text-right text-xs font-semibold tabular-nums text-muted">
        {pct}% match
      </span>
    </div>
  );
}
