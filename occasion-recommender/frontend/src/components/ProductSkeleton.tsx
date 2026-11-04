/** Placeholder with the exact card geometry so nothing shifts when results arrive. */
export function ProductSkeleton() {
  return (
    <li
      aria-hidden="true"
      className="flex flex-col overflow-hidden rounded-card border border-line bg-surface shadow-card"
    >
      <div className="skeleton-shimmer aspect-[4/3] w-full" />
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="skeleton-shimmer h-6 w-24 rounded-full" />
        <div className="space-y-2">
          <div className="skeleton-shimmer h-5 w-4/5 rounded-md" />
          <div className="skeleton-shimmer h-4 w-full rounded-md" />
          <div className="skeleton-shimmer h-4 w-2/3 rounded-md" />
        </div>
        <div className="flex gap-1.5">
          <div className="skeleton-shimmer h-6 w-20 rounded-md" />
          <div className="skeleton-shimmer h-6 w-24 rounded-md" />
        </div>
        <div className="mt-auto space-y-3 pt-1">
          <div className="skeleton-shimmer h-1.5 w-full rounded-full" />
          <div className="skeleton-shimmer h-7 w-28 rounded-md" />
        </div>
      </div>
    </li>
  );
}
