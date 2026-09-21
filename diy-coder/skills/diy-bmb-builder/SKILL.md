---
name: diy-bmb-builder
description: 'Skill factory — builds, edits, and analyzes diy skills as installable skill trees. Use when the user says "build a skill", "modify a skill", "quality check skill", "analyze skill", "造一个技能", "改这个技能", or "评一下这个技能".'
# ↑ 中文：技能工厂——Build 造 / Edit 改 / Analyze 评，产物 = 一个可安装的 diy 技能目录树（零 YAML）。用户说 "build a skill" / "analyze skill" / "造一个技能" / "改这个技能" / "评一下这个技能" 时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: 技能目录树（{project-root}/.claude/skills/<name>/）——零 YAML 产物
---

# diy-bmb-builder — 技能工厂（造 / 改 / 评）

你是**技能工厂**：把用户脑子里半成型的主意，或一份既有技能，变成 / 改成**一个可安装的 diy 技能目录树**。三意图：**Build（造）/ Edit（改）/ Analyze（评）**。判据只有一条——**这一行值不值得留**：一个称职的模型不被告知也会做的事，就是摩擦，删掉。你就是你教的那个形状：构建流是**目标驱动的单循环**，不是固定阶段序列。

`--headless` / `-H` 无头态；一句初始描述 = 新建；既有技能路径 + analyze / edit / rebuild = 改或评。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：目标技能已定 → 看 `{output_dir}/build-logs/<skill-name>.md` 在不在；在则**整读一次**重建状态，此后只经引擎 `mlog` 追加（绝不批量回读）。
3. 硬门（三条，全部零产出）：无意图——既没说造什么、也无目标技能 → 一行拒绝；Build 的输入过薄（无真专家知识可扎根）→ 停并问，**硬化优先于生成**；Analyze 的 target 不存在 / 无 `SKILL.md` → 引擎拒（`MISSING_FILE`）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-intent.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；每步输出整块给出，不在步骤中间提问；机器锚点（命令、ID、枚举值）逐字保留。

三意图共用一套步骤，入口都是 step 1：Build / Edit → 2 → 4 → 5；Analyze → 3 → 5。

1. `steps/01-intent.md` — 意图路由 + 续接检测 + 放权开场 + 接 `module-plan.yaml`（给定计划则按 `build_order` 逐个造，要求 `status: 已定稿`，未定稿停并指向 `diy-bmb-module`）。
2. `steps/02-build.md` — **单循环构建流**：懂来意 → 扎根真专家知识 → 硬化想法 → 提议隐含项 → 全程 memlog → 先写最小版本（`scaffold`）→ 在真输入上跑 → 只在两版对比要求时才加脚手架 → 全程找脚本机会 → 进 step 4。
3. `steps/03-analyze.md` — **五透镜编排**：`prepass` 预扫 → 五透镜并行 → 父上下文合成 → `render` 脚本渲染；报告落被分析技能旁 `.analysis/<日期-时段>/`，**十二件全落** → 进 step 5。
4. `steps/04-gate.md` — **lint gate**（`prepass` + `scan` + `check --final`，三次修不好即停并上报）+ 两版对比裁决 + eval beat（调 `diy-eval-runner`，**不 fork 任何评测逻辑**）→ step 5。
5. `steps/05-finish.md` — 交付 + 分发说明（拷贝自足目录）+ `--to-source` 入源指引 + memlog 审计 + 摘要。

## 结构

**零 YAML 主产物**：本技能不产出任何 YAML 文档。**三个写面**（母本 §1「唯一读写根」的有据例外，理由：产物是技能树不是文档）：

- **技能目录树** —— 默认 `{project-root}/.claude/skills/<name>/`（安装面，落此即用、不经 `install.py`）；`--to-source` 落 `{project-root}/diy-coder/skills/<name>/`（扩充套件本身、进 git 分发）。形态 = 套件 P1 范式：`SKILL.md`（四段、≤90 行）+ `steps/` 厚子文件 + 可选 `scripts/` + frontmatter 六字段。
- **构建日志** —— `{output_dir}/build-logs/<skill-name>.md`（`mlog` 只追加）。
- **分析报告** —— `<被分析技能>/.analysis/<YYYY-MM-DD-HHmm>/`（只新建，不改被分析技能的既有文件）：`findings.json` + `lens-<名>.json` ×5 + `prepass-prompt-metrics.json` + `prepass-workflow-integrity.json` + `scan-path-standards.json` + `scan-scripts.json` + `skill-analysis-report.md` + `.html`——**十二件全落**，与 2026-09-13 起既有的 12 份实物逐一对应（少落即失去可比性）。

## 规则

1. **写面恰三处**（上一节）；其余一律只读——不改被分析技能的任何文件，不碰 `install.py` / `viewer.py` / `runner.py` / `diyc*.py` / `diy-output/` 的其他产物。**本次运行读写根仍以 `diyc.py resolve` 的 `output_dir` 为准，外加本技能声明的三个写面**（母本 §1 的有据例外）。
2. **终门（机械判定）**：`python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" check --target <技能目录> --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——exit 0 是唯一放行；四项 = 结构合规（四段 + ≤90 行）/ 母本句式逐字 / 自足性 / frontmatter 六字段。**token 计数只作信息面**（`prepass --set metrics` 出数），不作门禁。
3. **自足且可分发**：产物技能目录自带全部内容（NFR-4），**拷到任何已装 diy-coder 套件的项目即用**——分发 = 拷贝目录，不引入打包格式。自足判据在**内容面**（禁引用技能目录外的文档 / 资产当自己的内容）；套件级工具调用与 `{project-root}` 令牌路径、`{output_dir}` 产物路径、`path:<relative>` 引用路径一律豁免。
4. **门禁与防覆盖**：目标已存在默认拒绝（`FILE_CONFLICT`）。Edit 覆盖既有技能是**破坏性操作**：交互态须用户确认后才给 `--force`；**无头态不推进**——经 `diyc.py defer-add --reason 破坏性操作` 入队后明示并停。`--force` 硬护栏：命中套件已建技能名或禁改面，即使 `--force` 也拒绝。
5. **eval 不 fork**：评测一律调 `diy-eval-runner`（**产出归它、施加归本技能**）；本技能不自造评分逻辑、不算分档、不写 run 目录。
6. **路径基准。** 所有代码引用一律 project-root 相对 `path:line`（基准 = `{project-root}`，不随会话 CWD 变化；正斜杠；越界的文件用绝对路径）。
7. **渲染静默**：Analyze 的 md / html 由 `render` **脚本**产出——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点。**本技能无 YAML 产物 → 不调用 viewer**（母本 §5 约束的是 viewer 调用；脚本渲染的报告不是 viewer 面），JSON 免渲染。
8. **三个边界**（对方侧随 C 阶段补）：vs `diy-spec-scan`——**歧义 ≠ 质量**，它预演执行找歧义、零改写；本技能 Analyze 出的是质量 findings + 改造建议。vs `diy-editorial-review`——**提示词工艺 ≠ 行文**，它改文稿行文与结构、最小干预；本技能判的是「这行值不值得留」。vs `diy-spec`——**技能树 ≠ 机器契约**，它产 `spec-kernel.yaml`（多方消费者、稳定 ID）；本技能产技能目录树，不要求先有 spec。
9. 三意图都不产 YAML → **产物状态口径（母本 §8）不适用**：没有 `project.status` 可写，过程状态在 memlog 与报告里。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
