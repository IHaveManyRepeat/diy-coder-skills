# placeholders:
// 示例测试（由 diy-test-framework 渲染）——证明 runner 能收集并执行；
// 真实用例由 diy-test-author 生成（消费 test-plan.yaml 的 TC）。
import { expect, test } from 'vitest';

test('脚手架就绪：断言链路可运行', () => {
  const total = [1, 2, 3].reduce((sum, value) => sum + value, 0);
  expect(total).toBe(6);
});
