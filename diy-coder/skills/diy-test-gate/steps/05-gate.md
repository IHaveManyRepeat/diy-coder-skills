# Step 5 — Gate（单一门决策：规则树 + overlay + 豁免）

Progress: `Preflight → Oracle → Matrix & Gaps → NFR → [Gate] → Finish`

**Read (input)：** 草稿记录已填的 `coverage` / `nfr` / `blockers`；`collect` 回执的 `soft_metrics` / `mutation`。
**Write (output)：** 草稿记录的 `gate`（`decision` / `hard_criteria` / `soft_criteria` / `blockers` / `waivers` / `basis` / `recommendations`）。

## 两组判据（名字与 target 固定，不自造）

**硬判据（一票否决：任一 `失败` → 整门 `FAIL`）**

| name | target | actual 取数 |
| --- | --- | --- |
| `p0_coverage` | `100%` | P0 AC 的 covered / total（covered = `FULL` / `UNIT-ONLY` / `INTEGRATION-ONLY`） |
| `overall_coverage` | `100%` | 全部 AC 的 covered / total |
| `p1_coverage` | `100%` | P1 AC；**无 P1 时记 `100%` + `通过`**（源 effectiveP1=100 口径） |
| `mutation_score` | `>=90%` | 回执 `mutation.score`（`mutation-report.yaml` 全部 run 的**最小值**，保守口径）；报告缺席 → `n/a` + warning（过渡期：C 阶段前不影响 decision，C 落地后记 `失败`） |
| `nfr_critical` | `0` | FAIL 域数 − `waivers` 已豁免域数（`安全` 域 FAIL **不可豁免**） |
| `p0_uncovered` | `0` | priority = P0 且 coverage = `NONE` 的行数 |

**软判据（任一 `失败` → 门降为 `CONCERNS`；不影响 FAIL 判定）**

| name | target | 口径（分子 / 分母） |
| --- | --- | --- |
| `business_rule_coverage` | `100%` | 带 `决策表` / `状态迁移` 的已验证 TC 覆盖的 AC 数 ÷ 矩阵 AC 总数 |
| `boundary_coverage` | `100%` | 带 `边界` 的已验证 TC 覆盖的 AC 数 ÷ 同上 |
| `negative_scenario_coverage` | `>=90%` | 带 `错误猜测` 的已验证 TC 覆盖的 AC 数 ÷ 同上 |
| `p0_depth_full` | `100%` | P0 AC 中「已验证 TC ≥2 类 type 且含 ≥1 条异常场景 TC」的占比 |
| `effective_case_ratio` | `>=95%` | （`ac` 可解析 + `kill_target` 非空 + `steps` 非空）的 TC 数 ÷ TC 总数 |
| `id_chain_resolvable` | `100%` | TC→AC→story 全链可解析的 TC 数 ÷ TC 总数（**不读源码**） |

`actual` 与 `result` 照 `collect` 回执的 `soft_metrics` 写；`estimated: true` 只用于引擎算不出的项，且**必须**填 `algorithm`（缺 → `EMPTY_FIELD` 违例）。`check` 会按记录内数据重算 `p0/overall/p1`、`nfr_critical`、`p0_uncovered`、`mutation_score` 并与你写的 `actual` / `result` 对账（`CRITERION_STALE`）——**禁手填估计值**。

## 规则树（decision 怎么定）

```
任一 hard_criteria 失败                        → FAIL
否则 有 soft_criteria 失败                     → 至少 CONCERNS
     或 任一 NFR 域 CONCERNS                   → 至少 CONCERNS
     或 overlay 命中                           → 至少 CONCERNS
否则（全部 通过、无域 CONCERNS、无 overlay）    → PASS
```

- **`FAIL` 优先**：硬指标不过就是不过，软指标再好也不改档。
- **没有「无法评估」档**：拿不到足够数据（如 oracle 解析不出）→ 走 HALT，**不落门产物**——半份记录会被下游当成已评估。
- 三线口径：源为 `P0=100% / overall>=80% / P1 目标 90% 且最低 80%`；**diy 拉满为三线全 `100%`**（2026-09-15 用户裁定），故 `p0_coverage` / `overall_coverage` / `p1_coverage` 的 target 都是 `100%`，覆盖率无中间档；CONCERNS 只出自软判据失败、NFR 域 CONCERNS、overlay 命中三处。

## Overlay

1. **合成 oracle**（引擎强制）：`oracle.source: 合成` 且 `confidence ≠ 高` → 覆盖全绿也只能到 `CONCERNS`。这是源 oracle-confidence overlay 的 diy 形态，别绕。
2. **弱证据 / live-only**（你的判断，源 live-only overlay 的 diy 对应物）：某 AC 的覆盖**只**由判定表 ③（`status: 通过` 但无红绿台账，即 `diy-e2e-tests` / `diy-augment` 追加用例那种「不可重跑、无台账」的来源）支撑时——把它写进 `gate.blockers`（`kind: 覆盖`）与 `recommendations`，说明「不可重跑、复核成本高」。
   **不自动抬档**：diy 的 ③ 有合法来源，一刀切会把合法路径全打成 CONCERNS；要抬档就必须有判据落点（该风险体现为某条软指标失败或某域 CONCERNS），否则 `check` 会判 `DECISION_INCONSISTENT`。

## 豁免（用户交互点，仅人工授权写入）

- `waivers` 每条的 8 键固定：`ref` / `approved_by` / `date` / `reason` / `expires` / `monitoring` / `fix_owner` / `fix_target`——**缺一键即 `WAIVER_INCOMPLETE`**。`expires` 必须显式给出（源文无默认到期）。
- `ref` 可以是域名、`AC-x.y`、`TC-x.y.z`；`ref: 安全` **被拒**（`安全` 域 FAIL 不可豁免）。
- **流程**：先列出「未获裁定的缺口 + 建议豁免项 + 后果」，交用户裁决；用户明确同意后才写入，`reason` 引用户的话（原话或贴近转述），`approved_by` 写用户。
- **无头 / 循环调用**：不停下等——缺口照计 blocker、门照判（通常是 `FAIL`），裁决请求落 `recommendations` 与 `open_questions`，供用户事后处理。
- 引擎**永不自动生成 waiver**；`diy-augment` 报的等价变异体同样要经用户裁定才落这里。

## 回填与下一步

写 `gate`：`decision` / 两组判据（照回执）/ `blockers`（`kind` ∈ `覆盖|非功能需求|启发式`，每条带 `why`）/ `waivers` / `basis`（一句话：为什么是这个档位，含「三线覆盖 + 域状态 + overlay」的落点）/ `recommendations`。

读完并执行 `./06-finish.md`。
