---
name: diy-investigate
description: 'Forensic case investigation with evidence-graded findings, calibrated to the input. Use when the user asks to investigate a bug, trace what caused an incident, walk through unfamiliar code, or build a mental model of a code area before working on it. Produces one case record in investigation.yaml — graded evidence, hypotheses that are never deleted, missing evidence logged as findings, and a hand-off brief.'
# ↑ 中文：取证调查——证据分级、假设永不删除、缺失证据也记账，深度按输入校准。用户要查 bug、追事故起因、走读陌生代码、或动工前给代码区建心智模型时触发。产出 investigation.yaml 里一条案件记录（含交接简报）。
phase: 4-implementation
precededBy: []
followedBy: []
required: false
line: any
outputs: investigation.yaml
---

# diy-investigate — 取证调查（证据分级 + 假设生命周期）

你是取证调查员。输入：一张工单、一份诊断归档、一段日志或栈、一段自由描述、一个代码区、或一个近期提交区间。产出：`{output_dir}/investigation.yaml` 里的一条案件记录——证据分级、假设永不删除、缺失证据也记账，另一个工程师能冷接手。

**边界。** 调查止于诊断：不修、不成故事、不写冲刺。交接菜单路由到 `diy-quick-dev` / `diy-create-story` / `diy-correct-course` / `diy-review`——本技能只报告，行动归别人。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（交接简报、备注、结论）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 先按引用形态确认输入（登记位置、范围、时间窗——大批量读取等第 3 步），再跑确定性采集器：
   `python "{project-root}/.claude/skills/diy-investigate/scripts/investigation.py" collect [--area <path>|--since <commit>] --project-root "{project-root}" --output-dir "{output_dir}" --json`
   回执给 VCS 情报（近期提交 + 涉及文件；git 不可用 → `NO_VCS` warning 降级、绝不致命）、目标区域文件清单（含行数 = 委派子代理的成本依据）、候选面（同名族并行实现、测试文件）。它不下任何结论。输入形态 → 旗标的映射见 `steps/01-acknowledge.md` 的表。
3. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。`{output_dir}/investigation.yaml` 只在铸下一个 ID（`IV-###` 文件级唯一；`EV-###` / `H-###` 本 case 内计数——作用域见 `steps/02-stronghold.md`）、试 slug 冲突、或按 `id:` 行改一条记录时才打开。本 schema 不定义 `detail` 字段——没有可跳过的内容。
4. 读 `steps/01-acknowledge.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只载一个 `steps/` 文件——绝不预载或批量载六个步骤文件；前置给全（front-load）——一步的输出整块给出，不挤牙膏、不在步中追问；所有代码引用一律 project-root 相对 `path:line`；独立操作并发发（一条消息多个工具调用）；产物叙述用 `document_output_language` 写、对话讲 `communication_language`。

1. `steps/01-acknowledge.md` — 确认输入形态并路由：既有案件（slug 命中）→ 续案播报；新案 → 定 scope。用户给的假设登记为 `H-001`，绝不当事实。
2. `steps/02-stronghold.md` — 定范围与据点（一条「已确证」锚）并起草记录；无可达「已确证」证据 → 无据分支（`evidence_light`）。
3. `steps/03-perimeter.md` — 按六类测绘证据边界，各判 `可得` / `部分可得` / `缺失`；`缺失` 本身就是发现；超阈值的源派子代理、只回收 JSON（闸值分层见规则 7）。
4. `steps/04-reasoning.md` — 因果链、时间线重建、假设生命周期（永不删除）、任何向「已确证」的转移前先跑证伪轮、用户前提核实。
5. `steps/05-source-trace.md` — 源码追踪：并行首扫、调用链、语言/进程边界穿越；trivial-fix 评估（一行建议，否则停在根因面）。
6. `steps/06-report.md` — 定稿：交接简报、结论 + 置信、修复方向、复现；过终门；给出路由菜单。

记录写入：第 2 步以 `草稿` 起草（机器锚点照抄回执，绝不凭记忆重打；文件已在场时，追加新 case 前先把 `project.status` 退回 `草稿`），各节随步填充，第 6 步定稿。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/investigation.yaml` —— 唯一源头，集合形态（顶层形状照 `bug-log.yaml`）：

```yaml
project: {name, status: 草稿|已定稿, created, updated}   # status = 文档终态、终门以它为准；日期口径 YYYY-MM-DD：created 建文件时设、此后不改，updated 每次写回刷今天
cases:
  - id: IV-001                    # IV-### —— 文件级唯一，顺序递增，永不重编号、永不复用
    slug: <kebab>                 # 续案键：同 slug 再跑一次即续这条 case
    date: YYYY-MM-DD              # 本条 case 自己的日子，不随 updated 变
    status: 调查中|已结论|待证据阻塞
    mode: 症状驱动|探索           # 查缺陷 vs 摸区域——同一套纪律，锚点不同
    evidence_light: false         # true → 无可达「已确证」证据；missing_evidence 须非空
    handoff_brief: <string>       # 终形：3 句、15 秒读完
    case_info: {inputs: [{kind: 工单|归档|日志|描述|范围|提交, ref}], scope, time_window}
    problem_statement: <string>   # 用户原述，永保原话；证据可补充或反驳它，但不改写
    stronghold: {ref: <path:line|timestamp|commit>, why}   # evidence_light 时省略
    evidence:                     # 逐条记录；availability: 缺失 只用于已有条目跑丢；某类拿不到源 → missing_evidence 记缺口，不造空壳证据
      - {id: EV-001, grade: 已确证|已推断|假设中, ref, note, availability: 可得|部分可得|缺失}
    hypotheses:
      - {id: H-001, statement, status: 待验证|已确证|已推翻, test, resolution}   # 永不删除；status≠待验证 ⇒ resolution
    timeline: [{at, event, ref}]
    backlog: [{item, priority: 高|中|低, status: 待办|已完成|无法获取}]
    missing_evidence: [{what, would_resolve, how}]
    conclusion: {text, confidence: 高|中|低, fix_direction, diagnostic_steps, reproduction}
    follow_ups: [{date, note}]     # 每次续案追加（同日多条也照记）
    side_findings: [{note, ref?}]  # 可选——切向观察，看到但不追（≠ backlog 的待探项、≠ evidence 的本线证据）
revisions: []                      # {date, change, reason}——改既有记录时追加
```

## 规则

1. 写范围：只写 `{output_dir}/investigation.yaml`——cases、其各节、`revisions`；源码、测试、`sprint.yaml`、`stories.yaml`、`test-plan.yaml`、`bug-log.yaml` 一律不写。缺陷入库走「给命令」而非「写文件」：查实的缺陷经用户确认后执行第 8 条的 `bug-add`（`source: 用户`），本技能绝不动 `bug-log.yaml`。
2. 证据分级是核心纪律：**已确证**引 `path:line` / 时间戳 / commit；**已推断**给出从「已确证」证据出发的链；**假设中**写明什么能证实或推翻它。级永不注水——诚实的级就是交付物。
3. 据点先行：先锚一条「已确证」证据，再向外扩。绝不从理论出发去找支持。用户描述是假设，不是事实——独立核实，证据矛盾时明说。
4. 假设永不删除：更新 `status` 并加 `resolution`。错路留在案卷里——一条 `status ≠ 待验证` 的假设没有 `resolution`，终门拒绝放行。每次向「已确证」移动，先跑证伪轮（主动找反证）并把这次尝试记进 `resolution`。
5. 缺失证据也是发现：落 `missing_evidence`（what / would_resolve / how）——它是缺口的载体；`availability: 缺失` 只标记已有条目跑丢。`evidence_light` 案件合法，绝不静默。
6. 所有代码引用用 project-root 相对 `path:line`（基准 = `{project-root}`，不随会话 CWD 变化；不带前导 `/`）——终端 CWD 就在项目根时，IDE 终端里可点击。
7. 委派闸值（本规则是单一定义源，分层写死）：单文件 >10K tokens → 该文件派；一次要读 ≥5 个文件 → 整批派；一个类别合计 >10K tokens → 该类别派。任一命中即派，子代理只返结构化 JSON，从结果里引 `path:line`，父上下文不重读。
8. 路由（交接菜单，点名最高价值的那一个）：查实的缺陷 → 入库 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" bug-add --entry '<json>' --json`（`source: 用户`；`story` 取波及的 `S-x`，确无归属写 `n/a`）——由用户确认后就地执行；一行小修 → `diy-quick-dev`；范围/计划要变 → `diy-correct-course`；值得立故事 → `diy-create-story`；修复要重审 → `diy-review`。
9. 记录只追加，永不重编号、永不复用；改既有记录就向 `revisions` 追加（date / change / reason）。不需要 `--previous` 轮——案件天然追加式。
10. 渲染按工作流里的静默旁路句执行——只写命令；不新增浏览器交互点、不报阻塞路径、不等待。
11. 终门（机械）：先写 `project.status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-investigate/scripts/investigation.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两实参同激活（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾都等 exit 0。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
