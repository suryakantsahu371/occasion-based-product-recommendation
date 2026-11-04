import { useCallback, useEffect, useState } from "react";

const KEY = "occasio-theme";

function systemPrefersDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/** Dark-mode state: respects the system preference until the user toggles, then remembers it. */
export function useTheme() {
  const [dark, setDark] = useState<boolean>(() =>
    document.documentElement.classList.contains("dark"),
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  useEffect(() => {
    // Follow live OS changes only while the user has not picked a theme explicitly.
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      try {
        if (!localStorage.getItem(KEY)) setDark(systemPrefersDark());
      } catch {
        /* storage unavailable: ignore */
      }
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  const toggle = useCallback(() => {
    setDark((prev) => {
      try {
        localStorage.setItem(KEY, prev ? "light" : "dark");
      } catch {
        /* storage unavailable: theme still applies for this session */
      }
      return !prev;
    });
  }, []);

  return { dark, toggle };
}
