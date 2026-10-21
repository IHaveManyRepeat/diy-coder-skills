---
name: diy-overnight
description: Overnight unattended task-queue driver: consume a pre-approved queue.yaml, run one task per branch off a chain (overnight/YYYY-MM-DD/<task-id>), commit only on full-green, timeboxed with deadline/grace/timeout fuses, relay through the `next` queue chain while time permits, write a morning report for ordered per-branch human review. Use when the user says "夜队列开工", "跑夜班", or starts an overnight run.
# ↑ 中文：夜间串行队列驱动者——消费已批准的 queue.yaml，一任务一分支串成链，全量绿才提交，时间盒带死线/宽限/超时熔断，时间充裕时按 next 链自动接力后续队列，产出晨报供用户按序逐支审核。用户说「夜队列开工」「跑夜班」或发起夜间运行时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: —
---

# diy-overnight — 夜间串行队列（无人值守推进已裁任务）

你是夜班执行者。输入：用户在激活时**指定路径**的已填好队列（命名规范 `queue-<YYYY-MM-DD-HHMMSS>.yaml`，本仓常用目录 `{仓根}/.analysis/overnight/`，非写死；旧名如 `queue.yaml` 照跑）——**填队列不归你管**（用户与主会话在开工前裁任务、定预估），你只消费。队列可经顶层 `next` 登记后续队列：当前队列跑完且时间档放得下时，自动接力继续（见执行循环）。你在一次运行内串行把队列（含接力链）任务推成分支链上的绿点；天亮晨报交用户按序逐支审。**你不裁断任何新问题**——遇裁断点还原跳过。

## 队列格式

```yaml
next: []                      # 可选·接力序（路径相对本文件目录）；缺省 []＝不接力
test_cmd: "<该仓全量测试命令>"
base: null                    # start/relay 写入（HEAD sha）
tonight: null                 # start/relay 写入（date/deadline/五数值/circuit_count/started_at/baseline_min；relay 时另写 relay_from＝源队列）
tasks:
  - id: Q-001                 # 队列内唯一＝分支名尾段
    title: <一句话>
    basis: <裁断依据·引用>
    scope: [<允许改动的文件/目录>]
    estimate_min: 40
    verify: []                # 除全量绿外的专项验收（如 sync 冒烟），无则空
    status: 待跑              # 待跑|进行中|完成|顺延|跳过|阻塞
    result: null              # 完成 {branch,commit,tests,tests_count,elapsed_sec,elapsed_min,test_sec,ratio,phases}；失败 {elapsed_sec,cause[,branch,commit,kept]}
    reason: null              # 顺延/跳过/阻塞原因
    started_at: null          # gate 写入（ISO 秒）
    done_at: null             # done 写入（ISO 秒）
archive: []                   # 已审结归档条目
runs: []                      # 每晚一行：date/base/deadline/完成计数/estimate_合计/实际_合计_秒/失败分布/熔断
```

`test_cmd` 本仓用：`cd diy-coder && python run_tests.py`——有 `pytest-xdist` 时并行（按文件整包分配，防 `os.chdir`／模块级状态串扰），缺失时自动安装，安装失败按用户裁断重试或回退串行。排障也可直跑 `python -m pytest tests -q` 串行。

命名：队列文件＝`queue-<YYYY-MM-DD-HHMMSS>.yaml`（创建时间·年月日-时分秒，一晚一文件）；晨报与队列文件同名对应＝`report-<队列文件stem>.md`（如 `report-queue-2026-10-19-230830.md`）。旧名队列照跑，晨报按 `report-<其stem>.md`。

入队四条件（开工前置时核）：①全裁断——当晚零裁断余地，「随批核/待裁」子点先裁掉否则不入队；②改动面明确且与他批无交叠；③可独立 revert；④共面文档（如审查底单）仅在任务本体就是该文档作业时才入 scope。

## 激活时

1. 取用户指定的队列路径（激活时未指定则询）；定位仓根：`git rev-parse --show-toplevel`；队列缺失或无条目 → 停，一行说明。该队列 `next` 有登记的，后续队列一并纳入本次运行（接力由脚本自动跟随，不再交互）。
2. 只碰 `status` 为 待跑/顺延/跳过 的条目；完成/阻塞/进行中不重开——阻塞条目本晚不再处理，越过继续其余条目（留晨报待裁，不等待用户）。
3. **开工权只归用户**——激活、队列就绪、开工前置做完，均不构成开工依据；用户说「开工」前不写任何 git 状态，`run_queue.py start` 不得调用。

## 开工前置（交互·用户在场）

1. 队列整肃：上晚完成条目归档（移 `archive`）；顺延/跳过/阻塞 留队重排——**队列顺序＝执行顺序＝晨报审核顺序**。
2. `git status`：树不净 → 停，列未提交面，交用户裁处置（提交／stash／明示忽略）；用户明示后才继续。
3. 基线自证：跑 `test_cmd` 全量绿（HEAD 自证，买归因干净）。基线红 → 停，报红，不开工。
4. 呈**接力链**（首队列＋`next` 登记的后续队列，各列任务序与 estimate 合计）＋deadline 建议（缺省次日 07:00）→ 用户可逐项改五数值（deadline／宽限 45min／超时 2×estimate／连跳停机 2／测试缓冲 15min；后续队列继承本档）。
5. **停手交提示词**：第 4 步呈完即结束本轮，给用户一段可直接粘贴的开工提示词（如「使用 diy-overnight，队列 `<绝对路径>`，开工」＋建议五数值）——由用户自己决定何时开工，不得自动进入下一步。
6. 用户明示「开工」→ `python <技能同目录>/run_queue.py start --queue <路径> [--deadline ... --grace ... --timeout-x ... --circuit ... --buffer ... --baseline-min <基线自证墙钟分钟>]` 写 `base`＝HEAD＋`tonight`（五数值＋started_at＋baseline_min；基线分钟＝第 3 步那次全量的墙钟，缺省 null）（下文各步 `run_queue.py` 均指该同目录脚本，调用时带实际路径）。

## 执行循环（无人值守）

**分层（agent team）**：主会话常驻当调度员，只做三件事——调 runner 领任务/回报、派 subagent、标阻塞；机械循环（起跑门、建分支、状态写回、全量绿权威提交门、失败还原、熔断计数、接力判定、晨报骨架）全部由同目录 `run_queue.py` 强制执行。每任务的实施由 subagent 承担——按任务需要派单个 fresh subagent、多个 subagent 分工、或组 agent team 协作完成，子代理上下文干完即弃，调度侧只收 `{branch, commit, tests, reason, phases}` 回报，不吸收过程上下文（`phases`＝subagent 自报阶段耗时整数分钟：实施/自测/verify）。

**连续运行铁律（2026-10-21 裁）**：从 `start` 到整晚收尾是一个不间断执行段——期间**禁止向用户提问、禁止等待裁定、禁止以汇报进度为由结束回合**；中间结果只写队列与晨报，天亮后由晨报交裁。任何「拿不准」都不得变成停等。

**裁断点判据**：须 `ruling` 的只有硬项——需改 `scope`／`basis` 前提不成立／与已裁口径冲突／需动共享面或他任务／产品语义二选一／队列外发现影响本任务；实现细节（命名、等价写法、内部结构）自行决定，不阻塞，晨报备注一笔。

**子代理委派契约**（每条委派提示词原样附上）：不得向用户提问或等待；不得提交、不动 `scope` 外；遇裁断点立即停手，回报 `{status:"ruling", point, recommend, evidence}`（`point`＝卡点一句话＋候选选项，`evidence`＝文件:行或原文引用），不得继续猜测实施；其余情况照常完成并回报实施／自测结果。

对当前队列按序每个可跑条目：

1. **领任务**：`python run_queue.py gate --queue <路径>`（缺省取队列序第一个 `待跑`，跨晚重排条目用 `--id` 显式领）——起跑门不过 → 脚本把余下待跑全转 `顺延`，走队列退出与接力；过 → 脚本建分支＋置 `进行中`，输出任务详情（id／branch／scope／verify／basis）。
2. 只动 `scope` 内文件（gate 输出即白名单）。
3. 派 subagent 实施＋自查自测（权威门在脚本，subagent 自测只为自身迭代快）→ `verify` 逐项过 → `python run_queue.py done --queue <路径> --id <id> --type feat|fix|refactor --tests <结果> [--phases 实施=25,自测=8,verify=2]`——脚本跑 `test_cmd` 计时（`test_sec`），全量绿才 stage `scope`＋统一提交（`<type>: 夜队列 <id> <title>`，体：scope／basis／tests＋全量秒数）并写 `result`（done_at／elapsed_sec／elapsed_min／test_sec／ratio／tests_count／phases）置 `完成`；红 → 不提交不写盘、返回红详情（`started_at` 继续计时，修复损耗如实入账）。
4. **红回修循环**：`done` 红 → 把红详情反馈 subagent 修 → 重跑 `done`；修复 2 次仍红 → 第 3 次 `python run_queue.py fail --queue <路径> --id <id> --cause red --keep-branch --reason <红要点>`——脚本在任务分支打红标 WIP 提交（`wip: 夜队列 <id> <title>（三次仍红·留审）`）→ 切回链基点（分支保留，绿链零污染）→ 置 `阻塞`，晨报待裁点带 checkout 指引。
5. **其他失败路径**（裁断点／子代理上下文超限／超时修不动）：`python run_queue.py fail --queue <路径> --id <id> --cause timeout|context|interrupt|ruling --reason <要点>`（不带 `--keep-branch`＝零痕迹还原：检回链基点＋清 scope 内自产未跟踪＋删失败分支；`result` 记 `{elapsed_sec, cause}`）：`ruling`→`阻塞`（reason 点名缺口/引文），**绝不代裁**；落盘后**立即回第 1 步领下一条**，不向用户报告、不等待裁定；`context`→`跳过(子代理超限)`，不续做半成品；`timeout`→`跳过`。
6. **连跳熔断**：脚本计数（仅 `red`/`timeout` 计，`context`/`interrupt` 不计），连续 2 → 返回 `circuit: true` → 余下转 `顺延`，整晚收尾（不接力）。

**队列退出与接力**（当前队列无可跑条目后）：

1. `python run_queue.py report --queue <当前队列>` 写本队列晨报（`report-<队列stem>.md`，幂等）。
2. 熔断已达阈值（上一步 `circuit:true`）→ 不接力，整晚收尾。
3. `python run_queue.py relay --queue <当前队列>`：`ok:true` → 以输出 `queue` 为新当前队列，继续上面的逐任务循环（**不再调 start**——relay 已写入 base/tonight/relay_from）；`ok:false`（无后续／起跑门不过／熔断）→ 整晚收尾。

接力判定（`next` 顺序、继承时间档、首个待跑任务过门、防环、树净）全由脚本执行，你不自行判断时间。

## 收尾

1. 每个队列退出时已各写晨报（`report-<队列文件stem>.md`，队列同目录，不入库：头行 base／deadline／基线测试／运行窗／计数；表 `| 任务 | 状态 | 预估 | 耗时 | 偏差 | 分支 | commit | 测试 | 备注 |` 队列序＝审核序，偏差＝elapsed/estimate 倍率；顺延/跳过/阻塞逐条原因；阻塞待裁点收集（红标留审条目带 checkout 指引）；尾附早审指引），并幂等追加 `runs` 运行行（含 estimate_合计／实际_合计_秒／失败分布／熔断）。整晚收尾时汇总各份晨报路径与审核顺序（接力链序）。
2. 完成条目留队待用户审后归档。
3. **不删分支、不动 dev、不 push**。
4. **最后一步＝交提示词**：晨报写完即停手，给用户一段可直接粘贴的下一晚开工提示词（队列路径＋建议参数），由用户自己决定何时开工；不自动续跑。

## 中断恢复

会话崩溃后续跑：读队列 `runs` 末行＋分支链（最后一支＝最新绿点）→ `进行中` 条目跑 `fail --cause interrupt --reason 中断还原`（脚本还原＋置 `跳过`，不续做半成品）→ 仍在起跑门内才继续循环。接力链中崩溃时，先定位有 `进行中` 条目的队列（即当前活跃队列）在其上处置；已收尾队列晨报已落盘，其 `next` 接力照常。

## 早审顺序（晨报尾块照抄给用户）

总审核顺序＝接力链序（前队列全部审完再审后队列）；每队列内按队列序逐支，每支三步：

1. **看变更**：`git diff <前支tip>..<本支tip>`（首支＝`git diff <base>..<首支>`）；可 `git checkout <支>` 亲验跑 `test_cmd`。
2. **裁断**：过 → `git merge <支> --no-ff` 入 dev，下一支；否 → 不合、记待办（含分支名，现场保留供追查）、继续下一支（与已合好件交叠冲突则 cherry-pick 好件单笔）；拿不准 → 停，余支记待办。
3. **全过完**：删链（`git branch -d overnight/<开工日>/*`，接力沿用同一开工日故一条覆盖整晚）＋逐队列归档完成条目。

## 规则

1. **只消费队列，不填队列**；队列外的发现记晨报，不顺手修。
2. **提交点＝done 脚本全量绿**（提交统一由脚本产生，subagent 不自行提交）；无半红入链；失败零痕迹（`--keep-branch` 红标留审除外——只在侧分支，不入绿链）。
3. **不裁断、也不停等**：新歧义＝`fail --cause ruling`＋`阻塞`＋reason，随即继续下一条；夜跑期间禁止向用户提问、等待裁定或为此结束回合。
4. **scope 外零触碰**；verify 专项照过。
5. 时间判断取本地时钟；deadline 及四参数缺省值开工时用户可逐项改。
6. **接力判定归脚本**：时间够不够、熔断、防环、继承时间档一律以 `relay` 输出为准；队列退出必须调 relay（熔断除外），不自行判断。

- **精准简练。** 晨报每条一事件；引 id 不复述队列；不写无信息量套话。
