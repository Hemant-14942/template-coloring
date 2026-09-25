import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  preview: {
    port: 4173,
    proxy: { "/api": { target: "http://localhost:8000", changeOrigin: true } },
  },
  server: {
    port: 5173,
    // Dev: forward /api to FastAPI so there are no CORS issues
    proxy: { "/api": { target: "http://localhost:8000", changeOrigin: true } },
  },
});
