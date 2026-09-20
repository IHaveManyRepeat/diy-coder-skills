# Step 4 — UX 对齐

Progress: `文档发现 → 需求清点 → 覆盖校验 → [UX 对齐] → 史诗质量评审 → 总评与定稿`

**Read (input):** 回执的 `docs.design` / `docs.architecture`；在场时的 `design.yaml` 与 `architecture.yaml`；缺 `design.yaml` 时的 `design.py detect` 回执。
**Write (output):** UX 类 finding（`area: ux`）——对齐缺口，或「被隐含却缺席」的告警。

## 文档状态

diy 里设计/UX 的单一源是 `design.yaml`（页面 `P-x`、design tokens）。回执说明它在不在场；源工作流那次 `*ux*.md` 检索与它一一对应——别去找 markdown 版 UX 文件。

## design.yaml 在场 —— 校验对齐

**UX ↔ PRD。** 设计展示的每条用户旅程都必须追溯到 PRD 需求（`FR-x.y`），否则记一条：页面承载了没有需求背书的功能 = PRD 从未批准的范围（`route: diy-prd`）；某条前端面需求设计从未覆盖 = 缺口（`route: diy-design`）。

**UX ↔ 架构。** 检查架构决策（`architecture.yaml` 的 `D-x`）支撑得住设计所需——设计隐含的响应式与加载时长目标、客户端状态、任何其后台服务无决策覆盖的 UI 组件。点名该决策、或点明它的缺席，都要带证据锚点。

这里的 finding 是 `area: ux`；severity 按后果定——需求无法照设计实现是 `高`，对齐欠债是 `中`，打磨项是 `低`。

## design.yaml 缺席 —— UX 是否被隐含？

缺席是合法的（CLI、库、后端服务）——但绝不假设它（源 step-4 规则「Don't assume UX is not needed」）。判据与本套件同一口径：取 `diy-design` 探测器（`design.py detect`）的 `has_frontend`，不要自拟一套「用户可见」的读法：

```bash
python "{project-root}/.claude/skills/diy-design/scripts/design.py" detect --project-root "{project-root}"
```

（resolved 实例时附 `--instance <name>`；脚本化时加 `--json`。）

- `has_frontend: true`（PRD 检出前端面需求）而 `design.yaml` 缺席 → 一条 finding：`area: ux`、`severity: 中`、`route: diy-design`，`evidence` 取探测器命中的 FR ID——源工作流那条告警，保留。
- `has_frontend: false` → 没有隐含前端面需求，明说一句、什么都不记；第 6 步按干净面汇报。diy-design 用同一探测器且会声明 SKIP——两处结论一致，不会对打。

## 播报与下一步

读全 `./05-epic-quality-review.md` 并照做。
