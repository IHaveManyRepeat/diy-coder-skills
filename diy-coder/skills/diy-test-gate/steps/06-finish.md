# Step 6 — 定稿收尾（Finish：终门 + 渲染 + 摘要）

Progress: `Preflight → Oracle → Matrix & Gaps → NFR → [Gate] → Finish`

**Read (input):** 已填完的草稿记录；`check` 的 JSON 回执。
**Write (output):** `{output_dir}/test-gate.yaml` 的定稿记录（`status: 已定稿` + 各段收口）；给用户的收尾摘要。

## 收口记录

1. 逐项自检：`oracle`（含 `inferred` / `unresolved`）、`coverage`（items / totals / by_level / heuristics）、`nfr`（四域 / overall_risk / adr / gaps）、`gate`（decision / 两组判据 / blockers / waivers / basis / recommendations）、`open_questions`——所有未决项**必须在文件里有落点**，不许只活在对话里。
   四条走查义务的落点对账：**证据时效**（`EVIDENCE_STALE` 的 TC / run 要么已重跑、要么已进 `gate.basis` 末句与 `recommendations`）、**重复覆盖候选**（`coverage.duplicates` 每条有判定，进 `gate.recommendations`）、**合规五标准行**（`nfr.domains[].findings` 五行齐 + 聚合行与逐域行口径一致）、**跨域合成行**（命中的组合在 `recommendations` 或 `findings` 有线，不成立也写明）。
2. 清 `[假设]`：起草期可以标，定稿前必须逐条落定（补证据、进 `open_questions`、或经用户裁定）；`--final` 面出现即 `ASSUMPTION_PRESENT`。
3. 写 `status: 已定稿`——**先落定稿态再跑终门**：`已定稿` 是终门要检的对象，不是它的产物。

## 终门（机械判定，唯一放行）

```
python "{project-root}/.claude/skills/diy-test-gate/scripts/gate.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

exit 0 是唯一放行；每条违规修掉并重跑。`--final` 会额外要求：`status: 已定稿`、`basis` 非空、hard / soft 两组判据齐、零 `[假设]`、合规五标准逐条记账（`COMPLIANCE_UNRECORDED` / `COMPLIANCE_AGGREGATE_MISMATCH`）、跨域合成候选有落点（`CROSS_DOMAIN_UNRECORDED`）；`mutation-report.yaml` 缺席只记 warning（过渡期口径），但其在场性一旦成立即参与 `mutation_score` 重算。

违规码速查：`DECISION_INCONSISTENT`（档位与判据 / 域状态 / overlay 不自洽）、`CRITERION_STALE`（判据 actual / result 与重算不符）、`WAIVER_INCOMPLETE` / `WAIVER_INAPPLICABLE`（豁免契约 / 安全域）、`THRESHOLD_UNSOURCED`、`UNKNOWN_THRESHOLD_PASS`、`COMPLIANCE_UNRECORDED` / `COMPLIANCE_AGGREGATE_MISMATCH`（合规五标准）、`CROSS_DOMAIN_UNRECORDED`（跨域合成）、`SET_MISMATCH`（totals / by_level / overall_risk / ADR 行数）、`UNKNOWN_ID`（引用悬空）、`EMPTY_FIELD` / `ENUM_INVALID` / `DUPLICATE_ID` / `STATUS_MISMATCH` / `ASSUMPTION_PRESENT`。JSON 回执（含计数）就是收尾证据。

## 渲染（静默旁路）

只写调用命令，不新增交互点、不等路径、不阻塞：

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

（resolved 实例时附 `--instance <name>`。）viewer 对 `test-gate.yaml` 走通用降级渲染，标签缺口由主 agent 登记，不在本技能补。

## 摘要（给用户，一段话 + 四行）

- **决策**：`PASS` / `CONCERNS` / `FAIL` + `basis` 一句话。
- **覆盖**：矩阵 N 行 / covered N（pct）；三线 P0 / overall / P1 的 actual；`by_level`。
- **Blocker**：按 `kind` 分组（覆盖 / 非功能需求 / 启发式）逐条一句——每条要能让接手方直接动手。
- **路由**：`PASS` → 主线继续（`diy-review` / 发布准备）；`CONCERNS` → `recommendations` + 到期豁免清单；`FAIL` → 建议 `diy-correct-course`（走变更流程重排）或把缺口回 `diy-dev` / `diy-test-design` 修复后重跑本门。

同时说明五件事：`sprint.yaml` 缺席时的降级（覆盖只认 test-plan `status`，已写进 `gate.basis` 末句）、`mutation_score` 是否 `n/a`、无台账 `通过`（判定表 ③）的条数与来源、重复覆盖候选的判定（`coverage.duplicates` 为空也要点一句）、证据时效（`EVIDENCE_STALE` 条数及处置）。

写盘与摘要都完成即结束——本步是最后一步，没有后续文件要读。
