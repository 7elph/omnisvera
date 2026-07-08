import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/health": "http://127.0.0.1:8787",
      "/index": "http://127.0.0.1:8787",
      "/notes": "http://127.0.0.1:8787",
      "/search": "http://127.0.0.1:8787",
      "/chat": "http://127.0.0.1:8787",
    },
  },
});
