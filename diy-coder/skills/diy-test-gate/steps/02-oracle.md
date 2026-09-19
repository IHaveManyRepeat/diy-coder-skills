# Step 2 — Oracle（覆盖基准解析）

Progress: `Preflight → [Oracle] → Matrix & Gaps → NFR → Gate → Finish`

**Read (input)：** `collect` 回执的 `items[]`（AC 行，已按 story 过滤）；`{output_dir}/stories.yaml` 的该 story 条目（**只读该 story**，按 ID 定位，不整份通读）。
**Write (output)：** 草稿记录的 `oracle` 与 `coverage.items` 骨架（判定值留在 step 3 复核后回填）。

## oracle 主源：stories.yaml 的 AC

diy 的默认主源**就是** AC——覆盖基准 = 该 story 的验收标准清单，逐条一行。回执 `items[]` 的 `ref` / `story` / `priority` 直接照抄：

- `priority` 由 `prd.yaml` 的 FR priority 推导（`must→P0` / `should→P1` / `could→P2`），一 AC 多 FR **取最高**，无 FR refs → `P2` + warning。推导是引擎做的，你只核对语义（例如 refs 抄错、AC 与 FR 对不上）。
- 覆盖状态（`FULL` / `PARTIAL` / `NONE` / `UNIT-ONLY` / `INTEGRATION-ONLY`）同样来自回执，step 3 复核。

## 降级链（源四级 → diy 保留的三级）

按顺序取第一个可用者，取到即停，并把它记进 `oracle.source`：

| 序 | 源 | diy 形态 | 落 `oracle` |
| --- | --- | --- | --- |
| 1 | 形式化需求 | `stories.yaml` 的 AC（默认主源） | `source: stories`, `confidence: high` |
| 2 | 规格产物 | `stories.yaml` 不可用、但 `prd.yaml` 的 FR 可作基准 | `source: stories`, `confidence: medium`（在 `basis` 说明基准换成 FR） |
| 3 | 合成推断 | 无形式化基准，从路由 / 页面名 / 源码推断旅程 | `source: synthetic`, `confidence: medium|low`，逐条列进 `oracle.inferred` |

**external pointer 类（Jira / Confluence 适配器）已裁剪**，不做；私有知识库与外部 MCP 不在读取面内。

## 合成 oracle 的保守化纪律（2026-09-15 裁定，§4 裁定 4）

- synthetic 推断**默认关闭**：只有用户显式要求「没有正式 AC，按旅程推」时才走第 3 级，且每条推断都要在 `oracle.inferred` 里逐条列出（「推了什么、从哪推的」）。
- `confidence` 不得自封 `high`：推断项没有形式化背书，起点就是 `medium`；只有用户逐条确认后才可写 `high`。
- overlay 后果（引擎在 `check` 强制）：`source: synthetic` 且 `confidence ≠ high` → 该门**至少 `CONCERNS`**，覆盖全绿也不给无条件 PASS。这是设计意图，不要为了拿 PASS 去抬 confidence。
- `oracle.unresolved` 收「解析不出、也没人认领」的条目（例如 AC 文本与任何实现都对不上）——它是给用户的清单，不是垃圾箱。

## 解析不出 → HALT

该 story 无 AC、且用户不接受降级 → **停下来**，不落门产物：

1. 一行说明：哪个 story、为什么解析不出（`stories.yaml` 里该 story 的 `acceptance_criteria` 为空 / 全部无 `refs` / 与实现无对应）。
2. 路由 `diy-epics-stories`（补 AC），或 `diy-prd`（先补 FR）。
3. **不写记录**——半份门记录比没有更坏：它会以「已评估」的姿态被下游读走。

## 把结果写回草稿

补 `oracle`，并把 `coverage.items` 的 `ref` / `story` / `priority` 填好（`coverage` / `tests` 留空，step 3 填）。

读完并执行 `./03-matrix-gaps.md`。
