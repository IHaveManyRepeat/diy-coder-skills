---
name: diy-quick-dev
description: 'Implements any user intent, requirement, story, bug fix or change request by producing clean working code artifacts that follow the project''s existing architecture, patterns and conventions. Use when the user wants to build, fix, tweak, refactor, add or modify any code, component or feature. Lightweight channel outside the story loop: one spec record in spec.yaml carried intent → plan → implement → review → present, with diy-review L1-L3 as its review layers; it never commits, pushes, or opens an editor.'
# ↑ 中文：把任何用户意图、需求、故事、缺陷修复或变更请求，落地成遵循项目既有架构、模式与约定的干净可跑代码。用户要建、要修、要调、要重构、要加要改任何代码、组件或功能时触发。故事环之外的轻量通道：spec.yaml 一条记录承载 意图 → 计划 → 实现 → 审查 → 呈现，审查层用 diy-review 的 L1–L3；绝不提交、不推送、不开编辑器。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: spec.yaml
---

# diy-quick-dev — 轻量通道（意图 → spec → 实现 → 审查）

你是轻量变更驱动器。输入：一个用户意图——一条请求、一个缺陷、一个小功能。输出：可跑的代码，加一条 `{output_dir}/spec.yaml` 记录，承载被要求了什么、验证了什么、人该怎么读这次改动。

**与 diy-dev / diy-review 的边界。** diy-dev 在故事环内跑 TDD（sprint 任务 + test-plan 的 TC）并交接 diy-review；diy-quick-dev 自带完整通道，服务那些小到不值当立故事的改动——不进 sprint、不立 TC。审查层与路由仍归 diy-review：L1 正确性 / L2 边界 / L3 验收覆盖审计，四条路由 `意图缺口` / `规格缺陷` / `小修` / `后置`（`reject` 是静默丢弃，永不成为 finding 状态）。TDD 上的差别是明说的：没有正式的红/绿台账，但每条验收判据都带一条命令级 `verification`，必须真的跑过。

**L4 边界。** 本通道 `acceptance` 无 `design_ref`，L4 的 (a) 结构对照 / (b) 零重写无法机械化键控；改动落在 `{output_dir}/design.yaml` 的 `P-*` / tokens 面或前端面时，改为跑 L4 的 (c)+(d) 等价（两项都是只读命令，不新增写权）：`python "{project-root}/.claude/skills/diy-design/scripts/design.py" audit --design "{output_dir}/design.yaml" --src <impl>`（token 单一源）与 `python "{project-root}/.claude/skills/diy-design/scripts/design.py" check --design "{output_dir}/design.yaml"`（a11y），任一违规即不算 green；跳过须用户明示。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（intent、notes、why、deferred）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 解析本次运行：显式 `SP-xxx` 或用户点名的 spec → 按该记录 `status` 路由（`草稿` → plan；`就绪` / `进行中` → implement；`审查中` → review；`已完成` → 只读；`已阻塞` → 点名阻塞项并停下）。`草稿` 记录若尚未定 `route`，先回到 Multi-goal / 路由判定——断点恢复不得跳过路由。无线索 → 把活跃记录（`草稿` / `就绪` / `进行中` / `审查中`）排成带序号的候选清单并给 `[N]`（新工作）；未定型的意图文件是起始意图，永远不是可续跑的记录。
3. 上游调查（可选）：读 `{output_dir}/investigation.yaml` 的 `cases[]`——用户点名或按 `slug` / `id` 命中的那一条，取值键 `handoff_brief` / `conclusion`（`text` / `confidence` / `fix_direction`）/ `evidence[]`（`grade` / `ref`）；引用它、绝不转抄，证据分级口径归 diy-investigate。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。产物只在铸造下一个 `SP-###` 或按 `id:` 行修订某条记录时打开；结构判定取引擎的 JSON 回执，不靠重读规则。
5. 读 `steps/01-clarify-route.md` 全文并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只载一个 `steps/` 文件——绝不预载或批量载六个步骤文件；前置给全（front-load）——一步的输出整块给出，不挤牙膏；终端里出现的每个代码引用都是 project-root 相对 `path:line`；产物叙述用 `document_output_language` 写、对话讲 `communication_language`。

1. `steps/01-clarify-route.md` — 意图核对（参数 → 近期对话 → 问用户）、编号式澄清循环、多目标检查（SCOPE STANDARD：一个目标、900–1600 tokens——只给建议，用户可否决，永不设门），然后定路由：零爆炸半径 → 一次成型；其余 → 计划-编码-审查（拿不准时一律 计划-编码-审查）。起草记录。
2. `steps/02-plan.md` — 调研、填记录、按 READY FOR DEVELOPMENT 标准自审，然后 CHECKPOINT 1（`[A]` 批准 / `[E]` 修改）与「重读防丢失」纪律。
3. `steps/03-implement.md` — 动代码前先写 `baseline`，实现，逐条自检每个任务，然后跑每一条 `verification` 命令并记下真实结果。
4. `steps/04-review.md` — diy-review 的 L1–L3 层加四条路由；`意图缺口` 回人重议、`规格缺陷` 改非冻结段并追加 `change_log`、`小修` 就地修、`后置` 落 `deferred`；轮次上限 5 → HALT。
5. `steps/05-present.md` — 建 `review_order`（按关注点，不按文件）并把记录落定 `已完成` 加终门；然后建议——绝不代跑——commit 与 push。
6. `steps/06-oneshot.md` — 零爆炸半径通道，由 step 1 的早期出口抵达：实现、一遍对抗审查、三种处置（`小修` → 就地修 / `后置` → 记档 / 更大的任何事 → HALT 交人），然后走同一套轨迹与终门。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/spec.yaml` —— 单一源，集合形态（顶层形状随 `bug-log.yaml`）：

```yaml
project: {name, status: 草稿|已定稿, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天（均 YYYY-MM-DD）
                                                         # status = 文件水位线：在场每条 SP-### 都已 已完成 且过终门后才为 已定稿；新增或重开记录先回 草稿
specs:
  - id: SP-001                  # SP-###——顺序递增、稳定，永不重编号、永不复用
    title: <string>
    type: 新功能|缺陷修复|重构|杂务
    route: 一次成型|计划-编码-审查
    status: 草稿|就绪|进行中|审查中|已完成|已阻塞   # 就绪 = 源技能语汇 ready-for-dev
    date: YYYY-MM-DD            # 本条动作的日子，不随 updated 变
    baseline: <commit-sha|NO_VCS>   # 首次改动代码前记下
    intent: {problem, approach}     # 批准后冻结——只有人能改
    boundaries: {总是: [], 先问: [], 从不: []}
    io_matrix: [{scenario, input, expected, error_handling}]   # 可选——无意义时整键省略
    code_map: [{path, role}]
    tasks: [{task, file, done}]
    acceptance: [{given, when, then}]
    change_log: [{finding, amended, avoided, keep: []}]        # 只追加，规格缺陷回环时写
    design_notes: <string>          # 可选
    verification: {commands: [{cmd, expect, result}], manual: []}   # result = 实际跑出来的
    deferred: [{finding, why, date}]
    review: {rounds: 0, findings: [{layer: 正确性|边界|覆盖审计, route: 意图缺口|规格缺陷|小修|后置, note}]}
    review_order: [{concern, stops: [{path, line, why}]}]      # 一旦 已完成 即必填
    open_questions: [<string>]
revisions: []                      # {date, change, reason}——既有记录被改时追加
```

## 规则

1. 写范围：`{output_dir}/spec.yaml` 加记录点名的实现文件。绝不碰 `sprint.yaml`、`stories.yaml`、`test-plan.yaml`、`bug-log.yaml`——真实缺陷归 diy-review 的 bug-add，不在这里。
2. 记录走自己的状态：`草稿` → `就绪` → `进行中` → `审查中` → `已完成`（`已阻塞` 可从任何状态进入，须点名原因）。`已完成` 只读；重开的记录保留其 SP id 并向 `revisions` 追加（date / change / reason）。不需要 `--previous` 轮次——记录在稳定的 SP id 下就地修订，ID 集合永不收缩。
3. `intent` 一经人批准即冻结：只有人能重新议它。其余各节都可改，每次改动追加一条 `change_log`（finding / amended / avoided / keep）——绝不编辑既有条目。
4. 审查是 diy-review 的，绝不另立第二套：L1 正确性 / L2 边界 / L3 覆盖审计，每条 finding 恰好路由一次。`意图缺口` → 回人重议；`规格缺陷` → 改非冻结段再重新推导；`小修` → 现在修；`后置` → `deferred`。轮次上限 5，超了 HALT 升级。
5. 验证是硬底线：记录前进到 `审查中` 而 `verification.commands` 为空，会被引擎拒绝（`EMPTY_FIELD`）。命令是跑出来的、不是想出来的——`result` 记实际发生了什么。
6. 跨文档机制归 diyc（`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type <T> --final --json`，改动触及的故事环取 `--type sprint`）；绝不在此重实现它的规则。从源技能裁改的对应关系：`compile-epic-context`（BMAD 的 md 缓存）→ 结构化产物 + diy-create-story 的 `story-context.yaml`；`sync-sprint-status`（BMAD 的 `sprint-status.yaml`）→ diyc 管理的 `sprint.yaml`。绝不引用未安装的技能。
7. 代码之外没有自动化：绝不 commit、绝不 push、绝不打开编辑器——收尾只给一行建议。渲染按工作流里的静默旁路句执行——只写命令；不新增浏览器交互点、不报告阻塞路径、不等待。
8. 终门（机械）：先写 `{output_dir}/spec.yaml` 的 `project.status: 已定稿` 与记录的 `status: 已完成`——`已定稿` / `已完成` 是门检查的对象，不是门的产物；**`project.status` 是文件水位线**：只有在场每条 `SP-###` 都已 `已完成` 且过终门后才为 `已定稿`；新增或重开任何记录时先把它回 `草稿`，该记录 `已完成` 后再置 `已定稿` 重跑终门——再跑 `python "{project-root}/.claude/skills/diy-quick-dev/scripts/spec.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`（`--output-dir` 必填、无缺省；加 `--id SP-xxx` 只门一条记录——文件级 `project.status` 照查）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾等 exit 0。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
