# placeholders:
// 合并 fixtures（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
// 用法：import { test, expect } from './fixtures'; —— 新夹具一律经 mergeTests 并入，不改 base。
import { test as base, expect } from '@playwright/test';

export const test = base.extend<{ api: { get: (path: string) => Promise<Response> } }>({
  api: async ({ request, baseURL }, use) => {
    await use({
      get: (path: string) => request.get(new URL(path, baseURL).toString()),
    });
  },
});

export { expect };
