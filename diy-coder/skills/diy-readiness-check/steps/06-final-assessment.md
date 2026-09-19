# Step 6 — 总评与定稿

Progress: `文档发现 → 需求清点 → 覆盖校验 → UX 对齐 → 史诗质量评审 → [总评与定稿]`

**Read (input):** 本轮由第 1–5 步填好的记录；`collect` 回执的计数。
**Write (output):** 定稿记录（`verdict` / `counts` / `status: 已定稿`，落在 `{output_dir}/readiness.yaml`）；渲染视图；收尾摘要。

## 定裁决

三档，由刚记下的 finding 推出来：

- **`就绪`** —— 没有阻塞项、也没有值得路由的问题：可以开工。
- **`有风险就绪`** —— 值得记下的非阻塞 finding（`中` / `低`）：开工，但睁着眼睛。
- **`未就绪`** —— 至少一条 `严重` 或 `高` finding：上游文档必须先改。

终门强制两条硬蕴含：`就绪` 不得带 严重/高 finding；`未就绪` 至少带一条。绝不把 `严重` 软化成 `中` 去凑 `就绪`——「不软化信息」正是本技能存在的理由。

## 汇编（源 step-6 §2/§3）

- 每条留档的 finding 都带 `message`（为什么是要紧事）与 `evidence`（显示它的锚点——文件、ID 或引述原句），属于别的技能时再带 `route`。
- `counts.findings_by_severity` 必须等于实际记下的 finding（终门按集合重算计数）；`coverage` 与回执给的一字不差。
- 收尾消息要带源报告有的东西：裁决、需要行动的严重问题、建议的下一步（1–3 条具体项）、以及「N 条 finding 跨 M 个面」——用 `document_output_language` 写。不写 markdown 报告：记录就是报告。

## 终门（机械）

1. 先写记录级 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物。
2. 跑 `python "{project-root}/.claude/skills/diy-readiness-check/scripts/readiness.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两个实参同激活（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑。JSON 回执（含计数）即收口证据。
3. 用 diy-viewer 渲染——SKILL.md 里的静默旁路命令——只在 exit 0 之后；不新增浏览器交互点、不报阻塞路径。

## 交接

- `就绪` / `有风险就绪` → diy-test-design（test-plan.yaml），随后 diy-sprint；用一行点名路由。
- `未就绪` → 每条 严重/高 finding 的 `route` 点名的归属技能（diy-prd / diy-architecture / diy-epics-stories / diy-design）；它们落地后重跑本技能。

## 收尾

这是最后一个步骤文件——终门 exit 0 后本轮到此结束。结果由 `verdict` 与 `findings[].route` 承载；不再读任何 `steps/` 文件。
