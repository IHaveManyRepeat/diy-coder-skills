// placeholders: TEST_DIR BASE_URL
// Playwright 配置（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '{{TEST_DIR}}',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [['html', { open: 'never' }], ['junit', { outputFile: 'test-results/junit.xml' }], ['list']],
  use: {
    baseURL: process.env.BASE_URL || '{{BASE_URL}}',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    trace: 'retain-on-failure-and-retries',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
