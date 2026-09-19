# Step 6 — 定稿、终门与收尾

**Read (input):** 台账全文（按记录 `id:` 定位本记录，只为补 `status` 与 `open_questions`）；`check` 回执。
**Write (output):** `{output_dir}/test-framework.yaml` 定稿记录 + `revisions`（改既有记录时）；会话摘要。

## 1. 落盘定稿
本记录置 `status: 已定稿`（gate 检的就是它）；新增记录追加进 `setups[]`，改既有记录时补一条 `revisions`（`{date, change, reason}`）。未裁定的未决项落 `open_questions`，**零 `[假设]`**。

## 2. 终门（机械判定）

```
python "{project-root}/.claude/skills/diy-test-framework/scripts/test_framework.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

exit 0 是唯一放行；修掉每一条报告的违规并重跑（`FILE_CONFLICT` / `CI_MISALIGNED` 类先按回执 `where` 定位到具体 order / path）；JSON 回执的 `counts` 就是收尾证据。

## 3. 渲染 + 摘要 + 路由
渲染（静默旁路，只给命令）：
`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）

摘要（收尾证据，写给用户）：
- 选型：框架 / 平台 / profile / 理由；
- 生成文件清单（`files[]`，新建 / 更新 分列）与 `skipped`（幂等重入）说明；
- 执行过的命令（`checks[]`，失败 项带 note）+ 人工处置项；
- CI 对齐结论：阻断 条目覆盖、阈值注入、`platform: none` 或 `test-plan` 缺席导致的跳过（含 warning 原文）；
- 基建面一行：缓存（路径 / 键口径）、产物（路径 + 保留 30 天）、失败通知（`NOTIFY_SECRET` 已配 / 待配）、脚手架注入扫描结论（`UNSAFE_INJECTION` 零违规）；
- 未决项（`open_questions`）与 `deferred`（`DA-0xx`）清单；
- **路由**：`→ diy-test-author`（消费 `test-plan.yaml` 的 TC 生成测试代码；本技能只建基建，不写用例）。

## 4. 清理
删除 `{output_dir}/scaffold-plan.json`（会话临时文件，非产物）。

## 播报与下一步

本技能到此结束——下一步读 `diy-test-author/SKILL.md`（若已建；未建则以摘要中的路由行交接）。
