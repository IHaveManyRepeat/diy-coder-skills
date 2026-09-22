# Step 3 — 出方案与写规格（Design Solution）

Progress: `[1 载场景 → 2 择法三选一 → 3 设计变更 → 4 写规格 → 5 规格签核] → ./04-implement.md`

**Read (input):** 本产物 `rounds[EV-<nn>].scope` 整段（上一文件已落盘）；`data/kaizen-principles.md` 的「标准化再改进」原则与「消除 Muda」清单；用户对「快修 / 先画 / 生成」三选一的回答。
**Write (output):** `rounds[EV-<nn>].design`（Change Scope / Update Specification / 新组件 / 前后对照 / 假设校验五件）+ `rounds[EV-<nn>].status: 设计`。

你是**方案的设计者**。这一步只做一件事：把上一段那份「要变成什么样」**落到可实施的程度**——但不写代码（那是 04-implement 的事）。

**本段纪律（源 `steps-d/step-01` 第 6a 的 Self-Review）**：① 每一个组件改动都要能被**改前 / 改后**两句话说完；② 边界情形（移动端 / 长文案 / 空态）**逐条过**，不许留给实现期即兴；③ 假设必须写出**失败判据**——只写成功判据的假设验不了伪。

## 第 1 步 —— 载场景（源 [D] step-01）

**先说清为什么**：为什么方案必须踩在场景上——场景定的是「这次改什么」，方案一旦超出它的边界，范围就悄悄回来了。用你自己的话讲。

**读什么、读出什么**：

| 读 | 抽出 |
| --- | --- |
| `rounds[EV-<nn>].scope.target` / `.desired_state` | 方案的靶子（改完要长成什么样） |
| `.scope.pages_affected[]` / `.components_touched` | 方案的落点（能改的清单——**清单外的页一律不碰**） |
| `.scope.journey.pain_points` | 方案要消掉的那个断点 |
| `.scope.risk` | 方案的自审强度（`High` 时第 5 步的签核要更重） |

**产出键**：无（读回靶子与「能改的页」清单）。

**落盘**：本步不写盘。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 复述靶子一句 + 能改的页清单 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 择法三选一`。

## 第 2 步 —— 择法三选一（源 [D] step-02）

**先说清为什么**：为什么不是每次都「出完整稿」——小改写成大稿，成本跑得比收益快，这正是 Kaizen 要消的 Muda（过度加工）。用你自己的话讲。

**三条路（源 [D] step-02 逐字）**：

| 路 | 判据（源） | 走法 |
| --- | --- | --- |
| **Quick fix** | 小的视觉 / 文案改动 | **跳过第 3 步**，直接进第 4 步写规格 |
| **Sketch first** | 布局或流改变 | 先画改前 / 改后，再写规格 |
| **Generate design** | 明显的视觉改变 | 源侧此处指向 Phase 6 资产工具——**diy 侧的对应物是 `diy-wds-assets`**（本技能**不调用它**，只把「需要生成资产」记进规格的 `assets_needed`，由用户自行决定走哪条） |

**产出键**：`design.approach: quick-fix|sketch-first|generate`（**由用户显式选**，不代选）。

〔**源侧处置**〕源 [D] step-2 第三条写「Use Phase 6 asset generation tools」且**未点名任何技能**（源侧靠人设菜单派发）。diy 侧**不跨技能直调**（写权边界：各技能只写自己的产物）——改为**记需求 + 给路由**。

**落盘**：本步不写盘。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 呈出三条路与各自的理由 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 设计变更`（选了 `quick-fix` 就整段跳过，进第 4 步）。

## 第 3 步 —— 设计变更（源 [D] step-03）

**先说清为什么**：为什么要明确标出「diff」——「改了什么」说得越具体，[I] 阶段越不容易顺手多改。用你自己的话讲。

**四件（源 [D] step-03 的 1–4）**：

1. **Before 快照**——现状的刻画或截取（**引用 `scope.current_state`，不复述**）
2. **After 概念**——期望态的刻画（新组件 / 新布局 / 新文案，逐项）
3. **Diff 视图**——**显式标出**：布局 / 组件 / 内容 / 行为四栏各变什么
4. **边界情形**——移动端？长文案？空态？（源侧原文三问，逐条答）

**迭代纪律**：呈给用户、收到反馈、改，**直到点头**（源 `Iterate until approved`）。

**产出键**：`design.before_after: {before, after, diff: {layout, components, content, behavior}, edge_cases}`。

**落盘**：本步不写盘（第 4 步成稿一次性落）。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 呈出 before / after / diff → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 写规格`。

## 第 4 步 —— 写规格（源 [D] step-04）

**先说清为什么**：为什么小改也要有一份规格——[I] 与 [T] 两步都要读它；没有它，「按验收判据逐条测」就退化成「我觉得没问题」。用你自己的话讲。

**mini page-spec 六段（源 [D] step-04 的模板，逐段对应到产物键）**：

```yaml
design:
  approach: quick-fix|sketch-first|generate     # 第 2 步
  change_summary: <一段话说清这次改什么>          # 源 Change Summary
  before: <改前>
  after: <改后——可实施的详细规格>
  components:                                    # 源 Components：逐件给新属性/行为
    - {name: <件名>, kind: 新增|修改|删除, props: <新属性>, behavior: <新行为>, file: <落点>}
  responsive: <跨断点怎么变>                      # 源 Responsive Behavior
  acceptance_criteria:                           # 源 Acceptance Criteria（从场景的成功判据落成可测条目）
    - {criterion: <一句可测的话>, source: <溯到 scope.success_criteria 或 journey.pain_points>}
  assets_needed: [<第 2 步选了 generate 时记的资产需求——不调用外部服务>]
  hypothesis:                                    # 源 `design-templates.md` 的假设校验模板
    {statement: <假设>, assumptions: [], risks: [],
     success_criteria: [], failure_criteria: []}
```

- **`acceptance_criteria` 与 `hypothesis.failure_criteria` 是本技能的验收两份底账**：前者供 `05-test.md` 逐条执行（**只验本轮增量**），后者供 `06-finish.md` 判断这轮到底算不算成立。
- 规格里**不许出现 `[假设]` 标记**（未决项写 `revisions` 或就地补问）——`check --final` 会机械判红。

**产出键**：`design` 整段。

**落盘**：`rounds[EV-<nn>].design` + `rounds[EV-<nn>].status: 设计` + `project.updated`。

**检查点（六拍）**：① 生成 → ② 落盘（`design` 段 + 状态推进）→ ③ 分隔 → ④ 呈出六段 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 5 步 —— 规格签核`。

## 第 5 步 —— 规格签核（源 [D] step-05）

**先说清为什么**：为什么签核要问三个具体问题而不是「可以吗」——「可以吗」永远得到「可以」，三个具体问题才有机会得到「不」。用你自己的话讲。

**三问（源 [D] step-05 逐字）**：

1. **它还对得上场景吗？**（对 `scope.target` 与 `.desired_state`，逐条对）
2. **验收判据可测吗？**（每条 `acceptance_criteria` 是否能被 [T] 独立复现——答「大概能」的**现在改成能**）
3. **范围还好管吗？**（对照 `scope.risk`——若设计过程中悄悄涨了，**回第 4 步收窄**，不许带病进 [I]）

**产出键**：`design.approved: {by, on, notes}`（三问的答案逐条留痕）。

**落盘**：签核结论进 `design.approved: {by: 用户, on: <日期>, notes: <评委原话>}` + `project.updated`。

**检查点（六拍）**：① 生成 → ② 落盘（`design.approved`）→ ③ 分隔 → ④ 呈出三问的答案 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

**收尾与路由**：规格已签，读 `./04-implement.md` 动手。

本文件到此结束，不再回头。
