import { defineConfig } from "@playwright/test";

const BACKEND_PORT = 10907;
const FRONTEND_PORT = 10906;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    headless: true,
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `uv run uvicorn onenote_mcp.server:http_app --host 127.0.0.1 --port ${BACKEND_PORT} --log-level warning`,
      port: BACKEND_PORT,
      cwd: "../",
      timeout: 30000,
      reuseExistingServer: true,
    },
    {
      command: "npm run dev -- --port 10906 --strictPort",
      port: FRONTEND_PORT,
      cwd: ".",
      timeout: 30000,
      reuseExistingServer: true,
    },
  ],
});
