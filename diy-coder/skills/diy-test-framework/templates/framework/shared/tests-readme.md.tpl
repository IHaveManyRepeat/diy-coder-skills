# placeholders: FRAMEWORK_NAME TEST_DIR INSTALL_CMD LINT_CMD TEST_CMD
# 测试目录说明（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）

测试框架：**{{FRAMEWORK_NAME}}**；测试目录：`{{TEST_DIR}}/`。选型与生成清单见 `{output_dir}/test-framework.yaml` 的 `setups[]`。

## 怎么跑

| 目的 | 命令 |
| --- | --- |
| 装依赖 | `{{INSTALL_CMD}}` |
| 静态检查（与 CI lint 阶段同一条命令） | `{{LINT_CMD}}` |
| 跑测试 | `{{TEST_CMD}}` |

本地跑的就是 CI 跑的——CI 的 lint / test 阶段直接调用上表命令，不要在流水线里另写一套。

## 约定

- 失败产物（trace / screenshot / 报告）默认**只在失败时**保留，命名与保留天数见 CI 配置。
- 测试文件命名与目录归属按框架默认约定；用例锚注释（`TC: TC-x.y.z`）由 diy-test-author 生成时写入。
- 真实用例由 `diy-test-author` 生成（消费 `{output_dir}/test-plan.yaml` 的 TC）；本目录内的示例文件只用于证明框架就绪。
