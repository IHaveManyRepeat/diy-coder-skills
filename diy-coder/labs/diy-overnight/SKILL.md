---
name: diy-overnight
description: Overnight unattended task-queue driver: consume a pre-approved queue.yaml, run one task per branch off a chain (overnight/YYYY-MM-DD/<task-id>), commit only on full-green, timeboxed with deadline/grace/timeout fuses, write a morning report for ordered per-branch human review. Use when the user says "夜队列开工", "跑夜班", or starts an overnight run.
# ↑ 中文：夜间串行队列驱动者——消费已批准的 queue.yaml，一任务一分支串成链，全量绿才提交，时间盒带死线/宽限/超时熔断，产出晨报供用户按序逐支审核。用户说「夜队列开工」「跑夜班」或发起夜间运行时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: —
---

# diy-overnight — 夜间串行队列（无人值守推进已裁任务）

你是夜班执行者。输入：用户在激活时**指定路径**的已填好队列（本仓常用 `{仓根}/.analysis/overnight/queue.yaml`，非写死）——**填队列不归你管**（用户与主会话在开工前裁任务、定预估），你只消费。你在一次运行内串行把队列任务推成分支链上的绿点；天亮晨报交用户按序逐支审。**你不裁断任何新问题**——遇裁断点还原跳过。

## 队列格式

```yaml
test_cmd: "<该仓全量测试命令>"
base: null                    # start 写入（HEAD sha）
tonight: null                 # start 写入（date/deadline/五数值/circuit_count）
tasks:
  - id: Q-001                 # 队列内唯一＝分支名尾段
    title: <一句话>
    basis: <裁断依据·引用>
    scope: [<允许改动的文件/目录>]
    estimate_min: 40
    verify: []                # 除全量绿外的专项验收（如 sync 冒烟），无则空
    status: 待跑              # 待跑|进行中|完成|顺延|跳过|阻塞
    result: null              # 完成后 {branch, commit, tests}
    reason: null              # 顺延/跳过/阻塞原因
archive: []                   # 已审结归档条目
runs: []                      # 每晚一行：date/base/deadline/完成计数
```

入队四条件（开工前置时核）：①全裁断——当晚零裁断余地，「随批核/待裁」子点先裁掉否则不入队；②改动面明确且与他批无交叠；③可独立 revert；④共面文档（如审查底单）仅在任务本体就是该文档作业时才入 scope。

## 激活时

1. 取用户指定的队列路径（激活时未指定则询）；定位仓根：`git rev-parse --show-toplevel`；队列缺失或无条目 → 停，一行说明。
2. 只碰 `status` 为 待跑/顺延/跳过 的条目；完成/阻塞/进行中之外的状态不重开（阻塞留待用户裁）。
3. **开工门是唯一交互点**——前置五步见下，用户说「开工」前不写任何 git 状态。

## 开工前置（交互·用户在场）

1. 队列整肃：上晚完成条目归档（移 `archive`）；顺延/跳过/阻塞 留队重排——**队列顺序＝执行顺序＝晨报审核顺序**。
2. `git status`：树不净 → 停，列未提交面，交用户裁处置（提交／stash／明示忽略）；用户明示后才继续。
3. 基线自证：跑 `test_cmd` 全量绿（HEAD 自证，买归因干净）。基线红 → 停，报红，不开工。
4. 呈队列顺序＋estimate 合计＋deadline 建议（缺省次日 07:00）→ 用户可逐项改五数值（deadline／宽限 45min／超时 2×estimate／连跳停机 2／测试缓冲 15min）。
5. 用户说「开工」→ `python <技能同目录>/run_queue.py start --queue <路径> [--deadline ... --grace ... --timeout-x ... --circuit ... --buffer ...]` 写 `base`＝HEAD＋`tonight` 五数值（下文各步 `run_queue.py` 均指该同目录脚本，调用时带实际路径）。

## 执行循环（无人值守）

**分层（agent team）**：主会话常驻当调度员，只做三件事——调 runner 领任务/回报、派 subagent、标阻塞；机械循环（起跑门、建分支、状态写回、失败还原、熔断计数、晨报骨架）全部由同目录 `run_queue.py` 强制执行。每任务的实施由 subagent 承担——按任务需要派单个 fresh subagent、多个 subagent 分工、或组 agent team 协作完成，子代理上下文干完即弃，调度侧只收 `{branch, commit, tests, reason}` 回报，不吸收过程上下文。

对队列按序每个可跑条目：

1. **领任务**：`python run_queue.py gate --queue <路径>`（缺省取队列序第一个 `待跑`，跨晚重排条目用 `--id` 显式领）——起跑门不过 → 脚本把余下待跑全转 `顺延`，走收尾；过 → 脚本建分支＋置 `进行中`，输出任务详情（id／branch／scope／verify／basis）。
2. 只动 `scope` 内文件（gate 输出即白名单）。
3. 派 subagent 实施 → `test_cmd` 全量绿 → 一任务一笔提交（信息 `feat|refactor|fix: 夜队列 <id> <title>`，体：改动面／basis／测试数）→ `verify` 逐项过 → `python run_queue.py done --queue <路径> --id <id> --tests <结果>` 写 `result` 置 `完成`。
4. **失败路径**（红修不动／超时 2×estimate／裁断点／子代理上下文超限）：`python run_queue.py fail --queue <路径> --id <id> --cause red|timeout|context|ruling --reason <要点>`——脚本执行零痕迹还原（检回链基点＋清 scope 内自产未跟踪＋删失败分支）并置 `跳过`/`阻塞`：`ruling`→`阻塞`（reason 点名缺口/引文），**绝不代裁**；`context`→`跳过(子代理超限)`，不续做半成品。
5. **连跳熔断**：脚本计数（仅 `red`/`timeout` 计，`context`/`interrupt` 不计），连续 2 → 返回 `circuit: true` → 余下转 `顺延`，收尾。

## 收尾

1. `python run_queue.py report --queue <路径>`——脚本写晨报落**队列同目录** `report-<YYYY-MM-DD>.md`（不入库：头行 base／deadline／运行窗／计数；表 `| 任务 | 状态 | 分支 | commit | 测试 | 备注 |` 队列序＝审核序；顺延/跳过/阻塞逐条原因；阻塞待裁点收集；尾附早审指引），并幂等追加 `runs` 运行行。
2. 完成条目留队待用户审后归档。
3. **不删分支、不动 dev、不 push**。

## 中断恢复

会话崩溃后续跑：读队列 `runs` 末行＋分支链（最后一支＝最新绿点）→ `进行中` 条目跑 `fail --cause interrupt --reason 中断还原`（脚本还原＋置 `跳过`，不续做半成品）→ 仍在起跑门内才继续循环。

## 早审顺序（晨报尾块照抄给用户）

队列序逐支，每支三步：

1. **看变更**：`git diff <前支tip>..<本支tip>`（首支＝`git diff <base>..<首支>`）；可 `git checkout <支>` 亲验跑 `test_cmd`。
2. **裁断**：过 → `git merge <支> --no-ff` 入 dev，下一支；否 → 不合、记待办（含分支名，现场保留供追查）、继续下一支（与已合好件交叠冲突则 cherry-pick 好件单笔）；拿不准 → 停，余支记待办。
3. **全过完**：删链（`git branch -d overnight/<日期>/*`）＋归档队列完成条目。

## 规则

1. **只消费队列，不填队列**；队列外的发现记晨报，不顺手修。
2. **提交点＝全量绿**；无半红提交；失败零痕迹。
3. **不裁断**：新歧义＝`阻塞`＋reason，等用户。
4. **scope 外零触碰**；verify 专项照过。
5. 时间判断取本地时钟；deadline 及四参数缺省值开工时用户可逐项改。

- **精准简练。** 晨报每条一事件；引 id 不复述队列；不写无信息量套话。
