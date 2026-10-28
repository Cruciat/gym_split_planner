import { defineConfig, devices } from '@playwright/test'

/**
 * Test end-to-end sull'app compilata (processo, § 7; ADR 0012): `npm run build`, poi
 * `npm run e2e`, oppure `make e2e`. Il backend parte su un database nuovo a ogni giro.
 */
const port = Number(process.env.E2E_PORT ?? 8799)

export default defineConfig({
  testDir: 'e2e',
  testMatch: '**/*.e2e.ts',
  fullyParallel: false,
  workers: 1,
  forbidOnly: process.env.CI !== undefined,
  retries: process.env.CI === undefined ? 0 : 1,
  reporter: process.env.CI === undefined ? 'list' : [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: `http://127.0.0.1:${String(port)}`,
    locale: 'it-IT',
    timezoneId: 'Europe/Rome',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1366, height: 900 } },
    },
    { name: 'telefono', use: { ...devices['Pixel 7'] } },
  ],
  webServer: {
    command: 'bash e2e/serve.sh',
    url: `http://127.0.0.1:${String(port)}/api/health`,
    reuseExistingServer: false,
    timeout: 120_000,
    env: { E2E_PORT: String(port) },
  },
})
