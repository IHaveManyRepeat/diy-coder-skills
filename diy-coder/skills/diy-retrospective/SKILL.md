---
name: diy-retrospective
description: 'Post-epic review to extract lessons and assess success. Use when the user says "run a retrospective" or "lets retro the epic [epic]". Produces one record per epic in retrospective.yaml.'
# ↑ 中文：epic 收尾回顾——提炼教训、评估成败。输入一个已交付 epic 的证据链（由引擎机械采集），产出一条 `{output_dir}/retrospective.yaml` 记录。用户说 "run a retrospective" / "lets retro the epic [epic]" 时触发。
phase: 4-implementation
precededBy: [diy-review]
followedBy: []
required: false
line: mainline
outputs: retrospective.yaml
---

# diy-retrospective — epic 收尾回顾（YAML 单一源）

你是**回顾主持人**。输入：一个已完成 epic 的证据链——`sprint.yaml` 任务块（`note` / `evidence` / `loop` / `review.findings`）、`bug-log.yaml`、`test-plan.yaml` 的覆盖、`stories.yaml`——由引擎机械采集。产出：`{output_dir}/retrospective.yaml` 里的一条记录。你提炼模式、亮点、挑战与有人认领的承诺。**与 diy-review 的边界**：diy-review 判一个任务的实现，本技能判 epic 作为已交付整体的成败——绝不改上游产物、绝不追责个人。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（主题、亮点、行动、就绪度）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 跑确定性开场——门 + 机械指标 + 接续输入：
   `python "{project-root}/.claude/skills/diy-retrospective/scripts/retrospective.py" collect --epic <E-x> --project-root "{project-root}" --output-dir "{output_dir}" --json`
   exit 1 是零产出的拒绝：转述它的一行理由与 `gate.route`，然后停下——拒绝永不变成记录。`PENDING_DECISION` warning ＝ epic 未收尾；partial 分支归第 1 步。
3. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。`{output_dir}/retrospective.yaml` 只在铸造下一个 `RT-###`、或按某条记录的 `id:` 行改它时才打开；指标与计数取回执，绝不从 `sprint.yaml` 重推。本 schema 不定义 `detail` 字段——没有可跳过的内容。
4. 读 `steps/01-discovery.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不预载或批量预载七个步骤文件；Front-load：一步的输出整块给出，步中不追问；**例外＝各 step 点名的交互点**——第 1 步的 epic 选择与未收尾三选项（含 `partial: true` 的用户裁定）、第 4 步的两问、第 6 步的五维就绪度盘问。每个断言可溯源：证据锚点（story / task / bug / AC ID，或 pattern / recovered blocker / defect class / clean augment round），**或**标注来源 `user-read`（用户口述、证据不支持）并说明锚点缺失。产物叙述文字用 `document_output_language` 写，对话用 `communication_language`。

1. `steps/01-discovery.md` — 选 epic（三级逻辑）、跑 `collect`、走未收尾分支、起草记录。
2. `steps/02-deep-analysis.md` — 挖结构化证据（任务 `note` / `evidence` / `loop` / `review.findings`、`bug-log`、`test-plan`），过四副镜片，只留跨 ≥2 个故事的 pattern。
3. `steps/03-continuity.md` — 以上一个 retro 的承诺对照本 epic 的证据；预览下一 epic 的依赖。
4. `steps/04-review.md` — 主持纪律与用户交互点；填 `wins` / `challenges` / `insights`。
5. `steps/05-actions.md` — SMART 行动项（带责任人、可观测的完成判据，绝不写工期估计）、准备项、关键路径、重大变更检测。
6. `steps/06-readiness.md` — 盘问就绪度五维（testing / deployment / acceptance / tech_health / blockers）；把阻塞项升进关键路径。
7. `steps/07-finish.md` — 终门、保存、路由（重大变更 → diy-correct-course）。

记录写入：第 1 步末尾按 `草稿` 建记录，各节随对应步骤填，第 7 步定稿。渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/retrospective.yaml` —— 唯一源头，集合形态（顶层形状对齐 `bug-log.yaml`）：

```yaml
project: {name, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天
retros:
  - id: RT-001                  # RT-###——顺序递增、稳定，永不重编号、永不复用
    epic: E-x                   # 须在 epics.yaml 可解析
    status: 草稿|已定稿
    date: YYYY-MM-DD            # 本条动作的日子，不随 updated 变
    partial: false              # 仅用户确认的部分回顾写 true
    metrics:                    # 照抄 collect 回执（结构化产物的真值）
      stories_total: 0
      stories_done: 0
      rounds_total: 0           # 本 epic 各任务 loop.rounds 之和
      blocked_count: 0
      augment_fail: 0
      bugs: {功能型: 0, 非功能型: 0}
    patterns:
      - {theme: <一行>, evidence: [S-x | BUG-0xx], count: N}   # ≥2 个故事，否则只是轶事
    wins: [<一行；带锚点，或标 user-read>]
    challenges: [<一行；系统视角>]
    insights: [<一行>]
    prev_followup:              # 首份 retro 省略
      - {retro: RT-yy, action, status: 已完成|部分完成|未完成, evidence}
    action_items:
      - {id: AI-001, action, owner, done_when, category: 流程|技术|文档|团队}
    prep_items: [{item, class: 关键|可并行|锦上添花, owner, effort}]
    critical_path: [{item, why, owner}]
    readiness: {testing, deployment, acceptance, tech_health, blockers}
    significant_changes:        # 可选；非空一律路由 diy-correct-course
      - {change, impact, recommended_action}   # owning skill 名写这里
    next_epic: {id: E-y|null, exists: true|false, dependencies: [<string>]}
revisions: []                   # {date, change, reason}——改既有记录时追加
```

## 规则

1. 写范围：只写 `{output_dir}/retrospective.yaml`——记录与其 `revisions`。绝不改 `sprint.yaml` / `stories.yaml` / `test-plan.yaml` / `bug-log.yaml` / `epics.yaml` 或源码：需要改它们才能落地的结论**一律**写成 `significant_changes` 条目、**一律**路由 `diy-correct-course`，owning skill 名写进该条目的 `recommended_action`（schema 既有键，不新增字段）。
2. 事实取自 `collect` 回执：`metrics` 与 `stories` 照抄，绝不手工重推。跨文档机械核对归 diyc——绝不拿眼睛复核 ID 链。
3. 不追责：每条 challenge 都写成系统 / 流程 / 工具的事实。全文不出现工期估计（小时、天、sprint）——只写轮次、计数与 `effort` 词。
4. 一个 epic 只有一条记录：`RT-###` 顺序铸造，永不重编号、永不复用；改既有记录就往 `revisions` 追加（date / change / reason）。不需要 `--previous` 轮——retro 原地更新（partial 补做也回到原记录），从不缩水。
5. 渲染守工作流里的静默旁路一句——只写命令；不新增浏览器交互点、不报路径阻塞等待、不等待。
6. 终门（机械）：先写 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-retrospective/scripts/retrospective.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾都等 exit 0。
7. 上游不动、不代写：需要改规格的发现点名 owning skill（diy-epics-stories / diy-prd / diy-architecture），该名字落 `recommended_action`；被 epic 证伪的计划按规则 1 路由 diy-correct-course，且一条 proposal 承载整批条目（交接形态见 `steps/07-finish.md`）。关键路径清了，下一 epic 才开。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
