import { Gift } from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface Props {
  src: string | null;
  alt: string;
  className?: string;
  eager?: boolean;
}

/** Lazy image with a blurred shimmer placeholder and a graceful fallback if the URL fails. */
export function ProductImage({ src, alt, className = "", eager = false }: Props) {
  const [status, setStatus] = useState<"loading" | "loaded" | "error">(src ? "loading" : "error");
  const ref = useRef<HTMLImageElement>(null);

  useEffect(() => {
    setStatus(src ? "loading" : "error");
  }, [src]);

  useEffect(() => {
    // Cached images can finish loading before React attaches onLoad.
    if (ref.current?.complete && ref.current.naturalWidth > 0) setStatus("loaded");
  }, [src]);

  return (
    <div className={`relative aspect-[4/3] w-full overflow-hidden bg-sunken ${className}`}>
      {status === "loading" && (
        <div className="skeleton-shimmer absolute inset-0 blur-sm" aria-hidden="true" />
      )}
      {status === "error" ? (
        <div
          role="img"
          aria-label={`${alt} (image unavailable)`}
          className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-accent-soft to-sunken text-accent/60"
        >
          <Gift className="h-10 w-10" aria-hidden="true" />
        </div>
      ) : (
        <img
          ref={ref}
          src={src ?? undefined}
          alt={alt}
          width={640}
          height={480}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          onLoad={() => setStatus("loaded")}
          onError={() => setStatus("error")}
          className={`h-full w-full object-cover transition-[opacity,transform] duration-300 ease-out group-hover:scale-105 ${
            status === "loaded" ? "opacity-100" : "opacity-0"
          }`}
        />
      )}
    </div>
  );
}
