import { motion } from "framer-motion";
import { RefreshCw, TriangleAlert } from "lucide-react";

interface Props {
  message: string;
  onRetry: () => void;
}

export function ErrorState({ message, onRetry }: Props) {
  return (
    <motion.div
      role="alert"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="mx-auto flex max-w-md flex-col items-center rounded-card border border-line bg-surface p-8 text-center shadow-card"
    >
      <span className="rounded-full bg-sunken p-3 text-danger">
        <TriangleAlert className="h-6 w-6" aria-hidden="true" />
      </span>
      <h2 className="mt-4 text-lg font-extrabold">We couldn&apos;t load your recommendations</h2>
      <p className="mt-1 text-sm text-muted">{message}</p>
      <motion.button
        type="button"
        whileTap={{ scale: 0.97 }}
        onClick={onRetry}
        className="mt-5 inline-flex items-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-sm font-bold text-accent-ink hover:opacity-90"
      >
        <RefreshCw className="h-4 w-4" aria-hidden="true" />
        Retry
      </motion.button>
    </motion.div>
  );
}
