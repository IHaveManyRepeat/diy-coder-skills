# placeholders: TEST_DIR
# 测试支撑目录说明（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）

前端 / 全栈面的测试支撑物统一收在 `{{TEST_DIR}}/support/` 下（源 framework checklist 的
「support/ 是关键模式」）：

| 目录 | 放什么 |
| --- | --- |
| `{{TEST_DIR}}/support/fixtures/` | 夹具与合并入口（`mergeTests` 的扩展点）；数据工厂归 `diy-test-author` |
| `{{TEST_DIR}}/support/helpers/` | 与框架无关的小工具（等待、取数、断言包装） |
| `{{TEST_DIR}}/support/page-objects/` | 页面对象（**可选**：只在跨用例复用确有益时引入） |

- 目录暂空时靠占位文件 `.gitkeep` 保住版本库里的存在；有内容后删占位文件。
- 本目录的测试代码由 `diy-test-author` 生成（消费 `{output_dir}/test-plan.yaml` 的 TC）。
