# Step 5 — 呈现与收尾

Progress: `Clarify & Route → Plan → Implement → Review → [Present]`

**Read (input):** `status: 审查中` 的记录连同其 `review` 块；自 `baseline` 以来的 diff。
**Write (output):** 记录的 `review_order` 与 `status: 已完成`；`project.status: 已定稿`；收尾摘要。

## 建带看顺序

构造自 `baseline` 以来的 diff，然后追加 `review_order`——一条有序的看点轨迹，让人能自上而下读完这次改动：

1. **按关注点排序，不按文件** —— 把看点按它们服务的概念性关注点分组（校验逻辑、schema 变更、UI 绑定）。一个文件可以出现在多个关注点下。
2. **入口点领读** —— 最能先揭示设计意图的那个 `path:line`。
3. 同一关注点内，从最重要 / 架构上最有意思的排到辅助性的；稍微偏向高风险或跨边界的看点。
4. **外围收尾** —— 测试、配置、类型等支撑性改动放最后。
5. 每个看点：`{path, line, why}`——`path` 用 project-root 相对、不带前导 `/`，`line` 是锚点，`why` 一行极简（≤15 词）说清此处为何用这种做法、达成了什么。不写段落。

## 落定记录

1. 写 `{output_dir}/spec.yaml` 的 `project.status: 已定稿` 与记录的 `status: 已完成`。
2. **终门（机械）：** 跑 `python "{project-root}/.claude/skills/diy-quick-dev/scripts/spec.py" check --final --id SP-xxx --project-root "{project-root}" --output-dir "{output_dir}" --json`（`--output-dir` 必填、无缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。`check --final` 要求记录已 `已完成`、每个任务都已 done、acceptance 非空、每条验证命令都有真实 `result`。

## 收尾

用 diy-viewer 渲染——SKILL.md 里的静默旁路命令（resolved 实例时附 `--instance <name>`）；不新增浏览器交互点、不报路径等待、不阻塞。

然后展示摘要：

- 改动的文件，各一行；终端里所有路径都是 project-root 相对 `path:line`，绝不带前导 `/`。
- 审查明细：用了多少轮、按路由分的 findings（已修 / 已延后 / 已丢弃）——若 findings 全被丢弃，直说。
- spec 路径，并说明它的 `review_order` 现在承载阅读轨迹。
- **提交与推送是人的事。** 绝不 commit、绝不 push、绝不打开编辑器——收尾只给一行建议（一条人自己能跑的 conventional 提交信息，外加一句「要不要我起草 PR 描述」）。工作树保持原样。
- 以 JSON 回执里的计数收尾（已完成任务数、按路由分的 findings、跑过的验证命令数、最终状态）。

## 播报与下一步

这是 计划-编码-审查 路线的最后一步——终门 exit 0 后本次运行到此结束。一次成型路线在 `./06-oneshot.md` 收尾；不再读任何 `steps/` 文件。
