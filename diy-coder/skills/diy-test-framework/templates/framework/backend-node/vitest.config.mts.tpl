// placeholders: TEST_DIR
// Vitest 配置（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['{{TEST_DIR}}/**/*.{test,spec}.?(c|m)[jt]s?(x)'],
    environment: 'node',
    globals: false,
    reporters: ['default'],
    coverage: { provider: 'v8', reporter: ['text', 'lcov'], reportsDirectory: 'test-results/coverage' },
    retry: process.env.CI ? 2 : 0,
  },
});
