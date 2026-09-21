---
name: diy-build-loop
description: Drive ONE sprint task from its current state to a terminal state (已完成/已阻塞) in a single invocation - the dev loop (TDD red/green per diy-dev), the review layers (per diy-review), and bounded rework rounds, all in one run. Writes every state transition back to sprint.yaml immediately (HALT protocol) so an external runner can resume from the breakpoint. Ambiguity it cannot resolve itself becomes blocked with a named reason - never spin. Use when the user says "run one iteration" / "iterate this task", or when the runner invokes it headless.
# ↑ 中文：一次调用把一个冲刺任务从当前状态推到终态（`已完成` 或 `已阻塞`）——dev 环（按 diy-dev 的红/绿 TDD）、审查层（按 diy-review）、有上限的返工轮，全在这一次运行里跑完。每次状态迁移立刻写回 sprint.yaml（HALT 协议），外部 runner 可从断点续跑。自己解不了的歧义转 `已阻塞` 并点名理由——绝不空转。用户说「跑一轮迭代」「迭代这个任务」，或 runner 无头调用它时使用。
phase: 4-implementation
precededBy: [diy-sprint]
followedBy: []
required: false
line: mainline
outputs: —
---

# diy-build-loop — 单次迭代（编码→自测→审查→修复，YAML 单一源）

你是迭代驱动者。输入：`sprint.yaml` + 一个目标任务。你在本次运行内编排 diy-dev 与 diy-review 的纪律；任务必须在本轮以终态（`已完成` 或 `已阻塞`）收场，且每次迁移都已写进 sprint.yaml。下一个任务不由你挑——调度归 runner（或用户），见规则。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（notes、`blocked_reason`、review 块的 finding note）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 硬门：`{output_dir}/sprint.yaml` 的 `project.status: 已定稿`。不满足 → 停下，一行说明缺什么，路由 `diy-sprint`。
3. 定目标：显式 story ID（本次调用的参数——交互侧由用户给出，无头侧由 runner 的提示词给出）；没有就取第一条非终态任务。`已完成` / `已阻塞` 的目标一律拒绝并点明其状态——终态即无活可干。
4. TDD 门（继承自 diy-dev）：`test_refs` 每一条都要在 test-plan.yaml 里解析得到；解析不到 → 置 `已阻塞`，`blocked_reason` 点名那些缺失/损坏的 TC ID（AC-9.2：歧义转阻塞，不靠猜）——HALT 写 `transition --to 已阻塞 --reason`（见 HALT 协议），零实现产出。`test_refs` 为空只有在该 story 于 test-plan.yaml 中确有 TC 时才算违规（引用集未同步）；AC 缺口全部裁 `已豁免` / `接受缺口` 的故事没有 TC，`test_refs: []` 是合法记录。

## 工作流

全局纪律：本次运行一次跑到底，不在步骤中间提问（无头侧无人可答）——解不动的歧义转 `已阻塞` 并点名理由，绝不空转。

### 单次运行协议

（下文 `diyc.py` 指代完整调用 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py"`。）

```
resume-at = 待办 ? dev : (进行中 ? dev : 待审查)
rounds = 既有任务条目的 loop.rounds（缺省 0）—— 中断恢复从中断时的轮次续算，不重置
if resume-at == dev:
    待办 → 进行中   （HALT：diyc.py transition --to 进行中 --rounds <rounds>）
    dev 阶段：逐条跑 test_refs 的 TC —— 红线、最小实现、static_checks（diyc.py static）、绿线（HALT：diyc.py green —— 证据 + test-plan 回填，一个批次）
    进行中 → 待审查    （HALT：diyc.py transition --to 待审查 --rounds <rounds>）
loop:
    审查阶段：按 diy-review 跑 L1-L4 层 + 路由；写 review 块（HALT 写）
    通过  → 已完成            （HALT：diyc.py done --rounds <rounds> —— 状态 + stories.yaml + test-plan.yaml，一个批次）；停
    失败:
        若有 finding 路由到 规格缺陷 → 已阻塞（HALT：diyc.py transition --to 已阻塞 --reason "<引文>" --rounds <rounds>）；停
        若 rounds == 2                → 已阻塞（HALT：diyc.py transition --to 已阻塞 --reason "轮次用尽 + 未决 findings" --rounds <rounds>）；停
        rounds += 1
        待审查 → 进行中 （HALT：diyc.py transition --to 进行中 --rounds <rounds>）
        dev 阶段：只返工被路由的 findings；证据按被返工的 TC 追加（diyc.py green）
        进行中 → 待审查 （HALT：diyc.py transition --to 待审查 --rounds <rounds>）；回到 loop
```

任何 dev 阶段里红转不了绿 → `已阻塞`，带 `blocked_reason`（按 diy-dev 的诚实规则）。

### 收尾

1. 一行复述目标、其状态、恢复点；随后按上面的协议跑。
2. 在终态渲染。渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。交互运行报出路径；无头（runner 调起）运行静默渲染、不报路径。渲染是尽力而为：命令不被 harness 放行或失败，就记一行说明继续——渲染失败永不阻断、回退或作废终态写。
3. 收尾用 JSON 回执里的计数：本次跑出的红/绿 TC 数、消耗的返工轮数、按路由分的 findings、终态状态 + 理由；若阻塞，点名确切的解除步骤（改规格 → diy-test-design；或澄清意图 → 带参数重跑）。

## 结构

`{output_dir}/sprint.yaml` 的任务条目新增（evidence / review 块形状见 diy-dev / diy-review）：

```yaml
  - story: S-9
    status: 已完成|已阻塞
    loop:                         # 由 diy-build-loop 写：中途每次 HALT 写 {at, rounds}；outcome 只在终态出现
      at: 2026-09-09              # 最近一次 HALT 写的日子
      rounds: 0-2                 # 本次运行已消耗的返工轮次（恢复时从此续算，不重置）
      outcome: 已完成|已阻塞        # 仅终态写入
    blocked_reason: string        # outcome 为 已阻塞 时必有：点名缺口 / 规格缺陷引文 / 轮次用尽
```

## 规则

1. **只编排，不复制。** dev 阶段行为（先红后绿、最小实现、trace 注释、证据行、绿前 `static_checks`）严格照 diy-dev；审查阶段行为（L1-L4 层、四条路由、判决规则）严格照 diy-review。
2. **要么终态，要么不结束。** 本次运行只以目标 `已完成` 或 `已阻塞` 收场（AC-9.1）。
3. **HALT 协议（FR-3.6）。** 每次状态迁移在发生的那一刻写进 sprint.yaml，并 bump `project.updated`（刷今天）——由 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to <状态> [--reason TEXT] [--rounds N] --json` 执行；`待审查→已完成` 例外，只有 `done` 命令能写。每次 HALT 写都带上当前返工轮次 `--rounds N`，中断也不丢；`loop.outcome` 只在终态出现（`已阻塞` 经 `transition --to 已阻塞`，`已完成` 经 `done`）。任何时刻中断，盘上留下的都是真实状态，下一次调用从它恢复（幂等：既有证据条目保留，只跑缺失的 TC）。
4. **返工轮次有上限、跨运行续算。** 封顶 2 轮（R-4 上限）；`rounds` 取既有 `loop.rounds` 续算、中断恢复**不重置**；到顶仍未决 → `已阻塞`，`blocked_reason` 点名 findings 与轮次。
5. **规格缺陷 → 已阻塞。** 修 stories.yaml / test-plan.yaml 归人与上游技能，不归执行者。
6. **自动模式不跑证伪轮。** diy-review 可选的收尾证伪轮只由用户触发，本技能不跑；也不额外记录——它没跑不算 finding。
7. **写范围收窄。** 只写目标任务的条目：周期里的各状态、`loop` 摘要，以及其阶段产出的 evidence / review 块。绝不碰其他任务，绝不改写 `test_refs`。
8. **终态写抵达真源——真源回填（BUG-012）。** `done` 命令（`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" done --story <S-x> --rounds N --json`）把 `待审查 → 已完成` 连同回填当一个原子批次做完：sprint.yaml 里任务 `status: 已完成` 且 `loop: {at, rounds, outcome: 已完成}`，stories.yaml 里该故事 `status: 已完成`，test-plan.yaml 里本次跑绿的每个 TC `status: 通过`（dev 阶段已按 diy-dev 写过，终态写做对账），并 bump 所有被触及的 `project.updated`。`已阻塞` 只是 sprint 层结论——不写 `stories.yaml`、不写 `test-plan.yaml`：故事未交付，什么也不算通过。**为什么：** 2026-09-13 证伪轮发现无头链已到 sprint 终态、真源却停在 `待办`。
9. **调度归 runner。** 无头串行驱动由 `runner.py` 负责（安装形态 `.claude/skills/diy-tools/scripts/runner.py`，**由人手动执行**）——签名 `python "{project-root}/.claude/skills/diy-tools/scripts/runner.py" [--project-root <目录>] [--instance <实例名>] [--claude-cmd <命令…>] [--max-retries N] [--allow <白名单条目>] [--deny <拒止条目>] [--skip-augment | --augment-only | --reopen-failed]`。示例：`python "{project-root}/.claude/skills/diy-tools/scripts/runner.py" --project-root "{project-root}"`。它逐条 spawn 本技能的无头运行；本技能自己绝不挑下一个任务。
10. 任何判断性取值都在 YAML 值上带 `[假设]` 前缀。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。
