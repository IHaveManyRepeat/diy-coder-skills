# Step 3 — Matrix & Gaps（矩阵复核 + 缺口 + 盲区走查）

Progress: `Preflight → Oracle → [Matrix & Gaps] → NFR → Gate → Finish`

**Read (input)：** `collect` 回执的 `items[]` / `coverage` / `gaps` / `soft_metrics` / `warnings`；`{output_dir}/test-plan.yaml` 中**该 story 的 TC**（按 `ac` 与 `id` 定位，不整份通读）。
**Write (output)：** 草稿记录的 `coverage`（`items` / `totals` / `by_level` / `heuristics`）与 `gate.blockers` 的 `kind: 覆盖` / `kind: 启发式` 部分。

## 覆盖判定表（口径，供你复核，不是让你手算）

引擎逐 TC 判；你核对**语义**对不对：

| 序 | TC 实况 | 判定 | 落点 |
| --- | --- | --- | --- |
| ① | `status: 失败` | **不计**（失败胜——即使同 TC 留有 green 台账） | `gate.blockers`（`kind: 覆盖`） |
| ② | `status: 通过` 且有 evidence（该 story 任务的条目 `red` / `green` 均非空） | 已验证 | 计入覆盖 |
| ③ | `status: 通过` 但无 evidence | 已验证 **+ warning** | 覆盖照算；warning 进摘要（合法无台账来源：`diy-e2e-tests` / `diy-augment` 追加用例不写台账；`diy-dev` 路径无台账属异常，须查） |
| ④ | `status: 待办` | 不计 | 缺口清单 |

AC 的五值（`items[].coverage`）：无 TC / 全未验证 → `NONE`；全验证且 type 全 `单元` → `UNIT-ONLY`；全 `集成` → `INTEGRATION-ONLY`；全验证且含 `端到端` 或 ≥2 类 type → `FULL`；部分验证 → `PARTIAL`。`totals.covered` 只数 `FULL` / `UNIT-ONLY` / `INTEGRATION-ONLY`——`PARTIAL` **不算覆盖**。

**你要复核的三件事**（脚本给不了）：

1. **TC ↔ AC 绑定是否正确。** 逐行看 `items[].tests`：有没有「用例其实验的不是这条 AC」的错绑？有 → 该 TC 记入 `open_questions`（绑定归 `diy-test-design`，你不改 test-plan）。
2. **`失败` 是不是真失败。** ① 里的每条 blocker，读该 TC 的 `steps` 与 `kill_target`，写清「它要暴露什么故障、现在什么现象」——一句 `why` 要能让 `diy-dev` 直接接手。
3. **`warnings` 里每条都有归宿。** 无 FR refs 的 AC、无台账的 `通过`、diyc 的上游违规——逐条要么进 `blockers`，要么进 `open_questions`，要么在摘要里点名并给理由。静默丢弃 warning = 伪造绿灯。

## 缺口分析

`gaps` 的 kind 含义与你该做的事：

| kind | 含义 | 处置 |
| --- | --- | --- |
| `none` | 无 TC 或全未验证 | 进 `recommendations`（补用例 → `diy-test-design`）并考虑进 `blockers` |
| `partial` | 部分 TC 已验证 | 写出「缺哪一类」：层级不够 → 走 `diy-test-author` 的层级纪律；类型不够 → 补负面 / 边界 |
| `blocker` | ① 的 `失败` | 必进 `gate.blockers` |
| `heuristic` | 5 类盲区候选（见下） | 你判定：真命中 → 进 `coverage.heuristics` + `blockers`（`kind: 启发式`）；误报 → 丢弃并在摘要写一句理由 |
| `accepted_gap` | test-plan `coverage_gaps` 的 `已豁免` / `接受缺口` | 记 `open_questions` 或 `recommendations`，**不**当缺口重复计 |
| `test_plan_pending` | 缺口仍 `decision: 待办` | 上游未定稿的信号：`test-plan --final` 会拦，`diyc.violations` 通常已报——别在本门替它裁 |

## 证据时效（>7 天 → 必须处置）

`collect` 对**超过 7 天（`EVIDENCE_TTL_DAYS`）没有新记录**的证据报 `EVIDENCE_STALE` warning：台账条目按 `red` / `green` 里的时间戳取最新一条算，`mutation-report.yaml` 按各 `run.date` 算；基准 = 采集当日。命中即**必须**二选一，不许静默：

- **重跑**刷新台账（走 `diy-dev` 的 TDD 循环 → `diyc.py green` 写回）；
- **用户确认沿用**——在 `gate.basis` 末句注明「本次门使用了 N 天前的证据（<TC/run>）」，并把该条写进 `recommendations`。

两条都不做 → 计 `gate.blockers`（`kind: 覆盖`，`why` 写明「证据 >7 天且未获确认」）。**7 天是源 trace checklist 的时效线**，不是可调参数。

## 重复覆盖检出（跨层冗余 / 可接受重叠）

`collect` 的 `coverage.duplicates` 给出候选：同一 AC 下「**同一 `technique` + 同一 `kill_target`**」在 ≥2 个 type 层级各有一条已验证 TC（`levels` 列层级、`tests` 列用例）。口径收窄在可读数据面（只比对技法 / 击杀目标 / 层级，不做语义去重），**可接受与否的判定是你的**：

- **可接受重叠**：AC 是 `P0`（关键路径）——纵深防御，写一行「保持」并说明防的是什么；
- **跨层冗余**：非 P0 —— 给**合并建议**（留哪一层、删哪一条），进 `gate.recommendations`；改 TC 绑定归 `diy-test-design`，本技能不写 test-plan。

候选非空时**逐条**落 `gate.recommendations`（每条写清 `AC` / 技法 / 层级 / 判定）；候选为空时在收尾摘要点一句「无跨层重复候选」。静默丢弃候选 = 伪造绿灯。

## 5 类盲区启发式走查

引擎按 AC 文本关键词 + 已验证 TC 的层级 / 技术给出候选，**最终判定是你的**。逐类问一句：

1. `endpoint-without-test` — 该 AC 对应的接口 / 端点，有没有一条集成层的用例真的打过它？
2. `auth-missing-negative-path` — 认证 / 权限类 AC：拒绝路径（错口令、越权、过期 token）有没有用例？
3. `happy-path-only` — 有用例，但全是正常路径？异常输入、超时、空值一条都没有？
4. `ui-journey-without-e2e` — UI 旅程只在 `单元` / `集成` 层验过，端到端从未跑通？
5. `ui-state-unasserted` — 页面只验了渲染，加载中 / 空态 / 校验失败 / 无权限四种状态无断言？

命中的写进 `coverage.heuristics`（字符串数组，每条写清「哪条 AC / 哪一类 / 依据」）。**口径按可读数据面收窄**：只从 `stories.yaml` / `test-plan.yaml` / `sprint.yaml` 可读数据判，**不读源码**——源码级盲区属 `diy-test-review` 的 `walkthrough`。

## 回填与下一步

`coverage.items` 照抄回执（`ref` / `story` / `priority` / `coverage` / `tests`）、`totals` / `by_level` 照抄；`heuristics` 写你的判定。脚本已算出的数字**禁手改**——`check` 会重算 `totals` / `by_level` 并判 `SET_MISMATCH`。

读完并执行 `./04-nfr.md`。
