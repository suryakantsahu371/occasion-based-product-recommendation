import { AnimatePresence, motion } from "framer-motion";
import { Search, X } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { iconFor } from "../lib/icons";
import { useDebounced } from "../lib/useDebounced";
import type { Occasion } from "../types";

interface Props {
  occasions: Occasion[];
  value: string;
  onChange: (value: string) => void;
  onSubmit: (query: string) => void;
  loading: boolean;
}

const MAX_SUGGESTIONS = 6;

/** Hero search: labelled combobox with autocomplete, "/" focus shortcut and Enter-to-search. */
export function SearchBar({ occasions, value, onChange, onSubmit, loading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [focused, setFocused] = useState(false);
  const uid = useId();
  const listId = `${uid}-list`;
  const debounced = useDebounced(value, 200);

  const suggestions = useMemo(() => {
    const q = debounced.trim().toLowerCase();
    const matches = q
      ? occasions.filter(
          (o) => o.label.toLowerCase().includes(q) || o.key.replace(/_/g, " ").includes(q),
        )
      : occasions;
    return matches.slice(0, MAX_SUGGESTIONS);
  }, [occasions, debounced]);

  // Press "/" anywhere (outside a text field) to jump to the search box.
  useEffect(() => {
    const onKey = (e: globalThis.KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const typing =
        target &&
        (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);
      if (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const choose = (label: string) => {
    onChange(label);
    setOpen(false);
    setActive(-1);
    onSubmit(label);
  };

  const submit = () => {
    const q = value.trim();
    if (!q) return;
    setOpen(false);
    onSubmit(q);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    const n = suggestions.length;
    if (e.key === "ArrowDown" && n) {
      e.preventDefault();
      setOpen(true);
      setActive((i) => (i + 1) % n);
    } else if (e.key === "ArrowUp" && n) {
      e.preventDefault();
      setOpen(true);
      setActive((i) => (i <= 0 ? n - 1 : i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (open && active >= 0 && suggestions[active]) choose(suggestions[active].label);
      else submit();
    } else if (e.key === "Escape") {
      if (open) setOpen(false);
      else if (value) onChange("");
    }
  };

  const showList = open && suggestions.length > 0;

  return (
    <form
      role="search"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      className="mx-auto w-full max-w-2xl"
    >
      <label
        htmlFor={`${uid}-input`}
        className="mb-2 block text-center text-sm font-semibold text-muted"
      >
        What&apos;s the occasion?
      </label>
      <div className="relative">
        <motion.div
          animate={{ scale: focused ? 1.02 : 1 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className={`flex items-center gap-2 rounded-2xl border bg-surface p-2 pl-4 shadow-card transition-[border-color,box-shadow] duration-200 ${
            focused ? "border-accent shadow-glow" : "border-line"
          }`}
        >
          <Search className="h-5 w-5 shrink-0 text-muted" aria-hidden="true" />
          <input
            id={`${uid}-input`}
            ref={inputRef}
            type="text"
            role="combobox"
            aria-expanded={showList}
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={showList && active >= 0 ? `${uid}-opt-${active}` : undefined}
            autoComplete="off"
            maxLength={100}
            value={value}
            placeholder="Diwali, shaadi, office party, baby shower…"
            onChange={(e) => {
              onChange(e.target.value);
              setOpen(true);
              setActive(-1);
            }}
            onFocus={() => {
              setFocused(true);
              setOpen(true);
            }}
            onBlur={() => {
              setFocused(false);
              setOpen(false);
            }}
            onKeyDown={onKeyDown}
            className="min-w-0 flex-1 bg-transparent py-2 text-base text-ink placeholder:text-muted/70 focus-visible:ring-0 focus-visible:ring-offset-0"
          />
          {value ? (
            <button
              type="button"
              aria-label="Clear search"
              onClick={() => {
                onChange("");
                inputRef.current?.focus();
              }}
              className="rounded-full p-1.5 text-muted transition-colors hover:bg-sunken hover:text-ink"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          ) : (
            <kbd
              aria-hidden="true"
              className="hidden rounded-md border border-line bg-sunken px-2 py-0.5 text-xs font-semibold text-muted sm:block"
              title='Press "/" to focus'
            >
              /
            </kbd>
          )}
          <motion.button
            type="submit"
            whileTap={{ scale: 0.97 }}
            disabled={!value.trim() || loading}
            className="rounded-xl bg-accent px-5 py-2.5 text-sm font-bold text-accent-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Searching…" : "Find gifts"}
          </motion.button>
        </motion.div>

        <AnimatePresence>
          {showList && (
            <motion.ul
              id={listId}
              role="listbox"
              aria-label="Occasion suggestions"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="absolute left-0 right-0 top-full z-20 mt-2 overflow-hidden rounded-2xl border border-line bg-surface p-1.5 shadow-float"
            >
              {suggestions.map((o, i) => {
                const Icon = iconFor(o.icon);
                return (
                  <li
                    key={o.key}
                    id={`${uid}-opt-${i}`}
                    role="option"
                    aria-selected={i === active}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => choose(o.label)}
                    onMouseEnter={() => setActive(i)}
                    className={`flex cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium ${
                      i === active ? "bg-accent-soft text-accent" : "text-ink"
                    }`}
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                    {o.label}
                  </li>
                );
              })}
            </motion.ul>
          )}
        </AnimatePresence>
      </div>
    </form>
  );
}
