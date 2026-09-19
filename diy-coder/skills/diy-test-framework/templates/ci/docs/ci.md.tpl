# placeholders: CI_PLATFORM CI_FILE FRAMEWORK_NAME TEST_DIR INSTALL_CMD LINT_CMD TEST_CMD REPORT_PATH CACHE_PATH CACHE_KEY P0_GATE P1_GATE NOTIFY_SECRET CI_PLATFORM_SECRETS_UI
# CI 流水线说明（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）

平台：**{{CI_PLATFORM}}**；流水线文件：`{{CI_FILE}}`；测试框架：**{{FRAMEWORK_NAME}}**（测试目录 `{{TEST_DIR}}/`）。
选型与生成清单见 `{output_dir}/test-framework.yaml` 的 `setups[]`（`ci` 段是阈值与对齐记录的**事实源**）。

## 阶段

| 阶段 | 干什么 | 关键约定 |
| --- | --- | --- |
| lint | 静态检查 | 命令 = test-plan 的 blocking 层命令（`{{LINT_CMD}}`）；改 CI 时必须与它保持一致 |
| test | 并行四路分片跑测试（`{{TEST_CMD}}`） | `fail-fast: false`：一片红不影响其余片跑完 |
| burn-in | 连跑 10 轮抓抖动 | 只跑 PR / 定时；后端面按需保留 |
| report | 汇总结果与产物 | 质量门：P0 {{P0_GATE}} / P1 {{P1_GATE}}（双 100%） |

## 本地先跑一遍

```sh
bash scripts/ci-local.sh       # 装依赖 + lint + 跑测试，与 CI 同一条命令、同一个 CI=true
bash scripts/burn-in.sh        # 抖动检测（连跑 N 轮，默认 10）
bash scripts/test-changed.sh   # 只跑改动相关的测试文件
```

分支没推送时 `test-changed.sh` 需要 `origin/main` 在场（先 `git fetch`）。
三个脚本内部就是流水线那三条命令：`{{INSTALL_CMD}}` / `{{LINT_CMD}}` / `{{TEST_CMD}}`——不要各写一套。

## 缓存

- 依赖缓存路径：`{{CACHE_PATH}}`；缓存键：`{{CACHE_KEY}}`（**键含锁文件哈希**：锁文件变即换键）。
- 浏览器缓存（前端 / 全栈面）：路径与键由同一 plan 注入，浏览器版本随锁文件走。
- Jenkins 无声明式缓存原语：依赖缓存由 agent 工作区保留承担，换 agent 或清理工作区后首轮为冷缓存。
- 缓存失配只会变慢，不会让流水线出错——清缓存是排查「本地能跑 CI 不能跑」的第一步。

## 产物

- 失败才上传（`if: failure()` / `when: on_failure`），保留 30 天；路径 = `test-results/` + `{{REPORT_PATH}}`。
- 报告阶段聚合各分片产物：`report` 作业把全部产物取回一个目录，便于一次下载。
- 产物里不得出现秘密：CI 输出的日志与 trace 会连同产物一起被下载。

## 失败通知

- 通知走 secret 变量 **{{NOTIFY_SECRET}}**（配置入口：{{CI_PLATFORM_SECRETS_UI}}）。
- 未配置该变量时通知步骤**跳过**（打印一行提示），流水线不会因此变红。
- 通知正文带运行链接；产物链接用运行页里的 Artifacts 段（见 `docs/ci-secrets-checklist.md`）。

## 故障排查

| 现象 | 先看 |
| --- | --- |
| 本地过、CI 红 | `bash scripts/ci-local.sh` 复现；多半是环境变量或浏览器版本差异 |
| 缓存没生效 | 键是否含锁文件哈希；是否换了 agent / 清理了工作区 |
| 只有某些分片红 | 分片参数是否被框架接受；片间是否有共享状态 |
| lint 红而本地不红 | CI 跑的是 test-plan 的 blocking 命令，不是编辑器插件 |

## 改 CI 的正确姿势

1. 改**技能内模板**（`diy-test-framework/templates/ci/...`），不要手改生成物——手改会在下次重入被
   `FILE_CONFLICT` 顶住，且 `check` 会现场重扫（注入防护、blocking 命令覆盖、阈值字面量三样都要过）。
2. 既有流水线（本技能不覆盖，记 `action: update`）由你自己维护：`run:` / `script:` / `command:` 里
   一律不得直接插值 `${{ inputs.* }}` / `${{ github.event.* }}` / `${{ parameters.* }}` / `<+input>`
   —— 必须经 `env:` / `variables:` / `envVariables` 中转后以 `"$ENV_VAR"` 引用。
3. 阈值改了要同步台账 `ci.gates`：`check` 会在流水线文件里找该字面量（缺 → `CI_MISALIGNED`）。
