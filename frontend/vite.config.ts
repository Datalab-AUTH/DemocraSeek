import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Configuration lives in the repository root .env, not in frontend/. Without
// envDir, Vite silently sees no VITE_* variables, the API base URL falls back
// to empty, and every /api request is answered by this dev server's SPA
// fallback with index.html - which surfaces as a JSON parse error in the browser.
const ENV_DIR = "..";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ENV_DIR, "VITE_");

  return {
    plugins: [react()],
    envDir: ENV_DIR,

    server: {
      port: 5173,
      // Same-origin /api in development, mirroring what nginx does in
      // production. Keeps CORS out of the picture and lets VITE_API_BASE_URL
      // stay empty in both environments.
      proxy: {
        "/api": {
          target: env.VITE_DEV_API_TARGET || "http://127.0.0.1:8000",
          changeOrigin: true,
        },
      },
    },
    build: { outDir: "dist", sourcemap: false },
  };
});
