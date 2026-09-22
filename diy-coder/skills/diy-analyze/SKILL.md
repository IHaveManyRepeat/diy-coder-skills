---
name: diy-analyze
description: 'Answer one concrete question about an existing codebase and commit the answer as analysis.yaml (question, architecture with a Mermaid string, components, data flows, dependencies, risks, recommendations). Entry skill — no upstream diy artifact; the gate is "the codebase is readable". Records what IS, never decides what to do. Use when the user says "analyze this codebase" / "how is X wired" / "map this repo".'
# ↑ 中文：就**一个具体问题**分析既有代码库，产物落 `analysis.yaml`（问题 / 架构总览含 Mermaid 字符串 / 组件 / 数据流 / 依赖 / 风险 / 建议）。**入口技能**——无上游 diy 产物，门禁 = 代码库可读。只记既有事实、不做技术决策。用户说 "analyze this codebase" / "how is X wired" / "map this repo" 时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: analysis.yaml
---

# diy-analyze — 单问架构分析（现状式 YAML 单一源）

你是**代码库的取证分析员**。输入：一个可读的代码库 + **一个**想弄明白的问题。产出：`{output_dir}/analysis.yaml`——问题 / 架构总览（含 Mermaid 字符串）/ 组件清单 / 数据流 / 依赖 / 风险 / 建议。**边界。** 本技能只记录既有事实、不做技术决策——`diy-architecture` 决定要做什么（决策式 `architecture.yaml`），这里只回答现状是什么；风险与建议**只是待办候选**，拍板归主线。深挖某一问时调用 `diy-elicit`、要多视角审视时调用 `diy-party-mode`（零写面：结果并入本记录）。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：跑 `list` 看有没有已在做的分析——**只回 `id` / `name` / `layer` / `responsibility` / `location` / `status` 六字段，不读正文**：
   `python "{project-root}/.claude/skills/diy-analyze/scripts/analyze.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json`
   有记录 → 播报六字段并问「① 接着做 / ② 复审调整 / ③ 推倒重来」，**HALT 等选择**；无记录 → 进第 3 步。
3. 门禁（零产出退出）：**代码库可读**——默认 `{project-root}`，用户可点名别的路径（`init --codebase <path>`）。路径不存在 / 不是目录 / 不可读 → 一行说明并**零产出停止**（`init` 会把门机械兜住：`MISSING_FILE`）。**要体检任意项目的代码库架构 → 用你的 `arch-analyze`（用户级全局技能）；要在本套件内回答一个架构问题并进产物链 → 用本技能**。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-define.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；除检查点外每步产出整块给出；`question` / `architecture` 与四个清单由你**直接编辑 `analysis.yaml`**（内容型产物，写权归会话），骨架与校验归引擎。

1. `steps/01-define.md` — 成文问题与定范围 → 产出形制与时间盒（**用户关卡**）→ `init` 铸骨架。
2. `steps/02-scan.md` — 目录结构 / 技术栈与入口点 → 配置与构建管线（**广度侦察，不深挖**）。
3. `steps/03-map.md` — 组件清单（铸 `AN-<nn>`）→ 数据流端到端 → 层 / 集成 / 状态 / 依赖 / 模式。
4. `steps/04-document.md` — 架构总览与 Mermaid 图 → 风险与建议 → 定稿、终门、渲染。

写回纪律：骨架由第 1 步的 `init` 铸为 `project.status: 草稿`；`project.name` / `created` 由 `init` 铸造后**不再由你改**；定稿 = `project.status: 已定稿`。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/analysis.yaml` —— 唯一源头；顶层设 `project.status`（母本 §8 两值口径）：

```yaml
project: {name, created, updated, status}   # status: 草稿|已定稿；created 建文件时设、此后不改
question: {text, scope, output_format, time_box, codebase}   # 源 step-01 的四项定义 + 被分析路径
architecture: {summary, tech_stack: [], overview, mermaid: "<字符串>", patterns: [], layers: []}
components: [{id: AN-01, name, layer, responsibility, location, status}]
                     # layer: 展示层|应用层|领域层|基础设施层|未分层；status: 已核实|待核实
data_flow: [{name, steps: [<string>], components: [AN-<nn>]}]   # 端到端，至少一条
dependencies: [{from, to, note}]            # from/to 引 AN-<nn>，或写外部系统名
risks: [{risk, severity: 高|中|低, location, impact}]
recommendations: [{action, priority: 高|中|低, effort, target}]   # 按 priority 降序排列
revisions: []                               # {date, change, reason} —— 改既有条目时追加
```

Mermaid 图住在 `architecture.mermaid` 的**字符串字段**里（不落散文件）；定稿前至少一张。

## 规则

1. **写范围**：只写 `{output_dir}/analysis.yaml`；**对代码库只读**——不改一行代码、不建任何扫描状态散文件、不产 markdown 文档集。
2. **检查点四选项**（每步产出后，六拍不得省）：① 生成本步产出 → ② 落盘（编辑对应键 / 记录）→ ③ 显示检查点分隔 → ④ 呈出本步产出 → ⑤ 出四选项 → ⑥ 等响应。
3. **选项落点**：`[a]` → 调 `diy-elicit`；`[p]` → 调 `diy-party-mode`（两者**零写面**，返回后回第 ② 拍重落盘）；`[c]` → 进下一步；`[y]` → 后续跳过 ⑤⑥，**②③④ 照旧**。无头 / 非交互 = 全程 `[y]`（摘要一行明示），**不入 `deferred-actions` 队列**。
4. **ID 体系**：`AN-<nn>` 两位序号、顺序递增、不重编不复用——`init` 铸骨架，记录号由你按序铸、引擎核唯一性与顺序性（重号 / 跳号 / 形态非法各判违规）。
5. **取证纪律**：`status: 已核实|待核实`——直接读到的记 `已核实`，由文档 / 命名推断的记 `待核实`；**绝不把推断写成事实**。
6. **终门（机械）**：先落 `project.status: 已定稿`，再跑 `python "{project-root}/.claude/skills/diy-analyze/scripts/analyze.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——`exit 0` 是唯一放行；零 `[假设]`（未决项写 `revisions` 或就地补问）。渲染与收尾都等 exit 0。
7. **违规码**：复用冻结集（`MISSING_FILE` / `UNPARSABLE_YAML` / `EMPTY_FIELD` / `ENUM_INVALID` / `DUPLICATE_ID` / `UNKNOWN_ID` / `SET_MISMATCH` / `STATUS_MISMATCH` / `ASSUMPTION_PRESENT`）；**本技能零新增码**。
8. **无 `--previous` 轮**：`components[]` 只增不减，无 ID 集合收缩面；改既有记录往 `revisions` 追加（date / change / reason，`change` 点名 `AN-<nn>` 而不复制内容）。副作用面：除产物与静默渲染外无任何外部动作；产物内引用一律 project-root 相对 `path:line`。
9. **边界（对方侧随 C 阶段补；本技能产 anytime 独立产物——不进主链 CHAIN、不被任何门禁引用）**：vs `diy-architecture`——**方向相反**：它是决策式（逐条 `affects` 引 FR ID、`status: 已定稿`），面向「要做什么」；本技能是文献式，面向「现状是什么」。vs 用户级 `arch-analyze`——见激活段第 3 步的边界句。vs `diy-spec-scan`——它扫**规格文本**的执行歧义，本技能扫**代码库结构**（≈0 重叠）。vs `diy-project-context`——它产项目语境档供 AI 上下文，本技能回答一个**具体问题**。vs `diy-investigate`——它是缺陷取证，本技能是架构取证。vs `diy-elicit` / `diy-party-mode`——不是竞争是调用（见规则 3）。
10. **不可机械的部分写明**：技术取舍、风险定级、建议排序**是人工判定**——引擎只核枚举、必填与顺序；凡推断一律记 `待核实`，不得与事实混写。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
