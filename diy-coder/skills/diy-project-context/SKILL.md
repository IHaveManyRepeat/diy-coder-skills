---
name: diy-project-context
description: 'Document brownfield projects for AI context and capture the rules AI agents must follow. Use when the user says "document this project", "generate project docs", "generate project context", or "create project context".'
# ↑ 中文：为棕地项目建 AI 语境档，提炼 AI 代理必须遵守的规则——单一源 project-context.yaml。用户说 "document this project" / "generate project docs" / "generate project context" / "create project context" 时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: project-context.yaml
---

# diy-project-context — 棕地扫描与 AI 规则（单一源）

你既是项目文档专员，又是技术引导者。输入：一个既有代码库——任何语言、单块多块皆可。产出：一个 `project-context.yaml`，装扫描事实（部件、技术栈、目录树、架构、集成）与 AI 代理必须遵守的实现规则。一个文件：绝不产 markdown 文档集，绝不建扫描状态的散文件。

**边界。** 本技能只记录既有事实。diy-prd 决定接下来做什么、diy-architecture 决定怎么做——两者都读本文件当棕地输入。这里不规划变更、不编辑代码。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（摘要、备注、规则、理由）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 目标文件：`{output_dir}/project-context.yaml`——唯一源头。它的 `scan` 块承载 mode / level / date / parts；不存在任何其它状态文件。
3. 模式判定：文件缺席 → **全量**；文件在场 → 读它的 `scan` 块并给三个选项：**重扫**（重扫整个项目，以记录的日期为增量窗口起点）、**深挖**（对单一区域穷尽）、或 **Cancel**（文件原样保留）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。`{output_dir}/project-context.yaml` 只在铸下一个 `PC-###`、按 `id:` 行改一条规则、或读 `scan` 块判模式时才打开。事实取引擎的 JSON 回执，绝不手工重扫。本 schema 不定义 `plain` / `detail` 字段——没有可跳过的内容。
5. 读 `steps/01-scan.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只载一个 `steps/` 文件——绝不预载或批量载五个步骤文件；前置给全（front-load）——一步的输出整块给出，不挤牙膏、不在步中追问；产物叙述用 `document_output_language` 写、对话讲 `communication_language`；所有代码引用一律 CWD 相对 `path:line`（基准 = `{project-root}`；会话 CWD 不在项目根时按 project-root 解析）。

1. `steps/01-scan.md` — 定模式与扫描档位，跑确定性扫描，与人确认探测到的部件，开草稿（`project` + `scan`）。
2. `steps/02-context.md` — 把回执落进 `stack` / `structure` / `architecture` / `integration`；绝不重扫。
3. `steps/03-rules.md` — AI 规则那一半：按类别逐条铸 `PC-###`，每条与人确认。
4. `steps/04-finalize.md` — LLM 语境复核、机械终门、交付与下游路由。
5. `steps/05-deep-dive.md` — 单区域穷尽深挖（`深挖` 模式）：逐文件实读，禁止抽样。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/project-context.yaml` —— 唯一源头；顶层形状对齐 `bug-log.yaml`（`project: {name, created, updated}`，不设顶层 status）：

```yaml
project: {name, created, updated}   # 日期口径 YYYY-MM-DD：created 建文件时设、此后不改；updated 每次写回刷今天
scan: {mode: 全量|重扫|深挖, level: 快速|深入|穷尽, date, parts: [{name, type, path}]}
                                    # date = 本次写 scan 块的日子（三种模式一律写今天，不是首扫日）= 下一次续跑播报的增量窗口起点
stack: [{part, language, framework, version, notes}]     # 清单未解析处写空串
structure: {tree: <string>, key_dirs: [{path, purpose}]}
architecture: [{part, summary, key_points: [<string>]}]  # 条件扫描（API / 数据 / 组件 / 状态）的结论落这里
integration: [{between: [<partA>, <partB>], contract, notes}]   # 多部件才填；单块项目省略
rules: [{id: PC-001, category, rule, why, where}]        # category: 技术栈|语言|框架|测试|质量|工作流|反模式
deep_dives: [{area, date, files_scanned, findings: [<string>], notes}]
                                    # 未跑过深挖时省略；date 记那一次深潜的日子，与 scan.date 不必相同
open_questions: [<string>]          # 可选；未决项（headless 下带 [假设] 的推断转来这里，不删不猜）
revisions: []                       # {date, change, reason} —— 改既有规则时追加
```

## 规则

1. 写范围 = `{output_dir}/project-context.yaml`，外加第 9 条规则的临时快照 `{output_dir}/project-context.yaml.prev`（写前建、终门比对后删，不作留存）。其余一律不写：源码、其他 `{output_dir}` 产物、项目自带文档。
2. 事实取回执：`scan` / `stack` / `structure` / `integration` 的值照抄引擎的 JSON 回执，绝不凭记忆重打。**人确认后的 part 清单是权威**——未被修正的值照抄回执，人修正过的 part 以人给的为准；`scan.parts` 与 `stack[].part`（以及 `architecture[].part` / `integration[].between`）逐一对齐该清单，回执里没有的行用人的原话补 `language` / `framework`、`version` 留空、`notes` 注明「人确认（引擎未解析）」。引擎解析不出的 part 或 type 交给用户——绝不发明。
3. `PC-###` ID 顺序递增、稳定，永不重编号、永不复用；删一条规则要留 `revisions` 条目。改既有规则就地改，并向 `revisions` 追加 date / change / reason——绝不另铸第二个 ID。
4. 推断值标记：`[假设]` 前缀只写在**值**上，不新增独立键；值以标记打头时整值加引号。带前缀的推断在 `--final` 前必须清零——交互态经用户确认后删前缀；**headless 态一律转成 `open_questions` 里的一条，不删不猜**。终门扫的字段集 = 整份 `project-context.yaml` 的全部字符串（引擎递归全扫，键与值都算；一处命中即 `ASSUMPTION_PRESENT`）。
5. `深挖` 模式要求逐文件实读。抽样、猜测、只靠工具输出都 FORBIDDEN：范围内每个文件都要读。
6. 语言无关：不假设任何工具链。引擎报为未解析的清单是给用户的问题——绝不猜。
7. 渲染按工作流里的静默旁路句执行——只写命令；不新增浏览器交互点、不报阻塞路径、不等待。
8. 终门（机械）：跑 `python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两个实参同激活（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾都等 exit 0。
9. 重写纪律——**重扫 / 深挖**，这两个模式重写既有文件（**全量**扫描没有要保留的东西）：既有各节整块前滚、就地编辑，绝不按骨架重写。写前 `cp {output_dir}/project-context.yaml {output_dir}/project-context.yaml.prev`；`check --previous` 与删除 `.prev` 都在 `steps/04-finalize.md` 的 Rewrite check 里执行，`exit 0`（= 无 `PC-###` 丢失）通过后才删——两处只留这一个出处。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
