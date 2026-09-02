import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Load VITE_* settings from the repository root.
const ENV_DIR = "..";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ENV_DIR, "VITE_");

  return {
    plugins: [react()],
    envDir: ENV_DIR,

    server: {
      port: 5173,
      // Mirror production's same-origin /api proxy.
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
