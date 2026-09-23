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
    port: 5174,
    strictPort: true,
    // Vite refuses requests whose Host it does not recognise, which blocks
    // an ngrok tunnel with an error that explains nothing. This allows
    // ngrok's domains, and PUBLIC_HOST for any other one-off tunnel.
    //
    // Note what this opens: the dev server becomes reachable by anyone with
    // the link, with no authentication, and every ingested document is
    // readable. Share the link knowing that, and close the tunnel after.
    allowedHosts: [
      ".ngrok-free.app",
      ".ngrok-free.dev",
      ".ngrok.app",
      ".ngrok.io",
      ...(process.env.PUBLIC_HOST ? [process.env.PUBLIC_HOST] : []),
    ],
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
