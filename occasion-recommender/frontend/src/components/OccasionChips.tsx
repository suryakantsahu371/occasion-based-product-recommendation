import { motion } from "framer-motion";
import { QUICK_PICKS } from "../lib/icons";

interface Props {
  active: string;
  onPick: (label: string) => void;
}

/** Quick-pick occasion chips with a short entrance stagger. */
export function OccasionChips({ active, onPick }: Props) {
  return (
    <ul aria-label="Popular occasions" className="mt-5 flex flex-wrap justify-center gap-2">
      {QUICK_PICKS.map(({ label, icon: Icon }, i) => {
        const selected = active.trim().toLowerCase() === label.toLowerCase();
        return (
          <motion.li
            key={label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 + i * 0.05, duration: 0.25, ease: "easeOut" }}
          >
            <motion.button
              type="button"
              whileTap={{ scale: 0.97 }}
              aria-pressed={selected}
              onClick={() => onPick(label)}
              className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${
                selected
                  ? "border-accent bg-accent text-accent-ink"
                  : "border-line bg-surface text-ink hover:border-accent hover:text-accent"
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {label}
            </motion.button>
          </motion.li>
        );
      })}
    </ul>
  );
}
