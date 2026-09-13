import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server binds 0.0.0.0 because it runs inside a container, and
// proxies /api to the backend service. The proxy is not just convenience:
// it puts a real reverse proxy between the browser and Django locally,
// which is the path where SSE buffering problems show up (see
// docs/planning/initial-thinking.md, "Deployment gotcha").
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: process.env.API_ORIGIN ?? "http://api:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
        // Keep SSE chunks unbuffered once streaming exists.
        configure: (proxy) => {
          proxy.on("proxyRes", (proxyRes) => {
            proxyRes.headers["x-accel-buffering"] = "no";
          });
        },
      },
    },
  },
});
