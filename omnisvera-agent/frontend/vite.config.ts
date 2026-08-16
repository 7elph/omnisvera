import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Public currently contains historical 600 MB Godot exports. They are
  // deployment archives, not frontend assets, so do not copy them into Vite.
  publicDir: false,
  // The Godot Web export lives beside the Vite bundle in dist/nimalis.
  // Keep it when rebuilding the Companion frontend.
  build: {
    emptyOutDir: false,
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/health": "http://127.0.0.1:8787",
      "/index": "http://127.0.0.1:8787",
      "/notes": "http://127.0.0.1:8787",
      "/search": "http://127.0.0.1:8787",
      "/chat": "http://127.0.0.1:8787",
      "/gm": "http://127.0.0.1:8787",
      "/player": "http://127.0.0.1:8787",
      "/characters": "http://127.0.0.1:8787",
      "/rolls": "http://127.0.0.1:8787",
      "/roll-requests": "http://127.0.0.1:8787",
      "/scenes": "http://127.0.0.1:8787",
      "/contracts": "http://127.0.0.1:8787",
      "/npcs": "http://127.0.0.1:8787",
      "/reputation": "http://127.0.0.1:8787",
      "/media": "http://127.0.0.1:8787",
    },
  },
});
