# Step 3 — 实现与实测

Progress: `Clarify & Route → Plan → [Implement] → Review → Present`

**Read (input):** `status: 就绪` 的记录；它的 `code_map` 与 `tasks`；那些路径点名的代码。
**Write (output):** 代码；记录的 `baseline`、`status: 进行中`、`tasks[].done`、`verification.commands[].result`。

## 前置

记录在盘上且 `status: 就绪`（续跑可能见到 `进行中`——从未完成的任务接着做）。否则 HALT 并问要做哪条记录；绝不替人猜。

## baseline 先行

记下 `baseline` = 当前 HEAD 提交，版本控制不可用时记 `NO_VCS`——**必须在首次改动代码之前**。审查（第 4 步）对着它取 diff。

## 接下记录

把记录置 `status: 进行中`。这是 spec 局部状态：改动在故事环之外，别处什么都不动。当改动同时触及 `sprint.yaml` 里已有的故事时，那个任务的状态仍由 diyc 拥有——用 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type sprint --json` 核跨文档真相并转述回执；绝不从这里写 `sprint.yaml`。（源技能在此处同步 `sprint-status.yaml`；diy 没有这个文件。）

## 实现

- 满足验收判据的最少代码，遵循项目既有架构、模式与约定——适用的架构决策（`D-x`）从 `architecture.yaml` 读，绝不重发明。
- 守 `boundaries`：`总是` 是不变量，`从不` 是禁行，`先问` 下的任何事在发生前 HALT 交人决定。
- diff 保持在 `code_map` 内；发现需要但未列出的文件是对记录的修订（若被密封的段有错，就是第 4 步的 `规格缺陷` 回环——绝不静默多改）。
- 追溯注释（`# trace: …`，diy-dev 的纪律）适用于改动触及 sprint 环内、ID 可解析的代码。环外没有可指的 `S-x` / `AC-x.y` / `TC-x.y.z`——不要铸一个；宁可不写 trace 行，也不写假的。

## 自检

离开本步之前，核验每条 `tasks[]` 都已完成并置 `done: true`。未完成的任务现在就做完，绝不静默延后。

## 跑验证

逐条跑 `verification.commands[].cmd` 并写下真实 `result`（命令实际打印了什么，通过或失败）。失败的命令要么在此修好、要么如实记录——绝不弱化、绝不省略、绝不想象。`manual` 条目仅在确实没有 CLI 检查可用时记录。`verification.commands` 为空时记录到不了 `审查中`（引擎拒绝：`EMPTY_FIELD`）。

## 播报与下一步

读全并照做 `./04-review.md`。
