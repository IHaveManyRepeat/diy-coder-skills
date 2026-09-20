---
name: diy-correct-course
description: 'Manage significant changes during sprint execution. Analyze impact across artifacts, draft concrete old-to-new edits, and hand the proposal off by scope. Accepts one trigger issue, or the `significant_changes` entries handed off by diy-retrospective — one proposal record carries all of them. Use when the user says "correct course" or "propose sprint change". Produces one proposal record in change-proposal.yaml.'
# ↑ 中文：执行期重大变更的导航——跨产物分析影响面、起草具体的 old → new 改动、按 scope 交接提案。输入两路：用户报出的单个触发问题，或 diy-retrospective 交来的 `significant_changes` 条目（一条 proposal 记录承载整批）。用户说 "correct course" / "propose sprint change" 时触发。产出一条 `change-proposal.yaml` 记录。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: change-proposal.yaml
---

# diy-correct-course — 执行期变更导航（只出提案，不改真源）

你是**变更导航员**。输入：一个执行期冒出的触发问题——用户报出的一个问题，或 diy-retrospective 交接的一批 `significant_changes` 条目。产出：`{output_dir}/change-proposal.yaml` 里的一条提案记录，承载影响集、具体改动与交接路由。你只分析与提案——真源由产物所有者技能执行。

**边界：只出提案，绝不改真源。** 本技能不写 `prd.yaml` / `epics.yaml` / `stories.yaml` / `architecture.yaml` / `openapi.yaml` / `design.yaml` / `test-plan.yaml` / `sprint.yaml`——`handoff.route` 点名哪个技能用自己的 update 模式落实改写。此处记下的提案本身不改动任何东西。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（trigger、why、rationale、note）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 输入面两路：
   - **用户报出的单个问题**——实施中发现的技术限制、干系人新要求、对原要求的误解、方向调整、失败的方案。
   - **diy-retrospective 的交接**——`{output_dir}/retrospective.yaml` 的 `significant_changes[]`，每条 `{change, impact, recommended_action}`。整批**只开一条 proposal**：N 条变化进同一条记录的 `impacts`（必要时加 `edits`），绝不拆成 N 条记录；`trigger` 写明来源（diy-retrospective 记录级 `id` 与那批条目的 `change` 摘句）。
   - **上游调查（可选）**：读 `{output_dir}/investigation.yaml` 的 `cases[]`——用户点名或按 `slug` / `id` 命中的那一条，取值键 `handoff_brief` / `conclusion`（`text` / `confidence` / `fix_direction`）/ `evidence[]`（`grade` / `ref`）；引用它、绝不转抄，证据分级口径归 diy-investigate。
3. 跑确定性开场（门 + 六文档影响面摘要 + 委派 diyc 跨文档核对 + 引用链）：
   `python "{project-root}/.claude/skills/diy-correct-course/scripts/change_proposal.py" collect --project-root "{project-root}" --output-dir "{output_dir}" [--target <ID>] --json`
   硬门 = `{output_dir}/prd.yaml`、`{output_dir}/epics.yaml`、`{output_dir}/stories.yaml` 三件套在场且各自的 `project.status: 已定稿`。exit 1 是零产出的拒绝：转述它的一行理由与 `gate.route`，然后停下——拒绝永不变成记录。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。`{output_dir}/change-proposal.yaml` 只在铸造下一个 `CP-###`、或按某条记录的 `id:` 行改它时才打开；文档摘要、`diyc.check.violations` 与 `chain` 取回执，绝不靠重读产物。本 schema 不定义 `detail` 字段——没有可跳过的内容。
5. 读 `steps/01-init.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不预载六个步骤文件；Front-load：一步的输出整块给出，不在步骤中间提问；每条影响与改动都带目标（产物用稳定 ID，基础设施文件用 `path:<relative>`）；产物叙述文字用 `document_output_language` 写，对话用 `communication_language`。

1. `steps/01-init.md` — 用用户原话确认触发、定 `mode`、起草记录。
2. `steps/02-analysis.md` — 走影响面视角清单；机械面取回执，判断面产出 `impacts`。
3. `steps/03-edits.md` — 起草具体改动：一处 `old → new`，各带 rationale。
4. `steps/04-proposal.md` — 定推荐路径（`approach`）、`ripple`、`effort`；写记录并呈现待审。
5. `steps/05-route.md` — 取显式批准、判 `scope`、定 `handoff`。
6. `steps/06-finish.md` — 收尾摘要、过终门、交接。

记录写入：第 1 步末尾按 `草稿` 建记录（事实照抄回执、绝不凭记忆重打），各节随对应步骤填，第 6 步定稿。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/change-proposal.yaml` —— 唯一源头，集合形态（顶层形状对齐 `bug-log.yaml`）：

```yaml
project: {name, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天
proposals:
  - id: CP-001                # CP-###——顺序递增、稳定，永不重编号、永不复用
    date: YYYY-MM-DD          # 本条动作的日子，不随 updated 变
    status: 草稿|已定稿|已批准|已驳回
    trigger: <string>         # 触发问题——用户原话优先；来自 diy-retrospective 时写 RT-id + change 摘句
    mode: 增量|批量
    scope: 轻微|中等|重大      # 第 1 步暂定、第 5 步定夺；终门强制它与 handoff.route 配对
    impacts:                  # 纯引用型影响清单（不复制内容）
      - {artifact: prd|epics|stories|architecture|openapi|design|test-plan, target: FR-x.y|F-x|S-x|AC-x.y|D-x|TC-x.y.z|..., kind: 修改|新增|删除, why: <string>}
      - {artifact: infra, target: 'path:<relative>', kind: 修改|新增|删除, why: <string>}   # 部署脚本 / CI / IaC 文件——目标写文件，绝不写产品 ID
    edits:                    # 具体提案（old → new 只引最小决定性取值）；`old` 引当前值，新增型写 (absent)
      - {artifact: <同一枚举>, target: <ID 或 path:<relative>>, field: <path>, old: <string>, new: <string>, rationale: <string>}
    ripple: [<string>]        # 沿引用链的下游连带影响
    effort: {estimate, risk, timeline_impact}
    approach: {path: 直接调整|回滚|MVP 复审, why: <string>}
    handoff: {route: <diy 技能名>, note: <string>}
    open_questions: [<string>]
revisions: []                 # {date, change, reason}——改既有记录时追加
```

## 规则

1. 写范围：只写 `{output_dir}/change-proposal.yaml`——记录与其 `revisions`。绝不改真源产物（`prd.yaml` / `epics.yaml` / `stories.yaml` / `architecture.yaml` / `openapi.yaml` / `design.yaml` / `test-plan.yaml` / `sprint.yaml`）；`handoff.route` 点名谁执行，改动是它的活。
2. 只引用、不复制：`impacts.target` 与 `edits.target` 带稳定 ID（产物类）或 `path:<relative>`（`artifact: infra`——部署 / CI / IaC 文件，绝不写产品 ID）；`old` / `new` 引最小决定性取值（一个 ID 加一行要点），绝不粘贴整段。整篇改写是产物所有者技能的活。
3. 影响事实取自 `collect` 回执：文档摘要、`diyc.check.violations` 与 `chain` 一律照抄，绝不手工重推。跨文档机械核对（ID 链、引用解析）归 diyc——绝不拿眼睛复核。
4. 触发不清就停：模糊的问题不写提案。每条影响都要点出显示它的证据——绝不虚构影响。起草期未确认的推断可带 `[假设]` 前缀；终门要求清零——要么与人确认落定，要么显式落成 `open_questions` 条目。
5. 记录只追加，永不重编号、永不复用；改既有记录就往 `revisions` 追加（date / change / reason）。不需要 `--previous` 轮——提案记录只追加，从不整篇重写。
6. 渲染守工作流里的静默旁路一句——只写命令；不新增浏览器交互点、不报路径阻塞等待、不等待。
7. 终门（机械）：先写 `status: 已定稿`（或 `已批准`）——它是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-correct-course/scripts/change_proposal.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两个实参同激活（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾都等 exit 0。**`已驳回` 是唯一例外**：终门对本条永不放行（`--final` 要求 `status ∈ {已定稿, 已批准}`），改跑**不带 `--final`** 的同一条 `check` 收口（见 `steps/06-finish.md`）。
8. 按 scope 路由（门强制配对；`steps/05-route.md` 的 allow-list 只是粗筛，真判据 = 被改产物的唯一所有者）：`轻微` → 产物所有者技能直接落实；`中等` → diy-sprint / diy-epics-stories / diy-prd 重组 backlog；`重大` → 规划层（diy-prd / diy-architecture / diy-epics-stories）重规划。批准先于路由——未批准的提案绝不交接。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
