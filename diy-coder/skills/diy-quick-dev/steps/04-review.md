# Step 4 — 审查与路由

Progress: `Clarify & Route → Plan → Implement → [Review] → Present`

**Read (input):** `status: 进行中` 的记录；自 `baseline` 以来的 diff（含已跟踪与未跟踪）；块级 diff 不够时读改动文件本身。
**Write (output):** 记录的 `review` 块（`rounds` / `findings`）、`规格缺陷` 回环时的 `change_log` 条目、`deferred` 条目，以及下一步的 `status`。

继续之前先把记录置 `status: 审查中`。层与路由都是 diy-review 的——本步只是跑它们；绝不另建第二套审查体系。

## 构造 diff

diff 自 `baseline` 以来的一切（`NO_VCS` → 从对话与文件 mtime 尽力重建）。只读检视：绝不 `git add`、绝不暂存。

## 层

- **L1 正确性.** 实现是否**恰好**做到 `acceptance` 所说——没有缺失的 then 从句，没有未被要求的额外行为？逐条对照。偏离记录的 `boundaries`（`总是` / `从不`）即一条 finding。
- **L2 边界.** 走一遍判据隐含却没写明的失败模式：坏输入、空值/None、并发、错误路径、静默回退。只报真会咬人的未处理情况——噪声不是 finding。
- **L3 覆盖审计.** 每条 `acceptance` 都必须有一条 `verification` 命令，其记录的 `result` 真实且支持其主张。判据没有命令、或结果不支持主张，即一条 finding 并点出 acceptance 序号——绝不靠肉眼重新验收。

有子代理可用时，用与本会话同等的模型能力、不带对话上下文启动它（继承了作者推理的审查者会被锚定），只取回 findings。没有子代理 → 内联跑同一遍；绝不另写审查提示文件（本技能的单一源是 `spec.yaml`）。

## 分类

1. 全部 findings 去重。
2. 每条 finding **恰好路由一次**。四个路由名与含义是 diy-review 的表——权威，绝不在此重述。其中两条在本通道落地不同，因为本通道没有 `stories.yaml` / `test-plan.yaml`：
   - `意图缺口` —— 按 diy-review 的定义：改动与冻结的 `intent` 相抵触或漏掉它。除非只有唯一可能的读法，否则不得推断意图。
   - `规格缺陷` —— diy-review 的目标（修规格、不动代码）在本通道落在记录的**非冻结**段：`boundaries` / `io_matrix` / `code_map` / `tasks` / `acceptance` 有错或含糊时，**被修的是记录**。在 `规格缺陷` 与 `小修` 之间拿不准时，选 `规格缺陷`——规格级修正产出的代码更自洽。
   - `小修` —— 按 diy-review 的定义：小、局部、无需人介入就地修掉。
   - `后置` —— **在此显式收窄**为不是本次改动问题的既有 findings；本次改动造成的真 finding 永不 `后置`。在 `后置` 与丢弃之间拿不准时，丢弃：只延后你有信心为真的 findings。
3. 按级联顺序处理——`意图缺口` / `规格缺陷` 触发回环，其后更轻的 findings 随之作废；每次回环递增 `rounds`；超过 5 即 HALT 并升级给人。

## 应用路由

- **意图缺口** —— 根因在冻结的 `intent` 里。回退代码改动，回环给人重新议意图，然后重跑 `./02-plan.md` → 本步。这次编辑归人所有；你绝不自己改写 `intent`。
- **规格缺陷** —— 根因在 `intent` 之外：非冻结段有错或含糊，所以**被修的是记录，不是代码**。动任何东西之前：抽出 KEEP 指令（哪些是有效的、必须留住）。修订受影响的段并追加**一条**新的 `change_log` 条目（`finding` / `amended` / `avoided` / `keep`），尊重每一条既有条目——绝不编辑它们。然后对着修订后的记录重新推导：回退被这次修订推翻的代码（且只回退那些），再重跑 `./03-implement.md` → 本步。
- **小修** —— 现在就修。这些是唯一能在回环后存活的 findings。
- **后置** —— 把 `{finding, why, date}` 追加进 `deferred`。记档，不阻塞。
- 没有路由的——噪声。静默丢弃，只在汇总里说一声（「N 条已丢弃」）。

写 `review` 块：`rounds`（消耗的回环次数）与 `findings`（`layer` / `route` / `note`，各一行；干净通过时该块可为空）。

## 结构检查

离开之前跑 `python "{project-root}/.claude/skills/diy-quick-dev/scripts/spec.py" check --project-root "{project-root}" --output-dir "{output_dir}" --json`——exit 0 表示记录（含 `review` 块）结构合法。修完违规再重跑。

## 播报与下一步

读全并照做 `./05-present.md`。
