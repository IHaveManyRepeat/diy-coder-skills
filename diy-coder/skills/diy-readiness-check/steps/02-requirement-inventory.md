# Step 2 — 需求清点

Progress: `文档发现 → [需求清点] → 覆盖校验 → UX 对齐 → 史诗质量评审 → 总评与定稿`

**Read (input):** `collect` 回执（`requirements`、`counts`、`diyc.check`）；只有当人问起某条需求的原文措辞时才读 `prd.yaml` 那一条。
**Write (output):** 记录的 `counts` 块（落定）；清点暴露出的问题落成 finding。

## 与源工作流的差别（先读这段）

源 step-2 通读整份 PRD（整篇或分片的 markdown），手工把每条 FR、NFR 抽进报告的散文小节。那次抽取本身就是失败面：手工计数会漂移，而漏掉一次的需求会从其后那张覆盖矩阵里静默消失。

diy 里 PRD 是结构化的（`prd.yaml`），所以清点由机器推导。`collect` 回执的 `requirements.frs` 列全部 FR 及其 `priority` 与所属 `feature`，`requirements.nfrs` 列全部 NFR，`counts` 给计数。不要重抽、不要重述——把回执呈上。

- 人预期有、回执却没有的 FR，不是抽取漏项：是 `prd.yaml` 里本来就没有。把它落成 finding 带 `route: diy-prd`，或者说明白并交人决定。
- 需求原文只引用、绝不抄进记录——指向 ID（`prd.yaml features[F-1].requirements[FR-1.1]`）。

## 呈上清点结果

一条消息，前置给全：

- FR 总数及其 必须/应该/可选 分布；NFR 总数；FR 列表写成 `FR-x.y (必须) — feature F-x`；
- 回执里的 epics / stories / AC 计数；
- PRD 还挂着的未决问题——`diyc.check` 回执把未关闭的 `open_questions` 报成 `PENDING_DECISION`；带着未决问题的 PRD 不算定稿输入。

HALT —— 停下让人扫这份清单：这是判断覆盖之前，最后一次逮住漏项的机会。

**完整性判读**（源 step-2 §6「PRD Completeness Assessment」）。直说 PRD 对这次建设读起来是否完整、无歧义：机械面（枚举、未决问题、重复 ID）由回执覆盖，清晰度由你读——某条需求的 statement 不靠猜就转不成 AC，就是一条 finding（`area: prd`、`route: diy-prd`），`evidence` 取该 FR ID。

## 附加需求（从不贴 FR/NFR 标签）

源工作流还会找没被任何标签接住的约束、假设与技术需求。在 diy 形态里，它们住在 `prd.yaml` 的 `out_of_scope` / `open_questions` / `nfrs` 与 `architecture.yaml` 的 decisions 里。人知道的某条约束哪一处都不在，就是一条 finding（`area: prd`、`route: diy-prd`）——绝不静默带着走。

## 来自 diyc 的证据（每条机械违规都落 finding）

`collect` 委派 diyc 跑的是 `prd` / `epics` / `stories` 三型检查，回执的 `diyc.check.violations` 三型合在一处（每条带 `where` 与 `type`）。三条硬规则：

1. **每条违规落一条 finding**，`evidence` 取该违规的 `where`；
2. **`area` 按 `where` 的文件名映射**（`prd.yaml`→`prd`、`epics.yaml`→`epics`、`stories.yaml`→`stories`；回执同一行带的 `type` 就是这根轴）；
3. **`route` 取引擎同表**（`prd.yaml`→`diy-prd`，`epics.yaml` / `stories.yaml`→`diy-epics-stories`）。

`severity` 分档：`PENDING_DECISION` / `DUPLICATE_ID` / `UNKNOWN_ID` / `SET_MISMATCH` → `高`（决策未落或 ID 链断，下游照着做就会错）；`ENUM_INVALID` / `EMPTY_FIELD` 及其余 → `中`。

机械判定不重复核查（原样带 `where`），记完重算 `counts.findings_by_severity`。

## 播报与下一步

读全 `./03-coverage-validation.md` 并照做。
