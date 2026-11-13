import { defineConfig } from "@playwright/test";

// Runs the real backend with the offline fake model and a throwaway database.
export default defineConfig({
  testDir: "e2e",
  timeout: 30_000,
  use: { baseURL: "http://localhost:5174", trace: "retain-on-failure" },
  webServer: [
    {
      command: "rm -f ../backend/data/e2e.db && cd ../backend && LLM_PROVIDER=fake LLM_MODEL=fake-local MISSION_DB=data/e2e.db uv run uvicorn app.main:create_app --factory --port 8011",
      url: "http://localhost:8011/api/health",
      reuseExistingServer: false,
    },
    {
      command: "API_URL=http://localhost:8011 npx vite --port 5174 --strictPort",
      url: "http://localhost:5174",
      reuseExistingServer: false,
    },
  ],
});
