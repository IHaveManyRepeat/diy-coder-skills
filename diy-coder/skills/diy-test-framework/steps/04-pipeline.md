# Step 4 — CI 流水线（模板渲染 + 三方对齐台账）

**Read (input):** step 2 的取值表；`detect` 回执的 `existing.ci`；`static_checks[]` 的 `order` 与 `gate`（引用用，不抄内容）；技能内 `templates/ci/` 的路径清单。
**Write (output):** `{output_dir}/scaffold-plan.json`（覆写为 CI 面）+ CI 文件 + 台账 `ci` 段 / `files[]` / `checks[]`。

## 1. 平台 → 路径 → 模板

| platform | 输出路径（相对 project-root，正斜杠） | 模板 |
| --- | --- | --- |
| `github-actions` | `.github/workflows/test.yml` | `ci/github-actions/<class>.yml.tpl` |
| `gitlab-ci` | `.gitlab-ci.yml` | `ci/gitlab-ci/<class>.yml.tpl` |
| `jenkins` | `Jenkinsfile` | `ci/jenkins/<class>.groovy.tpl` |
| `azure-devops` | `azure-pipelines.yml` | `ci/azure-devops/<class>.yml.tpl` |
| `harness` | `.harness/pipeline.yaml` | `ci/harness/<class>.yaml.tpl` |

`<class>` = `browser`（前端 / 全栈，含浏览器安装步骤）或 `backend`（无浏览器步骤）。**模板只有这五平台**：`circle-ci` 等无模板 → 用户改用五平台之一，否则 `platform: none`。`platform: none` → 跳过本步与对齐判定（台账照记，check 给 warning）。

## 2. 写 plan 并调用引擎（一次）

`part: "CI"`、`kind: "CI"`，`P0_GATE` / `P1_GATE` 固定 `100%`；调用形态同 step 3。**同一次调用里带上文档面**：`docs/ci.md`（`ci/docs/ci.md.tpl`）与 `docs/ci-secrets-checklist.md`（`ci/docs/ci-secrets-checklist.md.tpl`），`kind: 文档`。随后执行 `pending_commands` 并记 `checks[]`。

## 3. 台账 `ci` 段（引用式）

- `platform` / `file` / `stages`（`静态检查` / `测试` / `契约` / `预热` / `报告`）。
- `gates: {p0: '100%', p1: '100%'}`——**事实源在台账**，经 plan 注入 CI 文件；`check` 校验 CI 文件文本含该字面量（缺 → `CI_MISALIGNED`）。
- `static_check_alignment`：**按 `order` 引用** 阻断 层条目 + 该命令当前是否出现在 CI 文件（`in_ci`）。阻断 层必录、记录不阻断 层可选；`check` 会现场重算，台账与重算不符即违例。
- **注入防护段**（模板内的安全注释与 DATA-not-COMMAND 纪律）随模板逐字保留——渲染不得删改，也不得把 `${{ inputs.* }}` 一类不可信上下文直接引到 `run:`（扩展本流水线时照该段纪律办）。
- 既有 CI 文件（用户选 update）由本步 LLM 手改并记 `action: 更新`；引擎只写新文件，冲突即回滚 + 整条拒绝。

## 4. 命令与阶段提示
- `TEST_CMD` 取值可带分片参数（模板已注入 SHARD / `$CI_NODE_INDEX` / `$(SHARD_INDEX)` / `<+strategy.iteration>` 之一），如 `npx playwright test --shard=$SHARD/4`；分片语义由框架决定，模板不替框架发明参数。
- 预热 目标 = UI flakiness：backend-only 项目按需保留或移除该阶段（移除后 `stages` 同步）。

## 5. 缓存 / 产物 / 通知（模板已内置，取值见 step 2 §3.1）

- **缓存**：依赖一份，浏览器面再加浏览器一份；GHA / Azure 走 `actions/cache@v4` / `Cache@2`（`restore-keys` / `restoreKeys` 给回退），GitLab 走 `cache:key.files`，Harness 走 `stage.spec.caching`；Jenkins 无声明式原语——`CACHE_PATH` / `CACHE_KEY` 落注释（约定口径），依赖缓存由 agent 工作区保留承担。
- **产物**：失败才上传（`if: failure()` / `when: on_failure` / `condition: failed()`），路径 = `test-results/` + `REPORT_PATH`，保留 30 天；Jenkins 由 `post.always` 的 `junit` + `archiveArtifacts` 承担发布与聚合；GHA / Azure 的报告阶段把各分片产物**取回一个目录**再汇总（`download-artifact` / `download: current`），GitLab 由 `needs` 自动取回。
- **失败通知**：模板内置一步（GHA / GitLab / Azure / Jenkins 失败才跑，Harness 用 `when: pipelineStatus: Failure` 的收尾 stage），秘密名 = `NOTIFY_SECRET`；**未配置时打印一行提示并跳过**，不把流水线拖红。
- **秘密只入会话摘要 + `defer-add`**：配 secrets 属保留确认档（AI 做不了的事）——交互式停下问、无头经 `defer-add`（`reason: 仅人工可做`）入队，档位与 step 3 同（见 05 步 §4）；**本技能不代配、不执行**，`docs/ci-secrets-checklist.md` 是给用户的清单，摘要记「已配 / 待配」。
- **手改面同样被扫**：`check` 会对 CI 文件的 `run:` / `script:` / `command:` / `sh` 块做注入扫描（块内直接插值 `${{ inputs.* }}` / `${{ github.event.* }}` / `${{ github.head_ref }}` / `${{ parameters.* }}` / `<+input>` → `UNSAFE_INJECTION`）；注释里写示例不算违规。

## 播报与下一步

读 `./05-verify.md` 并照做。
