# Step 1 — 前置校验（Preflight：产物在场 + story 定位 + 采集）

Progress: `[Preflight] → Oracle → Matrix & Gaps → NFR → Gate → Finish`

**Read (input):** `collect` 的回执（On Activation 已跑）；`{output_dir}/test-gate.yaml` 的既有记录（只用于铸造下一个 `TG-###`）。
**Write (output):** `{output_dir}/test-gate.yaml` 的草稿记录（`id` / `date` / `status: 草稿` / `scope` / `story` / `oracle` / `coverage`）。

## 拒绝路径先落地

`collect` 退出码 1 = 门禁拒绝，本次运行在记录诞生前就结束：转述一行理由 + `gate.route`，然后停止并写零产出。

| 缺什么 | 引擎给的 route | 你说什么 |
| --- | --- | --- |
| `stories.yaml` 缺席 / 不可解析 / 无 AC | `diy-epics-stories` | AC 是 diy 的默认 oracle 主源，没有它就没有矩阵 |
| `test-plan.yaml` 缺席 / `project.status` 非 `已定稿` | `diy-test-design` | 覆盖证据的单一源必须定稿 |
| `prd.yaml` 缺席 / 不可解析 | `diy-prd` | priority 推导（必须→P0 / 应该→P1 / 可选→P2）是全门分数线的前提，**不得降级** |
| `--story S-x` 不存在 | `diy-epics-stories` | 先确认 story ID |

`diyc` 子进程报的 test-plan 违规（`diyc.violations`）**不是拒绝**——它们是上游实况，逐条落 `gate.blockers`（`kind: 覆盖`），并在摘要里点名。被吞掉的违规等于伪造绿灯。

## 定位本次门

- 一次门 = 一个 story（`scope: story`，唯一合法值；epic / release 为 v2 推迟项）。范围由用户给出或从对话上下文取；给了 `--story` 时按它，未给时 `collect` 回执的 `stories[]` 是候选清单，逐条问一次，不要替用户挑。
- 目标记录：`{output_dir}/test-gate.yaml` 里 **已存在** 的 `TG-###` 中，若同一 `story` 已有未定稿记录 → 继续填充它（不新开）；否则铸造下一条：序号 = 现有最大值 + 1，三位零填充，**不重用不重编号**。

## 落草稿记录

文件不存在时先建骨架：`project: {name: <diy-coder.yaml 的 project.name>, created: today, updated: today}` + 空 `gates: []` + 空 `revisions: []`。然后追加：

```yaml
  - id: TG-001            # 新铸造
    date: <today>
    status: 草稿
    scope: story
    story: S-x
    oracle: {source: stories, confidence: 高, items: <回执 items 数>, inferred: [], unresolved: []}
    coverage:
      items: []           # 下一步整块贴上（照抄回执，禁手抄数字）
      totals: {covered: 0, total: 0, pct: 0}
      by_level: {单元: 0, 集成: 0, 端到端: 0}
      heuristics: []
    nfr: {domains: [], overall_risk: NONE, adr: {rows: 29, passed: 0}, gaps: []}
    gate: {decision: '', hard_criteria: [], soft_criteria: [], blockers: [], waivers: [], basis: '', recommendations: []}
    open_questions: []
```

`oracle` 与 `coverage` 的填值口径在 step 2 / step 3；这里只保证记录壳子在，后续各步就地补字段。

## 播报与下一步

给用户一句话：本次门覆盖哪个 story、矩阵多少行、回执里已有多少 blocker / 缺口、下一步做 oracle 解析。

读完并执行 `./02-oracle.md`。
