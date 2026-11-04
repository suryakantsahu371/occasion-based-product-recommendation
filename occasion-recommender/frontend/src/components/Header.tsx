import { Gift, Moon, Sun } from "lucide-react";

interface Props {
  dark: boolean;
  onToggleTheme: () => void;
}

/** Brand mark plus the dark-mode toggle. */
export function Header({ dark, onToggleTheme }: Props) {
  return (
    <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
      <a href="/" className="flex items-center gap-2.5" aria-label="Occasio home">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-accent text-accent-ink">
          <Gift className="h-5 w-5" aria-hidden="true" />
        </span>
        <span className="text-xl font-extrabold tracking-heading">Occasio</span>
      </a>
      <button
        type="button"
        onClick={onToggleTheme}
        aria-pressed={dark}
        aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
        className="rounded-full border border-line bg-surface p-2.5 text-ink transition-colors hover:border-accent hover:text-accent"
      >
        {dark ? (
          <Sun className="h-5 w-5" aria-hidden="true" />
        ) : (
          <Moon className="h-5 w-5" aria-hidden="true" />
        )}
      </button>
    </header>
  );
}
