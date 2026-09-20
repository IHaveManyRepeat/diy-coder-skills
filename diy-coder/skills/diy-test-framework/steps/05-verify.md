# Step 5 — 冒烟自检与人工处置

**Read (input):** 台账 `checks[]` 当前内容；`detect` 回执的 `stack`（决定自检命令）。
**Write (output):** 台账 `checks[]` 追加项；`deferred[]`（经 `defer-add` 回执 ID）；会话摘要的人工处置清单。

## 1. 冒烟自检（**产物面**，必跑）

对生成物跑三件事，命令取自台账（`checks[]` 的 `command` 与 plan 取值）：

1. **静态检查**：`static_checks` 阻断 层命令（= `LINT_CMD`）；
2. **示例测试**：脚手架自带的示例文件（证明框架能收集并执行）；
3. **CI 配置语法**：平台 CLI 可用时就地校验（`actionlint` / `gitlab-ci-local` / Jenkins 语法插件 / Harness YAML 校验）；工具不在场 → 记 `checks` `result: 失败` + note「工具缺失」，并在摘要列为人工处置项（不阻塞）；
4. **助手脚本**：`bash scripts/ci-local.sh`（或至少 `bash -n` 语法检查三个脚本）——脚本与流水线同命令，脚本能跑通即 CI 大概率能跑通。

- 失败 → 修（改取值重跑 `scaffold`；plan 未覆盖的既有文件走手改通道）→ **重跑**。
- 修不了 → **HALT**：不进 step 6、不写 `status: 已定稿`；把失败命令 + 输出摘要摆给用户（源「本地测试失败即 HALT」保留）。

## 2. 自动化档动作（直接执行）

自生成脚本 `chmod +x`（本技能的三个：`scripts/ci-local.sh` / `scripts/burn-in.sh` / `scripts/test-changed.sh`；Git 只记模式位，Windows 上由 `git update-index --chmod=+x` 或提交时随 umask 落位）；结果记 `checks`。GUI 类（`maestro studio` 等）：交互终端可执行；无头 / CI / 沙箱 → 跳过且不阻塞（不报告路径、不等待）。

## 3. 保留确认档：写时保护钩子（可选步骤，**只入队、不生成文件**）

源技能的写时保护钩子（写入时拦截 `.only` / 硬等待 / 空断言一类反模式）带 1098 行脚本 + 三处注册，属 BMAD 生态资产（**已裁剪，本技能无 hook 模板**）。用户仍想要时，**不改** `.claude/settings.json`、也不手写脚本，只把这件事入队：

```
python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" defer-add --entry '{"skill": "diy-test-framework", "action": "装写时保护钩子：需用户/后续技能提供 hook 脚本，再合并进 .claude/settings.json 的 hooks", "reason": "用户配置", "target": ".claude/settings.json"}' --project-root "{project-root}" --json
```

台账 `deferred` 记回执 `id`（`DA-0xx`）；交互式调用时可当场问用户——**拿到脚本前不写文件**，仍照记 ID，摘要标「`DA-0xx` 已当场执行 + 日期」或「待用户提供脚本」。破坏性 git 操作、项目外写盘同走本档（入队不阻塞）。

## 4. 人工处置项（AI 做不了的事）
配 CI secrets（含失败通知的 `NOTIFY_SECRET`，见 `docs/ci-secrets-checklist.md`）/ 账号登录 / 装本地工具 → 会话摘要逐条列出（含为什么需要）。**秘密只落会话摘要，不写进任何项目文件、不进 `checks` 的 `command`**。

交互式：停下把清单摆给用户（并入 `open_questions`）；无头 / 循环调用：**不阻塞**，经 `defer-add` 入队（`reason: 仅人工可做`，`target` 写平台侧配置位置），台账 `deferred` 记回执 `id`：

```
python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" defer-add --entry '{"skill": "diy-test-framework", "action": "配置 CI 秘密 <名字>（值只由用户填）", "reason": "仅人工可做", "target": "<平台秘密库>"}' --project-root "{project-root}" --json
```

## 播报与下一步

读 `./06-finish.md` 并照做。
