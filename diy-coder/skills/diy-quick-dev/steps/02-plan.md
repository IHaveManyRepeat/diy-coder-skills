# Step 2 — 计划与批准

Progress: `Clarify & Route → [Plan] → Implement → Review → Present`

**Read (input):** 本次运行的草稿记录；意图触及的产物与代码。
**Write (output):** `{output_dir}/spec.yaml` 里填好的记录——调研结果、`code_map` / `tasks` / `acceptance` / `verification` / `io_matrix` / `design_notes`，随后 `status: 就绪`。

## 草稿续跑检查

若记录是从 `草稿` 续跑，读它并逐字保留其 `intent` 与 `boundaries`——冻结核务必原样保存，绝不重打。

## 调研

读改动将触及的代码与约束它的产物。有子代理时把深探隔离在子代理里、只取精炼摘要（上下文雪球正是此纪律防的失败模式）。按 ID 与 `path` 引用——把文档正文或代码块贴进记录是缺陷，不是周全。

## 填记录

- `io_matrix` —— 每个有意义的输入/输出场景一行（`scenario` / `input` / `expected` / `error_handling`）。没有任何有意义的 I/O 场景时**整键省略**——绝不写「N/A」或「None」。
- `code_map` —— 改动触及的每个文件一条（`path` / `role`），从调研结果填入，免得后来的人盲搜代码库。
- `tasks` —— `task`（动作）/ `file`（精确路径）/ `done: false`。优先一文件一任务；拆开会显得人工时，把紧耦合的改动并为一条。
- `acceptance` —— `given` / `when` / `then`，各一行。有 `io_matrix` 时补一条测试其边界情况的任务；acceptance 覆盖矩阵覆盖不了的系统级行为。
- `verification.commands` —— 每条验收判据至少一条 `{cmd, expect}`（优先 CLI 命令；确实无命令可用时才 `manual`）。这是轻量通道的硬底线：没有命令就没有证据，没有证据就没有审查。
- `design_notes` —— 仅在做法不显然时写；否则整键省略。

## 自审（READY FOR DEVELOPMENT）

- **可执行** —— 每条任务都点名文件路径与具体动作。
- **有逻辑** —— 任务按依赖排序。
- **可测** —— 每条验收都用 Given/When/Then，且配一条验证命令。
- **完整** —— 无占位符、无 TBD、无被静默搁置的未决问题。

意图缺口不靠幻想抹平：HALT 并问。**`spec body` ＝ 本次写入记录的正文**（`intent` / `boundaries` / `io_matrix` / `tasks` / `acceptance` / `verification` / `design_notes` 的字符串值，不含键名与 ID）；**计数口径 ＝ 字符数 ÷ 2 的近似**（中英混排的保守值）。超过 ~1600 即示出计数并 HALT：`[S] 拆分——切掉次要目标`（追加进 `deferred`，然后按收窄的范围**重新生成**记录——不做外科手术式切段）| `[K] 全留——接受风险`。计数只用于给出拆分建议，**计数误差不构成阻断**。

## CHECKPOINT 1

呈出摘要，然后 HALT：`[A] 批准` | `[E] 修改`。spec 路径用 project-root 相对形式显示（不带前导 `/`）。批准之前，人可以在此提问或要求修改。更深的挑战轮（elicitation / party mode）已由 `diy-elicit` / `diy-party-mode` 承接——就地调用即可，不必单开会话。

- **A** —— 从磁盘重读记录。
  - **缺失：** HALT。告诉人记录没了并 STOP——什么都不写、不设任何状态、不往下走。下面全部不跑。
  - **自写入后有变动：** 承认外部编辑，简报改了什么，用更新后的版本继续。
  - 然后把记录置 `status: 就绪`。`intent` 段此刻起锁定——此后只有人能重新议它。→ Step 3。
- **E** —— 应用所要求的修改，然后回到 CHECKPOINT 1。

## 播报与下一步

读全并照做 `./03-implement.md`。
