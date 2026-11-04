/** Design tokens. Colours are CSS variables (see src/index.css) so light/dark share one palette. */
const token = (name) => `rgb(var(--c-${name}) / <alpha-value>)`;

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        canvas: token("canvas"),
        surface: token("surface"),
        sunken: token("sunken"),
        line: token("line"),
        ink: token("ink"),
        muted: token("muted"),
        accent: token("accent"),
        "accent-ink": token("accent-ink"),
        "accent-soft": token("accent-soft"),
        deal: token("deal"),
        "deal-soft": token("deal-soft"),
        danger: token("danger"),
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
      // 8px grid: spacing utilities (p-2 = 8px, p-4 = 16px ...) come from Tailwind's default 4px unit.
      borderRadius: { card: "16px", control: "12px" },
      boxShadow: {
        card: "0 1px 2px rgb(var(--shadow) / 0.06), 0 4px 12px rgb(var(--shadow) / 0.05)",
        "card-hover": "0 2px 4px rgb(var(--shadow) / 0.08), 0 16px 32px rgb(var(--shadow) / 0.14)",
        glow: "0 0 0 4px rgb(var(--c-accent) / 0.18)",
        float: "0 24px 64px rgb(var(--shadow) / 0.28)",
      },
      letterSpacing: { heading: "-0.025em" },
      keyframes: {
        shimmer: { "100%": { transform: "translateX(100%)" } },
        float: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-8px)" } },
      },
      animation: { shimmer: "shimmer 1.6s infinite", float: "float 4s ease-in-out infinite" },
    },
  },
  plugins: [],
};
