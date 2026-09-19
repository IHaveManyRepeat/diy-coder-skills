# Step 5 — 拍板

Progress: `定向 → 带看 → 风险详查 → 亲手验证 → [拍板]`

**Read (input):** 本轮的草稿记录（`concerns` / `risks` / `observations` 已填部分）；带看对话。
**Write (output):** 定稿记录（`decision` / `reason` / `next` / `status`，落在 `{output_dir}/checkpoint.yaml`）；渲染视图；收尾摘要。

## 请人拍板

```
---

带看完了。这个 {change_type} 怎么定？
- **`批准`** —— 发车（我只记这次拍板；要先修的归 diy-dev，不归我）
- **`返工`** —— 回炉（回退、改规格、换路子）
- **`讨论`** —— 还有事在你心里
```

HALT —— 人给出选择前不要往下走。早先给过的选择（第 2–4 步提前退出）已满足本提示，直接用。

## 按结论行动

- **`批准`** —— 简短回应，定稿记录，写下 `next` 路由点名发车路径（比如目标是 sprint 任务时，把状态迁移交给 diy-review）。目标是 PR 且 `gh` 可用时，可提议走 `gh pr review --approve`——可选路径，执行前先确认：那是对共享资源的一次可见动作。人要先补丁，那是 diy-dev 的活儿：本技能绝不改代码。
- **`返工`** —— 问清哪里不对：路线、规格，还是实现？帮人选下一步（回退提交、开 issue、改规格）并写进 `next`。变更是别人的 PR 时，帮人起草挂到 `path:line` 的具体反馈。执行回退不是本技能的活儿。
- **`讨论`** —— 开放对话：答疑、展开顾虑、深钻任意一面。记录保持未定稿（`status: 草稿`）；聊完回到上面的提示。

## 定稿记录

1. 填 `decision`（`批准` / `返工` / `讨论`）、`reason`（人自己的话）与 `next`（路由建议，用 `document_output_language` 写）。没走到的节保持空——绝不编造。
2. 任何一次写回后做结构检查：`python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" check --project-root "{project-root}" --output-dir "{output_dir}" --json`——exit 0 表示记录结构合法；有违规就修完重跑。
3. **`批准` / `返工` → 终门（机械）：** 先写 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两个实参同上。exit 0 是唯一放行；逐条修完上报的违规再重跑。JSON 回执（含计数）即收口证据；渲染与收尾都等 exit 0。
4. **`讨论` → 循环：** 保持 `status: 草稿` 并回到决策提示；人落到 `批准` 或 `返工` 前，终门不适用。
5. **改既有记录**（迟些才定稿的 `讨论` 记录、被修订的结论）：往顶层 `revisions` 列表追加 `{date, change, reason}`——永不重编号、永不复用 `CK-###`，也绝不改写更早的历史。

## 收尾

用 diy-viewer 渲染——SKILL.md 里的静默旁路命令（resolved 实例时附 `--instance <name>`）；不新增浏览器交互点、不报路径等待。然后以结论与回执的计数（含 `counts`）收尾，并用一行点名 `next` 路由。

## 播报与下一步

这是最后一个步骤文件——终门 exit 0（`批准` / `返工`）或 `讨论` 循环交回给人后，本轮到此结束。路由写在记录的 `next` 字段里；不再读任何 `steps/` 文件。
