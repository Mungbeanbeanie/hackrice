import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // Root-relative, so no node:path and no @types/node just for one alias.
    // Vite resolves a leading "/" against the project root.
    alias: { "@": "/src" },
  },
  server: {
    // Mirrors the Caddy routing in production, so /api works the same in dev.
    proxy: { "/api": "http://localhost:8000" },
  },
  test: {
    environment: "jsdom",
  },
});
