// placeholders: TEST_DIR BASE_URL
// Cypress 配置（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    specPattern: '{{TEST_DIR}}/**/*.cy.ts',
    supportFile: '{{TEST_DIR}}/support/e2e.ts',
    baseUrl: process.env.BASE_URL || '{{BASE_URL}}',
    defaultCommandTimeout: 15_000,
    pageLoadTimeout: 30_000,
    retries: { runMode: 2, openMode: 0 },
    video: true,
    screenshotOnRunFailure: true,
    reporter: 'junit',
    reporterOptions: { mochaFile: 'test-results/junit-[hash].xml' },
  },
});
