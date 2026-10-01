# Step — 证伪轮（Falsification，可选）

**Read (input):** `--falsify <story|all>`（接受 `已完成` 目标；`all` = 本冲刺全部已完成任务）；`bug-log.yaml` 的模式；本实现面。
**Write (output):** 命中 → 经 `bug-add` 入库、任务离开 `已完成` → `进行中`（HALT）；干净一轮 → 任务 `note` 记一行。

**证伪轮（可选 —— `--falsify <story|all>`，接受 `已完成` 目标；`all` = 本冲刺全部已完成任务）。** 目标：打破已完成的工作——假定它就有 bug。用 `bug-log.yaml` 的模式瞄准本实现，走非功能清单（性能、用户体验、安全、兼容性、可靠性、边界）问「这个会怎么坏」，并跑临时攻击。命中即经 `bug-add` 入库、路由（`意图缺口` / `小修`），任务离开 `已完成` → `进行中`（HALT 写：`transition --story <S-x> --to 进行中 --json`——入口不变，引擎在该边上 `pop("augment")` 清掉旧判定，与 `runner.py --reopen-failed` 同语义）。干净一轮：任务 `note` 记一行（日期 + 「证伪轮通过」）。
