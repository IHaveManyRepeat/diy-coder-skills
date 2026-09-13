# BMAD 官方方法论技能全景图

> 生成日期：2026-09-13 ｜ 数据源：`_bmad/_config/bmad-help.csv` + `skill-manifest.csv` + 各技能实体文件
> 按模块划分，逐技能展开三类可选分支：技能内部菜单/动作、技能之间依赖编排、模块级可选路径。

## 总览

| 指标 | 数值 |
| --- | --- |
| 技能总数 | 94 |
| 本机已装实体 | 86 |
| 含内部菜单 | 65 |
| 含流程步骤 | 67 |

### 模块分布

| 模块 | 技能数 | 定位 |
| --- | --- | --- |
| [Core 核心层](#core) | 12 | 跨模块通用能力：头脑风暴、对抗评审、文档处理、规格提炼、定制覆盖 |
| [BMad Method 主流程](#bmm) | 32 | 主线开发流程：从分析到规划、方案设计、迭代实现 |
| [BMad Builder 构建器](#bmb) | 5 | 元能力：构建与质检 Agent、工作流、模块本身 |
| [Test Architecture Enterprise](#tea) | 10 | 测试架构企业版：风险驱动测试设计到追溯门禁的完整流水线 |
| [Creative Intelligence Suite](#cis) | 10 | 创意智能套件：创新策略、问题求解、设计思维、叙事 |
| [Web Design Studio](#wds) | 23 | Web 设计工作室：从产品简报、触发映射到 UX 规格与交付 |
| [BMad Automator 自动化](#automator) | 2 | 自动化执行：无人值守跑通故事构建与审查循环 |

## Core 核心层

共 12 个技能。跨模块通用能力：头脑风暴、对抗评审、文档处理、规格提炼、定制覆盖

### 阶段与依赖编排

| 阶段 | 技能 |
| --- | --- |
| anytime | BSP `bmad-brainstorming`（Brainstorming）<br>BC `bmad-customize`（BMad Customize）<br>EP `bmad-editorial-review-prose`（Editorial Review - Prose）<br>ES `bmad-editorial-review-structure`（Editorial Review - Structure）<br>BH `bmad-help`（BMad Help）<br>ID `bmad-index-docs`（Index Docs）<br>PM `bmad-party-mode`（Party Mode）<br>AR `bmad-review-adversarial-general`（Adversarial Review）<br>ECH `bmad-review-edge-case-hunter`（Edge Case Hunter Review）<br>SD `bmad-shard-doc`（Shard Document）<br>SP `bmad-spec`（Spec） |
| 未标阶段 | `bmad-advanced-elicitation`（Advanced Elicitation） |

#### `bmad-brainstorming` — Brainstorming

*工作流 ｜ 本机已装*

引导式头脑风暴会话：完成会话设置（议题、目标、续接检测）后，用户从四种方式选择技法（自选、AI 推荐、随机、渐进流程），在选定技法下持续发散——目标是 100+ 个经用户对话共同发展的想法（协作产出，非批量生成清单），最后收敛为组织好的想法与行动规划。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 指向 ./workflow.md；workflow.md 负责配置加载与输出路径解析后转 ./steps/ 系列 micro-file 步骤（每步一个自包含文件，frontmatter 记录进度）
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：{output_folder}/brainstorming
- **产出物**：brainstorming session
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-brainstorming`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `1` | 用户自选技术 | `User-Selected Techniques` | 浏览完整技术库（brain-methods.csv，61 个技术、10 类）并自行挑选 |
| `2` | AI 推荐技术 | `AI-Recommended Techniques` | 分析会话目标、约束与偏好，从技术库匹配推荐并说明理由 |
| `3` | 随机选择技术 | `Random Technique Selection` | 随机抽取互补技法组合，制造意料之外的发现 |
| `4` | 渐进式技术流 | `Progressive Technique Flow` | 设计从发散到收敛的分阶段技法序列，系统性推进创意旅程 |

**流程步骤**

1. **步骤 1：会话设置与续接检测** — 检查既有会话文件（只列文件名不读内容），询问继续/新建/查看全部；收集议题与目标，初始化会话文档 frontmatter，并让用户四选一技术选取方式。
2. **步骤 1b：工作流续接** — 仅在选择继续已有会话时进入：加载现有文档与 frontmatter 进度，列出已完成内容与剩余选项，不重复提问。
3. **步骤 2a：用户自选技术** — 充当技术图书管理员：按类别呈现 brain-methods.csv 技术库，由用户自行挑选，提供 [B] 返回 / [C] 继续。
4. **步骤 2b：AI 推荐技术** — 分析会话目标、约束与偏好，从技术库匹配推荐组合并给出理由，等待用户确认。
5. **步骤 2c：随机选择技术** — 随机抽取互补的技术组合制造意外发现，不干预或二次猜测随机结果。
6. **步骤 2d：渐进式技术流** — 设计从发散到收敛的分阶段技法旅程，给出旅程地图并等待确认。
7. **步骤 3：交互式技法执行** — 在选定技法下逐元素引导发散：一次至多提出一个新想法/挑衅/角度后等待用户输入，目标 100+ 个协作式想法（不批量生成），默认持续探索直到用户明确要求收敛。
8. **步骤 4：想法组织与行动规划** — 收敛整理全部想法，按优先级归类并形成可执行的下一步，完成会话文档与 frontmatter 收尾。

> 备注：同一 canonicalId 被 3 个模块重复登记：BMad Method 的 BP（phase 1-analysis、输出 planning_artifacts）、Core 的 BSP（anytime）、CIS 的 BS（anytime），故基线含 3 条 helpEntries；dependencies 顶层取 Core 主注册 BSP。技能内另有会话续接菜单 [1] 继续现有会话 / [2] 新建 / [3] 查看全部。

#### `bmad-customize` — BMad Customize

*工具 ｜ 本机已装*

把用户的定制意图翻译成正确落位的 TOML 覆盖文件（写入 {project-root}/_bmad/custom/）：分类意图（定向/探索/审计迭代/跨面）→ 用自带脚本枚举可定制技能 → 读目标的 customize.toml 确定 agent 或 workflow 覆盖面 → 按合并语义撰写稀疏覆盖（标量覆盖、数组追加、键控表按键合并）→ 选择团队/个人落位 → 展示确认后写入并用 resolve_customization.py 验证合并结果。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联（Preflight → Activation → Step 1-6 → Complete when），无独立流程文件；发现阶段调用技能自带 scripts/list_customizable_skills.py
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：{project-root}/_bmad/custom
- **产出物**：TOML override files
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-customize`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：技能根含 scripts/（list_customizable_skills.py 及其测试），扫描同级技能目录中的 customize.toml 并按 agent/workflow 分类；写入后依赖 {project-root}/_bmad/scripts/resolve_customization.py 验证，脚本缺失时回退人工合并说明。v1 范围仅限单技能 [agent]/[workflow] 覆盖，中央 config.toml 不在范围内。

#### `bmad-editorial-review-prose` — Editorial Review - Prose

*工具 ｜ 本机已装*

临床校对式文字评审：只修阻碍理解的沟通问题（语法、歧义、冗余等），不改观点、不做风格偏好改写，逐条给出最小修正，输出三列表格（原文 / 建议改法 / 改动说明）。可按读者类型（humans / llm）校准，并支持项目 style_guide 覆盖。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联 STEPS（Step 1-4），含 PRINCIPLES 与 HALT 条件，无独立流程文件
- **参数**：`[path]`
- **前置**：—
- **后续**：—
- **产出位置**：report located with target document
- **产出物**：three-column markdown table with suggested fixes
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-editorial-review-prose`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

#### `bmad-editorial-review-structure` — Editorial Review - Structure

*工具 ｜ 本机已装*

结构性评审，应在文字校对之前运行：按文档用途选择结构模型（教程 / 参考 / 解释 / 提示 / 战略），逐节评估存留价值，产出切分 / 合并 / 移动 / 压缩 / 质询 / 保留六类建议及预计缩减量。对 humans 读者保留理解辅助要素，对 llm 读者追求精度与密度。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联 STEPS（Step 1-6），含 Structure Models、Human/LLM Reader Principles 与 HALT 条件
- **参数**：`[path]`
- **前置**：—
- **后续**：—
- **产出位置**：report located with target document
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-editorial-review-structure`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

#### `bmad-help` — BMad Help

*工具 ｜ 本机已装*

BMad 导航与答疑：以 bmad-help.csv 目录（含 phase、preceded-by / followed-by 排序提示、required 门禁）为主数据源，结合配置与已产出的产物判断用户所处模块与阶段，解释菜单码与调用方式，推荐下一步应运行的技能（含参数），当下一步唯一明确时可直接提议帮你运行。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联（Purpose / Data Sources / CSV Interpretation / Response Format），无步骤文件
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-help`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

#### `bmad-index-docs` — Index Docs

*工具 ｜ 本机已装*

为指定文件夹生成或更新 index.md：扫描目录内容、按类型或用途分组、逐个读取文件内容生成 3-10 词简介，输出带 ./ 相对链接的索引文件（含子目录分组）。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联 EXECUTION（Step 1-4）与 OUTPUT FORMAT 模板
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-index-docs`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

#### `bmad-party-mode` — Party Mode

*Agent 角色 ｜ 本机已装*

多智能体圆桌：经 resolve_config.py 解析 agent 名单（_bmad 基础配置与 custom 覆盖共四层合并）后挑选 2-4 个相关角色，用 Agent 工具并行派生真实 subagent（各自独立判断、允许互相反对），逐条完整呈现观点并支持点名追问与交叉回应；--solo 模式退回单模型扮演全部角色。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联（On Activation + The Core Loop + Follow-ups），无步骤文件
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-party-mode`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `--model <model>` | 指定模型 | `--model` | 强制所有子代理使用指定模型（如 haiku、opus）；缺省时按话题深度为每轮选择合适模型 |
| `--solo` | 单人模式 | `--solo` | 不派生子代理，由编排者自己扮演所有角色响应（子代理不可用或更看重速度时使用） |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：支持 --model / --solo 调用参数（SKILL.md Arguments 一节），这两个参数未登记进 help CSV 的 args 字段。agent 名单由 resolve_config.py 输出（字段：code、name、title、icon、description、module、team），不再读取 agent-manifest.csv。

#### `bmad-review-adversarial-general` — Adversarial Review

*工具 ｜ 本机已装*

对抗式审查：以冷漠挑剔的审查者姿态全面挑刺（默认至少给出 10 条发现，零发现本身视为可疑），只列问题清单、不下结论、不做人身攻击。用于交付前的质量施压，其它模块的代码评审会内联调用它。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联 EXECUTION（Step 1-3）与 HALT 条件
- **参数**：`[path]`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-review-adversarial-general`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

#### `bmad-review-edge-case-hunter` — Edge Case Hunter Review

*工具 ｜ 本机已装*

边界条件猎人：机械枚举范围内每条分支路径与边界条件（控制流 + 领域边界），只报告未处理的路径，严格输出 JSON 数组（location / trigger_condition / guard_snippet / potential_consequence）。方法驱动而非态度驱动，与对抗审查正交互补。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联 EXECUTION（Step 1-4）与 OUTPUT FORMAT（严格 JSON）
- **参数**：`[path]`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-review-edge-case-hunter`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

#### `bmad-shard-doc` — Shard Document

*工具 ｜ 本机已装*

大文档分片：按二级标题把 Markdown 拆分为组织化的小文件（默认输出到与源文件同名的文件夹），调用 npx @kayvan/markdown-tree-parser explode 执行，校验分片与 index.md 生成，最后让用户决定原文档去留（删除 / 归档 / 保留）。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联 EXECUTION（Step 1-6），无独立流程文件
- **参数**：`[path]`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-shard-doc`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `d` | 删除原文档 | `Delete` | 删除原始大文档（推荐选项，分片可按序拼接还原） |
| `m` | 移入归档 | `Move to archive` | 把原文档移动到同目录 archive 子文件夹（可自定义归档路径） |
| `k` | 保留原文档 | `Keep` | 原文档留在原地（不推荐：会造成重复内容，且输入发现协议可能加载错版本） |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：实际拆分依赖外部 npm 包 @kayvan/markdown-tree-parser（通过 npx 调用）。

#### `bmad-spec` — Spec

*工作流 ｜ 本机已装*

把任意意图输入（简报、PRD、GDD、RFC、访谈记录、脑暴、多源混合）提炼为 SPEC.md 五字段内核（Why / Capabilities / Constraints / Non-goals / Success signal）+ 伴随文件，形成下游技能共同消费的机器契约；每次创建或更新后做连贯性与保全性双重自检并写决策日志，同一 slug 再次调用为原地更新且能力 ID 保持稳定。

- **阶段**：anytime
- **门禁**：可选
- **入口**：SKILL.md 内联（On Activation → Workspace → The Operation → Spec Law → Self-Validate → Output）；支持 interactive/headless 双模式，headless 按 assets/headless-schemas.md 返回 JSON
- **参数**：`[path]`
- **前置**：—
- **后续**：—
- **产出位置**：{output_folder}/specs/spec-{slug}
- **产出物**：SPEC.md + companion files
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-spec`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `express` | 快速提炼 | `Express` | 输入稀疏时尽力提炼，每个缺口记入 open_questions[]；headless 模式默认此项并记录选择 |
| `guided` | 引导式提炼 | `Guided` | 输入稀疏时与用户逐项走完五个内核字段；interactive 模式下由用户选择 |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：技能根含 customize.toml（顶层 [workflow] 块，暴露 spec_template、spec_output_path、run_folder_pattern、on_complete、persistent_facts 等可覆盖字段，BMAD 官方据此将其归为 workflow 类型）与 assets/（五字段模板、headless JSON schema）；无独立 workflow.md，流程内联在 SKILL.md。headless 模式定义 error_code：insufficient_intent（输入过薄）、missing_slug（缺 slug）。

#### `bmad-advanced-elicitation` — Advanced Elicitation

*工具 ｜ 本机已装*

在已有产出上叠加批判与增强方法：加载方法库 methods.csv（69 个方法、12 类），按当前上下文的类型与复杂度智能挑选 5 个方法供用户选择，套用后给出增强版本并询问是否应用；可独立使用，也可被其他技能间接调用以增强指定章节。

- **阶段**：—
- **门禁**：可选
- **入口**：SKILL.md 内联 FLOW（Step 1-3 + INTEGRATION 间接调用协议），无独立流程文件；方法库为同级 methods.csv；当 party-mode 可能参与时，经 _bmad/scripts/resolve_config.py 解析 agent 名单
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-advanced-elicitation`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `1-5` | 选择方法（动态 1-5） | `Select Method` | 从当前呈现的 5 个引导方法中选择一个执行；执行后询问是否把改动应用到文档，并再次回到本菜单 |
| `r` | 重新洗牌 | `Reshuffle` | 从方法库随机抽取 5 个新方法替换当前列表，尽量覆盖不同类别 |
| `a` | 列出全部方法 | `List All` | 以紧凑表格列出方法库全部 69 个方法及描述，可按名称或编号选择 |
| `x` | 继续 / 结束增强 | `Proceed / No Further Actions` | 结束本轮增强；若为间接调用则把增强后的内容返回给调用技能替换原章节 |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：该技能在项目级 .claude/skills 下有实体，但未登记进 help 目录（inHelpCatalog 为 false）：所有 module-help.csv 与主 bmad-help.csv 均无其行，仅出现在 skill-manifest.csv，因此无菜单码、基线 helpEntries 为空，dependencies 各字段如实留空。displayName 取自 SKILL.md 一级标题，非目录登记。


## BMad Method 主流程

共 32 个技能。主线开发流程：从分析到规划、方案设计、迭代实现

### 阶段与依赖编排

| 阶段 | 技能 |
| --- | --- |
| 1-analysis | `bmad-domain-research`<br>`bmad-market-research`<br>`bmad-prfaq`<br>`bmad-product-brief`<br>`bmad-technical-research` |
| 2-planning | `bmad-prd` `必需`<br>`bmad-ux` |
| 3-solutioning | `bmad-check-implementation-readiness` `必需`<br>`bmad-create-architecture` `必需`<br>`bmad-create-epics-and-stories` `必需` |
| 4-implementation | `bmad-checkpoint-preview`<br>`bmad-code-review`<br>`bmad-create-story`<br>`bmad-dev-story` `必需`<br>`bmad-investigate`<br>`bmad-qa-generate-e2e-tests`<br>`bmad-retrospective`<br>`bmad-sprint-planning` `必需`<br>`bmad-sprint-status` |
| anytime | `bmad-agent-tech-writer`<br>`bmad-correct-course`<br>`bmad-document-project`<br>`bmad-generate-project-context`<br>`bmad-quick-dev` |
| 未标阶段 | `bmad-agent-analyst`<br>`bmad-agent-architect`<br>`bmad-agent-dev`<br>`bmad-agent-pm`<br>`bmad-agent-ux-designer`<br>`bmad-create-prd`<br>`bmad-edit-prd`<br>`bmad-validate-prd` |

#### `bmad-domain-research`

*工作流 ｜ 本机已装*

对某个行业/领域做基于实时联网数据的系统性调研，产出带引用的权威研究文档（行业结构、监管、技术趋势、竞争格局、供应链）。要摸清一个行业再决定做什么时使用。

- **阶段**：1-analysis
- **门禁**：可选
- **入口**：{'command': 'bmad-domain-research', 'args': [], 'howZh': '按技能名调用。前提条件是必须能联网检索，否则应中止并告知用户。激活后先做主题快速发现（主题/目标/范围），再复制 research.template.md 建初始文件并载入 step-01。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：planning_artifacts\|project_knowledge
- **产出物**：research documents
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-domain-research`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **范围确认** — 与用户确认领域调研的范围与方法论（不开始检索），确认后写回文档并进入下一步。
2. **行业分析** — 聚焦市场规模、增长与行业动态做分析，并用联网检索核实现状。
3. **竞争格局** — 分析主要玩家、市场份额与竞争动态，检索核实。
4. **监管合规** — 聚焦影响该主题的法规与合规要求做专题分析。
5. **技术趋势** — 分析创新与新兴技术对该领域的影响，全部基于实时联网数据。
6. **综合成文与收尾** — 生成含执行摘要、目录、10 章正文与来源核验说明的完整研究报告，替换文首占位段并标记流程完成。

> 备注：step-06 的跨步引用编号与文件名错位：正文写“regulatory focus from step-03 / technical trends from step-04”，但监管实为 step-04、技术趋势实为 step-05（step-03 是竞争格局），疑似沿用旧版编号。step-06 的完成协议里 stepsCompleted 也写成了 [1,2,3,4,5]，漏 6，同文件另一处又写 [1,2,3,4,5,6]。全流程无“可跳过”步骤标注。输出文件命名：{planning_artifacts}/research/domain-{slug}-research-{date}.md。

#### `bmad-market-research`

*工作流 ｜ 本机已装*

围绕客户与竞争做市场调研：客户行为与分层、痛点与需求、决策路径，再到竞争格局，最终产出带引用的市场研究报告。需要判断“这个市场值不值得做”时使用。

- **阶段**：1-analysis
- **门禁**：可选
- **入口**：{'command': 'bmad-market-research', 'args': [], 'howZh': '按技能名调用。同 domain-research：必须能联网检索否则中止；先快速发现主题/目标/范围，再建 research 文件并载入 step-01。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：planning_artifacts\|project-knowledge
- **产出物**：research documents
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-market-research`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **初始化与范围确认** — 确认对研究主题的理解并确立清晰的研究范围。
2. **客户行为与分层** — 分析客户行为模式与人群分层特征。
3. **客户痛点与需求** — 梳理客户的挑战、挫败点与真实需求。
4. **客户决策与旅程** — 分析决策因素并绘制客户决策旅程。
5. **竞争分析** — 聚焦市场定位做全面竞争分析。
6. **综合成文与完成** — 产出含叙事性导言、详细目录与执行摘要的权威市场研究报告。

> 备注：全流程无“可跳过”步骤标注。输出文件命名：{planning_artifacts}/research/market-{slug}-research-{date}.md。CSV 的 outputLocation 用竖线并列 planning_artifacts\|project-knowledge，与 domain-research 的 planning_artifacts\|project_knowledge 写法不一致（同一含义两种拼法）。

#### `bmad-prfaq`

*工作流 ｜ 本机已装*

用亚马逊 Working Backwards 的 PRFAQ 方法锻造并拷问产品概念：先写“成品发布新闻稿”，再让客户几乎不可能回答的难题与内部可行性问题轮番质问，最后给出诚实判定。概念是否值得投入、要留档一份 PRFAQ 时使用。

- **阶段**：1-analysis
- **门禁**：可选
- **入口**：{'command': 'bmad-prfaq', 'args': ['-H', '--headless'], 'howZh': '按技能名调用即进入完整教练式“拷问”；加 --headless / -H 则依据给定上下文直接产出首稿（只校验输入 schema：customer/problem/stakes/solution 四项必需且不可含糊）。存在 {planning_artifacts}/prfaq-{project_name}.md 时仅读前 20 行 frontmatter 判断 stage 并询问是否续跑。'}
- **参数**：`-H`
- **前置**：—
- **后续**：—
- **产出位置**：planning_artifacts
- **产出物**：prfaq document
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-prfaq`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **前置准备** — 续跑检测 + 模式判定（headless 或完整交互）；随即定调：这不是温和探索，而是概念压力测试。
2. **Stage 1 点火** — 把原始概念摆上桌并强制客户优先：识别概念类型、采集客户/问题/利害/方案四要素，随后并行派出资料分析子代理与联网调研子代理，建档并写入首段内容。
3. **Stage 1 加速与退路** `可跳过` — 首条消息即含四要素可确认后直接建档进入下一阶段；若 2-3 轮后仍说不清客户或问题，则建议改用 bmad-brainstorming 继续发散。
4. **Stage 2 新闻稿** — 按标题→副标题→开篇→问题段→方案段→领导人引言→How It Works→客户引言→Getting Started 逐节锻造，标准是“无行话、无空话、经得起 so what 追问”。
5. **Stage 3 客户 FAQ** — 化身被辜负过的忙碌客户提出 6-10 个最狠的问题（怀疑、信任、实用、边界、最不敢答的那题），逐题给出诚实且具体的回答。
6. **Stage 4 内部 FAQ** — 换到工程/财务/法务/运营/CEO 视角提 6-10 题：可行性、商业可行性、资源现实、风险、战略契合，以及创始人不愿面对的那一题。
7. **Stage 5 判定与定稿** — 给出概念强度叙述式判定，分「已锻造成钢 / 还需加热 / 地基裂缝」三类结论，定稿 PRFAQ，并始终产出下游 PRD 用的蒸馏稿（distillate）。

> 备注：该技能自带的 bmad-manifest.json 声明 preceded-by=[brainstorming, perform-research]、followed-by=[create-prd]、phase-name=1-analysis，而基线 help CSV 的对应字段全为空——两个来源的依赖信息不一致（CSV 缺依赖）。产出物为两份：prfaq-{project_name}.md 与 prfaq-{project_name}-distillate.md，后者 CSV 未体现。Args -H 在 SKILL.md 有定义；-A 只出现在 product-brief 的 CSV，见该技能备注。

#### `bmad-product-brief`

*工作流 ｜ 本机已装*

通过对话式教练帮用户写出一份“尺寸合适”的产品简介（Product Brief）：不催、不代想、答案单薄就追问，最终产出 1-2 页能直接喂给 PRD 的 brief。已有明确概念、需要一页纸去说服别人时使用。

- **阶段**：1-analysis
- **门禁**：可选
- **入口**：{'command': 'bmad-product-brief', 'args': [], 'howZh': '按技能名调用；激活后问候并识别意图 create/update/validate。无 PRD 之前的轻量概念文档入口，也可由 bmad-agent-analyst 的 CB 菜单分派。'}
- **参数**：`-A`
- **前置**：—
- **后续**：—
- **产出位置**：planning_artifacts
- **产出物**：product brief
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-product-brief`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `create` | 创建简介 | `Create` | 先 Discovery 再成文；绑定 {planning_artifacts}/briefs/brief-{project_name}-{date}/ 并写出 brief.md 骨架（status: draft）与 .decision-log.md |
| `update` | 更新简介 | `Update` | 用变更信号对齐既有 brief 与 decision-log；改前先摆出与既往决定的冲突；若属根本性变更则建议改走 Create |
| `validate` | 校验简介 | `Validate` | 按 brief 自身目的做诚实点评，引用具体句子；结论直接对话内返回，除非用户要求单独成文 |
| `fast-path` | 快速路径 | `Fast path` | 把剩余缺口合并成一两次提问后直接成稿，推断处打 [ASSUMPTION] 标记；适合“明天就要讲” |
| `coaching-path` | 教练路径 | `Coaching path` | 逐步共创、对薄弱假设当场追问、逐节起草；适合想写出自己满意的 brief 且时间不紧 |

**流程步骤**

1. **激活与意图识别** — 解析 customization、执行 prepend、载入持久事实与 config，问候并判定 create/update/validate；headless 走无交互分支。
2. **Discovery 脑暴倾倒** — 先请用户把全貌倒出来并交上已有素材；读完现有材料再补问缺失信息，末尾一句“还有别的吗？”常能带出遗忘项。
3. **风险级别校准** — 尽早判断投入级别（业余项目/内部提案/投资输入/公开发布），据此决定追问力度与文档精细度。
4. **工作模式二选一** — Fast path（批量补齐缺口 + [ASSUMPTION] 标记）或 Coaching path（逐步共创、当场追问）。
5. **联网调研子代理** — 倒料期间并行派 web 调研子代理摸清行业与可比产品，父会话只收摘要；深度市场/领域工作则转荐 bmad-market-research 或 bmad-domain-research。
6. **Finalize 1 决策日志审计** — 逐条过 .decision-log.md，明确每条内容是进 brief、进 addendum 还是作为过程噪音搁置。
7. **Finalize 2 润色** — 并行子代理按 doc_standards（默认结构评审 + 文字评审两个技能）先 brief.md 后 addendum.md 施加。
8. **Finalize 3 外部交接** `可跳过` — 执行 external_handoffs 把产物送往 Confluence/Notion/工单等，回显 URL/ID；工具不可用则跳过并标注。
9. **Finalize 4 交付并指路** — 告知本地路径与外部落点，并调用 bmad-help 建议下一步。

> 备注：help CSV 给的 args 是 -A，但 SKILL.md 正文未定义 -A（正文只讲 headless 行为，未给旗标名），两者对不上。addendum.md 的角色是承接不属于 brief 主体但需要留档的深度内容，须在对话过程中就写、不必等到 finalize。CSV 的 output-location 写 planning_artifacts，实际落点是 {planning_artifacts}/briefs/brief-{project_name}-{date}/。

#### `bmad-technical-research`

*工作流 ｜ 本机已装*

对技术选型做基于实时联网数据的调研：技术栈、集成方式、架构模式、落地实现路径，最终产出带引用的技术研究报告。要在几个技术方案之间做取舍时使用。

- **阶段**：1-analysis
- **门禁**：可选
- **入口**：{'command': 'bmad-technical-research', 'args': [], 'howZh': '按技能名调用。必须能联网检索否则中止；先快速发现主题/目标/范围，再建 research 文件并载入 step-01。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：planning_artifacts\|project_knowledge
- **产出物**：research documents
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-technical-research`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **范围确认** — 与用户确认技术调研的范围与方法。
2. **技术栈分析** — 分析语言、框架、工具与平台，联网核实当前事实。
3. **集成模式** — 分析 API、通信协议与系统互通的集成模式。
4. **架构模式** — 围绕设计取舍与实现方式做架构模式分析。
5. **实现路径调研** — 聚焦可落地的实现方式与技术采用策略。
6. **综合成文与完成** — 产出含叙事导言、详细目录与执行摘要的权威技术研究报告。

> 备注：全流程无“可跳过”步骤标注。输出文件命名：{planning_artifacts}/research/technical-{slug}-research-{date}.md。三个 research 技能结构同族（SKILL.md 做主题发现 + 6 个 step 文件），仅步骤目录名与内容主题不同。

#### `bmad-prd`

*工作流 ｜ 本机已装*

由资深教练陪跑，创建、更新或校验一份与投入级别匹配的高质量 PRD：创建走 Discovery 挖需求，更新按变更信号对齐既往决策，校验只批改不动稿并产出 HTML 报告。需要一份能直接驱动 UX/架构/Epics 的 PRD 时使用。

- **阶段**：2-planning
- **门禁**：必需
- **入口**：{'command': 'bmad-prd', 'args': [], 'howZh': '按技能名调用；技能自己从对话判定意图（Create/Update/Validate），也可由 bmad-agent-pm 的 PRD 菜单或三个弃用垫片带 intent 转入。headless 调用走 references/headless.md 全流程。'}
- **参数**：`—`
- **前置**：bmad-product-brief
- **后续**：—
- **产出位置**：planning_artifacts
- **产出物**：prd
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-prd`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `create` | 创建 PRD | `Create` | 无既有 PRD 时：先查是否有未完成的 prd-* run 可供续跑，再绑定工作目录、建 prd.md（status: draft）与 .decision-log.md，然后 Discovery → Finalize |
| `update` | 更新 PRD | `Update` | 有既有 PRD 时：对 PRD、addendum、decision-log 与原始输入做来源抽取式对账，先摆出与既往决定的冲突再改动，随后直接进 Finalize |
| `validate` | 校验 PRD | `Validate` | 只批改不改稿：跑评审门 + 合成流水线，产出 validation-report.html 与 .md 并自动打开浏览器；结束后不执行 Finalize |
| `fast-path` | 快速路径 | `Fast path` | Discovery 工作模式之一：把剩余缺口合并成一两次提问后直接成稿，推断处打 [ASSUMPTION] 标记 |
| `coaching-path` | 教练路径 | `Coaching path` | Discovery 工作模式之一：共同走 PM 思考段落；入口再二选一——Vision + Features（能力优先）或 Journey-led（用户旅程优先），也可让 AI 建议 |

**流程步骤**

1. **激活与意图判定** — 解析 customization、执行 prepend、载入持久事实与配置；headless 转 headless 手册，否则问候并做误路由分流（一页纸→product-brief、验证点子→prfaq 等）。
2. **Create：续跑检测与建工作区** `可跳过` — 扫 prd_output_path 下未完成的 run 并询问是否续跑；否则绑定 {planning_artifacts}/prds/prd-{project}-{date}/ 并写 prd.md 骨架与决策日志。
3. **Discovery：脑暴倾倒** — 无论用户是否已铺垫背景，都先请其口述背景并交出已有输入（brief、调研、访谈等）；大文档交给子代理抽取，末尾补一句“还有别的吗？”。
4. **Discovery：联网调研子代理** `可跳过` — 默认并行派 web 调研子代理摸清同类产品与当前格局，父会话只收摘要。
5. **Discovery：风险校准与工作模式** — 先用一次短探校准 rigor（业余/内部/发布），再让用户选 Fast path 或 Coaching path；Coaching 下再选 Vision+Features / Journey-led 入口，选完即定章节顺序。
6. **Discovery：关注点扫描与形态确认** — 点名该产品真实承载的关注点（合规、集成密度、SLA、硬件约束、计费、数据治理等）以决定引入哪些模板章节；未言明形态时追问 mobile/web/desktop/多端/硬件/API。
7. **Discovery：用户旅程采集** `可跳过` — 旅程是采集而非创作：请用户以有名有姓的主角讲述真实使用过程，再整理为 UJ-N 并确认；内部工具、纯技术 PRD 等场景可降级或省略。
8. **成稿：Essential Spine + Adapt-In Menu** — 默认写全 Essential Spine（Vision/Target User/Glossary/Features+NFR/MVP/Success Metrics 等），按关注点引入 Adapt-In Menu 章节；篇幅随投入级别伸缩，溢出内容进 addendum.md。
9. **Finalize 1 决策日志审计** — 逐条过 .decision-log.md，明确每条被 PRD、addendum 吸收还是搁置。
10. **Finalize 2 输入对账** — 每个用户提供的输入配一个子代理对账 prd.md/addendum.md，产出 reconcile-{slug}.md 并只回摘要，重点捞定量结构漏掉的定性想法。
11. **Finalize 3 评审门** `可跳过` — 组菜单：rubric walker（默认项）+ finalize_reviewers + 临时评审；并行子代理各自写 review-{slug}.md 只回摘要，父会话分层呈现结论。低投入场景可静默执行或跳过。
12. **Finalize 4 开放项分级** — 逐个处理 Open Questions、[ASSUMPTION]、[NOTE FOR PM]：phase-blocker 一对一解决，非阻塞项带责任人与复查条件记入决策日志。
13. **Finalize 5 润色** — 按 doc_standards（默认结构评审 + 文字评审两个技能）先结构后文字施加于 prd.md 与 addendum.md；跨文档并行、单文档串行。
14. **Finalize 6 外部交接** `可跳过` — 执行 external_handoffs 把产物送出本地（Confluence/Notion 等）并回显 URL；工具不可用则跳过并标注。默认配置为空数组。
15. **Finalize 7 收尾** — 把 frontmatter status 置 final、更新时间戳、记录定稿，交付路径并提示常见下一步（bmad-ux / bmad-create-architecture / bmad-create-epics-and-stories）。
16. **Validate：评审与合成报告** `可跳过` — 跑评审门后必须走合成流水线：读全部 review-*.md，按评分卡七维度填 HTML 模板（Excellent/Good/Fair/Poor 四档），写 validation-report.html 与 .md 并打开浏览器（headless 跳过打开）。

> 备注：CSV 是唯一必填技能（required=true），且明确 preceded-by=bmad-product-brief，但 PRFAQ 路径并未在依赖里体现（bmad-manifest.json 的 prfaq 声明 followed-by=create-prd，链路靠 skill 文本自述）。校验评分卡为七维度：Decision-readiness / Substance over theater / Strategic coherence / Done-ness clarity / Scope honesty / Downstream usability / Shape fit。内部小矛盾：references/validate.md 说评审门默认会派 adversarial-general 评审员，而 customize.toml 的 finalize_reviewers 默认是空数组（需用户或组织 override 追加）。该技能在基线中 installedAs 为 null，但项目 .claude/skills/bmad-prd/ 实体齐全。

#### `bmad-ux`

*工作流 ｜ 本机已装*

以“采集而非代笔”的教练方式帮用户产出两份并列契约：DESIGN.md（视觉身份，遵循 Google Labs 规范）与 EXPERIENCE.md（信息架构、行为、状态、交互、可访问性、关键流程）。PRD 之后要把界面与体验定下来时使用。

- **阶段**：2-planning
- **门禁**：可选
- **入口**：{'command': 'bmad-ux', 'args': [], 'howZh': '按技能名调用（或由 bmad-agent-ux-designer 的 CU 菜单分派）；技能自行判定 Create/Update/Validate 意图，headless 调用走 references/headless.md。'}
- **参数**：`—`
- **前置**：bmad-prd
- **后续**：—
- **产出位置**：planning_artifacts
- **产出物**：ux design
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-ux`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `create` | 创建 UX 契约 | `Create` | 绑定 {planning_artifacts}/ux-designs/ux-{project}-{date}/，建 .working/、imports/、.decision-log.md 与两份仅有 frontmatter 的骨架，再走 Discovery → Finalize |
| `update` | 更新 UX 契约 | `Update` | 读两份 spine、日志与来源，必要时补建日志（本次更新即第一条记录），先摆出与既往决定的冲突再改，随后进 Finalize |
| `validate` | 校验 UX 契约 | `Validate` | 只批判不改稿；跑评审透镜菜单后走合成流水线，产出 validation-report.html/.md 并打开浏览器 |
| `fast-path` | 快速路径 | `Fast path` | 批量补齐缺口后直接起草两份 spine，推断处打 [ASSUMPTION]，跳过创意工具 |
| `coaching-path` | 教练路径 | `Coaching path` | 逐步共同决策，创意工具（配色主题、设计方向、Excalidraw 线框）穿插使用 |
| `design-handoff` | 设计外包交接 | `Design handoff` | 把采集到的 Discovery 内容整理成生产者格式的提示词，用户在外部工具（默认 Google Stitch）产出后回存到工作区；EXPERIENCE.md 可后续用 Update 补齐 |

**流程步骤**

1. **激活与意图判定** — 解析 customization、载入持久事实与配置，headless 转手册；否则问候并做误路由分流（PRD→bmad-prd、架构→bmad-create-architecture、游戏 UX→GDS 等）。
2. **Create：续跑检测与建工作区** `可跳过` — 扫 ux_output_path 下未完成 run（DESIGN.md frontmatter status 非 final）并询问是否续跑，否则建目录骨架。
3. **Discovery：来源扫描** — 对 {planning_artifacts}/ 做 glob 找候选输入，父会话只露路径不读内容，用户确认后由子代理抽取。
4. **Discovery：脑暴与风险校准** — 先请用户倾倒信息（大文档交子代理），加一句“还有别的吗？”，并判定投入级别（业余/内部/消费级/受监管）。
5. **Discovery：工作模式与创意工具** — Fast path / Coaching path / Design handoff 三选一；Creative tools 按需调用（默认 HTML 配色主题、设计方向、Excalidraw 线框，Finalize 时还有 1:1 关键屏 HTML 稿）。
6. **Discovery：关注点扫描** — 点名这份 UX 承载的关注点（可访问性、平台、品牌、受监管用语、动效、i18n、深色模式、离线、内容密度、输入方式、通知等），开放式清单，驱动自造章节。
7. **Discovery：旅程与形态、界面闭包** — 用户以有名主角讲述真实会话并整理成带高潮节拍的编号步骤；形态（手机/网页/桌面/多端）必须在 IA 定稿前确认；每个需求都要有承载界面、每个界面都要有旅程抵达，闭包失败就追问而非臆造。
8. **Finalize：蒸馏两份 spine** — 子代理读决策日志、.working/、imports/ 与来源，按 DESIGN.md spine（品牌与风格/色彩/字体/布局间距/层级/形状/组件/Do&Don't，顺序锁定可省略）与 EXPERIENCE.md spine（Foundation/IA/语气/组件模式/状态/交互原语/可访问底线/关键流程）产出，并主动跑评分卡 Pass 1 覆盖检查。
9. **Finalize：输入对账与开放项** — 每个用户输入配对账子代理产出 reconcile-{slug}.md，重点捞被丢掉的定性想法；随后一对一处理 Open Questions/[ASSUMPTION]/[NOTE FOR UX]。
10. **Finalize：评审门（可选）** `可跳过` — 先问是否要跑校验（明示可轻松跳过），再给透镜菜单（rubric walker + finalize_reviewers + 临时透镜如可访问性），用户可选全部/部分/不选；有透镜运行才走合成报告。
11. **Finalize：关键屏稿与覆盖确认** `可跳过` — 对布局驱动行为的界面渲染关键屏 HTML 稿到 .working/，再逐界面盘点“已出稿/仅靠 spine”，问用户是否还要视觉参考。
12. **Finalize：产物提升与定稿交付** — 蒸馏子代理回读 .working/ 与 imports/ 把视觉决定并回 DESIGN.md、行为决定并回 EXPERIENCE.md；把有留存价值的稿件提升到 mockups/ 或 wireframes/；按 doc_standards 润色、执行 external_handoffs、两份文件置 status: final，并提示常见下一步。

> 备注：CSV 为唯一 predecessor 指向 bmad-prd 的非必填技能（required=false）。评审评分卡为 5 项机械覆盖（流程覆盖/Token 完整/组件覆盖/状态覆盖/视觉引用覆盖）+ 3 项判断（臃肿与过度规格/继承纪律/形态契合）。ux 的评分卡不给总分级（PRD 版本给 Excellent/Good/Fair/Poor），只给逐项裁定。该技能在基线中 installedAs 为 null，但项目 .claude/skills/bmad-ux/ 实体齐全。

#### `bmad-check-implementation-readiness`

*工作流 ｜ 本机已装*

Phase 4 开工前的实施就绪校验（IR）：以需求可追溯性专家的视角，依次做文档清点、PRD 的 FR/NFR 全量提取、epic 覆盖校验、UX 与 PRD/架构的对齐检查、epic 质量评审（用户价值、独立性、依赖、技术型 epic 视为错误），最后给出总评与就绪结论，输出 implementation-readiness-report-日期.md。

- **阶段**：3-solutioning
- **门禁**：必需
- **入口**：直接调用技能；触发语如「check implementation readiness」。
- **参数**：`—`
- **前置**：bmad-create-epics-and-stories
- **后续**：—
- **产出位置**：planning_artifacts
- **产出物**：readiness report
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-check-implementation-readiness`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `IR` | 实施就绪校验 | `Check Implementation Readiness` | 开工前的对齐体检：文档清点 → PRD 全部 FR/NFR 提取 → epic 覆盖校验 → UX 对齐 → epic 质量评审 → 最终评估报告 |

**流程步骤**

1. **1. 文档发现** — 发现、清点并组织全部项目文档，识别重复版本并确定以哪一份为准。
2. **2. PRD 分析** — 完整读取 PRD（整篇或分片），提取全部功能性需求（FR）与非功能性需求（NFR），供后续与 epics 覆盖情况比对。
3. **3. epic 覆盖校验** — 校验 PRD 中每条功能性需求是否都被 epics/stories 文档捕获，找出覆盖缺口。
4. **4. UX 对齐** — 检查是否存在 UX 文档，并校验其与 PRD 需求、架构决策是否一致，架构是否同时照顾到 PRD 与 UX 的需要；若隐含 UI 需求却缺 UX 文档则给出警告。
5. **5. epic 质量评审** — 按 create-epics-and-stories 的实践标准审查 epics/stories：用户价值、独立性、依赖关系与可实施性；技术型 epic 被视为错误，需挑战任何偏离标准的写法。
6. **6. 最终评估** — 汇总全部发现并打磨报告，给出明确的建议与整体就绪状态，输出到 {planning_artifacts}/implementation-readiness-report-{{date}}.md（模板见 templates/readiness-report-template.md）。

> 备注：本地副本采用 step-file 架构（steps/ 下 6 个自包含步骤文件 + templates/ 报告模板），SKILL.md 只负责激活与指向第一步；输出文件路径由各 step 文件的 frontmatter outputFile 声明。文件头有「NEVER generate content without user input」「YOU ARE A FACILITATOR」等强约束。

#### `bmad-create-architecture`

*工作流 ｜ 本机已装*

以协作式分步发现的方式产出架构决策文档（CA）：从模板初始化 {planning_artifacts}/architecture.md，做项目上下文分析、起始模板评估（强制联网核实当前版本）、核心架构决策、实现模式与一致性规则、项目结构与边界，最后做架构校验、完成与交接，目标是让后续 AI 代理实现得一致。

- **阶段**：3-solutioning
- **门禁**：必需
- **入口**：直接调用技能；触发语如「lets create architecture」「create technical architecture」「create a solution design」。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：planning_artifacts
- **产出物**：architecture
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-create-architecture`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `CA` | 创建架构 | `Create Architecture` | 协作式架构设计：初始化文档 → 上下文分析 → 起始模板评估 → 核心决策 → 实现模式与一致性规则 → 结构与边界 → 校验 → 完成交接 |

**流程步骤**

1. **1b. 流程续做处理** `可跳过` — 检测是否存在进行中的架构工作流状态并正确接续（而非从头开始）。
2. **1. 架构工作流初始化** — 检测是否已存在架构文档（{planning_artifacts}/*architecture*.md）；从 architecture-decision-template.md 拷贝模板生成 {planning_artifacts}/architecture.md，初始化 frontmatter 并置 stepsCompleted: [1]。
3. **2. 项目上下文分析** — 分析项目上下文（PRD、现有系统、约束等），为架构决策建立事实基础。
4. **3. 起始模板评估** — 评估起始模板/脚手架选项，强制联网核实当前版本，绝不信任硬编码版本号；生成分析后在 A/P/C 菜单中选择，只有选 C（Continue）才保存并进入下一步。
5. **4. 核心架构决策** — 与用户共同敲定核心架构决策，记录到决策文档模板的各决策段。
6. **5. 实现模式与一致性规则** — 定义实现层面的模式与一致性规则，防止后续多个 AI 代理实现风格分叉。
7. **6. 项目结构与边界** — 确定项目目录结构、模块边界与文件组织方式。
8. **7. 架构校验与完成** — 校验架构文档的完整性与自洽性，补齐缺口。
9. **8. 架构完成与交接** — 给出完成总结与实施阶段的明确后续指引，更新 frontmatter 的最终状态收尾（本流程的最后一步）。

> 备注：本地副本为 step-file 架构（steps/ 下 9 个文件，含续做处理步 1b），另带 architecture-decision-template.md 与 data/ 下两份参考数据（domain-complexity.csv、project-types.csv）。所有步骤都强调「NEVER generate content without user input」「YOU ARE A FACILITATOR」以及「绝不做时间估算」。

#### `bmad-create-epics-and-stories`

*工作流 ｜ 本机已装*

把 PRD 需求与架构决策拆解成按用户价值组织的 epics 与 stories（CE）：校验前置文档并抽取 FR/NFR 及 UX/架构附加要求，设计 epic 清单，生成含完整验收标准的故事，最后做覆盖率终验，输出 {planning_artifacts}/epics.md。

- **阶段**：3-solutioning
- **门禁**：必需
- **入口**：直接调用技能；触发语如「create the epics and stories list」。
- **参数**：`—`
- **前置**：bmad-create-architecture
- **后续**：—
- **产出位置**：planning_artifacts
- **产出物**：epics and stories
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-create-epics-and-stories`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `CE` | 创建史诗与故事 | `Create Epics and Stories` | 需求拆解：校验前置文档并抽取需求 → 设计 epic 清单 → 生成 epics 与 stories → 覆盖率与就绪终验 |

**流程步骤**

1. **1. 校验前置条件并抽取需求** — 校验全部必需输入文档存在，抽取 FR、NFR 以及来自 UX/架构的附加要求；从 templates/epics-template.md 生成 {planning_artifacts}/epics.md 并在 frontmatter 的 inputDocuments 中列出输入文件；写入前先与用户确认纳入/排除哪些文档。每个阶段更新文档后需用户选 C（Continue）才进入下一步。
2. **2. 设计 epic 清单** — 基于需求设计 epic 列表（按用户价值组织），与用户确认后再继续。
3. **3. 生成 epics 与 stories** — 生成各 epic 的详细故事，包含完整、可执行的验收标准，写入 {planning_artifacts}/epics.md。
4. **4. 最终校验** — 校验全部需求的完整覆盖，确认故事达到可供开发的状态。

> 备注：本地副本为 step-file 架构（steps/ 下 4 个步骤文件 + templates/epics-template.md）。CSV 中该条 description 为空，故流程描述全部取自本地源。

#### `bmad-checkpoint-preview`

*工作流 ｜ 本机已装*

面向人的「带看变更」流程（human-in-the-loop）：先定方位（这是什么变更、想解决什么），再按设计意图（而非文件）走读，再做风险点详查（按爆炸半径排序），再给出可亲手验证的观察点，最后请人拍板 Approve/Rework/Discuss（CK）。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：直接调用技能（SKILL.md → step-01-orientation.md 顺序执行）；用户说 "checkpoint" / "human review" / "walk me through this change"。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-checkpoint-preview`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `—` | 通过 | `Approve` | 收尾决策之一：认可变更，可在发布前先做交互式修补；若是 PR 可提议 gh pr review --approve（需先确认，因为是共享资源上的可见操作）。 |
| `—` | 返工 | `Rework` | 收尾决策之一：弄清是方案、spec 还是实现的问题，帮助决定下一步（回退提交/开 issue/修订 spec），必要时起草绑定 path:line 的具体反馈。 |
| `—` | 继续讨论 | `Discuss` | 收尾决策之一：开放式答疑与深挖顾虑，讨论完回到决策提示。 |

**流程步骤**

1. **1. Orientation 定方位** — 按 4 层级联定位变更（显式参数 → 近期对话 → sprint tracking 中 status=review 的故事 → 当前 git 分支/HEAD → 询问，3 轮问不出则 HALT）；补全 spec 与 commit 的配对；判定 review_mode：full-trail（spec 带 Suggested Review Order）/ spec-only / bare-commit（凭提交信息推断意图，过短则标 [inferred]）；必要时用 generate-trail.md 生成审查线索。
2. **2. Walkthrough 按关注点走读** — 按设计意图（即 concern，如输入校验、状态管理、API 契约）而非文件组织内容，一个文件可出现在多个 concern 下；每个 concern 给「为什么这么做 + 关键 path:line 站点」，按理解顺序自上而下排列，典型 2-5 个 concern（超过 7 个提示范围可能过大）。
3. **3. Detail Pass 风险详查** — 扫描 diff 挑 2-5 个「一旦错代价最大」的位置并打风险标签（[auth]/[public API]/[schema]/[billing]/[infra]/[security]/[config]/[other]），按爆炸半径排序；不评严重度分数；若 spec 有 Spec Change Log 则呈现其中对人有启发性的决策；找不出高风险点就明说，不硬凑。
4. **4. Testing 亲手验证** — 针对可观察行为（UI/CLI 输出/API 响应/状态变化/错误路径）给 2-5 条「做什么-看什么-为何值得看」的观察建议；不重复 CI 与自动化测试；若无用户可见行为则明说。
5. **5. Wrap-Up 拍板** — 给出 Approve / Rework / Discuss 三选一并 HALT；按选择执行：通过则按需交互修补或提议批准 PR，返工则定位问题层级并起草反馈，讨论则继续答疑后回到决策。

> 备注：菜单项在源码中无代码，code 置 null。与 code-review 的区别：CR 面向机器分诊与状态推进（写故事文件、改 sprint 状态），CK 面向人的理解与拍板（不写文件、不自动改状态）。全局规则：所有代码引用用 CWD 相对 path:line 便于 IDE 点击；每步一次性完整输出不中途提问。

#### `bmad-code-review`

*工作流 ｜ 本机已装*

对抗式代码评审（CR）：先把评审目标（diff 来源 + 可选 spec）锁定，然后并行起三层互不共享上下文的评审子代理——Blind Hunter（只看 diff）、Edge Case Hunter（diff + 项目读权限）、Acceptance Auditor（diff + spec + 上下文文档），汇总去重后分诊为 decision_needed / patch / defer / dismiss，最后把结论写回故事文件的 Review Findings 段并据结果更新故事与 sprint 状态。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：直接调用技能；触发语如「run code review」「review this code」。step-01 有 5 层目标检索：显式参数（PR/SHA/分支/spec/diff 关键词）→ 近期对话 → sprint 中处于 review 状态的故事 → 当前 git 分支状态 → 都不成立才问用户。
- **参数**：`—`
- **前置**：bmad-dev-story
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-code-review`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `CR` | 代码评审 | `Code Review` | 故事循环的质检关：锁定 diff → 三层并行对抗评审 → 分诊归类 → 写回故事评审结论并决定故事回到 in-progress（有问题回 DS）还是 done（通过） |

**流程步骤**

1. **1. 收集上下文并构造 diff** — 按 5 层优先级确定评审目标：显式参数（PR 经 gh pr view 解析 / commit / 分支 / spec 文件 / staged·uncommitted·branch diff·commit range·粘贴 diff 等模式关键词）→ 近期对话 → sprint-status 中处于 review 的故事（唯一则建议之，多个则列选项）→ 当前非主分支的 HEAD（确认后按对主分支的分支 diff 处理）→ 最后才 HALT 询问。随后按来源构造 {diff_output}（staged 用 git diff --cached；未提交用 git diff HEAD；分支/区间先验证存在；文件清单逐个验证路径）。再确定 spec：有则 review_mode=full 并加载其 frontmatter context 引用的文档，无则 review_mode=no-spec。diff 超过约 3000 行时告警并提供按文件组切分。CHECKPOINT 展示 diff 统计并等用户确认。
2. **2. 并行执行三层对抗评审** — 无会话上下文地并行起子代理：Blind Hunter 只拿 diff（走 bmad-review-adversarial-general 技能）；Edge Case Hunter 拿 diff 且有项目读权限（走 bmad-review-edge-case-hunter 技能）；Acceptance Auditor 仅在 full 模式下启用，拿 diff + spec 内容 + 上下文文档，检查 AC 违背、偏离 spec 意图、漏实现、spec 约束与代码矛盾。三层都须以当前会话同等模型能力运行。子代理不可用时改为在 {implementation_artifacts} 生成每角色的评审 prompt 文件并 HALT，让用户分头在独立会话（最好换 LLM）跑完再贴回结果。任一子代理失败/超时/空结果记入 failed_layers 并继续用其余层。no-spec 时明确提示「Acceptance Auditor 已跳过」。
3. **3. 分诊归类** — 把三层结果归一化为统一字段（id/source/title/detail/location），跨层去重（同问题合并，具体证据优先，source 记合并来源），逐条归入四类之一：decision_needed（需人工定夺，仅 full 模式可能产生；no-spec 时降级为 patch 或 defer）、patch（可无歧义直接修）、defer（非本次改动引入的既有问题）、dismiss（噪音/误报）。丢弃 dismiss 并记录数量。failed_layers 非空时先报告失败层；若过滤后零发现且存在失败层，必须提示「评审可能不完整」而不是宣布干净通过。
4. **4. 呈现与行动** — 零发现时直接跳到 sprint 状态更新。有 spec_file 时把发现按 decision-needed（未勾选）→ patch（未勾选）→ defer（已勾选并标注 pre-existing）顺序追加到故事文件的 Review Findings 子段，defer 项另写入 {implementation_artifacts}/deferred-work.md。逐条解决 decision-needed（可 defer 并记录一行原因）。对 patch 给出处理选项：全部应用 / 留作待办（仅在写了 story 时）/ 逐条走查。最后按结果定状态：decision-needed 与 patch 全部解决且无遗留高中危问题 → 故事置 done；有留作待办的 patch 或未解决项 → 置 in-progress；同步 sprint-status 的 development_status[story_key]。收尾给出后续选项：开始下一个故事（跑 dev-story）/ 重跑评审 / 结束。

> 备注：本地副本用 steps/ 下 4 个微步骤文件（step-file 架构），流程与旧版全局副本的 CR 差异较大——三层对抗评审角色（Blind Hunter / Edge Case Hunter / Acceptance Auditor）与四分类分诊是本地版特征。本技能是故事循环里的可选项（CSV required=false）：评审通过时故事转 done 并进入下一个 CS 或 ER；发现问题则把故事打回 in-progress，由 dev-story 的评审续做路径处理。CSV 的 followed-by/outputs 为空，闭环同样只写在 description 文本里。

#### `bmad-create-story`

*工作流 ｜ 本机已装*

故事循环的起点（CS）。从 sprint-status.yaml 自动定位第一个 backlog 故事，对 epics/PRD/架构/UX/前序故事/git 历史做穷尽式上下文分析，产出一份「开发代理无需再翻其他文档」的完整故事文件并置为 ready-for-dev，同时同步 sprint 状态。可选再跑 VS（validate）做独立校验。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：直接调用技能；触发语如「create the next story」「create story 1-2-user-auth」，也可直接给故事文件路径。激活时先跑 resolve_customization.py 解析 workflow 块，再加载 _bmad/bmm/config.yaml 与 persistent_facts。
- **参数**：`—`
- **前置**：bmad-sprint-planning
- **后续**：bmad-create-story:validate
- **产出位置**：implementation_artifacts
- **产出物**：story
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-create-story`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `CS` | 创建故事 | `Create Story` | 主流程：定目标故事 → 穷尽分析产物 → 架构护栏 → 联网核实最新技术 → 生成含全部开发上下文的故事文件（ready-for-dev）→ 校验并同步 sprint-status |
| `VS` | 校验故事 | `Validate Story` | 可选独立校验：在全新上下文中按 checklist.md 审查已生成的故事文件，找出遗漏与错误并修复；建议在 dev-story 之前执行 |

**流程步骤**

1. **1. 确定目标故事** — 用户给了故事路径或编号（如 2-4、1.6、epic 1 story 5）则直接解析出 epic_num/story_num/story_key；否则必须完整读完 sprint-status.yaml，按顺序找第一个 key 形如 number-number-name 且状态为 backlog 的故事。如果这是该 epic 的第一个故事，把 epic 状态从 backlog/contexted 置为 in-progress；epic 已 done 或状态非法则 HALT。找不到 backlog 故事时给出 3 个选项：跑 sprint-planning / 加载 PM 跑 correct-course 补故事 / 跑 retrospective。
2. **2. 加载并分析核心产物** — 按 discover-inputs.md 加载 epics/PRD/架构/UX（整篇或分片），加上激活期加载的 project-context。从 epics 提取本 epic 目标/全部故事/本故事需求与 AC/技术约束/依赖/source hints。story_num>1 时读取上一个故事文件，提取其开发笔记、评审反馈、改动文件与踩坑经验；若检测到 git 仓库，分析最近 5 次提交的文件、模式、依赖与测试方式。
3. **3. 架构分析（开发护栏）** — 逐节判断架构文档中与本故事相关的内容：技术栈与版本、代码结构、API 模式、数据库 schema、安全、性能、测试标准、部署、集成。强制动作：找出架构中标记为 UPDATE（非 NEW）且本故事会改动的每个文件，完整读一遍，并在 dev notes 中记录当前行为、本次改动点、必须保持不变的行为——这是实现失败与返工的首要来源。
4. **4. 联网研究最新技术细节** — 对架构中提到的关键库/API/框架查最新稳定版本与关键变化（破坏性变更、安全更新、废弃项、当前版本最佳实践），把开发必须知道的外部信息写进故事。
5. **5. 生成完整故事文件** — 以 template.md 初始化 {implementation_artifacts}/{{story_key}}.md，依次写入故事头、需求、开发者上下文段、技术需求、架构合规、库/框架要求、文件结构要求、测试要求、前序故事情报、git 情报、最新技术信息、项目上下文引用与完成状态，最后把 Status 设为 ready-for-dev。
6. **6. 校验、落库与收尾** — 用 checklist.md 校验故事文件并修复；无条件保存。若 sprint-status 存在，把 development_status[{{story_key}}] 从 backlog 更新为 ready-for-dev 并更新 last_updated（保留全部注释与 STATUS DEFINITIONS）。最后输出完成报告并提示下一步：人工过一遍故事 → 跑 dev-story → 完成后跑 code-review（会自动置 done）。

> 备注：本地版是 6 步单文件流程；旧版全局副本的 3.5/3.6（测试用例生成与自动化分类）以及「验证自动化可行性报告归档脚本」在本地副本中不存在。VS（validate）动作在 CSV 中登记为独立条目，本地以 checklist.md 承载其校验逻辑。/bmad:tea:automate 被提为可选的 TEA 模块扩展，不是本流程必需步骤。

#### `bmad-dev-story`

*工作流 ｜ 本机已装*

执行故事实现（DS）：定位 ready-for-dev 故事并置 in-progress，按故事文件中任务的顺序逐个走「先写失败测试 → 最小实现 → 重构」，跑全量回归与质量检查，全部满足后把故事状态推到 review 并同步 sprint-status。若故事文件里已有代码评审结论，会自动识别为评审后续做，优先处理 [AI-Review] 待办项。

- **阶段**：4-implementation
- **门禁**：必需
- **入口**：直接调用技能；触发语如「dev this story <路径>」「implement the next story in the sprint plan」。也可显式传故事文件路径跳过自动发现。
- **参数**：`—`
- **前置**：bmad-create-story:validate
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-dev-story`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `DS` | 开发故事 | `Dev Story` | 故事循环主体：找 ready-for-dev 故事 → 标记 in-progress 并记录 baseline_commit → 逐任务 red-green-refactor → 测试与回归 → 满足 DoD 后置 review |

**流程步骤**

1. **1. 找到并加载下一个待开发故事** — 显式 story_path 优先，直接读完整个故事文件。否则完整读 sprint-status.yaml，按顺序取第一个状态为 ready-for-dev 的故事及其文件。找不到时给出 4 个选项：跑 create-story / 跑 validate-create-story（推荐的质量检查）/ 手动指定故事文件 / 查看 sprint 状态；并提示「ready-for-dev 的故事可能尚未校验」。
2. **2. 加载项目上下文与故事信息** — 加载 project-context（若存在）获取编码规范与项目模式，解析故事文件的 Story / AC / Tasks / Dev Notes / Dev Agent Record / File List / Change Log / Status 各段，把 Dev Notes 里的架构要求、前序经验、技术规格作为实现依据。
3. **3. 检测是否为评审后续做并提取评审上下文** — 检查故事文件是否存在「Senior Developer Review (AI)」段与 Tasks 下的「Review Follow-ups (AI)」子段。存在则置 review_continuation=true，提取评审结论、日期、严重度分布与未勾选待办项，并声明策略：优先处理带 [AI-Review] 标记的评审后续项，再继续常规任务。不存在则按全新实现开局。
4. **4. 标记故事为进行中** — 若故事 frontmatter 已含 baseline_commit 则保留不覆盖。若当前状态为 ready-for-dev 且无 baseline_commit，运行 git rev-parse HEAD 写入（无版本控制则写 NO_VCS）。sprint-status 存在时把状态从 ready-for-dev 更新为 in-progress 并更新 last_updated；本来已是 in-progress 则提示续做；无 sprint-status 则只在故事文件内跟踪。
5. **5. 按 red-green-refactor 循环实现任务** — 严格按故事文件中任务/子任务顺序执行。RED：先写会失败的测试并确认失败；GREEN：写最小实现使测试通过，并覆盖任务规定的错误与边界情况；REFACTOR：在测试保持绿色的前提下改善结构，遵循 Dev Notes 中的架构模式与编码规范。把技术方案记入 Dev Agent Record → Implementation Plan。需要故事外的新依赖、连续 3 次实现失败、缺少必要配置时 HALT。
6. **6. 编写完整测试** — 为核心业务逻辑写单元测试；按故事需求补组件交互的集成测试；关键用户流程按需补端到端测试；覆盖 Dev Notes 中识别出的边界与错误处理场景。
7. **7. 运行验证与测试** — 推断本仓库测试框架并运行全部既有测试确保无回归，运行新测试确认实现正确，按项目配置运行 lint 与质量检查，逐条核对故事的全部验收标准（定量阈值必须显式满足）。回归或新测试失败必须停下来修完再继续。
8. **8. 仅在完全完成后标记任务完成** — 校验门：本任务的测试确实存在且 100% 通过、实现与任务描述精确一致（不做多余功能）、相关 AC 全部满足、全量测试无回归。通过才勾选 [x]，更新 File List（相对仓库根的路径），并把完成说明写入 Dev Agent Record。若任务是 [AI-Review] 后续项，还要同步勾掉「Senior Developer Review (AI) → Action Items」中对应条目并记录「✅ Resolved review finding」。任务未清则回到 step 5，全清则进 step 9。
9. **9. 故事完成并标记待评审** — 重新扫描确认全部任务已勾选，跑完整回归套件，确认 File List 覆盖所有改动文件，执行增强版 DoD 校验（测试存在且通过、无回归、质量检查通过、仅修改了允许的故事段落等），把故事 Status 置为 review；sprint-status 存在则把对应 key 从 in-progress 更新为 review。任一校验门不过则 HALT。
10. **10. 完成沟通与用户支持** — 向用户汇报实现完成与关键改动、测试、文件清单，并按用户技术水平回答解释类问题。建议下一步：人工验证、跑 code-review（明确提示「最好换一个不同的 LLM 来做评审」），如装 TEA 模块可跑 /bmad:tea:automate 扩展护栏测试。

> 备注：本地版为 10 步、单文件流程，无独立 step 文件；RED/GREEN/REFACTOR 内嵌在 step 5 的 action 中，并非独立步骤（这是与旧版全局副本最直观的差异之一）。CSV 对 DS 的描述是「Execute story implementation tasks and tests then CR then back to DS if fixes needed」，但 CSV 的 followed-by / output-location / outputs 字段全为空；该闭环在本地副本中由 step 3（识别评审续做）与 step 8（处理 [AI-Review] 待办）实现，属于隐式而非显式声明的依赖关系。

#### `bmad-investigate`

*工作流 ｜ 本机已装*

取证式调查工作流：从可得证据重建"发生了什么"或"陌生代码区在做什么"，产出一份别人能冷手接续的结构化结案文件。全程在缺陷追查（有症状）与区域探索（无症状）之间校准，所有结论按「已证实（可直接引用 path:line/日志时间戳/commit）/已推断（展示推理链）/待验证（写明证实与证伪条件）」三级标注；假设只更新状态不删除，缺失证据本身也算一条发现。调查止于诊断，修复实现不在范围内。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：直接调用技能 bmad-investigate，参数为工单号、日志或诊断包路径、报错文本、代码区域名、问题描述，或指向已有结案文件的路径（该形态为续办，路由到 Outcome 0）。输出写入 {implementation_artifacts}/{workflow.case_file_subdir}/{workflow.case_file_filename}，即 {implementation_artifacts}/investigations/{slug}-investigation.md（slug 取工单号，否则与用户商定一个短名并规范为小写字母数字加连字符；路径冲突时询问改名为 slug-YYYY-MM-DD.md 还是续用原文件）。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：implementation_artifacts
- **产出物**：investigation report
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-investigate`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `IN` | 调查 | `Investigate` | help 目录登记条目（display-name 为 Investigate）：取证式排查，按证据等级重建事件经过或建立代码区域心智模型，产出结案文件。 |

**流程步骤**

1. **1. 解析 workflow 配置块** — 运行 resolve_customization.py --skill {skill-root} --key workflow；脚本失败即停止并暴露错误（与 agent 型不同，无手工兜底合并）。
2. **2. 执行 prepend 步骤** — 按顺序执行 {workflow.activation_steps_prepend} 的每一项（本地默认空数组）。
3. **3. 载入持久事实** — 把 {workflow.persistent_facts} 每一项当作基础上下文；file: 前缀项按 {project-root} 路径或通配符加载内容（默认 file:{project-root}/**/project-context.md），其余按字面事实。
4. **4. 载入配置** — 读取 _bmad/bmm/config.yaml，解析 user_name、communication_language、document_output_language、implementation_artifacts、project_knowledge；若 implementation_artifacts 未解析，回落到 ./investigations/ 并在初始化前明确告知用户该回落。
5. **5. 问候** — 按 {communication_language} 问候 {user_name}。
6. **6. 执行 append 步骤** — 按顺序执行 {workflow.activation_steps_append}（本地默认空数组），并在主流程开始前确认 prepend / append 均已按序执行完。
7. **7. 确认输入并路由** — 把用户输入登记为引用（只记录路径与 ID，不读原始内容）；若指向已有结案文件 → Outcome 0，否则 → Outcome 1。
8. **8. Outcome 0：载入并呈现既有案件** `可跳过` — 读结案文件，按序呈现开放假设（Status=Open）及其证实/证伪标准、未完结待办（Status≠Done）、缺失证据行、上次结论与置信度，然后询问要拉哪条线；新证据以 ## Follow-up: {YYYY-MM-DD} 块追加（同日重入加 #2、#3）；呈现完停下等用户指令。
9. **9. Outcome 1：确立范围与据点** — 按输入形态登记（工单：用 MCP 工具取全文；诊断包：记路径、文件数、时间窗；日志或堆栈：记路径与时间窗，仅用户消息里已有的栈帧入范围；自由描述：原文捕获并当作假设处理；代码区名：记入口；近期提交区：记提交范围）。用户自带假设则登记为 Hypothesis #1，但据点必须独立寻找——用户假设本身是要被据点验证或证伪的对象。据点 = 一条已证实证据（报错信息、函数名、HTTP 路由、配置项、测试用例）。分支前先用 {workflow.case_file_template} 初始化 {case_file}，填入 Hand-off Brief 粗稿、Case Info、问题陈述与初始证据清单。无任何可达的已证实证据时进入证据稀少分支：在 Hand-off Brief 标记 evidence-light、把待办填为按优先级排序的数据采集项、写下"要推进，我需要以下之一：…"，停下等用户补证据或授权 Outcome 2 扩大扫描。
10. **10. Outcome 2：摸清证据边界** — 在六类相互独立的证据上并行勘查：诊断包、工单系统、版本控制、测试结果、静态分析、源码；任一类超过约 10K token 就委派子代理，只回收 JSON 清单（路径、大小、时间窗、以 path:line 引用的关键片段）。逐类标注 Available / Partial / Missing（Missing 本身即一条发现），更新证据清单与调查待办。
11. **11. Outcome 3：有纪律地推理成因** — 追溯因果（症状驱动从症状反向追到产生条件与当时状态；探索型从输出——返回值、副作用、发出的消息——反向追到产生条件，同一手法换锚点）；交叉比对日志、系统事件、版本控制、用户观察重建时间线；假设先声明、再找证实与证伪证据、检索、定级为 Confirmed / Refuted / Open，假设永不删除只更新状态与 Resolution；每次假设趋近 Confirmed 都先主动做一轮证伪扫描并把尝试记进 Resolution；独立复核用户前提，证据不符就直说；新发现的线索入待办但不偏离当前线程。
12. **12. Outcome 4：追踪源码到关键处** — 第一轮并行发出：精确报错串 grep、对受影响目录 glob 找并行实现、git log 看近期变更。随后串行：读周边代码、跟调用链、留意语言与进程边界跨越（编译产物→脚本、IPC、宿主→设备、配置流）。按案件类型侧重——探索型做 I/O 映射（触发、输出、依赖）、高频词扫描、控制流过滤（分支、循环、错误处理、状态机转移）；症状型先评估深度（根因能否从局部上下文触达，否则需更大区域模型，扩大范围必须明说不得静默），再做 trivial-fix 评估（off-by-one、缺 null 检查、参数颠倒 → 报告中给一行建议或草稿 diff；非 trivial → 停在根因区域）。
13. **13. Outcome 5：定稿报告并干净交接** — 更新 {case_file}：Hand-off Brief 改为终稿（3 句、15 秒可读完）、Final Conclusion 带置信度（High=根因已证实且有确定性复现 / Medium=已推断、轻微不确定 / Low=待验证且有明确数据缺口）、适用时给修复方向（多因并存时按机制分类）与诊断步骤、适用时给 Reproduction Plan（探索型给验证计划）、Status 置 Active / Concluded / Blocked on evidence。随后呈现结论与下一步菜单：trivial fix → bmad-quick-dev、范围或计划调整 → bmad-correct-course、立成故事 → bmad-create-story、重新评审 → bmad-code-review，并推荐其中价值最高的一项；缓解措施与临时绕行只在用户明确要求时生成；{workflow.on_complete} 非空则执行。
14. **14. Follow-up 迭代与结案判定** `可跳过` — 后续工作一律以新的 ## Follow-up: {YYYY-MM-DD} 块追加到 {case_file}（同日重入加 #2、#3）。满足任一条件即结案：根因已证实；根因待验证但数据缺口明确；心智模型已足够支撑用户声明的目标（探索型）；待办只剩需不可得证据的项；用户明确结束。

> 备注：inHelpCatalog=true，已登记进 bmad-help.csv 与 _bmad/bmm/module-help.csv（菜单码 IN、display-name=Investigate、描述含 evidence-graded 字样），用户可通过 /bmad-help 发现入口。但该行存在列错位（见 discrepancies 第 1 条）：基线 helpEntries 里 args='4-implementation'、phase=''、followed-by='false'、required='implementation_artifacts'、output-location='investigation report'；本条目 dependencies 已按表内列语义解码为 phase=4-implementation、required=false、outputLocation=implementation_artifacts、outputs=investigation report、args='' 记录。三条本地定制项均有实体支撑：case_file_template=references/case-file-template.md（本地存在，含 Hand-off Brief、证据清单、时间线、三级结论、Follow-up 等 20 个段落的结案文件骨架）、case_file_subdir=investigations、case_file_filename={slug}-investigation.md；on_complete 为空串（结案后无自动化动作）。persistent_facts 默认只加载 project-context.md，activation_steps_prepend/append 均为空数组；_bmad/custom/bmad-investigate.toml 本机不存在。SKILL.md 未引用除模板外的其他文件，故 sourceFiles 仅 3 项。

#### `bmad-qa-generate-e2e-tests`

*工作流 ｜ 本机已装*

为已实现的功能生成自动化 API 与 E2E 测试（QA）：先探测项目已有的测试框架（没有就按技术栈推荐），确定被测特性后生成 API 测试（状态码、响应结构、正常路径 + 1-2 个错误场景）与 E2E 测试（用户流程、语义定位器、线性简单），跑通后输出测试摘要到 {implementation_artifacts}/tests/test-summary.md。明确不做代码评审与故事校验（那是 CR 的职责）。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：直接调用技能；触发语如「create qa automated tests for <feature>」。
- **参数**：`—`
- **前置**：bmad-dev-story
- **后续**：—
- **产出位置**：implementation_artifacts
- **产出物**：test suite
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-qa-generate-e2e-tests`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `QA` | QA 自动化测试 | `QA Automation Test` | 为已实现代码补自动化测试：探测框架 → 定位特性 → 生成 API 与 E2E 测试 → 运行修复 → 出测试摘要；不替代代码评审 |

**流程步骤**

1. **0. 探测测试框架** — 检查项目中已有的测试框架（package.json 依赖里的 playwright/jest/vitest/cypress 等）与现有测试文件的写法，一律沿用项目既有框架；完全没有时分析项目类型（React/Vue/Node API 等）并联网查该技术栈当前推荐的框架，向用户确认后使用。
2. **1. 识别被测特性** — 询问用户要测什么：具体特性/组件名、要扫描的目录，或让工具在代码库中自动发现特性。
3. **2. 生成 API 测试（如适用）** — 针对 API 端点/服务生成测试：校验状态码（200/400/404/500）、验证响应结构、覆盖正常路径加 1-2 个错误场景，并沿用项目既有测试框架的写法。
4. **3. 生成 E2E 测试（如存在 UI）** — 针对 UI 生成端到端测试：覆盖用户工作流、使用语义化定位器（role/label/text）、聚焦点击/填表/导航等交互、断言可见结果、保持测试线性简单，并遵循项目既有测试模式。
5. **4. 运行测试** — 用项目既有命令执行测试，出现失败立即修复。
6. **5. 生成测试摘要** — 输出 markdown 摘要（生成的 API/E2E 测试清单、覆盖率统计、下一步建议），保存到 {implementation_artifacts}/tests/test-summary.md，并按 checklist.md 校验。

> 备注：本地副本为线性 Step 0-5，无独立 step 文件；末尾将「风险驱动测试策略、测试设计规划、质量门与 NFR 评估」等高级能力导向 TEA（Test Architecture Enterprise）模块，并附安装链接。CSV 描述特意强调「NOT for code review or story validation — use CR for that」，与 SKILL.md 的 Your Role 表述一致。

#### `bmad-retrospective`

*工作流 ｜ 本机已装*

epic 结束时的团队复盘（ER，**可选**）：由 Amelia 主持多方对话，深挖本 epic 全部故事记录、核对上个 retro 的行动项落实、预览下一个 epic，产出 SMART 行动项与下一 epic 准备任务，写入 {implementation_artifacts}/epic-N-retro-日期.md 并把 retrospective 状态置 done。若检测到重大发现（架构假设被推翻、范围重大变化、技术路线需根本调整等），会要求先更新下一个 epic 的计划再启动它。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：直接调用技能；触发语如「run a retrospective」「lets retro the epic 2」。可带 epic 号参数。
- **参数**：`—`
- **前置**：bmad-code-review
- **后续**：—
- **产出位置**：implementation_artifacts
- **产出物**：retrospective
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-retrospective`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `ER` | 史诗复盘 | `Retrospective` | epic 收尾的可选复盘：故事分析 + 上轮行动项对账 + 下个 epic 预览 → 行动项与准备任务 → 写复盘文档并标记完成；有重大发现则先改下一个 epic 计划 |

**流程步骤**

1. **1. epic 发现（三级优先级）** — 先查 sprint-status.yaml 找已完成故事的最高 epic 号并请用户确认；找不到就直接问用户刚完成哪个 epic；仍不确定则回退扫描 {implementation_artifacts} 中编号最高的故事文件推断。确定后核对该 epic 是否真的全部故事 done：未完成时提示三个选项（先做完剩余故事（推荐）/ 继续做部分复盘 / 跑 sprint-planning 刷新），用户选否则 HALT，选是则标记 partial_retrospective 并给出警示。
2. **0.5 发现并加载项目文档** `可跳过` — 按 Input Files 表加载：epic（SELECTIVE_LOAD，只取本 epic，支持整篇/分片）、上一个 epic 的复盘（可选）、架构与 PRD（FULL_LOAD）、棕地项目文档（INDEX_GUIDED）。
3. **2. 深度故事分析** — 逐个读本 epic 的故事文件，从 Dev Notes/挑战/实现笔记中提取卡点、意外复杂度、失败的技术决策；从评审段落提取反复出现的反馈主题；从经验教训段提取显式学习；从技术债/TODO 段提取捷径与债务；从测试段提取覆盖缺口与 bug 模式。再跨故事综合出共性卡点（2 个以上故事出现）、反复评审意见、突破性做法、速度趋势与协作亮点，作为复盘讨论素材。
4. **3. 加载并整合上一个 epic 的复盘** `可跳过` — 仅当存在上一个 epic（prev_epic_num >= 1）时执行：按 {implementation_artifacts}/epic-{prev}-retro-*.md 找到复盘，逐项核对上轮承诺的行动项落实状态（✅完成/⏳进行中/❌未处理）、经验是否被应用、流程改进是否有效、技术债是消是长；既表彰成功应用的经验，也从无指责视角分析被忽略的教训与阻碍。
5. **4. 预览下一个 epic 并检测变化** `可跳过` — 加载下一个 epic（先试分片 epic-{N+1}.md，再回退整篇文档），分析其目标、故事与复杂度、对本 epic 产物的依赖、新增技术需求、风险与成功标准；识别未完成工作造成的阻塞依赖、需要提前准备的技术/知识/重构/文档，以及必须就绪的 API、数据迁移、测试基础设施与部署环境。
6. **5. 以丰富上下文初始化复盘** — 用已收集的 epic 内容、故事分析结论、上轮复盘对照与下一个 epic 预览，设定本次复盘的参与者与议题框架，开始团队对话。
7. **6. epic 回顾讨论（哪些做得好、哪些不好）** — 主持多方对话式复盘，遵循心理安全、不追责、聚焦系统与流程、要求具体例子，逐个主题收集成功经验与改进点。
8. **7. 下一个 epic 准备讨论** — 围绕下一个 epic 的准备事项交互讨论：需要补齐的技术前置、知识空白、重构与清理、关键路径阻塞项。
9. **8. 综合行动项并检测重大变化** — 产出 SMART 行动项（明确描述、负责人、时间点、成功标准、类别）与下一 epic 准备任务清单，附关键路径阻塞项；随后做关键分析：若出现架构假设被推翻、重大范围变更、技术路线需根本调整、新依赖、用户需求理解偏差、性能/安全/合规问题、集成假设错误、团队能力缺口、技术债不可持续等任一情况，则发出重大发现告警，指出下一个 epic 基于哪些已失效的假设、需要哪些更新，并建议先开一次 epic 计划评审会（必要时更新 PRD），经用户同意后加入关键路径。
10. **9. 关键就绪度探索（交互深挖）** — 关闭复盘前的最后就绪检查：epic 在 sprint-status 里标记完成，但是否真的完成了——逐项确认并请用户裁定。
11. **10. 复盘收尾** — 以庆祝与承诺收束：回顾成果、确认各方对行动项与准备任务的认领。
12. **11. 保存复盘并更新 sprint 状态** — 确保 {implementation_artifacts} 存在，生成含 epic 摘要与指标、参与者、优势与挑战、关键洞察、上轮复盘落实分析、下一 epic 预览与依赖、行动项与负责人、准备任务、关键路径、重大发现与更新建议、就绪评估的完整文档，存为 epic-{N}-retro-{date}.md；再把 sprint-status 中 epic-{N}-retrospective 置为 done（找不到该 key 时提示需手工同步）。
13. **12. 总结与交接** — 输出复盘完成总结：epic 主题、复盘文档路径、承诺清单与下一步（准备任务、下一个 epic 的启动条件）。

> 备注：CSV 该条描述原文为「Optional at epic end: Review completed work lessons learned and next epic or if major issues consider CC」——整条 ER 在 epic 结束时是可选动作，且「若发现重大问题建议走 CC（correct course）」；本地 SKILL.md 确实实现了重大发现检测并会要求先更新下一个 epic 计划（step 8 的 SIGNIFICANT DISCOVERY ALERT、step 9 的就绪探索），但全文未显式点名调用 correct-course，CC 的关联来自官方目录描述。文件内步骤顺序为 1 → 0.5 → 2 → … → 12（0.5 为插入的文档加载步）。

#### `bmad-sprint-planning`

*工作流 ｜ 本机已装*

从 epics 文件生成 sprint 追踪表（SP）：解析全部 epic 与故事，按「epic → 其故事 → 其 retrospective → 下一个 epic」的顺序构建 development_status，做智能状态检测（已存在故事文件的至少升为 ready-for-dev，已有状态文件中更高级的状态绝不降级），写出 sprint-status.yaml 并校验覆盖率与取值合法性。

- **阶段**：4-implementation
- **门禁**：必需
- **入口**：直接调用技能；触发语如「run sprint planning」「generate sprint plan」。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：implementation_artifacts
- **产出物**：sprint status
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-sprint-planning`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `SP` | Sprint 规划 | `Sprint Planning` | 实施阶段启动动作：解析 epics → 建状态结构 → 智能识别已有进度 → 生成 sprint-status.yaml → 校验并汇报统计 |

**流程步骤**

1. **1. 解析 epic 文件并提取全部工作项** — 文档发现：优先整篇（epics.md / bmm-epics.md / *epic*.md），否则按分片（epics/index.md + 各 epic-*.md）全部读入，两者都存在时用整篇；名称匹配要宽容。从标题提取 epic 号（## Epic 1:）与故事（### Story 1.1: User Authentication），把 Epic.Story: Title 转换成 kebab-case key（1-1-user-authentication）。
2. **2. 构建 sprint 状态结构** — 每个 epic 按固定顺序生成三类条目：epic-{num}（默认 backlog）、各故事 key（默认 backlog）、epic-{num}-retrospective（默认 optional）。
3. **3. 智能状态检测** — 逐个故事检查 {story_location}/{story-key}.md 是否存在，存在则状态至少升为 ready-for-dev。已存在 status 文件时保留其中更高级的状态，绝不降级（例如不会把 done 改回 ready-for-dev）。状态机：epic backlog→in-progress→done；故事 backlog→ready-for-dev→in-progress→review→done；retrospective optional↔done。
4. **4. 生成 sprint 状态文件** — 写出 {implementation_artifacts}/sprint-status.yaml：元数据（generated/last_updated/project/project_key/tracking_system/story_location）同时以注释和 YAML 字段两种形式出现，并内嵌 STATUS DEFINITIONS 状态定义与流程说明，最后是 development_status 段。
5. **5. 校验与汇报** — 校验：epic 文件中的每个 epic/故事都出现在状态文件中、每个 epic 都有 retrospective 条目、状态文件没有多余条目、所有状态取值合法、YAML 语法正确。统计 epic/故事总数与进行中/已完成数并展示，提示用户后续由各代理在工作的同时更新状态、需要时重跑本流程刷新。

> 备注：本地副本无独立 step 文件，5 步均在 SKILL.md 的 <workflow> 内；checklist.md 与 sprint-status-template.yaml 为配套校验清单与模板。描述状态流转时允许把遗留状态 contexted→in-progress、drafted→ready-for-dev 做兼容映射（见 sprint-status 技能）。

#### `bmad-sprint-status`

*工作流 ｜ 本机已装*

随时可用的 sprint 汇总与路由入口（SS）：解析 sprint-status.yaml，按状态计数并识别风险（有 review 故事就建议 CR、全 backlog 就建议 CS、状态文件超 7 天未更新就告警、出现孤儿故事或空 epic 也告警），然后按优先级推荐下一个该跑的工作流。另含 data 与 validate 两个非交互模式，供其他流程内部调用。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：直接调用技能；触发语如「check sprint status」「show sprint status」。可带 mode 参数（data / validate）供其它工作流调用。
- **参数**：`—`
- **前置**：bmad-sprint-planning
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-sprint-status`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `SS` | Sprint 状态 | `Sprint Status` | 随时可跑：汇总各状态计数、列出风险、按优先级推荐下一步该跑哪个工作流，也可导出数据或校验状态文件 |

**流程步骤**

1. **0. 判定执行模式** — 调用方传了 mode 就用传入值，否则默认 interactive；data 跳到 step 20，validate 跳到 step 30，interactive 继续 step 1。
2. **1. 定位 sprint 状态文件** — 加载 project-context（若存在），尝试读取 {implementation_artifacts}/sprint-status.yaml；文件不存在则提示先跑 sprint-planning 并退出。
3. **2. 读取解析、校验与风险检测** — 完整读入并解析元数据；把 development_status 的 key 分为 epic（epic- 开头且非 -retrospective 结尾）、retrospective（-retrospective 结尾）与故事三类；做遗留映射（drafted→ready-for-dev、contexted→in-progress）；按状态计数。出现无法识别的状态时列出并要求用户给出修正（或跳过）。风险检测：有 review 故事→建议 code-review；有 in-progress 且无 ready-for-dev→建议专注当前故事；全 epic 都是 backlog 且无 ready-for-dev→建议 create-story；last_updated 超 7 天（缺失则回退 generated）→告警可能陈旧；故事 key 找不到对应 epic→孤儿故事告警；epic 进行中却无故事→告警。
4. **3. 选择下一步推荐** — 按优先级取唯一推荐：有 in-progress 故事→dev-story（取其中第一个）；否则有 review→code-review；否则有 ready-for-dev→dev-story；否则有 backlog→create-story；否则有 retrospective 为 optional→retrospective；全无则宣告实施项全部完成。取「第一个」时按 epic 号再故事号排序。
5. **4. 展示汇总** — 输出项目与追踪信息、故事各状态计数、epic 各状态计数、下一步推荐及其命令，以及风险列表。
6. **5. 提供操作选项** — 四选一：立即运行推荐工作流（若目标带故事则设置 story_key）/ 按状态分组列出全部故事 / 展示 sprint-status.yaml 原文 / 退出。
7. **20. data 模式输出** — 非交互：同 step 2/3 解析与推荐后，以 template-output 导出 next_workflow_id、next_story_id、各状态计数与 risks，返回调用方。
8. **30. validate 模式校验** — 非交互：校验文件存在性与必需元数据字段、development_status 非空、状态取值合法，导出 is_valid / error / suggestion / message，供其它流程做前置检查。

> 备注：本地副本含 data 与 validate 两种非交互模式（旧版全局副本无此结构），这是它被其它流程当作「状态查询/校验服务」调用的原因，也是 CSV required=false（随时可用）的实际含义。

#### `bmad-agent-tech-writer`

*Agent 角色 ｜ 本机已装*

人设型 agent「Paige · 技术文档专家」，负责把复杂概念写成可读文档、画 Mermaid 图、校验文档规范、做项目文档化，沉淀项目知识供人和后续 AI 复用。用户说“找 Paige”或“要技术文档专家”时激活。

- **阶段**：anytime
- **门禁**：可选
- **入口**：{'command': 'bmad-agent-tech-writer', 'args': [], 'howZh': '按技能名调用（或用户点名 Paige）。激活序列与其它 agent 相同：解析 agent 配置 → 人设 → 持久事实 → 配置 → 问候 → 呈现菜单或直接分派。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：project-knowledge
- **产出物**：document
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-agent-tech-writer`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `DP` | 项目文档化 | `Generate comprehensive project documentation (brownfield analysis, architecture scanning)` | 对既有项目做全面文档生成（棕地分析、架构扫描），调用 bmad-document-project |
| `WD` | 写文档 | `Author a document following documentation best practices through guided conversation` | 多轮对话澄清意图后，按文档最佳实践撰写完整文档（写 → 研究 → 起草 → 复核） |
| `MG` | 生成 Mermaid 图 | `Create a Mermaid-compliant diagram based on your description` | 按描述建议图形类型并生成符合 Mermaid 语法与 CommonMark 围栏规范的图 |
| `VD` | 文档校验 | `Validate documentation against standards and best practices` | 针对指定文档输出按优先级排列的可操作改进建议 |
| `EC` | 概念讲解 | `Create clear technical explanations with examples and diagrams` | 面向指定受众，用示例与 Mermaid 图把复杂概念讲清楚 |

**流程步骤**

1. **解析 agent 配置块** — 同其它 agent：脚本解析失败则按 base→team→user 手工合并 customize.toml。
2. **采用 Paige 人设** — 技术文档专家身份，叠加 role/identity/communication_style/principles。
3. **载入持久事实与配置** — 载入 persistent_facts（默认 project-context.md）与 _bmad/bmm/config.yaml。
4. **问候 + 菜单分派** — 以 Paige 身份问候并提醒 bmad-help，然后按菜单码分派到 DP/WD/MG/VD/EC 之一。
5. **WD 写文档子流程** — 澄清意图 → 子代理研究参考资料 → 起草 → 子进程复核内容与规范，产出完整文档。
6. **MG 绘图子流程** — 明确要可视化的对象 → 推荐图形类型 → 严格按 Mermaid 语法生成 → 按反馈迭代。
7. **VD 校验子流程** — 完整读入文档 → 按文档标准与用户指定焦点分析 → 输出按优先级排序的改进清单。
8. **EC 讲解子流程** — 明确概念与受众 → 按任务导向拆节 → 配代码示例与 Mermaid 图 → 用适配受众的语言交付。

> 备注：help CSV 与该技能实体存在两处对不上：(1) CSV 列有 US（Update Standards，action=update-standards，输出到 _bmad/_memory/tech-writer-sidecar），但 SKILL/customize.toml 菜单里已无 US，改为 DP（项目文档化）——菜单集不同但条数恰好都是 5；(2) 项目内 _bmad/_memory 目录不存在，US 的 outputLocation 当前落空。另 CSV 的 output-location 命名不统一（WD 用 project-knowledge，EC 用 project_knowledge，MG/VD 用 planning_artifacts）。

#### `bmad-correct-course`

*工作流 ｜ 本机已装*

冲刺执行期的重大变更导航（CC）：锁定触发问题后，用变更分析清单全面评估对 PRD、epics、架构、UX 的影响，起草逐处 old→new 的具体改动提案，汇总成一份 Sprint Change Proposal，并按变更规模把手交出去——Minor 由开发者直接实施、Moderate 需 PO/Dev 重排 backlog、Major 需 PM/架构师重新规划。

- **阶段**：anytime
- **门禁**：可选
- **入口**：直接调用技能；触发语如「correct course」「propose sprint change」。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：planning_artifacts
- **产出物**：change proposal
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-correct-course`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `CC` | 纠正航向 | `Correct Course` | 任何时候可用的变更管理：分析影响 → 起草具体改动 → 生成 Sprint Change Proposal → 按 Minor/Moderate/Major 分级路由，可能建议回滚、更新 PRD、重做架构或重新 sprint planning |

**流程步骤**

1. **1. 初始化变更导航** — 确认变更触发点，让用户描述问题；核对文档可得性（PRD 与当前 Epics/故事为必需，架构与 UI/UX 可选）；让用户选交互模式：Incremental（推荐，逐条协作精修）或 Batch（一次性呈现全部改动）。触发问题描述不清，或 PRD/Epics 不可得时 HALT。
2. **2. 执行变更分析清单** — 逐节执行 checklist.md 的系统性分析并与用户交互，每项标记 [x] Done / [N/A] 跳过 / [!] 需跟进，持续记录发现与影响，每完成一个大节汇报进度。清单无法完成时先与用户解决阻塞项。
3. **3. 起草具体变更提案** — 按清单发现为每个受影响产物给出明确的编辑提案：故事改动（old→new 文本 + 故事 ID + 章节 + 理由）、PRD 修改（精确章节 + 当前 vs 提议 + 对 MVP 范围的影响）、架构变更（受影响组件/模式/技术选型、需更新的图、连带影响）、UI/UX 更新（具体界面/组件、线框或流程改动、用户体验影响）。Incremental 模式逐条呈现并等 Approve/Edit/Skip。
4. **4. 生成 Sprint Change Proposal** — 汇总五段式提案：①问题摘要（触发点、发现时机与背景、证据）②影响分析（对 epic、当前与后续故事、PRD/架构/UI-UX 冲突、代码与基础设施的技术影响）③推荐路径（Direct Adjustment 改/加故事、Potential Rollback 回滚已完成工作、MVP Review 缩范围或改目标，附理由、工作量、风险与时间线影响）④详细变更提案（按产物分组，含 before/after 与论证）⑤实施交接（Minor 开发者直接做 / Moderate 需重组 backlog / Major 需根本性重新规划）。写入 {planning_artifacts}/sprint-change-proposal-{date}.md 并请用户确认或修改。
5. **5. 敲定并路由实施** — 取得用户对提案的明确批准（yes/no/revise；revise 则回到 step 3 或 step 4）。批准后按规模分级交接：Minor → 开发者代理直接实施，交付最终编辑提案与实施任务；Moderate → PO/开发者代理，交付提案 + backlog 重组方案；Major → PM/方案架构师，交付完整提案 + 升级通知。确认交接完成并记录在流程执行日志中。
6. **6. 工作流收尾** — 总结本次执行（处理的问题、变更规模、改动产物、交接对象），确认交付物齐全（提案文档、含 before/after 的具体编辑提案、实施交接计划），向用户报告完成并重申成功标准与开发者代理的后续步骤。

> 备注：本地目录下 checklist.md 开头仍引用 `./workflow.md`（本地副本无此文件），属迁移遗留的失效路径引用；实际执行时按 SKILL.md step 2 的指引读取同目录 checklist.md 即可。CSV 描述明确本技能可能建议「start over / update PRD / redo architecture / sprint planning」，对应 step 4 的三条推荐路径与 step 5 的三级交接，但本地文本用的是 Direct Adjustment / Rollback / MVP Review 这套术语。

#### `bmad-document-project`

*工作流 ｜ 本机已装*

把既有（棕地）项目扫描成结构化文档集，供人和 LLM 当上下文用。支持首次全量扫描、重扫，以及针对某模块的逐文件深挖。用户说“document this project”“生成项目文档”时使用。

- **阶段**：anytime
- **门禁**：可选
- **入口**：{'command': 'bmad-document-project', 'args': [], 'howZh': '按技能名调用。SKILL.md 落激活序列后转 instructions.md 路由器：先查断点状态文件，再决定 initial_scan / full_rescan / deep_dive 模式并转对应子工作流。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：project-knowledge
- **产出物**：*
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-document-project`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `resume` | 断点续跑 | `Resume from where we left off` | 存在 project-scan-report.json 时选择 1：从记录的 current_step 继续，复用缓存的 project type |
| `full-rescan` | 全量重扫 | `Re-scan entire project` | 已存在 index.md 时选择 1：按最新变更更新全部文档（旧状态归档到 .archive/） |
| `deep-dive` | 指定区域深挖 | `Deep-dive into specific area` | 已存在 index.md 时选择 2：对某功能/模块/目录做 exhaustive 级逐文件深挖文档 |
| `cancel` | 取消 | `Cancel` | 保留既有文档原样退出；状态文件超过 24 小时则自动归档并重新扫描 |

**流程步骤**

1. **载入文档需求数据** — 非续跑时载入 documentation-requirements.csv，取得各项目类型应产出的文档清单。
2. **识别项目结构并分类** — 探测项目部件（parts）并归类项目类型，决定后续分析范围。
3. **盘点既有文档与用户上下文** — 按 README/ARCHITECTURE/API 等模式扫描既有文档，建立清单并补采用户上下文。
4. **逐部件分析技术栈** — 解析 package.json/go.mod 等清单，产出框架、语言、版本、依赖的技术表。
5. **按项目类型做条件分析** — 依 scan_level（quick/deep/exhaustive）分批读文件、提取、写盘、校验并清出上下文。
6. **生成带注释的源码树** — 产出 source-tree 分析文档，标注关键目录与文件职责。
7. **提取开发与运维信息** — 整理构建、部署、环境变量、运行方式等开发运维信息。
8. **检测多部件集成架构** `可跳过` — 仅当项目含多个部件时：梳理部件间 REST/GraphQL/gRPC/消息队列等契约与数据流。
9. **逐部件生成架构文档** — 为每个部件产出架构说明。
10. **生成配套文档** — 产出项目概览等支撑文档。
11. **生成主索引** — 产出 index.md 作为 AI 检索的主入口。
12. **校验与复核文档** — 对生成文档做完整性与质量校验。
13. **收尾并给出下一步** — 交付文档并提示后续动作。
14. **深挖子流程（13a-13g）** `可跳过` — 选定区域 → exhaustive 逐文件扫描 → 关系与数据流分析 → 关联代码与相似模式 → 生成深挖文档 → 回写主索引 → 询问继续或结束。

> 备注：instructions.md 路由器步骤号从 n=1 直接跳到 n=3，中间没有 step 2（疑似编号遗留）。子工作流以 scan_level=quick/deep/exhaustive 控制深度，deep-dive 一律 exhaustive 且明令禁止抽样。deep-dive-instructions.md 的步骤编号为 13a-13g，与主流程 0.5-12 同属一条编号序列。CSV 的 outputs 写的是 "*"（产出整套文档而非单一文件）。

#### `bmad-generate-project-context`

*工作流 ｜ 本机已装*

扫描既有代码库生成精简、面向 LLM 优化的 project-context.md（GPC）：只记录 AI 代理在实现代码时容易被忽略的关键规则、模式与约定，棕地项目尤其重要。产出为 {output_folder}/project-context.md。

- **阶段**：anytime
- **门禁**：可选
- **入口**：直接调用技能；触发语如「generate project context」「create project context」。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：output_folder
- **产出物**：project context
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-generate-project-context`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `GPC` | 生成项目上下文 | `Generate Project Context` | 棕地项目必备：发现既有上下文与技术栈 → 按类别生成 LLM 优化规则 → 精简定稿为 project-context.md |

**流程步骤**

1. **1. 上下文发现与初始化** — 查找 {project_knowledge}/project-context.md 或 {project-root}/**/project-context.md 等既有上下文与技术栈线索，识别 AI 代理必须知道的关键实现规则；从 ../project-context-template.md 拷贝模板到 {output_folder}/project-context.md 并初始化 frontmatter。
2. **2. 上下文规则生成** — 按规则类别逐项生成内容，聚焦 LLM 容易遗忘的非显然细节，与用户协作确认。
3. **3. 上下文完成与定稿** — 为 LLM 上下文效率复核并优化内容，确保关键规则均已捕获且可执行，更新 frontmatter 完成状态收尾（本流程最后一步）。

> 备注：本地副本为 step-file 架构（steps/ 下 3 个步骤文件 + project-context-template.md）。CSV 的 output-location 记作 output_folder，与 step-01 中的 {output_folder}/project-context.md 一致，具体目录由 config 解析。

#### `bmad-quick-dev`

*工作流 ｜ 本机已装*

把任意意图直接变成可评审代码的通用通道（QQ）：澄清意图并判定路由（epic 故事走缓存/编译的 epic 上下文，自由意图走规划产物），写出 900-1600 token 的单目标 spec 并经人工批准，交给子代理实现，再用三层对抗评审做意图缺口/坏 spec/patch/defer 分类与回环，最后给出 Suggested Review Order、提交并打开编辑器。零爆炸半径的小改动走一步到位的 one-shot 通道。

- **阶段**：anytime
- **门禁**：可选
- **入口**：直接调用技能；当用户想「build/fix/tweak/refactor/add/modify」任何代码时使用。可传 spec 文件路径（带 status frontmatter）直接续做草稿/实现/评审阶段。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：implementation_artifacts
- **产出物**：spec and project implementation
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-quick-dev`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `QQ` | 快速开发 | `Quick Dev` | 意图进、代码出：澄清与路由 → 写并批准 spec → 实现 → 三层对抗评审与回环 → 呈现评审顺序并提交；小改动走 one-shot |

**流程步骤**

1. **1. 澄清与路由** — 先做意图判定（显式参数里若是带 status frontmatter 的 spec，按 draft/ready-for-dev/in-progress/in-review 分别早退到 step-02/03/04；done 只当上下文）→ 近期对话 → 否则扫描 {implementation_artifacts} 中活跃 spec 让用户选择或新建。加载上下文：判断是否为 epic 故事，是则优先复用 {implementation_artifacts}/epic-N-context.md 缓存（无效则按 compile-epic-context.md 由子代理编译，失败则内联编译并校验），并加载同 epic 中编号更小且 done 的 spec 做连续性上下文；非 epic 则按需选择加载 PRD/架构/UX/epics/brief。随后澄清意图（成串提问须逐条答完）、版本控制健全检查（工作树脏或分支与意图明显不符须 HALT）、多目标检查（按 SCOPE STANDARD 判定是否需拆分，HALT 让用户选拆分或保留）。最后路由：零爆炸半径走 step-oneshot.md，其余走 plan-code-review（不确定时选后者）。
2. **2. 计划** — 草稿续做时保留 <frozen-after-approval> 原文；调查代码库（深度探索隔离到子代理，只回蒸馏摘要）；按 spec-template.md 填写并写入 {implementation_artifacts}/spec-{slug}.md；按「Ready for Development」标准自审；有意图缺口就提问不臆测；spec 超过 1600 token 时展示计数并让用户选拆分或保留。CHECKPOINT 1 展示摘要（路径用 CWD 相对格式）并提示可用 bmad-advanced-elicitation / bmad-party-mode / bmad-code-review 外部打磨，HALT 让用户选 [A] 批准或 [E] 编辑。批准后重读磁盘文件（若文件消失则 HALT 停止），承认外部改动并把 status 置 ready-for-dev，frozen 区锁定。
3. **3. 实现** — 先记录 baseline_commit（无版本控制记 NO_VCS）到 spec frontmatter，status 置 in-progress 并按 sync-sprint-status.md 同步；若 frontmatter 的 context 列表非空则先加载这些文件（交给子代理时随提示词一并给出）。把 spec 交给子代理实现，无子代理则自己直接实现。路径书写规则：spec 内链接用 spec 相对路径，终端输出用 CWD 相对加 :line。离开本步前逐项自检 Tasks & Acceptance，未完成的当场做完。
4. **4. 评审** — status 置 in-review；按 baseline_commit 构造含未跟踪文件的 diff（只读，不 git add）。无会话上下文地并行起三层子代理：Blind hunter（仅 diff，走 bmad-review-adversarial-general）、Edge case hunter（diff + 项目读权限，走 bmad-review-edge-case-hunter）、Acceptance auditor（diff + spec + spec 中 context 列出的文档）；无子代理则生成三份评审 prompt 文件并 HALT。去重后分类：intent_gap（改动引起且意图不完整）、bad_spec（改动引起、spec 本应写清，存疑时优先归此类）、patch（可小修）、defer（既有问题，记入 deferred-work.md）、reject（噪音丢弃）。级联处理：intent_gap/bad_spec 触发回环（回滚代码，前者回到人工澄清后重跑 step 2-4，后者先提炼 KEEP 指令、查 Spec Change Log、追加变更日志后重跑 step 3-4），specLoopIteration 超过 5 次则 HALT 升级。
5. **5. 呈现** — 按 baseline_commit 生成 diff 并追加「Suggested Review Order」段（按关注点而非文件排序、以入口点领起、外围放最后，全部用 spec 相对的可点击链接并配一行说明）。spec status 置 done，按 sync-sprint-status.md 把 sprint 状态置 review。有版本控制且工作树脏时用约定式信息创建本地提交（绝不自动 push）。用 code -r 打开仓库根与 spec 供点击浏览，失败则降级提示路径。输出总结（含提交哈希、改动文件列表、评审结论统计、导航提示）并提供推送/建 PR 的选项后 HALT。
6. **one-shot 通道：实现、评审、呈现** `可跳过` — 零爆炸半径、无意架构决策的清晰意图走此通道：同步 sprint 状态为 in-progress 后直接实现；用子代理跑 bmad-review-adversarial-general（无会话上下文，子代理不可用则写评审 prompt 文件并 HALT）；只分 patch（立即自动修）/defer（记入 deferred-work.md）/reject（丢弃）三类，若发现问题严重到不是小修则 HALT 交人工决定；随后生成精简 spec trace（frontmatter 加 route: one-shot，只保留标题与意图、Suggested Review Order），状态置 done 并同步 sprint 为 review；有版本控制则提交；最后打开编辑器呈现总结并 HALT。

> 备注：本地副本的 step 文件直接放在技能根目录（不是 steps/ 子目录），另有 compile-epic-context.md、sync-sprint-status.md、spec-template.md 三个被引用的配套文件。这是「随时可用」的通用实现入口（CSV phase=anytime、required=false），与故事循环（CS→DS→CR→ER）并行，不依赖 sprint 规划，但若识别出是 epic 故事会尝试复用 epic 上下文并同步 sprint 状态。

#### `bmad-agent-analyst`

*Agent 角色 ｜ 本机已装*

人设型 agent「Mary · 商业分析师」。在立项前的研究/分析阶段陪用户做创意发散、市场与领域调研、需求梳理，把模糊想法变成有证据支撑的结论。用户说“找 Mary”或“要商业分析师”时激活。

- **阶段**：—
- **门禁**：可选
- **入口**：{'command': 'bmad-agent-analyst', 'args': [], 'howZh': '按技能名调用（或用户点名 Mary）。激活后先采纳人设、载入 persistent_facts 与 bmm/config.yaml，再按菜单分派；用户首句若已明确意图则跳过菜单直接执行。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-agent-analyst`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `BP` | 头脑风暴 | `Expert guided brainstorming facilitation` | 专家引导式创意发散，调用 bmad-brainstorming 技能 |
| `MR` | 市场调研 | `Market analysis, competitive landscape, customer needs and trends` | 市场分析、竞争格局、客户需求与趋势，调用 bmad-market-research |
| `DR` | 领域调研 | `Industry domain deep dive, subject matter expertise and terminology` | 行业领域深挖、术语与专业知识，调用 bmad-domain-research |
| `TR` | 技术调研 | `Technical feasibility, architecture options and implementation approaches` | 技术可行性、架构选型与实现路径，调用 bmad-technical-research |
| `CB` | 产品简介 | `Create or update product briefs through guided or autonomous discovery` | 创建或更新 Product Brief，调用 bmad-product-brief |
| `WB` | PRFAQ 挑战 | `Working Backwards PRFAQ challenge` | 亚马逊 Working Backwards 式概念锻造与压力测试，调用 bmad-prfaq |
| `DP` | 项目文档化 | `Analyze an existing project to produce documentation for human and LLM consumption` | 扫描既有项目生成文档（跨阶段技能，属 anytime），调用 bmad-document-project |

**流程步骤**

1. **解析 agent 配置块** — 运行 resolve_customization.py 取 agent 段；失败则按 base→team→user 顺序手工合并 customize.toml 与 _bmad/custom/*.toml。
2. **采用人设** — 代入 Mary / 商业分析师身份，叠加 role、identity、communication_style、principles。
3. **载入持久事实** — 把 persistent_facts 作为全程基础上下文（默认 file:{project-root}/**/project-context.md）。
4. **载入配置** — 读 _bmad/bmm/config.yaml，解析 user_name、communication_language、planning_artifacts、project_knowledge。
5. **问候并呈现菜单** — 以人设图标 + 用户名问候，提醒可随时用 bmad-help，然后渲染菜单等待输入或直接分派明确意图。
6. **会话内保持人设** — 分派到子技能后，Mary 的人设、图标前缀与语言设置继续贯穿每个回合，直到用户解除。

> 备注：inHelpCatalog=false：bmad-help.csv 未登记该 agent 自身，依赖字段留空。 基线 help CSV 中无该 agent 的任何条目，菜单与角色描述全部取自 customize.toml。菜单里 DP 指向 phase=anytime 的 bmad-document-project、BP 指向 core 模块的 bmad-brainstorming，属跨阶段/跨模块分派。activation_steps_prepend/append 默认为空数组，可被 override 追加。

#### `bmad-agent-architect`

*Agent 角色 ｜ 本机已装*

人格化 agent：Winston，系统架构师。在 BMad Method 的方案设计阶段把 PRD 与 UX 转成能让实现不跑偏的技术架构决策，主张「抽象前先三次重复」「用保守技术求稳」「开发者生产力即架构」，回答给权衡而非结论。用户点名 Winston 或要求找架构师时激活。

- **阶段**：—
- **门禁**：可选
- **入口**：直接调用技能 bmad-agent-architect（或在对话里点名 Winston / 架构师）。激活链：解析 agent 配置块 → 执行 prepend → 采用 Winston 人格 → 载入 persistent_facts 与 _bmad/bmm/config.yaml → 以 🏗️ 图标前缀问候并渲染菜单等待选择；人格、图标前缀与通信语言在此后每轮延续，直至用户解除。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-agent-architect`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `CA` | 创建架构 | `Guided workflow to document technical decisions to keep implementation on track` | 引导式记录技术决策，使实现全程可对齐；调用 bmad-create-architecture。 |
| `IR` | 实现就绪检查 | `Ensure the PRD, UX, Architecture and Epics and Stories List are all aligned` | 校验 PRD、UX、架构与史诗/故事清单四者是否对齐；调用 bmad-check-implementation-readiness。 |

**流程步骤**

1. **1. 解析 agent 配置块** — 运行 resolve_customization.py --skill {skill-root} --key agent；脚本失败则自行按 base→team→user 顺序读取 customize.toml、_bmad/custom/{skill-name}.toml、_bmad/custom/{skill-name}.user.toml 并做同样的结构合并（标量覆盖、表深合并、按 code/id 键的数组替换同名项并追加新项、其余数组追加）。
2. **2. 执行 prepend 步骤** — 按顺序执行 {agent.activation_steps_prepend} 的每一项（本地默认空数组）。
3. **3. 采用 Winston 人格** — 在 Overview 身份之上叠加定制层：扮演 {agent.role}（把 PRD 与 UX 转成架构决策以保障实现）、体现 {agent.identity}（Martin Fowler 的务实 + Werner Vogels 的云规模现实主义）、按 {agent.communication_style}（沉稳务实、权衡而非结论）说话、遵循 {agent.principles}；用户解除前不出戏，调用其他技能时人格延续。
4. **4. 载入持久事实** — 把 {agent.persistent_facts} 每一项当作全程基础上下文；file: 前缀项按 {project-root} 下的路径或通配符加载实际内容，其余按字面事实（默认 file:{project-root}/**/project-context.md）。
5. **5. 载入配置** — 读取 _bmad/bmm/config.yaml，解析 user_name（问候用）、communication_language（全部沟通）、document_output_language（输出文档）、planning_artifacts（输出位置与产物扫描）、project_knowledge（额外上下文扫描）。
6. **6. 问候用户** — 以 Winston 身份按 {communication_language} 热情称呼 {user_name}，问候开头带 {agent.icon}（🏗️）便于一眼识别发言人，并提醒用户随时可调用 bmad-help；此后每条消息都保留图标前缀。
7. **7. 执行 append 步骤** — 按顺序执行 {agent.activation_steps_append}（本地默认空数组）；完成后确认 prepend / append 均已在主流程开始前按序执行完。
8. **8. 分发或展示菜单** — 用户首条消息若已明确对应菜单项（如"Winston，我们来设计架构"）则跳过菜单直接分发；否则把 {agent.menu} 渲染为 Code / Description / Action 编号表并停下等待输入，接受序号、菜单码或模糊描述匹配；两项以上接近时才追问一句，都不匹配则继续对话（闲聊、澄清、bmad-help 始终可用）。

> 备注：inHelpCatalog=false，bmad-help.csv 与 _bmad/bmm/module-help.csv 均未登记该 agent，用户无法通过 /bmad-help 目录发现。属该模块系统性现象：5 个人格 agent 中仅 bmad-agent-tech-writer 登记了目录条目，architect 与其余 3 个 agent 一样只能靠点名或直接调用技能名进入。菜单 2 项（CA / IR）来自 customize.toml 的 [[agent.menu]]，help 表中无对应行，故 dependencies 为空对象。persistent_facts 默认只加载项目内 project-context.md，activation_steps_prepend/append 均为空数组、可被 override 追加；项目级定制文件 _bmad/custom/bmad-agent-architect.toml 本机不存在。

#### `bmad-agent-dev`

*Agent 角色 ｜ 本机已装*

人格化 agent：Amelia，高级软件工程师。以测试先行（红-绿-重构，顺序不可换）纪律执行已批准的故事，交付满足每条验收标准的可验证代码；菜单覆盖实现、快速开发、测试生成、代码评审、冲刺规划、故事准备、史诗复盘与调查共 8 项。风格极简，以文件路径与 AC 编号为语言，用户点名 Amelia 或要求开发 agent 时激活。

- **阶段**：—
- **门禁**：可选
- **入口**：直接调用技能 bmad-agent-dev（或在对话里点名 Amelia / 开发 agent）。激活链与 architect 同构：解析 agent 配置块 → prepend → 采用 Amelia 人格 → 载入 persistent_facts 与 _bmad/bmm/config.yaml → 以 💻 图标前缀问候并渲染 8 项菜单；人格延续至用户解除。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-agent-dev`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `DS` | 开发故事 | `Write the next or specified story's tests and code` | 按测试先行写下一条或指定故事的测试与实现代码；调用 bmad-dev-story。 |
| `QD` | 快速开发 | `Unified quick flow — clarify intent, plan, implement, review, present` | 一体化快速流程：澄清意图 → 计划 → 实现 → 评审 → 交付；调用 bmad-quick-dev。 |
| `QA` | 生成端到端测试 | `Generate API and E2E tests for existing features` | 为已有功能生成 API 测试与 E2E 测试；调用 bmad-qa-generate-e2e-tests。 |
| `CR` | 代码评审 | `Initiate a comprehensive code review across multiple quality facets` | 发起覆盖多个质量维度的综合代码评审；调用 bmad-code-review。 |
| `SP` | 冲刺计划 | `Generate or update the sprint plan that sequences tasks for implementation` | 生成或更新为任务排定实现顺序的冲刺计划；调用 bmad-sprint-planning。 |
| `CS` | 创建故事 | `Prepare a story with all required context for implementation` | 准备故事并附上实现所需的全部上下文；调用 bmad-create-story。 |
| `ER` | 史诗复盘 | `Party mode review of all work completed across an epic` | 以 party mode 会审形式复盘某个史诗内已完成的全部工作；调用 bmad-retrospective。 |
| `IN` | 调查 | `Forensic case investigation with evidence-graded findings, calibrated to the input` | 取证式排查，产出按证据等级标注的调查结论；调用 bmad-investigate。 |

**流程步骤**

1. **1. 解析 agent 配置块** — 运行 resolve_customization.py --skill {skill-root} --key agent；脚本失败则按 base→team→user 顺序手工读取 customize.toml 与 _bmad/custom/{skill-name}(.user).toml 并做同样的结构合并。
2. **2. 执行 prepend 步骤** — 按顺序执行 {agent.activation_steps_prepend} 的每一项（本地默认空数组）。
3. **3. 采用 Amelia 人格** — 叠加定制层：扮演 {agent.role}（以测试先行纪律实现已批准故事并交付可验证代码）、体现 {agent.identity}（Kent Beck 的 TDD 纪律 + 务实程序员的精确）、按 {agent.communication_style}（极简、以文件路径与 AC 编号说话、每句可引用、无废话）说话、遵循 {agent.principles}（无通过测试不算完成、红绿重构顺序不可换、任务按书写顺序执行）。
4. **4. 载入持久事实** — 把 {agent.persistent_facts} 每一项当作全程基础上下文；file: 前缀项按 {project-root} 下的路径或通配符加载内容（默认 file:{project-root}/**/project-context.md）。
5. **5. 载入配置** — 读取 _bmad/bmm/config.yaml，解析 user_name、communication_language、document_output_language、planning_artifacts、project_knowledge。
6. **6. 问候用户** — 以 Amelia 身份按 {communication_language} 称呼 {user_name} 问候，开头带 {agent.icon}（💻），提示可随时调用 bmad-help；此后每条消息保留图标前缀。
7. **7. 执行 append 步骤** — 按顺序执行 {agent.activation_steps_append}（本地默认空数组），并在进入主流程前确认 prepend / append 均已按序执行完。
8. **8. 分发或展示菜单** — 用户首条消息若已明确对应菜单项（如"Amelia，实现下一条故事"）则跳过菜单直接分发；否则渲染 {agent.menu} 的 Code / Description / Action 编号表并停下等待输入，接受序号、菜单码或模糊描述匹配；无匹配则不强行分流，继续对话或转 bmad-help。

> 备注：inHelpCatalog=false，bmad-help.csv 与 _bmad/bmm/module-help.csv 均未登记该 agent，用户无法通过 /bmad-help 目录发现（同模块 5 个人格 agent 中仅 bmad-agent-tech-writer 有目录条目）。菜单 8 项（DS/QD/QA/CR/SP/CS/ER/IN）全部来自 customize.toml 的 [[agent.menu]]，help 表中无对应行，故 dependencies 为空对象；其中 IN → bmad-investigate 与本模块缺失条目同源，QD → bmad-quick-dev 的目录菜单码实为 QQ（help 表登记值），两处码不一致来自不同来源（本地 agent 菜单 vs help 目录）。activation_steps_prepend/append 默认空数组，persistent_facts 默认只加载 project-context.md；_bmad/custom/bmad-agent-dev.toml 本机不存在。

#### `bmad-agent-pm`

*Agent 角色 ｜ 本机已装*

人设型 agent「John · 产品经理」，通过用户访谈和需求挖掘把产品愿景变成可开发的小增量 PRD，并负责把 Epics/Stories 和就绪检查串起来。用户说“找 John”或“要产品经理”时激活。

- **阶段**：—
- **门禁**：可选
- **入口**：{'command': 'bmad-agent-pm', 'args': [], 'howZh': '按技能名调用（或用户点名 John）。激活后采纳人设、载入 persistent_facts 与配置、问候，然后按菜单分派；首句意图明确则跳过菜单。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-agent-pm`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `PRD` | PRD 全流程 | `Create, update, or validate a PRD` | 创建/更新/校验 PRD，说出意图即可，未说明时技能会主动问；调用 bmad-prd |
| `CE` | 创建史诗与故事 | `Create the Epics and Stories Listing that will drive development` | 生成驱动开发的 Epics 与 Stories 清单；调用 bmad-create-epics-and-stories（属 3-solutioning 阶段） |
| `IR` | 实现就绪检查 | `Ensure the PRD, UX, Architecture and Epics and Stories List are all aligned` | 核对 PRD/UX/架构/Epics-Stories 四者是否对齐；调用 bmad-check-implementation-readiness |
| `CC` | 中途改道 | `Determine how to proceed if major need for change is discovered mid implementation` | 实现中途发现重大变更需求时决定如何继续；调用 bmad-correct-course |

**流程步骤**

1. **解析 agent 配置块** — 脚本解析 agent 段，失败则按 base→team→user 手工合并 customize.toml。
2. **采用 John 人设** — 产品经理身份（以 Marty Cagan / Teresa Torres 为思维参照、Bezos 六页纸写作纪律），叠加自定义 role/principles。
3. **载入持久事实与配置** — 载入 persistent_facts（默认 project-context.md）与 _bmad/bmm/config.yaml。
4. **问候并分派** — 以 John 身份问候，提醒可随时用 bmad-help，然后渲染菜单等待输入或按首句意图直接分派。

> 备注：inHelpCatalog=false：bmad-help.csv 未登记该 agent 自身，依赖字段留空。 基线 help CSV 无该 agent 条目。菜单里有 3 项（CE/IR/CC）指向 3-solutioning 与 4-implementation 阶段的技能，属跨阶段分派；本技能自身归属 2-plan-workflows 目录。

#### `bmad-agent-ux-designer`

*Agent 角色 ｜ 本机已装*

人设型 agent「Sally · UX 设计师」，把用户需求翻译成交互设计与 UX 规范，兼顾共情与边界情况严谨性，为架构与实现提供明确的设计意图。用户说“找 Sally”或“要 UX 设计师”时激活。

- **阶段**：—
- **门禁**：可选
- **入口**：{'command': 'bmad-agent-ux-designer', 'args': [], 'howZh': '按技能名调用（或用户点名 Sally）。激活序列与其它 agent 一致，之后按菜单分派。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-agent-ux-designer`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `CU` | 创建 UX | `Guidance through realizing the plan for your UX to inform architecture and implementation` | 引导把 UX 方案落地成规范，供架构与实现使用；调用 bmad-ux |

**流程步骤**

1. **解析 agent 配置块** — 脚本解析 agent 段，失败则按 base→team→user 手工合并 customize.toml。
2. **采用 Sally 人设** — UX 设计师身份（以 Don Norman 的人本设计与 Alan Cooper 的角色纪律为参照），叠加自定义 role/principles。
3. **载入持久事实与配置** — 载入 persistent_facts（默认 project-context.md）与 _bmad/bmm/config.yaml。
4. **问候并分派** — 以 Sally 身份问候并提醒 bmad-help，菜单当前只有 CU 一项，通常直接进入 bmad-ux。

> 备注：inHelpCatalog=false：bmad-help.csv 未登记该 agent 自身，依赖字段留空。 基线 help CSV 无该 agent 条目；菜单仅 1 项（CU → bmad-ux），是三个 bmm agent 中菜单最短的，本质上是 bmad-ux 的人设外壳。

#### `bmad-create-prd`

*工具 ｜ 本机已装*

已废弃的兼容垫片，把旧调用名转发给 bmad-prd 的 create 意图，并在转发前向用户提示弃用信息。仅为兼容既有按名调用与 _bmad/custom/bmad-create-prd.toml 覆盖文件而保留，v7 计划移除。

- **阶段**：—
- **门禁**：可选
- **入口**：{'command': 'bmad-create-prd', 'args': [], 'howZh': '按旧技能名调用即触发；先解析 customization，再显式告知弃用通知，然后以 intent=create 的上下文调用 bmad-prd，自身不再执行后续步骤。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-create-prd`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **解析旧定制字段** — 取 activation_steps_prepend/append、persistent_facts、on_complete 四个遗留字段。
2. **载入配置** — 读 _bmad/bmm/config.yaml 解析 user_name 与 communication_language。
3. **发出弃用通知** — 以用户语言提示已弃用，并说明迁移到 bmad-prd 后可获得更多定制字段。
4. **转发到 bmad-prd** — 带 intent=create、预解析的遗留定制与用户原始输入调用 bmad-prd，之后不再执行任何步骤。

> 备注：inHelpCatalog=false：help 目录将 create/update/validate 三种意图合并登记为单条 bmad-prd（menuCode=PRD），该 shim 自身无登记行，依赖字段留空。 基线 help CSV 无任何条目（无菜单码、无 phase），因此该技能在 help 体系里不可见；其存在意义仅为向后兼容。旧版本（C:/Users/93559/.claude/skills/bmad-create-prd/）仍是完整 PRD 全流程 + steps-c 步骤目录，与本项目内的垫片版本完全不同——比较跨机技能时需注意。

#### `bmad-edit-prd`

*工具 ｜ 本机已装*

已废弃的兼容垫片，把旧调用名转发给 bmad-prd 的 update 意图（修改既有 PRD），并提示弃用信息。仅为兼容旧调用名与旧覆盖文件保留，v7 计划移除。

- **阶段**：—
- **门禁**：可选
- **入口**：{'command': 'bmad-edit-prd', 'args': [], 'howZh': '按旧技能名调用即触发；转发时会把用户原始输入（目标 PRD 路径、变更信号等）原样带给 bmad-prd。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-edit-prd`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **解析旧定制字段** — 取四个遗留字段（prepend/append/persistent_facts/on_complete）。
2. **载入配置** — 读 bmm/config.yaml 解析用户名与语言。
3. **发出弃用通知** — 提示已弃用并说明迁移方式。
4. **转发到 bmad-prd（update）** — 带 intent=update 与用户原始输入调用 bmad-prd，之后止步。

> 备注：inHelpCatalog=false：help 目录将 create/update/validate 三种意图合并登记为单条 bmad-prd（menuCode=PRD），该 shim 自身无登记行，依赖字段留空。 基线 help CSV 无条目。与 bmad-create-prd、bmad-validate-prd 构成同一批弃用垫片，三者结构完全同构，仅 intent 不同。

#### `bmad-validate-prd`

*工具 ｜ 本机已装*

已废弃的兼容垫片，把旧调用名转发给 bmad-prd 的 validate 意图（只批改、产出校验报告），并提示弃用信息。仅为兼容旧调用名与旧覆盖文件保留，v7 计划移除。

- **阶段**：—
- **门禁**：可选
- **入口**：{'command': 'bmad-validate-prd', 'args': [], 'howZh': '按旧技能名调用即触发；转发时把用户原始输入（目标 PRD 路径等）原样带给 bmad-prd。'}
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-validate-prd`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **解析旧定制字段** — 取四个遗留字段（prepend/append/persistent_facts/on_complete）。
2. **载入配置** — 读 bmm/config.yaml 解析用户名与语言。
3. **发出弃用通知** — 提示已弃用并说明迁移方式。
4. **转发到 bmad-prd（validate）** — 带 intent=validate 与用户原始输入调用 bmad-prd，之后止步；实际校验逻辑与 HTML 报告由 bmad-prd 承担。

> 备注：inHelpCatalog=false：help 目录将 create/update/validate 三种意图合并登记为单条 bmad-prd（menuCode=PRD），该 shim 自身无登记行，依赖字段留空。 基线 help CSV 无条目。旧版本（全局安装）该技能自带 steps-v 校验流程，本项目版本已退化为纯转发垫片，验证能力全部合并进 bmad-prd。


## BMad Builder 构建器

共 5 个技能。元能力：构建与质检 Agent、工作流、模块本身

### 阶段与依赖编排

| 阶段 | 技能 |
| --- | --- |
| anytime | `bmad-agent-builder`<br>`bmad-bmb-setup`<br>`bmad-module-builder`<br>`bmad-workflow-builder` |
| 未标阶段 | `bmad-eval-runner` |

#### `bmad-agent-builder`

*Agent 角色 ｜ 本机已装*

以架构向导身份，通过对话式发现把粗糙的 agent 设想打磨成精简、结果导向的 agent 技能；也可对既有 agent 做质量分析或定向编辑。当用户要创建、分析或编辑 Agent 时使用。构建产物分无状态 / 记忆 / 自主三种形态。

- **阶段**：anytime
- **门禁**：可选
- **入口**：bmad-help 菜单 BA（构建 Agent）或 AA（分析 Agent）；也可直接描述需求、给出现有 agent 路径并说明分析/编辑/重建；支持 --headless / -H 非交互模式。
- **参数**：`{-H: headless mode}\|{description: initial agent concept}\|{path: existing agent to edit or rebuild}`
- **前置**：—
- **后续**：bmad-agent-builder:quality-analysis
- **产出位置**：bmad_builder_output_folder
- **产出物**：agent skill
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-agent-builder`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `BA` | 构建 Agent | `Build an Agent` | 通过对话式发现创建、编辑或重建 agent 技能。 |
| `AA` | 分析 Agent | `Analyze an Agent` | 对现有 agent 运行质量分析——结构、内聚性、提示词工艺与增强机会。 |

**流程步骤**

1. **三向路由** — 读取调用意图，在 Create / Edit / Analyze 间分派，只加载对应的流程文档（build-process / edit-guidance / quality-analysis）。
2. **理解来意与确定形态** — 从开放陈述中提炼核心结果与人格定位，通过自然提问确定无状态 / 记忆 / 自主形态（形态不设菜单，在产出时收敛）。
3. **提出愿景蕴含的能力** — 补充用户未提出但目标隐含的能力与人格角度，用户取舍全程写入 {target-agent-path}/.memlog.md。
4. **先写最小可用版本** — 按 prompt-quality-canon 写最小 persona + capabilities 草稿；逐能力在“引用已装技能”与“内部编写”之间做 fork。
5. **先看草稿再接线** — 在改动代价最低时向用户展示人格口吻、能力清单与 First Breath 体感，暴露不确定点并迭代。
6. **eval 节点** `可跳过` — 调用 bmad-eval-runner 对产出 agent 做 trigger / baseline / quality\|variant 验证；evals_required 非空时成为发布门槛。
7. **定制化取舍与交付** — 询问是否暴露 customize 覆盖钩子（默认否）；剥离仪式、并行跑 lint 门、按模板输出 agent 文件树，并带用户过一遍 memlog 审计。
8. **分析流程（AA）** `可跳过` — 确定性 pre-pass JSON → 并行派发 6 个基础 lens（记忆型另加 sanctum lens）→ 自行合成 findings.json → 渲染并打开 HTML 报告。

> 备注：help CSV 仅注册 BA / AA 两个动作，且二者互为先后（BA followedBy AA，AA precededBy BA）；技能正文另有 Edit 路径（references/edit-guidance.md，保持既有设计的定向改动）未注册为菜单项。定制化配置键为 [agent]（customize.toml），这同时是将其归类为 agent 型技能的依据。

#### `bmad-bmb-setup`

*工作流 ｜ 本机已装*

把 BMad Builder 模块安装并配置到项目中：收集用户偏好，写入 config.yaml / config.user.yaml 与 module-help.csv，创建输出目录并清理旧版安装目录，使模块能力进入 help 菜单。

- **阶段**：anytime
- **门禁**：可选
- **入口**：菜单 SB，或说 install bmb module / configure BMad Builder / setup BMad Builder；支持 -H 与内联值（如 user name is X）跳过交互提问。
- **参数**：`{-H: headless mode}\|{inline values: skip prompts with provided values}`
- **前置**：—
- **后续**：—
- **产出位置**：{project-root}/_bmad
- **产出物**：config.yaml and config.user.yaml
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-bmb-setup`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `SB` | 配置 Builder 模块 | `Setup Builder Module` | 安装或更新 BMad Builder 模块配置与帮助条目。 |

**流程步骤**

1. **读取模块元数据** — 读取 assets/module.yaml 获取模块标识（name/code/version）与变量定义。
2. **检测安装类型** — 区分全新安装、更新（config.yaml 已有本模块 section）、legacy 迁移（存在 _bmad/bmb/config.yaml 等旧格式），并告知用户。
3. **收集配置** — 默认优先级：现有新配置 > legacy 配置 > module.yaml 默认值；核心设置（output_folder、document_output_language 等）与个人设置（user_name、communication_language）分开收集。
4. **写入配置与 help 注册** — 写临时 JSON 答案文件后并行执行 merge-config.py 与 merge-help-csv.py（反僵尸模式：先移除本模块旧条目再写新值），两者失败即停。
5. **创建输出目录并清理 legacy** — 按配置创建尚不存在的输出目录；确认技能已装到 .claude/skills/ 后用 cleanup-legacy.py 删除安装器包目录（幂等，缺目录不算错）。
6. **确认结果** — 依据脚本 JSON 输出展示写入内容、新增 help 条目、fresh install 或 update，最后展示 module_greeting。

> 备注：个人设置（user_name / communication_language）只写入 config.user.yaml（设计上应被 gitignore）；{project-root} 在配置值中是字面 token 不得替换，但在传给脚本的文件系统路径参数中必须先解析为真实项目根，否则脚本报错。

#### `bmad-module-builder`

*工作流 ｜ 本机已装*

规划、创建并校验 BMad 模块：IM 以创意会话产出模块计划文档，CM 把已建好的技能脚手架成可安装模块（多技能生成 -setup 技能、单技能嵌自注册），VM 校验模块结构与能力注册的完整性。

- **阶段**：anytime
- **门禁**：可选
- **入口**：菜单 IM / CM / VM；或按关键词路由（ideate/plan → IM，create/scaffold 或给路径 → CM，validate/check → VM）；CM 与 VM 支持 --headless。
- **参数**：`{description: initial module idea}`
- **前置**：—
- **后续**：bmad-module-builder:create-module
- **产出位置**：bmad_builder_reports
- **产出物**：module plan
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-module-builder`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `IM` | 构思模块 | `Ideate Module` | 头脑风暴并规划 BMad 模块——探索想法、确定架构并产出构建计划。 |
| `CM` | 创建模块 | `Create Module` | 把已建技能脚手架成可安装的 BMad 模块基础设施。 |
| `VM` | 校验模块 | `Validate Module` | 检查模块结构是否完整正确、全部能力是否注册到位。 |

**流程步骤**

1. **IM·建立计划文档** — 复制 module-plan-template 为计划文档，先占位结构化区块；捕捉模块火花并锁定模块身份（名称、2-4 字母代码、描述、独立或扩展）。
2. **IM·创意探索** — 用头脑风暴工具包深挖能力设想、边界案例与惊喜点，只写 Ideas Captured 原始区，刻意不提前结构化。
3. **IM·架构决策** — 软门确认后进入结构化写作；引导“带能力的单 agent”与“多 agent 分工”之间的架构选择，并记录记忆架构与跨 agent 模式。
4. **IM·配置与扩展** — 确定配置变量（key、prompt、默认值）、外部依赖（CLI/MCP）、UI 可视化与 setup 技能扩展，无配置也要显式写明。
5. **IM·技能简报与能力评审** — 为每个规划技能写可零上下文交接给 BA/BW 的自包含简报（人格、核心结果、能力、输入输出、记忆），并逐技能交用户评审迭代到确认。
6. **IM·定稿交接** — 补全计划文档全部区块并置 status=complete；按构建路线图指出第一个要建的技能，主动提议立即进入 BA 或 BW。
7. **CM·发现技能与确认路线** — 读取技能文件夹内每个 SKILL.md（≤4 个并列读、≥5 个用并行子代理）并读 customize.toml 元数据；判定多技能（生成 -setup 技能）或单技能（standalone 自注册）路线。
8. **CM·身份/能力/名册/配置** — 收集模块身份与版本；逐能力定义 help CSV 行（菜单码、action、args、前后依赖、输出）；填充 agent 名册与配置变量、外部依赖。
9. **CM·生成确认与脚手架** — 预览完整 module.yaml 与 module-help.csv 直到确认；运行 scaffold-setup-skill.py（多技能）或 scaffold-standalone-module.py（单技能），standalone 还需把注册检查接入技能 On Activation。
10. **CM·确认与后续** — 展示创建的文件与结构，说明安装方式；standalone 另需提示补全 marketplace.json 分发信息并可用 VM 校验。
11. **VM·结构校验** — 运行 validate-module.py 确定性检查：模块结构、module.yaml 完整性、CSV 缺项/孤儿/重复菜单码/断裂前后引用/缺失必填字段（standalone 另验自注册文件与合并脚本）。
12. **VM·质量评估与报告** — 逐条核对 CSV 与实际能力的完整性/准确性/描述质量/顺序关系/菜单码直觉性/agent 名册漂移；合并脚本发现输出报告，可保存为持久文件，headless 返回结构化 JSON。

> 备注：IM → CM → VM 在 help CSV 中构成三段递进链（IM followedBy CM，CM followedBy VM），且全部 phase=anytime。CM 的 headless 模式需要模块计划文档路径。IM 的计划文档本身就是给 BA/BW 的交接物，形成“IM → (BA/BW 逐个建技能) → CM → VM”的模块生产闭环。

#### `bmad-workflow-builder`

*工作流 ｜ 本机已装*

以技能构建伙伴身份，把半成型想法做成精简、结果导向的 workflow 或 utility 技能；也可编辑既有技能，或用并行扫描器分析既有技能质量并出报告。

- **阶段**：anytime
- **门禁**：可选
- **入口**：菜单 BW（构建工作流）/ AW（分析工作流）/ CW（转换技能）；也可直接描述需求或给出既有技能路径（说 analyze / edit / rebuild）；支持 --headless / -H。
- **参数**：`{-H: headless mode}\|{description: initial skill concept}\|{path: existing skill to edit or rebuild}`
- **前置**：—
- **后续**：bmad-workflow-builder:quality-analysis
- **产出位置**：bmad_builder_output_folder
- **产出物**：workflow skill
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-workflow-builder`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `BW` | 构建工作流 | `Build a Workflow` | 创建、编辑或重建 workflow 或 utility 技能。 |
| `AW` | 分析工作流 | `Analyze a Workflow` | 对现有 workflow/技能运行质量分析——结构与效率及增强机会。 |
| `CW` | 转换技能 | `Convert a Skill` | 把任意技能转换为 BMad 合规、结果导向的等价物，附前后对比 HTML 报告。 |

**流程步骤**

1. **路由并加载流程** — 读取意图（Build / Edit / Analyze）并只加载对应流程文档；Build 与 Edit 共用同一条循环（编辑只是把循环指向既有技能）。
2. **理解来意** — 从开放陈述与对话史中提炼用户真正要完成的事和他们对“好”的定义，只补问缺口。
3. **用真实经验打底并打磨想法** — 索取能带来项目独有知识的来源（runbook、内部文档、事故记录、评审意见、手工做过一次的记录）；对半成型想法主动施压（一个还是三个技能、真实输入是什么、哪里会失败）。
4. **提出隐含模式并持续记忆** — 提出想法隐含但未说出的模式与兄弟意图；决策与方向持续通过 memlog.py 写入 {target-skill-path}/.memlog.md，作为续跑与交接审计的凭据。
5. **先脚手架最小版本** — 用 init_skill.py 规范化命名并生成 SKILL.md 模板；默认把整个 workflow 内联写进 SKILL.md（按相关性测试与 BMad 切分约定才外移），只写最小可用版本。
6. **真实输入试跑与 eval 节点** — 在用户真实、混乱的输入上跑最小版本并读 transcript（试多种方案=指令太模糊、照搬不适用指令=太宽、在选项间卡住=没给默认值）；baseline 与 trigger 模式的 eval-runner 为可选项，evals_required 设置后成为发布门槛。
7. **有证据才加结构** — 不做拍脑袋的脚手架——只有当两版本对比暴露了可命名的问题时才加结构，先自问更锐利的结果陈述能否替代。
8. **脚本机会与定制化决策** — 全程用确定性测试与信号动词扫描挖掘脚本机会（pre-pass JSON 模式）；按 customize-toml-guide 询问一次是否暴露 customize.toml（默认否）。
9. **接线通用形态、剥离仪式并发布** — 接线通用形态（工作状态策略、下游消费的 distillation、按需投影、评审门）；跑自身精简扫描器与 token 预算门、组织标准门；lint 三件套通过后交接并走 memlog 审计。
10. **分析流程（AW）** `可跳过` — 确定性 pre-pass（4 个脚本并行）→ 并行 5 lens（leanness/architecture/determinism/customization/enhancement）→ 应用组织门 → 自行合成 findings.json → 渲染并打开报告（不手改 HTML）。

> 备注：CW（convert-process）的 help CSV 注册（args 含 --convert，输出为 converted skill + 前后对比报告）在本地技能副本中找不到实现：SKILL.md Intents 表只有 Build / Edit / Analyze 三条，references/ 无 convert 文档，故未提取 CW 的 steps，此 CW 信息仅来自基线目录。定制化配置键为 [workflow]（customize.toml），这是将其归类为 workflow 型技能的依据。BW 与 AW 在 help CSV 中互为先后关系。

#### `bmad-eval-runner`

*工具 ｜ 本机已装*

运行某个技能的 evals 并如实汇报结果，用于评测技能、跑基准、校验触发词、优化描述或评审输出质量；所有运行时差异藏在 platform adapter 之后，不硬编码模型名。

- **阶段**：—
- **门禁**：可选
- **入口**：直接调用并传技能路径与参数（位置参数为技能目录；--evals / --mode / --variant-path / --project-root / --output-dir / --runs / --headless）；基线 help CSV 中未注册任何菜单项。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-eval-runner`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **激活与配置解析** — 按 bmad-workflow-builder 的方式解析配置（config.yaml / config.user.yaml，回退 bmb/config.yaml）；headless 时跳过所有确认取最安全默认；glob 输出目录检查未完成 run 的 .memlog.md 以续跑。
2. **定位技能与 adapter** — 校验 <skill-path>/SKILL.md 存在（否则明确报错终止）；按 --adapter → BMAD_EVAL_ADAPTER → adapter.json → 内置 claude-code 适配的顺序解析 adapter。
3. **发现 cases 文件** — 依次在 --evals、技能 evals/、上层 evals/<skill-name>/、项目 evals/ 中查找，取首个命中；找不到即终止——runner 不发明 case。
4. **执行评测** — 按模式调用脚本：baseline / variant / quality 用 run_evals.py（每个 case 在干净工作目录隔离运行，立即落盘 timing.json），trigger 用 run_triggers.py 测量真实触发命中。
5. **质量评分** — quality 模式按 case 另起 grader 子代理按 rubric 评分（不给部分分，标注无区分度的断言）；子代理出错时标记 grading_error 而非默认通过。
6. **多次运行的聚合** `可跳过` — --runs > 1 时用 aggregate_benchmark.py 产出均值、样本标准差、极值与配置间差值。
7. **产物与汇报** — 每个 run 写带日期的永久产物目录（prompt、transcript、cwd/、timing.json、grading.json）并记录 memlog；告知用户 run 目录位置，绝不删除或覆盖历史 run。

> 备注：基线 help CSV 中本条 helpEntries 为空（无菜单码、phase、依赖等信息），但技能实体本地完整（SKILL.md + scripts + references + adapter 资产）。技能内部实际有四种模式：baseline（能否胜过裸模型）、variant（某段落是否值得保留）、quality（输出是否满足 rubric）、trigger（描述是否命中正确查询），由 --mode 选择、可多选。失败或结果偏弱时可走 references/self-improvement.md 与 references/description-optimization.md。


## Test Architecture Enterprise

共 10 个技能。测试架构企业版：风险驱动测试设计到追溯门禁的完整流水线

### 阶段与依赖编排

| 阶段 | 技能 |
| --- | --- |
| 0-learning | TMT `bmad-teach-me-testing`（Teach Me Testing） |
| 3-solutioning | CI `bmad-testarch-ci`（CI Setup）<br>TF `bmad-testarch-framework`（Test Framework）<br>TD `bmad-testarch-test-design`（Test Design） |
| 4-implementation | AT `bmad-testarch-atdd`（ATDD）<br>TA `bmad-testarch-automate`（Test Automation）<br>NR `bmad-testarch-nfr`（NFR Evidence Audit）<br>RV `bmad-testarch-test-review`（Test Review）<br>TR `bmad-testarch-trace`（Traceability） |
| 未标阶段 | `bmad-tea`（Murat — Master Test Architect and Quality Advisor） |

#### `bmad-teach-me-testing` — Teach Me Testing

*工作流 ｜ 本机已装*

TEA Academy：7 节课的渐进式测试教学，覆盖 QA 新人、开发者、Tech Lead、VP 四类角色，30-90 分钟一节课，可 1-2 周自定进度、随时暂停续学。每节课流程为「按需载入 TEA 文档 → 讲授 → 知识测验 → 生成课堂笔记 → 更新进度文件 → 回到课次菜单」。

- **阶段**：0-learning
- **门禁**：可选
- **入口**：以技能名直接调用（Claude Code/Cursor/Windsurf 用 /bmad-teach-me-testing，Codex 用 $bmad-teach-me-testing），或在 bmad-tea 菜单选 TMT。进度文件 {test_artifacts}/teaching-progress/{name}-tea-progress.yaml，课堂笔记与结业总结写在 {test_artifacts}/tea-academy/{name}/ 下。创建模式入口 steps-c/step-01-init.md，续学入口 steps-c/step-01b-continue.md。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：test_artifacts
- **产出物**：progress file<br>session notes<br>completion summary
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-teach-me-testing`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 开始学习 | `Create` | 开始新的学习会话，或从已有进度续学 |
| `V` | 校验 | `Validate` | 审查教学流程质量并生成校验报告 |
| `E` | 编辑 | `Edit` | 修改教学内容或结构 |
| `01` | 快速上手 | `Quick Start` | 30 分钟：TEA Lite 入门，实跑一遍 automate 工作流，理解参与模式 |
| `02` | 核心概念 | `Core Concepts` | 45 分钟：风险驱动测试、DoD、把测试当作工程的理念 |
| `03` | 架构与模式 | `Architecture & Patterns` | 60 分钟：fixture、网络先行模式、数据工厂、step-file 架构 |
| `04` | 测试设计 | `Test Design` | 60 分钟：风险评估与可测性评估、覆盖率规划 |
| `05` | ATDD 与自动化 | `ATDD & Automate` | 60 分钟：ATDD 红相位、Automate 工作流、组件 TDD、API 测试 |
| `06` | 质量与追溯 | `Quality & Trace` | 45 分钟：测试评审与 Trace 工作流、质量指标 |
| `07` | 进阶模式 | `Advanced Patterns` | 时长不限：按菜单探索 59 个知识片段 |

**流程步骤**

1. **Step 1：初始化 / 续学检测** — 新建进度文件，或检测已有进度并恢复；同时校验 {test_artifacts} 可写
2. **Step 2：学员评估** — 按角色（QA/Dev/Lead/VP）与经验等级（beginner/intermediate/experienced）确定学习路径
3. **Step 3：课次菜单** — 展示 7 节课，允许按经验跳课；课程先修关系由 curriculum.yaml 定义（第 3-6 节均需先完成第 2 节）
4. **Step 4：逐节授课（7 节课）** — 每节：按需载入 TEA 文档 → 讲授内容 → 交互式测验（≥70 分及格，每题最多 3 次机会）→ 生成笔记 → 更新进度 → 返回菜单
5. **Step 5：结业总结** — 7 节全部完成才生成 completion summary（含完成日期、得分、技能清单、产物路径与后续建议）

> 备注：TEA 中 phase 0-learning 的唯一技能，与 testarch 流水线无前后依赖，属于并行可选轨道。跳课会失去结业资格：curriculum.yaml 规定 completion.minimum_sessions=7，选择了 intermediate/experienced 路径的 skip_optional 即 forfeited 结业总结。工作流为 tri-modal（steps-c/steps-e/steps-v）。课程内容映射到 tea-resources-index.yaml 与 session-content-map.yaml。

#### `bmad-testarch-ci` — CI Setup

*工作流 ｜ 本机已装*

搭建 CI/CD 质量流水线：接入测试执行、burn-in 重复跑批与产物收集，并配置质量门禁与通知。支持 5 个平台（GitHub Actions / GitLab CI / Jenkins / Azure DevOps / Harness）。

- **阶段**：3-solutioning
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-testarch-ci），或经 bmad-tea 菜单码 CI。创建模式入口 steps-c/step-01-preflight.md；工作流内可选 Create/Resume/Validate/Edit 四模式。
- **参数**：`—`
- **前置**：bmad-testarch-framework
- **后续**：—
- **产出位置**：test_artifacts
- **产出物**：ci config
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-testarch-ci`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 创建 | `Create` | 从头执行工作流 |
| `R` | 恢复 | `Resume` | 恢复被中断的创建运行 |
| `V` | 校验 | `Validate` | 依据 checklist.md 校验已有产物 |
| `E` | 编辑 | `Edit` | 修改已有产物 |

**流程步骤**

1. **Step 1：预检** — 探测现有 CI 配置、Node/包管理器版本、测试栈与框架，解析平台（ci_platform 默认 auto）
2. **Step 2：生成流水线** — 按平台模板生成流水线文件并接入测试执行与 burn-in 循环
3. **Step 3：质量门禁与通知** — 配置 gate 判定、产物收集与通知
4. **Step 4：校验与总结** — 跑 checklist 校验并输出总结

> 备注：workflow.yaml 的 default_output_file 为 {project-root}/.github/workflows/test.yml（GitHub Actions 为默认，其余平台覆盖）——产物落在仓库而非 test_artifacts，与基线 outputLocation 口径不一致。技能自带 5 个平台模板：github-actions-template.yaml、gitlab-ci-template.yaml、jenkins-pipeline-template.groovy、azure-pipelines-template.yaml、harness-pipeline-template.yaml。执行提示为 interactive:false + autonomous:true + iterative:true（尽量自动检测、不阻塞提问）。

#### `bmad-testarch-framework` — Test Framework

*工作流 ｜ 本机已装*

初始化生产级测试框架架构（Playwright 或 Cypress），含 fixture、helpers、配置与运行脚本。支持 auto 检测项目规模与框架偏好，默认偏好 TypeScript。

- **阶段**：3-solutioning
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-testarch-framework），或经 bmad-tea 菜单码 TF。创建模式入口 steps-c/step-01-preflight.md；工作流内可选 Create/Resume/Validate/Edit 四模式。
- **参数**：`—`
- **前置**：bmad-testarch-test-design
- **后续**：bmad-testarch-ci
- **产出位置**：test_artifacts
- **产出物**：framework scaffold
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-testarch-framework`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 创建 | `Create` | 从头执行工作流 |
| `R` | 恢复 | `Resume` | 恢复被中断的创建运行 |
| `V` | 校验 | `Validate` | 依据 checklist.md 校验已有产物 |
| `E` | 编辑 | `Edit` | 修改已有产物 |

**流程步骤**

1. **Step 1：预检** — 检查现有框架、package.json、目录与依赖，判定是否可初始化
2. **Step 2：框架选择** — 按项目规模与偏好选 Playwright 或 Cypress（framework_preference 默认 auto）
3. **Step 3：搭建框架骨架** — 生成配置、fixtures、helpers 与目录结构
4. **Step 4：文档与脚本** — 写测试目录 README 与运行脚本
5. **Step 5：校验与总结** — 跑 checklist 校验并输出总结

> 备注：workflow.yaml 的 default_output_file 为 {test_dir}/README.md，即 {project-root}/tests/README.md，落在项目源码树而非 test_artifacts——基线 outputLocation 与工作流自述口径不一致。技能自带 resources/hooks/tea-enforce.cjs（可挂 CI 强制钩子）与 framework-setup-progress.example.md。

#### `bmad-testarch-test-design` — Test Design

*工作流 ｜ 本机已装*

风险驱动测试设计。自动判定模式：系统级（有 PRD+ADR、尚无 epic）做架构可测性评审，产出给架构/QA 团队的三份文档；epic 级（有 epic+stories）做单个 epic 的测试计划。含风险评估、优先级分类与执行顺序。

- **阶段**：3-solutioning
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-testarch-test-design），或经 bmad-tea 菜单码 TD。创建模式入口 steps-c/step-01-detect-mode.md；工作流内可选 Create/Resume/Validate/Edit 四模式。
- **参数**：`—`
- **前置**：—
- **后续**：bmad-testarch-framework
- **产出位置**：test_artifacts
- **产出物**：test design document
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-testarch-test-design`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 创建 | `Create` | 从头执行工作流 |
| `R` | 恢复 | `Resume` | 恢复被中断的创建运行，读出进度元数据后路由到下一个未完成步骤 |
| `V` | 校验 | `Validate` | 依据 checklist.md 校验已有产物 |
| `E` | 编辑 | `Edit` | 修改已有产物 |

**流程步骤**

1. **Step 1：模式与前置检测** — 判定系统级 / epic 级（用户意图优先：有 PRD+ADR 无 epic 走系统级，有 epic+stories 走 epic 级，两者都有优先系统级），并解析 run_key 命名进度检查点
2. **Step 2：载入上下文与知识库** — 读取 PRD/ADR/epic、项目上下文，并按 tea-index.csv 拉取所需知识片段
3. **Step 3：可测性与风险评估** — 评估架构可测性缺口，识别测试阻塞项与风险等级
4. **Step 4：覆盖率计划与执行策略** — 按风险定覆盖层级与执行顺序，含 Not in Scope 排除项及其缓解说明
5. **Step 5：生成产物并校验** — 按模式写系统级三份文档或 epic 级一份文档，并跑 checklist 校验

> 备注：基线只登记 3-solutioning，但工作流是双模式：系统级（Phase 3）产出 test-design-architecture.md（给架构）+ test-design-qa.md（给 QA）+ {project_name}-handoff.md（TEA→BMAD 交接）三份；epic 级（Phase 4）产出 test-design-epic-{n}.md 一份。刻意无 default_output_file，输出由模式决定。进度检查点按 run_key（system 或 epic-{num}）隔离，多 epic 并行或中断后不会互相覆盖；Resume 模式会拒绝续接属于另一个 run 的检查点。

#### `bmad-testarch-atdd` — ATDD

*工作流 ｜ 本机已装*

在实现之前生成红相位（失败态）验收测试脚手架，走 TDD 红-绿-重构循环。产出实现清单与可运行的失败测试，供随后 dev-story 逐个转绿。是 TEA 流水线里唯一横跨 BMad Method 模块的技能（前置 create-story、后接 dev-story）。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-testarch-atdd），或经 bmad-tea 菜单码 AT。创建模式入口 steps-c/step-01-preflight-and-context.md；工作流内可选 Create/Resume/Validate/Edit 四模式。
- **参数**：`—`
- **前置**：bmad-create-story:create
- **后续**：bmad-dev-story
- **产出位置**：test_artifacts
- **产出物**：atdd-checklist<br>red-phase acceptance tests
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-testarch-atdd`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 创建 | `Create` | 从头执行工作流 |
| `R` | 恢复 | `Resume` | 恢复被中断的创建运行 |
| `V` | 校验 | `Validate` | 依据 checklist.md 校验已有产物 |
| `E` | 编辑 | `Edit` | 修改已有产物 |

**流程步骤**

1. **Step 1：预检与上下文载入** — 读 story、框架配置，检查现存 fixture 与相似测试模式
2. **Step 2：生成模式选择** — 确定生成策略与范围（API / E2E / 两者）
3. **Step 3：测试策略** — 按 story 验收标准划定测试策略与断言层级
4. **Step 4：编排自适应红相位脚手架生成** — 并行子代理：4A 生成 API 失败测试、4B 生成 E2E 失败测试，4C 聚合结果；由 step-04 编排并控制执行模式
5. **Step 5：校验与完成** — 校验测试确实处于红相位、产出 atdd-checklist-{story_key}.md 并收尾

> 备注：TEA 唯一跨模块依赖链：precededBy=bmad-create-story:create（bmm 模块）、followedBy=bmad-dev-story（bmm 模块），说明 ATDD 被设计为嵌在 BMad Method 的 story 循环里跑，而非独立跑。default_output_file = {test_artifacts}/atdd-checklist-{story_key}.md，模板为 atdd-checklist-template.md。execution_hints.interactive=false，倾向少打断。

#### `bmad-testarch-automate` — Test Automation

*工作流 ｜ 本机已装*

实现之后扩充测试自动化覆盖：在存量代码库上识别目标、生成分层测试（API / 后端 / E2E / 移动端）、补齐 fixture 与数据工厂，最后出 DoD 摘要。既可在 BMad 流程内跑，也可在无 BMad 产物的纯代码库上独立跑。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-testarch-automate），或经 bmad-tea 菜单码 TA。创建模式入口 steps-c/step-01-preflight-and-context.md；工作流内可选 Create/Resume/Validate/Edit 四模式。
- **参数**：`—`
- **前置**：bmad-testarch-atdd
- **后续**：—
- **产出位置**：test_artifacts
- **产出物**：test suite
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-testarch-automate`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 创建 | `Create` | 从头执行工作流 |
| `R` | 恢复 | `Resume` | 恢复被中断的创建运行 |
| `V` | 校验 | `Validate` | 依据 checklist.md 校验已有产物 |
| `E` | 编辑 | `Edit` | 修改已有产物 |

**流程步骤**

1. **Step 1：预检与上下文载入** — 读源码、既有测试与 BMad 产物，确认覆盖目标（coverage_target 默认 critical-paths）
2. **Step 2：识别自动化目标** — 定位未覆盖的关键路径与缺口优先级
3. **Step 3：编排自适应测试生成** — 按栈派发子代理：3A API 测试、3B 后端测试、3B E2E 测试、3B 移动端测试，3C 聚合结果
4. **Step 4：校验与总结** — 校验测试可运行，产出 automation-summary.md

> 备注：workflow.yaml 声明 standalone_mode: true，可在无 BMad 产物的存量代码库上单独运行（这是 TEA 各技能里唯一显式声明独立运行的）。TA 是分叉点：测试评审（RV）与 NFR 证据审计（NR）都以它为前置。default_output_file = {test_artifacts}/automation-summary.md。

#### `bmad-testarch-nfr` — NFR Evidence Audit

*工作流 ｜ 本机已装*

审计已实现的非功能需求证据：先定义类别与阈值，再收集证据，然后按安全、性能、可靠性、可维护性四个方向做证据审计，最后出 NFR 报告与行动建议。触发前提是实现证据已存在。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-testarch-nfr），或经 bmad-tea 菜单码 NR（也可经 GATE 路由项）。创建模式入口 steps-c/step-01-load-context.md；工作流内可选 Create/Resume/Validate/Edit 四模式。
- **参数**：`—`
- **前置**：bmad-testarch-automate
- **后续**：—
- **产出位置**：test_artifacts
- **产出物**：nfr report
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-testarch-nfr`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 创建 | `Create` | 从头执行工作流 |
| `R` | 恢复 | `Resume` | 恢复被中断的创建运行 |
| `V` | 校验 | `Validate` | 依据 checklist.md 校验已有产物 |
| `E` | 编辑 | `Edit` | 修改已有产物 |

**流程步骤**

1. **Step 1：载入上下文与知识库** — 读 story、测试结果、指标与日志，载入知识片段并确认证据可得性
2. **Step 2：定义 NFR 类别与阈值** — 确定标准四类（安全/性能/可靠性/可维护性）的阈值，可加自定义类别（custom_nfr_categories）
3. **Step 3：收集证据** — 按阈值要求定位测试结果、监控指标与日志作为证据
4. **Step 4：编排自适应 NFR 证据审计** — 并行子代理：4A 安全、4B 性能、4C 可靠性、4D 可维护性，4E 聚合结果
5. **Step 5：生成报告与校验** — 按 nfr-report-template.md 写报告并校验

> 备注：触发前提写在 description 里：实现证据已存在时才运行（「Audit NFR evidence ... Use when implementation evidence exists」）。default_output_file = {test_artifacts}/nfr-assessment.md，模板 nfr-report-template.md，另有 nfr-status-definitions.md 定义状态口径。与 RV 同属 TA 之后的分叉支线，两者可并行，再汇入 TR。

#### `bmad-testarch-test-review` — Test Review

*工作流 ｜ 本机已装*

对已写测试做质量审计：按知识库与最佳实践评估确定性、隔离性、可维护性、性能四个维度，聚合成 0-100 总分，并给出可执行的修复建议（含违规行定位）。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-testarch-test-review），或经 bmad-tea 菜单码 RV（也可经 GATE 路由项）。创建模式入口 steps-c/step-01-load-context.md；交互模式下可选 Create/Resume/Validate/Edit 四模式。
- **参数**：`—`
- **前置**：bmad-testarch-automate
- **后续**：—
- **产出位置**：test_artifacts
- **产出物**：review report
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-testarch-test-review`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 创建 | `Create` | 从头执行工作流 |
| `R` | 恢复 | `Resume` | 恢复被中断的创建运行 |
| `V` | 校验 | `Validate` | 依据 checklist.md 校验已有产物 |
| `E` | 编辑 | `Edit` | 修改已有产物 |

**流程步骤**

1. **Step 1：载入上下文与知识库** — 解析 review 范围（review_scope 或权威的 review_files）、只读 context_files，并载入知识片段
2. **Step 2：发现并解析测试** — 发现测试文件并解析结构；review_files 非空时跳过 glob 发现，以之为完整评审集
3. **Step 3：编排自适应质量评估** — 按执行模式（auto/subagent/agent-team/sequential）跑四维检查：3A 确定性、3B 隔离性、3C 可维护性、3E 性能，3F 聚合为 0-100 总分
4. **Step 4：生成报告与校验** — 写 review report（默认 {test_artifacts}/test-review.md），可选出内联 TODO 注释，并跑 checklist

> 备注：TEA 中唯一支持 headless 非交互运行的工作流（headless=true 时跳过问候与模式菜单，供 tea-test-review CLI 调用），并暴露 review_files / context_files / output_file_override / generate_inline_comments 四个一等输入。质量维度是 4 个（确定性、隔离性、可维护性、性能），不含第 5 个；聚合为 0-100 分。默认 generate_inline_comments=false 即纯报告模式，不改动被测文件。评分规则见 steps-c/criteria-registry.md，分 CRITICAL/HIGH 等门类，并对项目既有惯例做「已确立/新兴/不存在/未知」四种状态的推断后决定是否扣分。checklist.md 与 test-review-template.md 为配套。

#### `bmad-testarch-trace` — Traceability

*工作流 ｜ 本机已装*

两阶段收敛：Phase 1 把覆盖基准（正式需求、契约或合成旅程）映射到测试，生成追溯矩阵并分析覆盖缺口；Phase 2 依据证据出质量门禁判定 PASS / CONCERNS / FAIL / WAIVED。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-testarch-trace），或经 bmad-tea 菜单码 TR（也可经 GATE 路由项）。创建模式入口 steps-c/step-01-load-context.md；工作流内可选 Create/Resume/Validate/Edit 四模式。
- **参数**：`—`
- **前置**：bmad-testarch-test-review
- **后续**：—
- **产出位置**：test_artifacts
- **产出物**：traceability matrix<br>gate decision
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-testarch-trace`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 创建 | `Create` | 从头执行工作流 |
| `R` | 恢复 | `Resume` | 恢复被中断的创建运行 |
| `V` | 校验 | `Validate` | 依据 checklist.md 校验已有产物 |
| `E` | 编辑 | `Edit` | 修改已有产物 |

**流程步骤**

1. **Step 1：解析覆盖基准并载入知识库** — 按序解析 coverage oracle：正式需求 → 契约/规格产物 → 可解析的外部指针 → 从源码推断的合成需求；并持久化 coverage_basis 与 summary_confidence
2. **Step 2：发现并编目测试** — 按 coverage_levels（默认 e2e,api,component,unit,live）发现并编目测试
3. **Step 3：覆盖基准映射到测试** — 建立要求/旅程到测试的映射关系
4. **Step 4：完成 Phase 1 覆盖率矩阵** — 生成追溯矩阵并分析缺口
5. **Step 5：Phase 2 门禁判定** — 按 gate_type（默认 story）与 decision_mode（默认 deterministic 规则判定）出 PASS/CONCERNS/FAIL/WAIVED，写 gate-decision.json

> 备注：基线只登记 stage 为单一 phase 4-implementation，但技能内部明确分两阶段（Phase 1 矩阵、Phase 2 门禁），bmad-tea 的菜单描述也强调这一点。除 default_output_file（{test_artifacts}/traceability-matrix.md）外还产 e2e-trace-summary.json 与 gate-decision.json 供 CI/CD 消费；allow_gate 控制是否输出门禁信号，collection_mode 支持 contract_static/inventory_only/runtime_manifest/deferred_shared/waived/restricted/inaccessible 七种采集模式。checklist.md 与 trace-template.md 为配套。TR 是 TEA 流水线的末端收敛点：precededBy 只有 test-review，但 GATE 路由项描述里 RV 与 NR 都是可选的并行前置。

#### `bmad-tea` — Murat — Master Test Architect and Quality Advisor

*Agent 角色 ｜ 本机已装*

TEA 模块的总入口与人格化测试架构师（Murat）。统管风险驱动测试策略、fixture 架构、ATDD、API/UI 自动化、CI/CD 治理与质量门禁，本身不产出文档，而是把用户路由到 9 条 testarch 工作流与 TMT 教学技能。启动时加载 test_artifacts 与模块配置，并强制持久化人格与图标前缀。

- **阶段**：—
- **门禁**：可选
- **入口**：以技能名直接调用（Claude Code 用 /bmad-tea，Codex 用 $bmad-tea），或说“找 Murat / Test Architect”。激活序列共 8 步：解析 agent 定制块 → 执行 prepend → 采用人格 → 载入持久事实 → 读 {project-root}/_bmad/tea/config.yaml → 问候 → append → 展示菜单或直接派发。菜单项定义在 customize.toml 的 [[agent.menu]]。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-tea`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `TMT` | 测试教学 | `Teach Me Testing` | 7 节渐进式测试课程教学，从基础到进阶 |
| `TD` | 测试设计 | `Test Design` | 风险评估、NFR 规划与覆盖率策略（系统级或 epic 级） |
| `TF` | 测试框架 | `Test Framework` | 初始化生产级测试框架架构 |
| `CI` | CI 流水线 | `Continuous Integration` | 推荐并搭建 CI/CD 质量流水线 |
| `AT` | 验收测试驱动开发 | `ATDD` | 开发前生成失败态验收测试与实现清单 |
| `TA` | 测试自动化 | `Test Automation` | 为 story 或 feature 生成分优先级的 API/E2E 测试、fixture 与 DoD 摘要 |
| `GATE` | 发布门禁（路由项） | `Release Gate` | 先判断现有证据，再推荐正确顺序：可选 test-review 最终质量审计、可选 NFR 证据审计，最后 trace Phase 2 出 PASS/CONCERNS/FAIL/WAIVED 判定。明确要求不合并这三个工作流 |
| `RV` | 测试评审 | `Review Tests` | 按知识库与最佳实践对已写测试做质量检查 |
| `NR` | 非功能需求证据审计 | `NFR Evidence Audit` | 评估已实现的 NFR 证据并给出行动建议 |
| `TR` | 覆盖追溯 | `Trace Coverage` | Phase 1 需求到测试的映射，Phase 2 出质量门禁判定 |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：登记错位（非无实现）：实体完整可用（baseline location=project，skillDir 指向项目级 .claude/skills），仅 skill-manifest.csv 有登记，bmad-help.csv 与 module-help.csv 均无行（inHelpCatalog=false），故 /bmad-help 发现不到该入口。customize.toml 定义 10 项菜单（9 项绑定技能 + 1 项 GATE 为 prompt 型路由）。GATE 不是技能，而是引导用户自行走 RV→NR→TR 的发布门禁路径。另：技能载入 ./resources/tea-index.csv（59 个知识片段索引）按需拉取 resources/knowledge/ 下的片段，并强制校验 Playwright/Cypress/Pact/k6/pytest/JUnit/Go test 与 CI 平台官方文档。


## Creative Intelligence Suite

共 10 个技能。创意智能套件：创新策略、问题求解、设计思维、叙事

### 阶段与依赖编排

| 阶段 | 技能 |
| --- | --- |
| anytime | DT `bmad-cis-design-thinking`（Design Thinking）<br>IS `bmad-cis-innovation-strategy`（Innovation Strategy）<br>PS `bmad-cis-problem-solving`（Problem Solving）<br>ST `bmad-cis-storytelling`（Storytelling） |
| 未标阶段 | `bmad-cis-agent-brainstorming-coach`（Carson — Elite Brainstorming Specialist）<br>`bmad-cis-agent-creative-problem-solver`（Dr. Quinn — Master Problem Solver）<br>`bmad-cis-agent-design-thinking-coach`（Maya — Design Thinking Maestro）<br>`bmad-cis-agent-innovation-strategist`（Victor — Disruptive Innovation Oracle）<br>`bmad-cis-agent-presentation-master`（Caravaggio — Visual Communication + Presentation Expert）<br>`bmad-cis-agent-storyteller`（Sophia — Master Storyteller） |

#### `bmad-cis-design-thinking` — Design Thinking

*工作流 ｜ 本机已装*

以共情驱动的设计思维流程引导人本设计：从 EMPATHIZE 建立用户理解，到 DEFINE 框定问题、IDEATE 发散方案、PROTOTYPE 做可感知原型、TEST 用户验证，最后规划下一轮迭代。全程把用户放在中心，发散阶段不做评判。

- **阶段**：anytime
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-cis-design-thinking），或经 bmad-cis-agent-design-thinking-coach（Maya）菜单码 DT。工作流为 SKILL.md 内联的 7 步 <workflow>，无独立 steps 目录。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：output_folder
- **产出物**：design thinking
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-design-thinking`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `a` | 高级引导 | `Advanced Elicitation` | 检查点选项；文档只给出选项名，未在本文件内定义语义（名称与 core 模块的 bmad-advanced-elicitation 一致） |
| `c` | 继续 | `Continue` | 保存当前产物并进入下一步（文档内唯一明确定义的选项） |
| `p` | 多方模式 | `Party-Mode` | 检查点选项；文档只给出选项名，未在本文件内定义语义（名称与 core 模块的 bmad-party-mode 一致） |
| `y` | YOLO | `YOLO` | 检查点选项；文档只给出选项名 [y] YOLO，未在本文件内定义语义 |

**流程步骤**

1. **Step 1：收集背景并定义设计挑战** — 明确要解决的设计挑战、目标用户与约束
2. **Step 2：EMPATHIZE 建立用户理解** — 用共情阶段方法（用户访谈、共情地图、影子观察、旅程地图、日记研究）理解真实用户
3. **Step 3：DEFINE 框定问题** — 用定义阶段方法（问题框定、How Might We、观点陈述）把洞察收敛成清晰问题
4. **Step 4：IDEATE 生成多样方案** — 发散阶段不做评判，产出多样化解法
5. **Step 5：PROTOTYPE 让想法可感知** — 快速做出低成本原型
6. **Step 6：TEST 用户验证** — 用用户测试验证原型假设，收集反馈
7. **Step 7：规划下一轮迭代** — 综合验证结果决定迭代方向

> 备注：方法库 design-methods.csv 共 30 个方法，按阶段均分 6 类各 5 个（empathize / define / ideate / prototype / test / implement）；注意方法库有 6 个阶段而工作流只走 7 步覆盖前 5 个阶段 + 迭代规划，implement 阶段的方法未被流程显式使用。路径：default_output_file={output_folder}/design-thinking-{date}.md。与 bmad-cis-agent-design-thinking-coach（Maya）直接对应。

#### `bmad-cis-innovation-strategy` — Innovation Strategy

*工作流 ｜ 本机已装*

通过严谨的市场分析、选项生成与执行规划，识别颠覆机会并设计商业模式创新。先逼出市场真相、再拆解现有商业模式、寻找颠覆向量，最后给出 3 个战略选项与推荐路线图。属于随时可用的创意/战略引导，不绑定开发阶段。

- **阶段**：anytime
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-cis-innovation-strategy），或经 bmad-cis-agent-innovation-strategist（Victor）菜单码 IS。工作流为 SKILL.md 内联的 9 步 <workflow>，无独立 steps 目录。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：output_folder
- **产出物**：innovation strategy
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-innovation-strategy`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `a` | 高级引导 | `Advanced Elicitation` | 检查点选项；文档只给出选项名，未在本文件内定义语义（名称与 core 模块的 bmad-advanced-elicitation 一致） |
| `c` | 继续 | `Continue` | 保存当前产物并进入下一步（文档内唯一明确定义的选项） |
| `p` | 多方模式 | `Party-Mode` | 检查点选项；文档只给出选项名，未在本文件内定义语义（名称与 core 模块的 bmad-party-mode 一致） |
| `y` | YOLO | `YOLO` | 检查点选项；文档只给出选项名 [y] YOLO，未在本文件内定义语义 |

**流程步骤**

1. **Step 1：建立战略背景** — 问清公司/业务、驱动因素、现有商业模式、约束边界与突破性成功的定义
2. **Step 2：市场格局与竞争动态分析** — 从市场分析类框架（TAM SAM SOM、五力、竞争定位图、市场时机）中选 2-4 个执行
3. **Step 3：拆解现有商业模式** — 从商业模式类框架（商业模式画布、价值主张画布、收入/成本结构创新）中选 2-3 个，识别模型弱点
4. **Step 4：识别颠覆机会** — 从颠覆类框架（颠覆式创新、JTBD、蓝海、平台革命）中选 2-3 个，寻找非消费者与未满足任务
5. **Step 5：生成创新机会** — 从战略/价值链类框架中选 2-4 个，产出 5-10 项具体创新机会（商业模式、价值链、伙伴生态、技术驱动）
6. **Step 6：形成并评估战略选项** — 合成 3 个不同战略方向，逐一评估契合度、市场时机、防御性、资源可行性与风险回报
7. **Step 7：推荐战略方向** — 给出大胆推荐及理由，列出必须先验证的关键假设与关键成功要素
8. **Step 8：构建执行路线图** — 分三阶段（立即见效 / 打基础 / 规模化）排出举措、资源、指标与决策门
9. **Step 9：定义指标与风险缓解** — 区分领先/滞后指标，设决策门，识别致命风险与备份方案

> 备注：CIS 四个工作流结构一致：SKILL.md 内联 <workflow>（无 steps-c/e/v 目录、无 instructions.md/checklist.md），配 template.md 与方法库 CSV。本技能方法库 innovation-frameworks.csv 共 30 个框架，6 类各 5 个（market_analysis / business_model / disruption / strategic / value_chain / technology）。路径：template_file=./template.md、innovation_frameworks_file=./innovation-frameworks.csv、default_output_file={output_folder}/innovation-strategy-{date}.md。硬性行为约束：不得给时间估算；每次 <template-output> 后立即落盘并在检查点暂停等用户响应。含 energy-checkpoint 环节（第 3、5、8 步）。

#### `bmad-cis-problem-solving` — Problem Solving

*工作流 ｜ 本机已装*

系统化地诊断复杂问题：先把模糊抱怨精炼成精确问题陈述，再做边界诊断与根因分析，然后生成并评估方案，最后产出可落地的实施与验证计划。强调先诊断后开方，不做时间估算。

- **阶段**：anytime
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-cis-problem-solving），或经 bmad-cis-agent-creative-problem-solver（Dr. Quinn）菜单码 PS。工作流为 SKILL.md 内联的 9 步 <workflow>，无独立 steps 目录。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：output_folder
- **产出物**：problem solution
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-problem-solving`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `a` | 高级引导 | `Advanced Elicitation` | 检查点选项；文档只给出选项名，未在本文件内定义语义（名称与 core 模块的 bmad-advanced-elicitation 一致） |
| `c` | 继续 | `Continue` | 保存当前产物并进入下一步（文档内唯一明确定义的选项） |
| `p` | 多方模式 | `Party-Mode` | 检查点选项；文档只给出选项名，未在本文件内定义语义（名称与 core 模块的 bmad-party-mode 一致） |
| `y` | YOLO | `YOLO` | 检查点选项；文档只给出选项名 [y] YOLO，未在本文件内定义语义 |

**流程步骤**

1. **Step 1：定义并精炼问题** — 用 Problem Statement Refinement 把模糊抱怨转成精确陈述，明确现状与目标的差距
2. **Step 2：诊断并界定问题边界** — 用 Is/Is Not Analysis 划定发生/不发生的人、时、地、事，找出模式
3. **Step 3：根因分析** — 从诊断类方法（五个为什么、鱼骨图、系统思考）中选 2-3 个下钻到根因与系统动力
4. **Step 4：分析驱动力与约束** — 用力场分析列出推动/阻碍因素，识别真正的主约束（区分真实与假想）
5. **Step 5：生成方案选项** — 从综合类与创意类方法（TRIZ、形态分析、仿生、横向思维、假设打破、逆向头脑风暴）中选 2-4 个，产出至少 10-15 个方案含「野」点子
6. **Step 6：评估并选定方案** — 共同定义评估标准，从评估类方法（决策矩阵、成本效益、风险矩阵）中选 1-2 个执行并给出推荐及理由
7. **Step 7：规划实施** — 确定实施策略（试点/分阶段/一次性），排出动作、顺序、依赖、责任人与资源，用 PDCA 迭代
8. **Step 8：建立监控与验证** — 设成功指标与阈值、验证方式与试点，识别实施风险与触发调整/转向的条件
9. **Step 9：沉淀经验教训** `可跳过` — 回顾过程：哪些有效、哪些要改、有什么意外洞察

> 备注：唯一带明确 optional 步骤的 CIS 工作流：Step 9（经验教训）标记 optional=true，且文档说明若不跑 Step 9，Step 8 结束时就执行 workflow.on_complete 终结指令。方法库 solving-methods.csv 共 30 个方法，6 类各 5 个（diagnosis / analysis / synthesis / evaluation / implementation / creative）。路径：default_output_file={output_folder}/problem-solution-{date}.md。含 energy-checkpoint（第 5、8 步），硬性不得给时间估算。

#### `bmad-cis-storytelling` — Storytelling

*工作流 ｜ 本机已装*

用成熟叙事框架把想法变成有感染力的故事：先选故事框架，再收集素材、设计情绪弧、打磨开场钩子、写正文，然后做多渠道变体与使用指引，最后生成终稿。强调保留用户真实声音。

- **阶段**：anytime
- **门禁**：可选
- **入口**：以技能名直接调用（/bmad-cis-storytelling），或经 bmad-cis-agent-storyteller（Sophia）菜单码 ST。工作流为 SKILL.md 内联的 10 步 <workflow>，无独立 steps 目录。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：output_folder
- **产出物**：narrative/story
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-storytelling`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `a` | 高级引导 | `Advanced Elicitation` | 检查点选项；文档只给出选项名，未在本文件内定义语义（名称与 core 模块的 bmad-advanced-elicitation 一致） |
| `c` | 继续 | `Continue` | 保存当前产物并进入下一步（文档内唯一明确定义的选项） |
| `p` | 多方模式 | `Party-Mode` | 检查点选项；文档只给出选项名，未在本文件内定义语义（名称与 core 模块的 bmad-party-mode 一致） |
| `y` | YOLO | `YOLO` | 检查点选项；文档只给出选项名 [y] YOLO，未在本文件内定义语义 |

**流程步骤**

1. **Step 1：故事背景设定** — 明确受众、目的、渠道与期望效果
2. **Step 2：选择故事框架** — 从 story-types.csv 的 25 种故事类型中挑选合适框架
3. **Step 3：收集故事素材** — 围绕所选框架收集人物、冲突、转折与细节素材
4. **Step 4：设计情绪弧** — 规划情绪起伏曲线
5. **Step 5：打磨开场钩子** — 设计能立刻抓住注意力的开头
6. **Step 6：撰写核心叙事** — 按框架与情绪弧写出主体故事
7. **Step 7：生成故事变体** — 按不同渠道/时长改写版本
8. **Step 8：使用指引** — 给出讲/用这个故事的建议
9. **Step 9：精修与下一步** — 按反馈精修
10. **Step 10：生成最终产出** — 写终稿到 {output_folder}/story-{date}.md 并确认完成

> 备注：故事框架库 story-types.csv 共 25 条，5 类各 5 个（transformation / strategic / persuasive / analytical / emotional），每类含 5 个具体类型（如 hero-journey、pixar-spine、customer-journey、data-story、vulnerable-story 等）。路径：default_output_file={output_folder}/story-{date}.md。与 bmad-cis-agent-storyteller（Sophia）直接对应。

#### `bmad-cis-agent-brainstorming-coach` — Carson — Elite Brainstorming Specialist

*Agent 角色 ｜ 本机已装*

头脑风暴引导专家 Carson，用创造性技术与系统化创新方法主持高产出创意会，营造「野想法安全落地、优中选优」的氛围。本身是人格化入口，实际执行时调用 core 模块的 bmad-brainstorming 技能。

- **阶段**：—
- **门禁**：可选
- **入口**：说「找 Carson / Brainstorming Specialist」或按技能名直接调用激活。激活序列 8 步：解析 agent 定制块 → prepend → 采用人格 → 载入持久事实 → 读 {project-root}/_bmad/cis/config.yaml → 问候（带图标前缀）→ append → 展示菜单。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-agent-brainstorming-coach`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `BS` | 引导式头脑风暴 | `Facilitate a guided brainstorming session on any topic` | 调用 bmad-brainstorming 技能，用一种或多种技术主持头脑风暴 |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：登记错位（非无实现）：实体完整可用（baseline location=project，skillDir 指向项目级 .claude/skills），仅 skill-manifest.csv 有登记，bmad-help.csv 与 module-help.csv 均无行（inHelpCatalog=false），故 /bmad-help 发现不到该入口。其菜单指向的 bmad-brainstorming 在 skill-manifest 中归属 core 模块，却在 cis module-help.csv 里以菜单码 BS 登记，形成「入口登记模块 ≠ 技能归属模块」的跨模块错位（该技能在 bmad-help.csv 中共有 3 条登记：BMad Method/BP、Core/BSP、CIS/BS）。

#### `bmad-cis-agent-creative-problem-solver` — Dr. Quinn — Master Problem Solver

*Agent 角色 ｜ 本机已装*

系统化问题求解专家 Dr. Quinn，用 TRIZ、约束理论、系统思考等方法解剖复杂难题，把根因逼出水面。人格化入口，实际执行时路由到 bmad-cis-problem-solving 工作流。

- **阶段**：—
- **门禁**：可选
- **入口**：说「找 Dr. Quinn / Master Problem Solver」或按技能名直接调用激活；激活后从菜单选 PS 触发工作流。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-agent-creative-problem-solver`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `PS` | 系统化问题求解 | `Apply systematic problem-solving methodologies to a hard challenge` | 调用 bmad-cis-problem-solving 工作流，对复杂挑战做结构化求解 |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：登记错位（非无实现）：实体完整可用（baseline location=project，skillDir 指向项目级 .claude/skills），仅 skill-manifest.csv 有登记，bmad-help.csv 与 module-help.csv 均无行（inHelpCatalog=false），故 /bmad-help 发现不到该入口。其路由目标 bmad-cis-problem-solving 本身已登记（PS，anytime）。人物设定参考 Genrich Altshuller 的 TRIZ 与 Donella Meadows 的系统思考。

#### `bmad-cis-agent-design-thinking-coach` — Maya — Design Thinking Maestro

*Agent 角色 ｜ 本机已装*

设计思维引导师 Maya，用共情驱动方法带团队走完人本设计流程，把真实用户需求转化为经验证的方案。人格化入口，实际执行时路由到 bmad-cis-design-thinking 工作流。

- **阶段**：—
- **门禁**：可选
- **入口**：说「找 Maya / Design Thinking Maestro」或按技能名直接调用激活；激活后从菜单选 DT 触发工作流。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-agent-design-thinking-coach`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `DT` | 端到端设计思维引导 | `Guide a human-centered design process end-to-end` | 调用 bmad-cis-design-thinking 工作流，走完共情到验证的完整流程 |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：登记错位（非无实现）：实体完整可用（baseline location=project，skillDir 指向项目级 .claude/skills），仅 skill-manifest.csv 有登记，bmad-help.csv 与 module-help.csv 均无行（inHelpCatalog=false），故 /bmad-help 发现不到该入口。其路由目标 bmad-cis-design-thinking 本身已登记（DT，anytime）。人物设定参考 Tim Brown（IDEO）与 Don Norman 的人本设计方法。

#### `bmad-cis-agent-innovation-strategist` — Victor — Disruptive Innovation Oracle

*Agent 角色 ｜ 本机已装*

颠覆式创新战略家 Victor，识别颠覆机会并设计商业模式创新，让战略转向落到真正有价值的位置。人格化入口，实际执行时路由到 bmad-cis-innovation-strategy 工作流。

- **阶段**：—
- **门禁**：可选
- **入口**：说「找 Victor / Disruptive Innovation Oracle」或按技能名直接调用激活；激活后从菜单选 IS 触发工作流。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-agent-innovation-strategist`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `IS` | 创新策略 | `Identify disruption opportunities and architect business-model innovation` | 调用 bmad-cis-innovation-strategy 工作流，寻找颠覆机会并设计商业模式创新 |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：登记错位（非无实现）：实体完整可用（baseline location=project，skillDir 指向项目级 .claude/skills），仅 skill-manifest.csv 有登记，bmad-help.csv 与 module-help.csv 均无行（inHelpCatalog=false），故 /bmad-help 发现不到该入口。其路由目标 bmad-cis-innovation-strategy 本身已登记（IS，anytime）。人物设定参考 Clayton Christensen 的颠覆理论（与菜单描述里的 disruption opportunities 呼应）以及 Kim & Mauborgne 的蓝海战略重构。

#### `bmad-cis-agent-presentation-master` — Caravaggio — Visual Communication + Presentation Expert

*Agent 角色 ｜ 本机已装*

视觉传达与演示专家 Caravaggio，设计提案、路演、发布会与视频解说等各类演示与视觉叙事，覆盖从多页幻灯片到单张概念图。是 6 个 CIS agent 中唯一全部菜单项都为 prompt 型（不绑定任何技能）的一个。

- **阶段**：—
- **门禁**：可选
- **入口**：说「找 Caravaggio / Presentation Expert」或按技能名直接调用激活；激活后从 7 项菜单中选具体演示类型（全部为 prompt 直接执行，无绑定技能）。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-agent-presentation-master`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `SD` | 多页幻灯片 | `Create a multi-slide presentation with professional layouts and visual hierarchy` | 用 Excalidraw 帧式布局做多页演示，含专业版式与视觉层级 |
| `EX` | 视频解说版式 | `Design a YouTube/video explainer layout with visual script and engagement hooks` | 产出含视觉脚本与留人钩子的视频解说版式 |
| `PD` | 投资人路演 | `Craft an investor pitch presentation with data visualization and narrative arc` | 构建「问题→方案」叙事弧并配数据可视化的路演材料 |
| `CT` | 大会演讲 / 工作坊 | `Build a conference talk or workshop presentation with speaker notes` | 逐页配演讲者备注的会议或工作坊演示 |
| `IN` | 信息可视化 | `Design creative information visualization with visual storytelling` | 按内容选图表/图解类型做创意信息可视化 |
| `VM` | 概念插画 | `Create conceptual illustrations (Rube Goldberg machines, journey maps, creative processes)` | 制作鲁布·戈德堡机械、旅程地图或创意流程类概念插画 |
| `CV` | 单张概念图 | `Generate a single expressive image that explains an idea creatively and memorably` | 生成一张能创造性地讲清某个想法的表达性图片 |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：登记错位（非无实现）：实体完整可用（baseline location=project，skillDir 指向项目级 .claude/skills），仅 skill-manifest.csv 有登记，bmad-help.csv 与 module-help.csv 均无行（inHelpCatalog=false），故 /bmad-help 发现不到该入口。特征最特殊：7 项菜单全部是 prompt 型（其余 5 个 CIS agent 各只有 1 项且均为 skill 型），意味着它的能力完全不在 help CSV 可发现范围内，只能靠激活该 agent 才能触达。CIS 模块另有视觉工具配置项 visual_tools: intermediate（见 cis/config.yaml）。

#### `bmad-cis-agent-storyteller` — Sophia — Master Storyteller

*Agent 角色 ｜ 本机已装*

叙事大师 Sophia，用成熟故事框架让想法被记住、被传播、被信服，擅长情绪心理与叙事机制。人格化入口，实际执行时路由到 bmad-cis-storytelling 工作流。

- **阶段**：—
- **门禁**：可选
- **入口**：说「找 Sophia / Master Storyteller」或按技能名直接调用激活；激活后从菜单选 ST 触发工作流。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-cis-agent-storyteller`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `ST` | 叙事创作 | `Craft compelling narrative using proven story frameworks` | 调用 bmad-cis-storytelling 工作流，用成熟故事框架写有感染力的叙事 |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：登记错位（非无实现）：实体完整可用（baseline location=project，skillDir 指向项目级 .claude/skills），仅 skill-manifest.csv 有登记，bmad-help.csv 与 module-help.csv 均无行（inHelpCatalog=false），故 /bmad-help 发现不到该入口。其路由目标 bmad-cis-storytelling 本身已登记（ST，anytime）。人物设定参考 Robert McKee 的结构主义与 Joseph Campbell 的神话弧。


## Web Design Studio

共 23 个技能。Web 设计工作室：从产品简报、触发映射到 UX 规格与交付

### 阶段与依赖编排

| 阶段 | 技能 |
| --- | --- |
| 0-wds-agents | `bmad-wds-idun`<br>`wds-agent-freya-ux`<br>`wds-agent-saga-analyst` |
| 0-wds-pitch | `wds-0-alignment-signoff` |
| 1-wds-strategy | `bmad-wds-platform-requirements`<br>`wds-1-project-brief` `必需`<br>`wds-2-trigger-mapping` `必需` |
| 2-wds-design | `bmad-wds-conceptual-sketching`<br>`bmad-wds-conceptual-specs` `必需`<br>`bmad-wds-design-delivery` `必需`<br>`bmad-wds-functional-components`<br>`bmad-wds-storyboarding`<br>`wds-3-scenarios` `必需`<br>`wds-4-ux-design` `必需`<br>`wds-6-asset-generation`<br>`wds-7-design-system` |
| 3-wds-build | `bmad-wds-usability-testing`<br>`wds-5-agentic-development`<br>`wds-8-product-evolution` |
| 未标阶段 | `memory`<br>`sync`<br>`wds-0-project-setup`<br>`wds-agent-mimir-builder` |

#### `bmad-wds-idun`

*Agent 角色 ｜ 仅目录登记*

CSV 登记的 Setup and governance agent：通过访谈组织来配置 Agent Space 与权限模型。manifest 中无任何对应技能，本地 .claude/skills 下也无实现目录，属纯目录条目。

- **阶段**：0-wds-agents
- **门禁**：可选
- **入口**：—
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：仅目录登记

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：description「Setup and governance agent. Interviews org to configure Agent Space and authority model.」中的 Agent Space / 权限模型概念在当前安装的任何 WDS 文件中均未出现。

#### `wds-agent-freya-ux`

*Agent 角色 ｜ 本机已装*

WDS 的专职 UX 设计师 persona（Freya），覆盖阶段 3-8 的设计工作：UX 场景、页面设计与规格、视觉资产生成、设计系统与产品演进。用户说「和 Freya 对话」或「找 WDS 设计师」时激活；激活时会检查前置条件并向用户提供菜单。安装 WDS 后它取代 BMM 的 Sally（bmad-agent-ux-designer）。

- **阶段**：0-wds-agents
- **门禁**：可选
- **入口**：用户以自然语言召唤（如「和 Freya 对话」「找 WDS 设计师」）触发激活序列：解析 agent 配置（customize.toml + _bmad/custom 覆盖）→ 载入 persistent_facts 与 persona → 读取 _bmad/wds/config.yaml → 问候并按意图直接派发或渲染菜单等待选择。经 sync 同步后也可用全局命令 /freya 调用。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-agent-freya-ux`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `SC` | 场景梳理 | `Scenarios` | 梳理用户流程与旅程（阶段 3），派发 bmad-wds-outline-scenarios |
| `UX` | UX 设计 | `UX Design` | 创建页面与故事板（阶段 4），派发 bmad-wds-conceptual-sketching |
| `SP` | 规格撰写 | `Specifications` | 编写内容、交互、功能规格（阶段 4），派发 bmad-wds-conceptual-specs |
| `SA` | 规格审计 | `Audit` | 检查规格完整性与质量（阶段 4），派发 bmad-wds-spec-audit（CSV 未登记，职能落在 wds-4 的 [V] Validate Specs） |
| `GA` | 资产生成 | `Generate Assets` | 用 Nano Banana、Stitch 等服务生成资产（阶段 6），派发 bmad-wds-visual-design |
| `DS` | 设计系统 | `Design System` | 构建设计令牌与组件库（阶段 7），派发 bmad-wds-design-system |
| `DD` | 设计交付 | `Design Delivery` | 打包交付流程给开发（菜单标阶段 5；内容见 wds-4 的 [H] Handover），派发 bmad-wds-design-delivery |
| `PE` | 产品演进 | `Product Evolution` | 面向在线产品的持续改进（阶段 8），派发 bmad-wds-product-evolution |

**流程步骤**

1. **Resolve Agent Block** — 运行 resolve_customization.py 解析 agent 配置；失败时按 base→team→user 顺序手工合并
2. **Execute Prepend Steps** — 按序执行 activation_steps_prepend 中的条目
3. **Adopt Persona** — 采用 Freya / WDS Designer 身份，叠加定制 persona 的角色、沟通风格与原则
4. **Load Persistent Facts** — 载入 persistent_facts；file: 前缀条目按路径/通配加载为事实
5. **Load Config** — 读取 _bmad/wds/config.yaml，解析 user_name、communication_language、document_output_language
6. **Greet the User** — 以 persona 身份问候用户（带 agent.icon 前缀），提示可随时调用 bmad-help
7. **Execute Append Steps** — 按序执行 activation_steps_append 中的条目
8. **Dispatch or Present the Menu** — 意图明确则直接派发对应菜单项，否则渲染编号菜单并等待输入

> 备注：principle 明确「Replaces BMM Sally (UX Designer) when WDS is installed」。领域覆盖：阶段 3、4、5、6、7（可选）、8。菜单中的 bmad-wds-visual-design 标「(Phase 6)」是 visual-design→wds-6-asset-generation 映射的关键证据。

#### `wds-agent-saga-analyst`

*Agent 角色 ｜ 本机已装*

WDS 的战略分析师 persona（Saga，领域为阶段 1-2），通过对话创建产品简报（Product Brief）与触发地图（Trigger Map）两份北极星文档，用于协调从愿景到交付的所有团队。安装 WDS 后取代 BMM 的 Mary（bmad-agent-analyst）。

- **阶段**：0-wds-agents
- **门禁**：可选
- **入口**：用户召唤「和 Saga 对话」触发激活序列。激活时按 config 的 starting_point 分支：pitch（先自由对话再进 Product Brief）或 brief（直接进 [PB]）；意图明确则直接派发菜单项。经 sync 同步后也可用全局命令 /saga 调用。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-agent-saga-analyst`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `AS` | 对齐与签核 | `Alignment & Signoff` | 开工前锁定干系人对齐（阶段 0），派发 bmad-wds-alignment |
| `PB` | 产品简报 | `Product Brief` | 创建含战略基础的综合产品简报（阶段 1），派发 bmad-wds-project-brief |
| `TM` | 触发地图 | `Trigger Mapping` | 创建含用户心理与业务目标的触发地图（阶段 2），派发 bmad-wds-trigger-mapping |
| `BP` | 项目头脑风暴 | `Brainstorm Project` | 引导式头脑风暴探索项目愿景与目标，派发 bmad-brainstorming（core 模块） |
| `RS` | 调研 | `Research` | 市场、领域、竞品或技术调研，派发 bmad-market-research（BMM 模块） |
| `DP` | 项目文档化 | `Document Project` | 分析既有项目产出文档（存量项目），派发 bmad-document-project（BMM 模块） |

**流程步骤**

1. **Resolve Agent Block** — 运行 resolve_customization.py 解析 agent 配置（失败则手工按 base→team→user 合并）
2. **Execute Prepend Steps** — 按序执行 activation_steps_prepend
3. **Adopt Persona** — 采用 Saga / WDS Analyst 身份与定制 persona
4. **Load Persistent Facts** — 载入 persistent_facts（含 file: 前缀的路径/通配条目）
5. **Load Config** — 读取 config.yaml：user_name、communication_language、document_output_language、project_name、starting_point
6. **Greet the User** — 以 Saga 身份问候并自我介绍（按 project_name 定制），提示可随时调用 bmad-help
7. **Execute Append Steps** — 按序执行 activation_steps_append
8. **Dispatch or Present the Menu** — 意图明确直接派发；否则按 starting_point 走 pitch/brief 分支，或渲染菜单等待选择

> 备注：principle 明确「Replaces BMM Mary (Analyst) when WDS is installed」。菜单跨模块引用 BMM/Core 技能（bmad-brainstorming、bmad-market-research、bmad-document-project），说明 WDS agent 是模块编排入口。

#### `wds-0-alignment-signoff`

*工作流 ｜ 本机已装*

开工前与干系人对齐想法并取得签核：适用于需要他人批准的场景（顾问向客户提案、企业采购外包、内部立项审批），产出 pitch、合同/服务协议/内部签核三类文档。自己独立做产品可跳过，直接进 Product Brief。

- **阶段**：0-wds-pitch
- **门禁**：可选
- **入口**：Saga 菜单 [AS] 派发；或项目需要干系人批准时直接使用。初始化时读取 config.yaml 与设计日志，从 steps-c/step-01a-understand-situation.md 开始。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：design_artifacts/A-Product-Brief
- **产出物**：pitch service-agreement signoff
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-0-alignment-signoff`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **Start & Understand** — 评估用户处境（01a-01e）：判断是否需要本流程、可否从现有沟通材料提取信息、确定探索起点
2. **Explore Sections** — 按灵活顺序探索对齐文档的 10 个章节（02a-02k）：现实认知→解决方案→价值→路径→承诺 等
3. **Synthesize & Present** — 综合理解并回述确认（03a）、生成对齐文档（03b）、提交干系人批准（03d）
4. **Generate Signoff** — 提供签核选项（04a）并按业务模式路由（04b）：合同 / 服务协议 / 内部签核
5. **Build Contract** — 构建合同 11 个章节（05a-05l）：项目概述、业务模式、范围、付款、时间线、保密、上限、启动、条款、批准
6. **Build Internal Signoff** — 生成内部批准文档（06a-06b）并保存

> 备注：完成后的 AFTER COMPLETION 指向 skill:wds-1-project-brief。步骤体系较大（35 个步骤文件），合同章节 05a-05l 覆盖完整商务条款。

#### `bmad-wds-platform-requirements`

*工作流 ｜ 仅目录登记*

技术边界定义：平台、设备、集成与约束。CSV 标注「Skip for simple landing pages」，preceded-by 为项目简报。

- **阶段**：1-wds-strategy
- **门禁**：可选
- **入口**：并入 wds-1-project-brief：阶段 1 的步骤 27-32（Platform Init→Tech Stack→Integrations→Contact Strategy→Multilingual→Create Platform Document）。
- **参数**：`—`
- **前置**：bmad-wds-project-brief
- **后续**：—
- **产出位置**：design_artifacts/A-Product-Brief
- **产出物**：platform-requirements.md
- **实体路径**：仅目录登记

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：在 CSV 的 1-wds-strategy 分组中与 project-brief、trigger-mapping 并列，但 manifest 未单列。

#### `wds-1-project-brief`

*工作流 ｜ 本机已装*

建立所有设计工作的战略地基：通过协作探询产出 Product Brief（愿景、定位、业务模式、目标用户、成功标准、约束），并延伸出内容与语言、视觉方向、平台需求三份配套文档。CSV 标注为必需（required=true），并要求每个设计决策可回溯到这份文档。

- **阶段**：1-wds-strategy
- **门禁**：必需
- **入口**：阶段 0 路由（Greenfield）或 Saga 菜单 [PB] 派发；也可由 wds-0-alignment-signoff 完成后交接。按 config 的 brief_level 分流：simplified 走 step-00-simplified-brief.md，complete 走 step-01-init.md；带 validate 参数走 workflow-validate.md。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：design_artifacts/A-Product-Brief
- **产出物**：project-brief.md
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-1-project-brief`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **Simplified Brief (alternative entry)** `可跳过` — brief_level=simplified 时的替代入口：一份精简简报替代完整 36 步流程
2. **01 Init** — 载入上下文，确认就绪
3. **01a Client Profile** — 客户画像：组织、关键人、决策文化、内部驱动因素
4. **02 Vision** — 探索并记录项目愿景
5. **03 Positioning** — 定义市场定位
6. **05 Business Model** — 定义收入/业务模式（文档步骤编号从 03 跳到 05，无 04 步）
7. **06 Business Customers** `可跳过` — 识别 B2B 客户（如适用）
8. **07 Target Users** — 定义最终用户
9. **07a Product Concept** — 澄清产品概念
10. **08 Success Criteria** — 定义可衡量的成功指标
11. **09 Competitive Landscape** — 分析竞争格局
12. **10 Constraints** — 记录项目约束
13. **10a Platform Strategy** — 定义平台策略
14. **11 Tone of Voice** — 建立品牌语气
15. **12 Create Product Brief** — 生成 Product Brief 主文档
16. **13 Content Init** — 初始化内容与语言策略
17. **14 Personality** — 定义品牌人格
18. **15 Tone** — 细化语气指南
19. **16 Languages** — 制定语言策略
20. **17 SEO Keywords** — 定义关键词地图
21. **17a Content Structure** — 搭建内容架构
22. **18 Create Content Document** — 生成内容与语言文档
23. **19 Inspiration Workshop** — 分析参考站点
24. **20 Visual Init** — 初始化视觉方向
25. **21 Existing Brand** — 记录现有品牌资产
26. **22 References** — 收集视觉参考
27. **23 Design Style** — 定义设计风格
28. **24 Layout & Effects** — 定义布局模式与效果
29. **25 Imagery** — 确定摄影与插画方向
30. **26 Create Visual Document** — 生成视觉方向文档
31. **27 Platform Init** — 初始化平台需求
32. **28 Tech Stack** — 定义技术选型
33. **29 Integrations** — 梳理第三方集成
34. **30 Contact Strategy** — 定义联系表单与通讯策略
35. **31 Multilingual** — 多语言设置
36. **32 Create Platform Document** — 生成平台需求文档
37. **33 Analyze Brief** — 复核阶段 1 全部产物
38. **34 Create Summary** — 生成交接摘要
39. **35 Update Design Log** — 在设计日志记录阶段 1 决策
40. **36 Provide Activation** — 给出阶段 2 的激活提示

> 备注：本技能含大量模板资源（resources/wds-1-project-brief/templates/：project-brief、content-language、platform-requirements、visual-direction、simplified-brief、pitch、contract、service-agreement、signoff 等）。dependencies 的 outputLocation/outputs 取主条目值；platform-requirements 条目的独立值为 outputLocation=design_artifacts/A-Product-Brief、outputs=platform-requirements.md、required=false。

#### `wds-2-trigger-mapping`

*工作流 ｜ 本机已装*

通过结构化工作坊把业务目标映射到用户心理：依次产出业务目标、目标群体、驱动因素与优先级，再生成人物画像、特征影响分析与 Mermaid 影响力图，形成协调所有团队的战略北极星。方法基于 inUse 的 Effect Mapping（Mijo Balic 与 Ingrid Domingues），WDS 做了简化（去特征）并增强负向驱动因素。

- **阶段**：1-wds-strategy
- **门禁**：必需
- **入口**：Saga 菜单 [TM] 派发；或由 wds-1-project-brief 完成后交接。三个入口：默认从零工作坊（step-01-overview）、从既有文档综合（step-00a-documentation-synthesis）、validate 校验（workflow-validate.md）。
- **参数**：`—`
- **前置**：bmad-wds-project-brief
- **后续**：—
- **产出位置**：design_artifacts/B-Trigger-Map
- **产出物**：trigger-map.md personas/ feature-impact-analysis.md
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-2-trigger-mapping`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `W` | 工作坊 | `Workshop` | 我主持、你提供洞察（45-60 分钟）；选 W 后再选全部 4 个工作坊一次跑完 [A] 或逐个进行 [O] |
| `S` | 建议模式 | `Suggest` | 我逐步建议、你逐步复核（20-35 分钟），基于 WDS 方法+产品简报+领域研究生成 |
| `D` | 代做模式 | `Dream` | 我自主完成全部步骤、你复核最终结果（15-25 分钟），含设计日志与自审循环 |

**流程步骤**

1. **Mode Selection** — 展示阶段 2 概览并提供 Workshop/Suggest/Dream 三种参与模式（禁止替用户自动选择）
2. **Documentation Synthesis (alternative entry)** `可跳过` — 从既有文档综合提取（step-00a-00f）：业务目标、目标群体、驱动因素、优先级提取与差距分析
3. **Business Goals** — 梳理并确认业务目标
4. **Target Groups** — 识别并划分目标群体
5. **Driving Forces** — 识别正向与负向驱动因素
6. **Prioritization** — 对驱动因素做优先级排序
7. **Feature Impact Analysis** — 提取特征并按驱动因素评分（06a-06e），生成特征影响文档
8. **Generate Documents** — 生成产出（07a-07g）：hub、业务目标、主/次/三级人物画像、关键洞察，含质量检查
9. **Mermaid Impact Map** — 生成 Mermaid 影响力图（08a-08h）：结构、业务目标、平台、目标群体、驱动因素、连接与样式
10. **Finalize & Handover** — 收尾（09a-09d）：定稿 hub、加交叉引用、质量检查、创建交接包

> 备注：阶段编号差异：技能文档自述「Phase 2: Trigger Mapping」，CSV 归「1-wds-strategy」（见 discrepancies）。工作流含严格步骤纪律（禁止同时载入多个步骤文件）与 5 层生成管线（Learn Form→Project Context→Domain Research→Generate→Self-Review，Dream/Suggest 模式下最多 5 轮自审循环）。

#### `bmad-wds-conceptual-sketching`

*工作流 ｜ 仅目录登记*

详细规格前的快速粗略视觉探索（「Skip for straightforward scenarios」）。

- **阶段**：2-wds-design
- **门禁**：可选
- **入口**：并入 wds-4-ux-design：对应 [C] Discuss（创意对话+线框迭代）与 [K] Analyse Sketches（解读用户草图）；Freya 菜单 UX 项直接指向本 catalog 名。
- **参数**：`—`
- **前置**：bmad-wds-outline-scenarios
- **后续**：—
- **产出位置**：design_artifacts/C-UX-Scenarios
- **产出物**：sketches
- **实体路径**：仅目录登记

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：工作流文件注明 [C] 是「default design activity」，与 CSV 的「快速粗略探索」定位存在一定宽窄差异。

#### `bmad-wds-conceptual-specs`

*工作流 ｜ 仅目录登记*

为每个页面的每个元素记录全部设计决策，开发者据此直接构建（required=true）。

- **阶段**：2-wds-design
- **门禁**：必需
- **入口**：并入 wds-4-ux-design：对应 [P] Write Specifications（steps-p/ 9 步）；Freya 菜单 SP 项直接指向本 catalog 名。
- **参数**：`—`
- **前置**：bmad-wds-outline-scenarios
- **后续**：—
- **产出位置**：design_artifacts/C-UX-Scenarios
- **产出物**：page-specs scenario-specs
- **实体路径**：仅目录登记

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：CSV 中 required=true 的 design 阶段条目；Freya 菜单 SP 项为其入口证据。

#### `bmad-wds-design-delivery`

*工作流 ｜ 仅目录登记*

校验规格完整性并打包为 DD yaml 交付包，附验收标准，移交开发（required=true）。

- **阶段**：2-wds-design
- **门禁**：必需
- **入口**：并入 wds-4-ux-design：对应 [H] Design Delivery / Handover（steps-h/ 6 步，产出 DD-XXX）；Freya 菜单 DD 项直接指向本 catalog 名。
- **参数**：`—`
- **前置**：bmad-wds-conceptual-specs
- **后续**：—
- **产出位置**：design_artifacts/E-Development
- **产出物**：delivery-package acceptance-criteria
- **实体路径**：仅目录登记

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：design-delivery.template.yaml 与 workflow-handover.md 的「Package a complete testable flow into a Design Delivery」描述高度一致。

#### `bmad-wds-functional-components`

*工作流 ｜ 仅目录登记*

把规格中的可复用模式提取为组件定义（「Skip if Design System Mode None」），产出组件候选。

- **阶段**：2-wds-design
- **门禁**：可选
- **入口**：并入 wds-7-design-system：对应 workflow-create.md 的「Build a new design system or add components from specifications」与重复检测流程；wds-4 的 [M] 亦含页面内提取规则。
- **参数**：`—`
- **前置**：bmad-wds-conceptual-specs
- **后续**：—
- **产出位置**：design_artifacts/C-UX-Scenarios
- **产出物**：component-candidates
- **实体路径**：仅目录登记

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：CSV 中它是 bmad-wds-design-system 的 preceded-by。

#### `bmad-wds-storyboarding`

*工作流 ｜ 仅目录登记*

把用户旅程按屏幕序列化：入口点、转场与错误路径（「Skip for simple scenarios」）。

- **阶段**：2-wds-design
- **门禁**：可选
- **入口**：并入 wds-4-ux-design：storyboard 材料分布于 [S] Suggest / [D] Dream 流程与 storyboard 模板；无独立活动码。
- **参数**：`—`
- **前置**：bmad-wds-outline-scenarios
- **后续**：—
- **产出位置**：design_artifacts/C-UX-Scenarios
- **产出物**：storyboards
- **实体路径**：仅目录登记

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：「storyboard」在 wds-4 的 workflow.md、workflow-suggest.md、workflow-dream.md 中均有出现，但未形成带菜单码的独立活动。

#### `wds-3-scenarios`

*工作流 ｜ 本机已装*

把触发地图转成具体 UX 场景大纲：以「人物+目标+结果」定义用户旅程的阳光路径，让所有待设计页面暴露出来接受审视。步骤 02 与 04 设用户确认关卡，步骤 07 按评分表做质量校验。

- **阶段**：2-wds-design
- **门禁**：必需
- **入口**：Freya 菜单 [SC] 派发；或由 wds-2-trigger-mapping 交接。初始化后从 steps-c/step-01-load-context.md 开始；带 validate 参数走 workflow-validate.md。
- **参数**：`—`
- **前置**：bmad-wds-trigger-mapping
- **后续**：—
- **产出位置**：design_artifacts/C-UX-Scenarios
- **产出物**：scenario-overview.md
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-3-scenarios`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **Load Context** — 读取全部前置产物（产品简报、触发地图），检测项目状态
2. **Analyze Scope** — 确定站点类型、页面与规模策略（用户确认关卡）
3. **Build Strategic Context** — 从触发地图提取战略上下文
4. **Suggest Scenarios** — 提交场景计划供批准（用户确认关卡）
5. **Outline Scenario** — 逐个细化场景（循环执行每个场景）
6. **Generate Overview** — 生成 00-ux-scenarios.md 索引与覆盖矩阵
7. **Quality Review** — 对照评分表自审
8. **Update Design Log** — 在项目日志记录阶段完成
9. **Handover** — 完成阶段 3 并准备阶段 4

> 备注：阶段编号差异：技能自述「Phase 3」，CSV 归「2-wds-design」。另有 workflow-validate.md（steps-v/ 5 项校验：场景覆盖、导航模式、大纲完整性、跨场景一致性、SEO 关键词对齐）。

#### `wds-4-ux-design`

*工作流 ｜ 本机已装*

以场景为驱动的设计主战场：启动时读取设计日志呈现自适应仪表盘，建议下一步；围绕每个场景做讨论、草图解读、建议式/代做式设计，撰写实现级页面规格，生成视觉表现，管理设计系统并打包交付。产出开发可直接实现的页面规格与 Design Delivery 包。

- **阶段**：2-wds-design
- **门禁**：必需
- **入口**：Freya 菜单 [UX]/[SP] 等派发；或由 wds-3-scenarios 交接（scenario 的 design_intent 可预选活动）。初始化读取 config.yaml 与 _progress/00-design-log.md，无日志则先引导做阶段 0 设置；带 validate 参数走 workflow-validate.md。
- **参数**：`—`
- **前置**：bmad-wds-outline-scenarios
- **后续**：—
- **产出位置**：design_artifacts/C-UX-Scenarios
- **产出物**：page-specs scenario-specs
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-4-ux-design`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 讨论 | `Discuss` | 页面设计的创意对话（默认活动）：讨论页面需求→可视化→写规格，跑 8 步设计循环 |
| `K` | 解读草图 | `Analyse Sketches` | 分析用户提供的草图（照片、截图、线框）并转成结构化页面规格 |
| `S` | 建议式设计 | `Suggest Design` | 我来提议设计、你逐步确认 |
| `D` | 代做式设计 | `Dream Up Design` | 我全部做完、你来复核（自主模式） |
| `P` | 编写规格 | `Write Specifications` | 内容、交互、间距、排版规格的完整编写（steps-p/ 9 步） |
| `V` | 校验规格 | `Validate Specs` | 审计规格完整性与质量（steps-v/ 10 项校验） |
| `W` | 视觉设计 | `Visual Design` | 用 Nano Banana、Stitch、Figma、Pencil.io 等工具创建视觉表现并整合回规格 |
| `M` | 设计系统 | `Design System` | 提取或更新共享组件（首次出现内联、第二次使用才提取） |
| `H` | 设计交付 | `Design Delivery` | 把完整可测的流程打包为 DD-XXX Design Delivery 并移交开发（steps-h/ 6 步） |

**流程步骤**

1. **Design** `可跳过` — 设计与探索组：讨论（C）、解读草图（K）、建议（S）、代做（D）
2. **Specify** `可跳过` — 规格组：编写规格（P）、校验规格（V）
3. **Produce** `可跳过` — 产出组：视觉设计（W）、设计系统（M）、设计交付（H）

> 备注：Freya 菜单用 CSV 名称引用本技能的两个活动：UX→bmad-wds-conceptual-sketching、SP→bmad-wds-conceptual-specs、DD→bmad-wds-design-delivery，可作为映射的直接证据。storyboarding 无独立活动码，storyboard 相关文件（data/modular-architecture/02-workflows/storyboards-guide.md、templates/storyboard-specification.template.md）出现在 suggest/dream 流程中。设计日志（Design Log）是本技能跨会话的记忆机制，含 Backlog/Current/Design Loop Status/Log 四区。

#### `wds-6-asset-generation`

*工作流 ｜ 本机已装*

把规格变成生产级资产：线框、页面设计稿、UI 元素、图标、图片、视频、策略文案与 Figma 导出共 8 类。内置设计风格库与内容风格库保证视觉一致性，支持批量生成与参考图，优先走 MCP 服务生成、不可用时导出提示词给外部工具。

- **阶段**：2-wds-design
- **门禁**：可选
- **入口**：阶段 5/6 由 Freya 菜单 [GA] 派发（菜单引用 bmad-wds-visual-design 并标注 Phase 6）；或直接调用。初始化读取 config.yaml 与设计日志后进入活动菜单。
- **参数**：`—`
- **前置**：bmad-wds-conceptual-specs
- **后续**：—
- **产出位置**：design_artifacts/C-UX-Scenarios
- **产出物**：html-prototypes visual-designs
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-6-asset-generation`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `W` | 线框图 | `Wireframes` | 从页面规格生成轮廓线框 |
| `P` | 页面设计稿 | `Page Designs` | 完整的页面设计构图 |
| `U` | UI 元素 | `UI Elements` | 按钮、卡片、表单、组件类资产 |
| `I` | 图标 | `Icons` | 图标集与单个图标 |
| `M` | 图片 | `Images` | 照片、插画、背景图 |
| `V` | 视频 | `Videos` | 动效内容与动画 |
| `C` | 文案内容 | `Content` | 策略性文本内容（5 模型框架） |
| `E` | 导出到 Figma | `Export to Figma` | 把规格与资产推送到 Figma |

**流程步骤**

1. **Load Context** — 读取相关页面规格、设计系统与视觉方向
2. **Asset Inventory** — 盘点所需资产（单个或批量）
3. **Select Style** — 从风格库选择设计风格与内容风格
4. **Reference Images** — 附参考图保证批量视觉一致性（服务支持时）
5. **Craft Prompts** — 把规格+风格+参考翻译为生成提示词
6. **Select Service** — 路由到 MCP 服务或导出提示词供外部工具使用
7. **Generate & Review** — 执行生成、审阅结果、迭代

> 备注：本技能覆盖 8 类资产、体量较大（styles 目录含 6 类设计风格与 10 类内容风格）。产出位置与 CSV 记录不一致：本技能实际输出 {output_folder}/E-Assets/（按类型组织），CSV 记为 design_artifacts/C-UX-Scenarios。

#### `wds-7-design-system`

*工作流 ｜ 本机已装*

创建、导入、浏览、编辑、维护设计系统：组件与设计令牌以代码为唯一事实源，新增组件时内部做相似度重复检测（复用/扩展/新建三选一），并可生成一次性的 localhost 应用做可视化浏览（令牌浏览器、关系视图、意图搜索、组件目录），Figma 用于视觉编辑。

- **阶段**：2-wds-design
- **门禁**：可选
- **入口**：Freya 菜单 [DS] 派发；或由 wds-4 的 [M] Manage Design System 深入而来。初始化读取 config.yaml（含 design_system_mode: none/basic/full）与设计日志后进入活动菜单。
- **参数**：`—`
- **前置**：bmad-wds-functional-components
- **后续**：—
- **产出位置**：design_artifacts/D-Design-System
- **产出物**：components/ design-tokens.md
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-7-design-system`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `C` | 创建设计系统 | `Create Design System` | 从规格构建新设计系统（含重复检测） |
| `I` | 导入设计系统 | `Import Design System` | 引入既有设计系统 |
| `V` | 预览组件 | `View Components` | 在 localhost 预览选定组件 |
| `E` | 编辑组件 | `Edit Components` | 在 Figma 中打开选定组件编辑 |
| `B` | 浏览设计系统 | `Browse Design System` | 在 localhost 搜索与探索令牌和组件 |

**流程步骤**

1. **Initialize** `可跳过` — 初始化设计系统结构：令牌类别、组件组织、命名规范（steps-c/step-08a）
2. **Duplicate Detection** — 新增组件前做重复检测（steps-c/step-01-07）：扫描既有、属性对比、相似度计算、机会与风险识别、呈现决策
3. **Create or Update Component** — 执行决策（steps-c/step-08b-08e）：新建/更新/加变体/生成目录

> 备注：「Skip if Design System Mode None」与本技能的 design_system_mode 配置（config.yaml: none/basic/full）直接对应，是 functional-components 归属本技能的依据之一。产出位置：{output_folder}/D-Design-System/components/*.md、design-tokens.md、component-library-config.md。

#### `bmad-wds-usability-testing`

*工作流 ｜ 仅目录登记*

在用户真实环境中做真人测试，含回顾式出声思考（think-aloud）环节；displayName 登记为「Acceptance Testing」。

- **阶段**：3-wds-build
- **门禁**：可选
- **入口**：并入 wds-5-agentic-development：按 displayName 与流程链位置对应 [T] Acceptance Testing 活动（steps-t/ 5 步）。
- **参数**：`—`
- **前置**：bmad-wds-agentic-development
- **后续**：—
- **产出位置**：design_artifacts/E-Development
- **产出物**：test-results findings
- **实体路径**：仅目录登记

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：描述与本地实现的差异见 wds-5-agentic-development 的 notes：本地 [T] 是 designer validation，think-aloud 真人测试表述仅在 PROTOTYPE-ANALYSIS.md 出现，未形成完整流程，判定为版本演进差异。

#### `wds-5-agentic-development`

*工作流 ｜ 本机已装*

AI 辅助的开发、测试与逆向工程：菜单驱动而非线性，从原型、生产开发、修缺陷、功能演进、代码分析、逆向工程到验收测试共 7 类活动任选。核心原则「规格即事实」——所有工作回溯到已批准的规格，设计日志驱动状态跟踪。

- **阶段**：3-wds-build
- **门禁**：可选
- **入口**：Freya 菜单（阶段 5）或直接调用。初始化读取 config.yaml 与设计日志后呈现活动菜单。
- **参数**：`—`
- **前置**：bmad-wds-design-delivery
- **后续**：—
- **产出位置**：_progress/agent-experiences
- **产出物**：experience-documents
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-5-agentic-development`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `P` | 原型构建 | `Prototyping` | 从规格构建可交互原型（steps-p/ 含逻辑视图拆解、分节实现、展示测试） |
| `D` | 生产开发 | `Development` | 编写生产代码（steps-d/ 5 步：界定与计划、环境、实现、验证、收尾） |
| `F` | 缺陷修复 | `Bugfixing` | 修复既有代码中的缺陷（steps-f/ 5 步：复现、调查、修复、验证、记录） |
| `E` | 功能演进 | `Evolution` | 为在线产品添加功能（steps-e/ 5 步：界定变更、影响分析、实现计划、实现、验证与记录） |
| `A` | 代码分析 | `Analysis` | 理解自己的代码库并产出分析文档（steps-a/ 4 步） |
| `R` | 逆向工程 | `Reverse Engineering` | 从任意软件/网站提取规格（steps-r/） |
| `T` | 验收测试 | `Acceptance Testing` | 从规格验收标准设计并运行测试（steps-t/ 5 步：准备、执行、记录问题、报告、迭代） |

**流程步骤**

无独立流程文件（或该技能为单步执行）。

> 备注：未完全对齐之处：CSV 的 usability-testing 描述为「Test on real users in their environment with retrospective think-aloud sessions」（真人用户环境测试），而本地 [T] Acceptance Testing 是设计师对照规格验证（data/testing-guide.md 标题为「Acceptance Testing (Designer Validation)」），think-aloud 表述仅见于 data/guides/PROTOTYPE-ANALYSIS.md 的「real usability testing」提法，未见完整流程。二者按 displayName 一致 + 流程链位置判定为同一职能的新旧版本差异。

#### `wds-8-product-evolution`

*工作流 ｜ 本机已装*

存量产品的持续改良：完整 WDS 流水线的微缩版，每个循环聚焦一处改进（分析→界定→设计→实现→验收→部署），每次变更走独立 git 分支直至部署。基于 Kaizen 理念：小步、增量、数据驱动，每个循环反哺下一个。

- **阶段**：3-wds-build
- **门禁**：可选
- **入口**：新项目判定为 Brownfield 时由阶段 0 路由进入；Freya 菜单 [PE] 派发；或对既有产品做改进时直接调用。初始化读取 config.yaml 与设计日志后进入活动菜单。
- **参数**：`—`
- **前置**：bmad-wds-usability-testing
- **后续**：—
- **产出位置**：design_artifacts
- **产出物**：updated-artifacts
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-8-product-evolution`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `A` | 分析产品 | `Analyze Product` | 理解现状、寻找改进目标（steps-a/，借用阶段 3 场景方法） |
| `S` | 界定改进 | `Scope Improvement` | 为具体更新创建场景（借用阶段 3） |
| `D` | 设计方案 | `Design Solution` | 草拟并规格化更新（steps-d/，借用阶段 4 UX 设计） |
| `I` | 实现 | `Implement` | 在新分支写代码（借用阶段 5） |
| `T` | 验收测试 | `Acceptance Test` | 对照规格测试（steps-t/，借用阶段 5 的 [T]） |
| `P` | 部署 | `Deploy` | 提 PR 并交付团队（steps-p/，借用阶段 4 的 [H] 交付） |

**流程步骤**

1. **Analyze** — 理解产品现状并找改进目标
2. **Scope** — 把改进界定为一个场景（单视图、单一改进点）
3. **Design** — 草拟并规格化改进方案
4. **Implement** — 在独立分支编码
5. **Test** — 对照规格做验收测试
6. **Deploy** — PR 与交付

> 备注：阶段编号差异：技能自述「Phase 8」，CSV 归「3-wds-build」。产出路径：{output_folder}/evolution/{scenarios,specs,test-reports}/。工作流明确「Full Pipeline in Miniature」并标注各活动借用自哪个主阶段。

#### `memory`

*工具 ｜ 本机已装 ｜ **禁止直接调用***

WDS 的会话状态后端：两个操作 save/load，把各 agent 的会话状态写到项目根的 progress/ 目录（机器本地、不进 git）。明确标注「从不被用户直接调用」——save 由 wrap 与 handoff 调用，load 由 start 调用。

- **阶段**：—
- **门禁**：可选
- **入口**：无用户入口。由 WDS 工具链内部调用：wrap/handoff 的第 3 步调用 save；start 的第 2 步调用 load。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/memory`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **save** — 确保项目根存在 progress/；把调用方给的状态块原样写入 progress/[agent_id].md；返回保存路径
2. **load** — 检查 progress/[agent_id].md 是否存在：存在返回全文，不存在返回空（由调用方处理全新会话）

> 备注：SKILL frontmatter 声明 agents: [saga, freya, mimir]，即三个 agent 共用的状态后端。文档建议 progress/ 加入 .gitignore（机器本地会话上下文，非项目内容）。

#### `sync`

*工具 ｜ 本机已装 ｜ **禁止直接调用***

把当前项目 _bmad/wds/ 下的 WDS 技能同步到 ~/.claude/commands/（以及 ~/.claude/wds/tools 与 data），使 /saga /freya /mimir /start /wrap /handoff 在任意项目的 Claude Code 会话中可用。每次 agent 激活时静默执行，用户也可直接触发。

- **阶段**：—
- **门禁**：可选
- **入口**：两种：agent 每次激活时的静默调用（首次询问一次、之后按需静默同步，失败不阻塞激活）；用户显式请求（说「sync」「update WDS」「sync skills」「check for updates」）进入 verbose 模式逐步汇报。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/sync`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **Locate Project Installation** — 定位项目根的 _bmad/wds/；不存在时静默停止（verbose 模式提示先安装）
2. **Detect Home Directory** — 识别 HOME（Mac/Linux 用 $HOME，Windows 用 $env:USERPROFILE）并确定命令/工具/数据三类目标目录
3. **Check Sync State** — 检查 ~/.claude/commands/wrap.md 是否存在；已同步则 diff 比对，相同则静默结束
4. **First Time Ask** `可跳过` — 首次同步前询问一次（[Y/n]）：是否将技能加入全局；选 n 则本会话不再询问
5. **Sync Files** — 创建目标目录，复制 6 个命令文件（saga/freya/mimir/start/wrap/handoff）与 memory、glossary、agent-contracts、shared-activation；缺失源文件跳过不报错
6. **Report** — 按场景输出同步结果（首次/直接调用详细；静默更新简略；无变化时不输出或提示已最新）

> 备注：源文件清单显示 WDS 技能以 skills/saga.activation.md、freya.activation.md、mimir.activation.md、start.md、wrap.md、handoff.md 为全局命令源；本机 ~/.claude/commands/ 未发现这些文件（仅 loop-start.md），说明本项目尚未执行过 sync。

#### `wds-0-project-setup`

*工作流 ｜ 本机已装*

每个 WDS 项目的起点（3-5 分钟）：介绍 WDS、判定新项目（Greenfield）还是存量项目（Brownfield）、产品复杂度（落地页/网站/应用）、技术栈与组件库、brief 层级（完整/简化）与战略分析深度（full/simplified/skip），创建目录结构并路由到正确阶段。文档明言头号错误是「带着存量代码从阶段 1 开始」。

- **阶段**：—
- **门禁**：可选
- **入口**：首次使用 WDS、开始新项目、加入既有项目或不确定用哪个工作流时进入。已在 steps/step-01-welcome.md 起步。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-0-project-setup`

**内部可选分支**

无内部菜单（单一动作技能）。

**流程步骤**

1. **Welcome & Orientation** — 简介 WDS，判定 Greenfield（走阶段 1-7）还是 Brownfield（走阶段 8）
2. **Configuration & Structure** — 配置项目名、复杂度、技术栈、组件库、brief 层级、战略分析深度；创建目录结构并生成项目大纲；按类型路由

> 备注：整体可跳过：项目大纲 .wds-project-outline.yaml 已存在、明确知道所需阶段、或继续既有 WDS 项目时。配置项与影响在 workflow.md 有完整表格（Project Type/Complexity/Tech Stack/Component Library/Brief Level/Strategic Analysis）。产出路由：Greenfield→阶段 1（full 分析时进阶段 2）；Brownfield→阶段 8。

#### `wds-agent-mimir-builder`

*Agent 角色 ｜ 本机已装*

WDS 的实现 agent（Mimir），负责技术审计、PRD 与构建三件事：读 Freya 的 Work Order，写成正式需求，然后一次一个任务地实现并逐项验证。非创造型角色——创造发生在上游，他只做严谨的实现与验证。

- **阶段**：—
- **门禁**：可选
- **入口**：用户召唤「和 Mimir 对话」或作为 WDS 阶段 5 的执行入口。激活时先读 _wds/tools/memory/SKILL.md 的 load 操作恢复状态（agent_id: mimir），再扫描 E-Development/ 目录判断路由（无技术审计→/TA；有 Work Order 无 PRD→/PR；有 PRD→/BU）。
- **参数**：`—`
- **前置**：—
- **后续**：—
- **产出位置**：—
- **产出物**：—
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/wds-agent-mimir-builder`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `TA` | 技术审计 | `Tech Audit` | 读取代码库并产出现行架构文档 E-Development/000-tech-audit.md（首次进入） |
| `PR` | 需求文档 | `PRD` | 把 Freya 的 Work Order 写成正式 PRD：平台需求、接口需求、验收标准 |
| `BU` | 构建 | `Build` | 按 PRD 逐条实现：实现→提交→验证→下一条 |

**流程步骤**

1. **Load State** — 调用 memory 的 load 操作恢复 mimir 会话状态；有状态则展示「上次进度/下一步」并等待确认
2. **Scan Project Context** — 扫描输出目录的 E-Development/（Work Order、PRD、技术审计）并识别代码库根目录
3. **Route** — 按条件路由：无审计→/TA；有 Work Order 无 PRD→/PR；PRD 就绪→/BU；带参数则直达对应工作流

> 备注：输出路径文档写作 _wds/tools/memory/SKILL.md（注意前缀为 _wds 而非 _bmad/wds），且 config 使用 {output_folder}。principle 明确「Domain: Phase 5 (Agentic Development)」，但 CSV 无对应 phase 记录。


## BMad Automator 自动化

共 2 个技能。自动化执行：无人值守跑通故事构建与审查循环

### 阶段与依赖编排

| 阶段 | 技能 |
| --- | --- |
| 4-implementation | `bmad-story-automator`<br>`bmad-story-automator-review` |

#### `bmad-story-automator`

*工作流 ｜ 本机已装*

以构建循环编排者身份，自动化一个或多个 epic 中全部故事的开发：在隔离 tmux 会话中按序编排 create-story → dev-story → 测试自动化 → code-review → retrospective，全程可续跑、可并行、只在需要决策时升级打断用户。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：菜单 SA，或说 run story automator / automate stories / run build cycle；内部模式词 create / resume / validate / edit（或 -r / -v / -e）决定入口步骤；前置条件是 sprint-status.yaml 已由 sprint-planning 生成。
- **参数**：`—`
- **前置**：bmad-sprint-planning
- **后续**：—
- **产出位置**：implementation_artifacts
- **产出物**：story automation run
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-story-automator`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `SA` | 故事自动化 | `Story Automator` | 自动化 BMAD 故事构建循环，覆盖创建、开发、QA、评审与回顾步骤。 |

**流程步骤**

1. **初始化** — 校验并安装 Stop hook（防编排中途停止，安装后需重启会话；Codex 需先信任项目）、加载编排规则、搜索未完成编排状态、强制校验 sprint-status.yaml 存在（缺失即中止并指向 sprint-planning）。
2. **续跑（可选）** `可跳过` — 若发现未完成编排（或用户指定 state 文档），由 step-01b 载入已有状态并选择继续点，而非从零开始。
3. **预检** — 确认 epic 文件（默认 planning-artifacts/epics.md）、解析故事清单与当前 sprint 状态、选择故事范围、用 Python 助手对每个故事强制程序化复杂度打分（禁止人工评估）、展示复杂度矩阵、收集自定义指令并落 preflight 快照。
4. **预检配置** — 询问执行设置（是否跳过 automate 步骤、最大并行会话数）与复杂度感知的 agent 配置（默认 / 统一 / 自定义 / 载入预设，按 low/medium/high 分配主备 agent），创建编排状态文档。
5. **预检定稿** — 写入 complexity 与 agents 文件、创建运行时 marker（并把 marker 条目加入 .gitignore）、状态置 IN_PROGRESS，进入执行。
6. **执行循环：创建与开发** — 逐故事推进：A. create-story（故事文件已存在则跳过）→ B. dev-story；每步独立 spawn / monitor / kill tmux 会话（禁止链式执行），失败最多 5 次重试并交替 agent，同一任务 3 次平台期则 defer 该故事。
7. **执行循环：自动化与评审** — C. automate 测试护栏（可被 overrides 跳过，失败 3 次后降级为告警跳过）→ D. code-review 循环，直到审查通过。
8. **收尾：提交 / 校验 / 复盘触发** — E. git 提交（每个故事必做，失败升级）→ F. 校验 sprint 状态（故事文件作为回退依据，未 done 则回评审循环）→ G. 故事完成；H. 当 epic 内全部故事通过评审且 sprint 状态确认 done 时触发该 epic 的自动化复盘（YOLO 模式，失败只告警不阻塞）。
9. **执行完成汇总** — 全部完成后输出故事结果表（或计数摘要）、说明并行批次与升级触发条件，状态置 EXECUTION_COMPLETE。
10. **收尾总结** — 生成运行摘要、合并 learnings.md 累积经验、按观察给出建议、状态置 COMPLETE 并移除运行时 marker，工作流终止。

> 备注：help CSV 中 SA 的 action/args 为空。技能内部有四种运行模式：Create（步骤 steps-c/step-01-init 起）、Resume（-r，step-01b）、Validate（-v，steps-v/step-01-check 校验状态文档完整性与会话健康）、Edit（-e，steps-e/step-e-01-load 修改既有编排配置），另有 steps-c/step-03c 等微文件步骤架构（每次只加载当前步骤文件）。多 epic 支持：各 epic 独立处理与复盘。编排强依赖 tmux 与外部 helper CLI（scripts/story-automator 提供 tmux-wrapper / monitor-session / orchestrator-helper / commit-story 等命令），运行策略固定在 data/orchestration-policy.json。

#### `bmad-story-automator-review`

*工作流 ｜ 本机已装*

运行 story automator 会话使用的自主代码审查流程：以对抗性审查核对故事声明与实际实现（AC、任务勾选状态、git 差异、代码与测试质量），支持自动修复，并把结果同步进故事文件与 sprint-status。

- **阶段**：4-implementation
- **门禁**：可选
- **入口**：菜单 SAR；实际使用场景是 story automator 在非交互编排中要求对某个故事做审查时调用（“当 story automator 要求对故事做非交互审查时”）。
- **参数**：`—`
- **前置**：bmad-dev-story
- **后续**：—
- **产出位置**：implementation_artifacts
- **产出物**：review report
- **实体路径**：`F:/code2/bmad-tool/.claude/skills/bmad-story-automator-review`

**内部可选分支**

| 菜单码 | 中文名 | 英文原名 | 说明 |
| --- | --- | --- | --- |
| `SAR` | 故事自动化·代码审查 | `Story Automator Review` | 运行 story automator 使用的自主代码审查流程，含自动修复处理与 sprint 状态同步。 |

**流程步骤**

1. **加载故事并发现真实变更** — 读完整故事文件，解析 Story / AC / Tasks / Dev Agent Record → File List；用 git status/diff 找出实际变更，与故事 File List 交叉比对，记录三类差异（改动未记录、声称却无变更、未提交未记录）。
2. **构建审查攻击计划** — 提取全部 AC 与任务完成状态（[x] vs [ ]），制定四路计划：AC 验证、任务审计、代码质量（安全/性能/可维护性）、测试质量（真实断言 vs 占位）。
3. **执行对抗性审查** — 逐个验证声明：标记 [x] 却未完成 = CRITICAL，AC 未实现 = HIGH，未记录的文件变更 = MEDIUM；逐文件深查安全（注入/校验/鉴权）、性能、错误处理与测试质量；目标每次至少给出 3-10 个具体问题（要求核实证据，不凑数）。
4. **呈现发现并处置** — 按 CRITICAL / MEDIUM / LOW 分级展示后询问处置：1) 自动修复全部 HIGH+MEDIUM 并更新测试与故事记录；2) 作为 action items 写入故事 Tasks 的 Review Follow-ups 小节；3) 只看某个问题的细节。
5. **更新状态并同步 sprint** — 仅按 CRITICAL 残留决定故事状态（0 个 → done，≥1 → in-progress）；若 sprint-status.yaml 存在则同步对应 story key 的 development_status（保留全部注释与结构），失败时明确告警。

> 备注：SKILL.md 极薄，只做四件事：读 workflow.yaml → 读 instructions.xml → 用 checklist.md 做校验 → 确定性执行；实际流程与 19 项验证清单全在 instructions.xml 与 checklist.md 中。instructions.xml 沿用 bmm code-review 风格的分级措辞（CRITICAL/HIGH/MEDIUM/LOW），v3.0 起只有 CRITICAL 阻塞自动化流转。workflow.yaml 的 config_source 指向 bmm 模块配置（{project-root}/_bmad/bmm/config.yaml），说明它设计上作为 bmm 工作流的伴生审查器由 automator 驱动；“自动修复”由调用方的 invocation 决定，非交互模式下不等待菜单。


## 数据口径

本图以**项目本地副本**（`F:/code2/bmad-tool/.claude/skills/<id>/`）为唯一真值来源，因为那是本机上实际生效、可被调用的那份。同名技能的全局副本（`~/.claude/skills/<id>/`）存在版本差异，不作为本次提取依据。

- 技能条目 = `_bmad/_config/skill-manifest.csv` 的 86 条；另有 8 条仅登记在 `bmad-help.csv` 的目录条目（其功能已被实体技能吸收），单独标注。
- `sourceFiles` 全部指向项目本地真实存在的文件，可用 `scripts/check_sources.py` 复验（当前 321 处引用 0 失配）。

## 数据口径与已知差异

- 目录登记 86 条，实际展开 94 条。
- 目录登记条目已全部覆盖。
