# Step 6 — 定稿门与收尾

Progress: `立案 → 分析 → 改动 → 提案 → 路由 → [收尾]`

**Read (input):** 第 1–5 步填好的本轮记录。
**Write (output):** `{output_dir}/change-proposal.yaml` 里定稿的记录（`status` / `handoff` 终值）；渲染视图；收尾摘要。

## 终门（机械）

1. 先写终态——`已定稿`（分析已落定、尚未获准）或 `已批准`（人说了 yes）——`已定稿` / `已批准` 是门检查的对象，不是门的产物。
2. 跑 `python "{project-root}/.claude/skills/diy-correct-course/scripts/change_proposal.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两个实参同激活（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑。JSON 回执（含计数）即收口证据。
3. 门强制的正是路由的前提：`handoff.route` 在场且在该 scope 的 allow-list 内、`impacts` 非空、路径已定（`approach`）、零 `[假设]`——未确认的推断先与人落定，或落成一条显式 `open_questions` 再进终门。
4. 渲染用 diy-viewer——SKILL.md 里的静默旁路命令——只在 exit 0 之后：不新增浏览器交互点、不报路径阻塞等待。

## `已驳回` 出口（不读终门）

第 5 步选了「既不批准、也不返修」时，记录已写 `status: 已驳回`，保留作审计轨迹。

- 终门对本条**永不放行**——`--final` 要求 `status ∈ {已定稿, 已批准}`；把它改写成终态就是抹掉审计轨迹。**不读、不跑终门。**
- 改跑**不带 `--final`** 的同一条命令收口：`python "{project-root}/.claude/skills/diy-correct-course/scripts/change_proposal.py" check --project-root "{project-root}" --output-dir "{output_dir}" --json`——exit 0 即记录形态合格（终门专属义务如 `impacts` 非空、`handoff` 在场在此不适用）；逐条修完上报的违规再重跑。
- 不做交接路由、不渲染，也不算「交给谁」那一项；一行说明本记录以 `已驳回` 收口即可。

## 收尾摘要

一条收尾消息，四个事实加下一步：

- **处理了什么** —— 一行写出 `trigger`；
- **变更规模** —— `scope` 及其落档理由；
- **波及产物** —— `impacts` 上去重后的 `artifact` 集合（加 edits 条数）；
- **交给谁** —— `handoff.route` 与它继承什么；
- **下一步** —— 路由技能跑它自己的门；在那之前本记录不改动任何东西。改动日后落地又出现新证据时，新开一条 `CP-###`——本记录永不重写。

## 播报与下一步

这是最后一个步骤文件——终门 exit 0（或 `已驳回` 出口 exit 0）后本轮到此结束。结果写在记录的 `handoff.route` 字段里；不再读任何 `steps/` 文件。
