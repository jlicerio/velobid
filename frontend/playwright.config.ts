import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for VeloBid UI smoke tests.
 * Target: deployed Docker app at VELOBID_URL (default http://192.168.1.237:8000).
 *
 * Usage:
 *   VELOBID_URL=http://localhost:8000 npx playwright test
 *   VELOBID_URL=http://192.168.1.237:8000 npx playwright test --project=chromium
 *   npm run test:smoke
 */
const BASE_URL = process.env.VELOBID_URL || 'http://192.168.1.237:8000';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : 1,
  reporter: [['html', { open: 'never' }], ['list']],
  timeout: 30000,
  expect: { timeout: 10000 },

  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],

  webServer: [],
});
