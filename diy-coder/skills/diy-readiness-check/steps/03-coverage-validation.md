# Step 3 — 覆盖校验

Progress: `文档发现 → 需求清点 → [覆盖校验] → UX 对齐 → 史诗质量评审 → 总评与定稿`

**Read (input):** `collect` 回执（`coverage`、`diyc.check.violations`、`counts`）；只有当某条 finding 背后的映射需要落定时才读 `stories.yaml` / `epics.yaml`（含 `stories.yaml` 顶层 `notes:` 的 skip lines）。
**Write (output):** 记录的 `coverage`（落定）与覆盖类 finding。

## 覆盖取自回执

`collect` 按 diyc 对 `stories.yaml` 强制的同一条规则算出 `coverage`（每条必须级 FR 至少被一条 AC 引用），并跑 diyc 拿机械结论：

- `coverage.must_frs` / `coverage.covered` / `coverage.gaps` —— 要记的数；
- `diyc.check.violations` 中 `type: stories` —— 没有 AC 引用某条必须级 FR 时是 `SET_MISMATCH`，AC 的 `refs` 指向 `prd.yaml` 里不存在的 FR/NFR ID 时是 `UNKNOWN_ID`。

两者都不在这里重新推导。你的活儿是矩阵的人读那一列：每条 FR 由哪个 story/AC 承载，以及缺口怎么办。

## 搭覆盖矩阵

对每条必须级 FR——以及每条产出了 finding 的应该/可选 FR——点名承载它的 AC 与 story：

```
FR-1.1 (必须) — covered by S-1 / AC-1.1 (epic E-1)
FR-1.2 (必须) — NOT FOUND
```

以 `stories.yaml` 的 `acceptance_criteria[].refs` 为准：FR 由 AC 引用覆盖，绝不靠叙述相似。某条 story 的文本明显服务某 FR、其 AC 却没引用，就是一条 finding（`area: stories`、`route: diy-epics-stories`）——引用才是契约。

**反方向。** 源工作流还会点出史诗里声称、PRD 却从未要求的 FR。diyc 只裁 AC `refs` 的解析，故意放着 `epics.feature_refs` 与 `stories.epic` 不管（`diyc_check_docs.py:12` —— 不在那次裁定的范围内），所以搭矩阵时若见某 epic 声称的 feature ID（`F-x`）`prd.yaml` 没定义、或某 story 点了不存在的 epic（`E-x`），就是一条 finding，`route: diy-epics-stories`。就在矩阵旁边报告你看到的——绝不为此重扫全文档集。

## 每个缺口都要记录（源 step-3 §5）

对每条未覆盖的 FR：

- FR ID 与它为什么要紧——必须级 FR 没有 AC，就无法干净地进冲刺（diy-sprint 的门会挡住，或者活儿静默掉地上）；
- 影响，用大白话写；
- 建议：该由哪个 epic 承接，或者 PRD 应当撤下它。

**缺口 finding 的映射**（`area` 是硬枚举，填错卡终门）：

| 缺口类型 | `area` | `route` |
|---|---|---|
| AC 该引未引（story 文本服务某 FR，其 AC 没引用） | `stories` | `diy-epics-stories` |
| 无任何 epic/story 承接 | `epics` | `diy-epics-stories` |
| 该 FR 应从 PRD 撤下 | `prd` | `diy-prd` |

**Skip line 先于判档**（B7）：应该级 FR 未覆盖时，先读 `stories.yaml` 顶层 `notes:` 里逐行的 skip line（`<FR-x.y>: <为什么故意不覆盖>`）——有 skip line = 已刻意声明，不落 finding；没有 skip line 的才按产品价值判档（仍未覆盖且有产品价值 → `高`）。

Severity：未覆盖的**必须**级 FR → `严重`；未覆盖的应该/可选 FR 有真实产品价值 → `高`；刻意推迟或低价值 → `中`/`低`，理由写进 `message`。

## 覆盖统计

把 `coverage` 原样照抄进记录——终门检查 `must_frs == covered + len(gaps)`。用一行向人报比例：`covered / must_frs`。

## 播报与下一步

读全 `./04-ux-alignment.md` 并照做。
