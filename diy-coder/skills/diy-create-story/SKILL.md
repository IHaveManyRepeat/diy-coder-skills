---
name: diy-create-story
description: 'Create the implementation context pack for one story — the acceptance criteria it must satisfy, the tests that verify them, the architecture decisions it must follow, the files it will touch with their current state, and the carry-over from prior work — referenced by ID and path, never copied. Use when the user says "create the next story" or "create story [story identifier]".'
# ↑ 中文：为一条故事产出实施上下文包——它必须满足的验收标准、验证它们的用例、它必须遵守的架构决策、它将触碰且带当前状态的文件、前序工作的遗留——一律按 ID 与路径引用，绝不复制。用户说 "create the next story" / "create story [story identifier]" 时触发。
phase: 4-implementation
precededBy: [diy-sprint]
followedBy: [diy-dev]
required: false
line: mainline
outputs: story-context.yaml
---

# diy-create-story — 故事实施上下文包（引用式，YAML 单一源）

你是**故事上下文引擎**：输入 `stories.yaml` 里的一条故事 + `test-plan.yaml` / `sprint.yaml` / `architecture.yaml` + 它将触碰的代码，产出 `{output_dir}/story-context.yaml` 里的一条 `SC-###` 记录。你的职责是**指向**既有事实（ID 与路径），而不是转抄它们——以此挡住经典的实现灾难：重造轮子、用错库、文件放错位置、踩坏回归、谎报完成。

**与循环的边界。** 本技能只产出**一条**故事的上下文包；绝不写 `stories.yaml` / `test-plan.yaml` / `sprint.yaml`，绝不移动任务状态，绝不碰源码。主线下一步是 diy-dev。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 落定目标故事：用户显式给的 story ID；否则取 `{output_dir}/sprint.yaml` `tasks[]` 里文件序第一条 `status` 非 `已完成` 的任务（跳过 `已阻塞`）；两者都不成立 → 停下问用户，给出尚未 `已完成` 的故事 ID。
   然后跑确定性开场：`python "{project-root}/.claude/skills/diy-create-story/scripts/story_context.py" collect --story <S-x> --project-root "{project-root}" --output-dir "{output_dir}" --json`
   exit 1 是零产出拒绝：转述它的一行理由与其 `gate.route`（diy-epics-stories）或 `suggestions` 列表，然后停下——拒绝永不变成记录。
3. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
   `{output_dir}/story-context.yaml` 只在铸下一个 `SC-###`、或按某条记录的 `story:` 行改它时才打开；AC / TC / 决策 / 前序事实一律取回执，绝不手工回读 `stories.yaml` / `test-plan.yaml` / `architecture.yaml`——唯一例外是第 4 步判据取材时读 `{output_dir}/test-plan.yaml` 的 `static_checks` 段。本 schema 不定义 `detail` 字段——无内容可跳。
4. 读 `steps/01-target.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每个步骤结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不预载或批量预载这五个步骤文件；front-load——一步的输出整块给出，不在步骤中间提问；跨文档的每个事实都是 ID 引用或 CWD-relative 路径，绝不转抄；产物散文用 `document_output_language` 写，对话用 `communication_language`。

1. `steps/01-target.md` — 落定故事、跑 `collect`、按回执起草记录。
2. `steps/02-artifacts.md` — 上游事实全取回执（`acs` / `tcs` / `decisions` / `prior` / `git`），不读文档：引用 AC 与 TC、挑出适用的决策、提炼遗留。
3. `steps/03-code-survey.md` — 勘察故事将触碰的每个文件：完整读每个 `更新` 目标并记 `current_state` + `preserve`；`新建` 文件按项目既有结构落位。
4. `steps/04-compose.md` — 风险、命令级 `verify`、未决问题；与用户确认整包。
5. `steps/05-finish.md` — 终门、交付、路由 diy-dev。

记录写入：第 1 步末以 `草稿` 建记录（机器锚点从回执复制，绝不凭记忆重打），每个小节随其步骤完成填充，第 5 步定稿。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/story-context.yaml` — 单一源，集合形态（顶层形状照 `bug-log.yaml`）：

```yaml
project: {name, created, updated}     # created 建文件时设、此后不改；updated 每次写回刷今天
contexts:
  - id: SC-001                  # SC-### — 顺序递增、稳定，永不重编号、永不复用
    story: S-x                  # stories.yaml 里既有的故事（一故事一记录）
    status: 草稿|已定稿
    date: YYYY-MM-DD            # 本条动作的日子，不随 updated 变
    epic: E-x                   # 须等于该故事在 stories.yaml 里的 epic
    ac_refs: [AC-x.y]           # 该故事的 AC，按 ID 引用——正文留在 stories.yaml
    tc_refs: [TC-x.y.z]         # 绑定这些 AC 的用例（test-plan.yaml）
    design_ref: P-x             # 可选：该故事 AC 带 design_ref 时的主页面
    decisions: [D-x]            # 适用的架构决策，按 ID
    files:                      # 本故事将触碰的文件（勘察所得，绝不猜）
      - path: <relative>        # CWD-relative，正斜杠
        action: 新建|更新
        why: <one-line>
        current_state: <string> # 仅 更新 型，必填：该文件今天做什么
        preserve: <string>      # 仅 更新 型，--final 必填：不得破坏的行为
    prior_story:                # 可选（项目首条故事 → 省略）
      ref: S-y
      carryover: [<string>]     # 每行点名其来源（sprint S-y note / evidence）
    risks: [<string>]
    verify: [<string>]          # 命令级完成判据
    open_questions: [<string>]  # final 前须为空，或逐行带 [CLOSED] 前缀与所采取的决定
revisions: []                   # {date, change, reason} — 记录变更时追加
```

## 规则

1. 写范围：只写 `{output_dir}/story-context.yaml`——记录与其 `revisions`。绝不写 `stories.yaml` / `test-plan.yaml` / `sprint.yaml` / `architecture.yaml` 或源码。移动任务状态归 diy-dev。
2. 引用纪律（diy 的核心改动）：跨文档的每个事实都是 ID（`S-x` / `AC-x.y` / `TC-x.y.z` / `D-x` / `P-x`）或路径——绝不转述、绝不复制别处的散文。dev agent 去读被引的源；副本会漂走。
3. 一故事一记录、原位重写：记录以 `story` 为键；重跑更新那条记录并追加 `revisions`——绝不为同一故事铸第二条。ID 为 `SC-###`，顺序、稳定，永不重编号或复用。无需 `--previous` 轮——本技能原位重写一条记录，ID 集合不会收缩。
4. 门（零产出）：`{output_dir}/stories.yaml` 缺席、不可解析，或它的 `project.status != 已定稿`，或目标故事不存在 → 拒绝，转述理由加路由（diy-epics-stories）或 `suggestions` 列表，什么都不写。`sprint.yaml` / `test-plan.yaml` / `architecture.yaml` 缺席 → 只出 warning：运行在更薄的引用面上继续。
5. 文件勘察不是可选项：每个 `更新` 条目带 `current_state`，`--final` 时另有 `preserve`。「读你要改的文件」是源工作流不可让渡的那条——跳过它是实现失败与返工的首因。
6. `[假设]` 前缀只写在**值**上，不新增独立键（需要独立承载时在 schema 里点名该字段）。带前缀的推断在 `final` 前必须清零：交互态经用户确认后删前缀；**headless 态一律转成 `open_questions` 里的一条，不删不猜**。终门扫的字段集 = 整条记录的全部键与字符串值（`risks` / `verify` / `open_questions` / `carryover` / `files[].why` / `current_state` / `preserve` 等），一处命中即 `ASSUMPTION_PRESENT`。
7. 渲染照 Workflow 的静默旁路句——只写命令；不新增浏览器交互点、不报告会阻塞的路径、不等待。
8. 终门（机械）：先写 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-create-story/scripts/story_context.py" check --final --json --project-root "{project-root}" --output-dir "{output_dir}"`（`--output-dir` 必填，永不取缺省）。exit 0 是唯一放行；修完每条报告的违规再重跑；JSON 回执（含计数）即收口证据。**门非 0 → 先把 `status` 回退 `草稿`**，修完重走本步；离开本次运行前文档不得停在未过门的 `已定稿`。渲染与收尾等 exit 0。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
