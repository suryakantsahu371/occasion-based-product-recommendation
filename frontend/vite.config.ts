import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// In dev, proxy API calls to the FastAPI backend so the browser sees a single origin.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backend = env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
  return {
    plugins: [react()],
    server: { port: 5173, proxy: { "/api": backend, "/health": backend } },
  };
});
