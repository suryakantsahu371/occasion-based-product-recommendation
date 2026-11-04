import { motion } from "framer-motion";
import { QUICK_PICKS } from "../lib/icons";

interface Props {
  query: string;
  onPick: (label: string) => void;
}

/** Friendly "nothing matched" state with an original inline illustration and clickable suggestions. */
export function EmptyState({ query, onPick }: Props) {
  return (
    <motion.div
      role="status"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="mx-auto flex max-w-md flex-col items-center py-12 text-center"
    >
      <svg viewBox="0 0 200 160" className="h-40 w-52 animate-float" aria-hidden="true">
        <ellipse cx="100" cy="146" rx="62" ry="8" className="fill-sunken" />
        <path
          d="M52 78h96v58a8 8 0 0 1-8 8H60a8 8 0 0 1-8-8V78z"
          className="fill-accent-soft stroke-accent"
          strokeWidth="3"
        />
        <path
          d="M44 62a6 6 0 0 1 6-6h100a6 6 0 0 1 6 6v16H44V62z"
          className="fill-surface stroke-accent"
          strokeWidth="3"
        />
        <path d="M100 56v88" className="stroke-accent" strokeWidth="3" />
        <path
          d="M100 56c-8-22-34-24-34-8s22 16 34 8zm0 0c8-22 34-24 34-8s-22 16-34 8z"
          className="fill-none stroke-accent"
          strokeWidth="3"
          strokeLinejoin="round"
        />
        <path
          d="M88 104q12 10 24 0"
          className="fill-none stroke-accent"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <circle cx="86" cy="94" r="3" className="fill-accent" />
        <circle cx="114" cy="94" r="3" className="fill-accent" />
        <path d="M162 28l3 8 8 3-8 3-3 8-3-8-8-3 8-3z" className="fill-accent" />
        <path d="M34 36l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" className="fill-accent/60" />
      </svg>
      <h2 className="mt-4 text-xl font-extrabold">No gifts found for “{query}”</h2>
      <p className="mt-2 text-sm text-muted">
        We couldn&apos;t match that to anything in the catalog. Check the spelling, try a broader
        occasion, or pick one of these.
      </p>
      <ul className="mt-5 flex flex-wrap justify-center gap-2" aria-label="Suggested occasions">
        {QUICK_PICKS.map(({ label, icon: Icon }) => (
          <li key={label}>
            <motion.button
              type="button"
              whileTap={{ scale: 0.97 }}
              onClick={() => onPick(label)}
              className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-2 text-sm font-semibold transition-colors hover:border-accent hover:text-accent"
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {label}
            </motion.button>
          </li>
        ))}
      </ul>
    </motion.div>
  );
}
