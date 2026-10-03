# BMAD 产物名词与关系（原文对读版）

- 生成：2026-10-03 ｜ 用途：给 BMAD→diy 迁移工程做产物词汇底座；讲解采用「引原文 + 通俗解释」对读格式
- 取材：本机安装的 BMAD 技能原件（`C:/Users/93559/.claude/skills/bmad-*/`）+ `_bmad/_config/bmad-help.csv` 阶段目录 + `docs/bmad-skill-map/BMAD技能全景图.md` 交叉核对
- 口径注意：本机部分技能带本地定制痕迹（如 story 模板含中文注记），文中已标注；引用均为当时安装版原文

---

## 一、总链一览：四阶段产物流水

BMAD 用四个阶段组织全部产物（`bmad-help.csv` 的 phase 列）：

```
阶段1 分析          阶段2 规划         阶段3 方案化                阶段4 实施
─────────────      ─────────────     ──────────────────────     ─────────────────────
调研文档 ──┐
头脑风暴 ──┤
           ├→ Product Brief ─→ PRD ─┬→ UX 设计规范 ──────────┐
PRFAQ ─────┘   （或 PRFAQ 二选一）    │                       ├→ Epics 文档 ─→ 就绪报告
                                     └→ Architecture ─┬→ OpenAPI 契约    │
                                                      └─────────────────┤
                                                                        ↓
                                            sprint-status.yaml ←（读 Epics）
                                                    ↓
                                            Story 文件（逐个建）──→ 编码/审查/回顾
```

一句话：**想法与材料 → 简报 → 需求（PRD）→ 设计与架构 → 拆解（Epics/Stories）→ 排期（sprint）→ 逐故事施工**。

---

## 二、名词逐条（原文对读）

### 1. 调研文档（Research Documents）

> 原文（bmad-help.csv，市场调研行）：*"Market analysis competitive landscape customer needs and trends."*
> （市场分析、竞争格局、客户需求与趋势。）

> 原文（领域/技术调研行）：*"Industry domain deep dive subject matter expertise and terminology."* / *"Technical feasibility architecture options and implementation approaches."*

> 原文（`bmad-market-research/research.template.md`，市场/技术两技能共用同一模板，frontmatter）：*`research_type` / `research_topic` / `research_goals` / `inputDocuments` / `web_research_enabled: true` / `source_verification: true`*；正文仅 *"# Research Report: {{research_type}}... ## Research Overview"*

> 原文（步骤名=节名）：市场 = customer-behavior → pain-points → decisions → competitive；技术 = technical-overview → integration-patterns → architectural-patterns → implementation-research

通俗解释：动手定需求之前攒的三类背景材料——市场调研（谁买、竞品如何）、领域调研（行话与规则）、技术调研（可行性与候选方案）。**名词很弱**：只有文档头元数据（类型/主题/目标）+ 四个分析节名；`source_verification` 只是旗标，来源全部行内引用写在正文里——无逐来源编号、无登记簿、无「哪条断言靠哪条来源」的结构化挂钩，整份 markdown 连记录级 ID 都没有（diy 侧升级见附录 A3）。

### 2. Product Brief（产品简报）

> 原文（`bmad-product-brief/resources/brief-template.md`）：*"This is a flexible guide for the executive product brief... The brief should be 1-2 pages. If it's longer, you're putting too much detail into it — that's what the distillate is for."*

> 原文（模板默认八段）：*"## Executive Summary / ## The Problem / ## The Solution / ## What Makes This Different / ## Who This Serves / ## Success Criteria / ## Scope / ## Vision"*

通俗解释：1-2 页的「高管简报」——这是什么、解决谁的什么痛、凭什么不同、给谁用、怎么算成功、第一版做什么不做什么、成了会变成什么。它是 PRD 的前身输入：先用人话把方向钉死，再展开成完整需求。

> 原文（SKILL.md，与 PRFAQ 二选一的定位）：*"optionally, a token-efficient LLM distillate capturing all the detail for downstream PRD creation"*
> （可选产出一份省 token 的蒸馏摘要，给下游 PRD 创建用——distillate 见附录 A2。）

**与 PRFAQ 怎么挑（原文对读）**：
> 原文（bmad-help.csv，Brief 行）：*"a gentler approach than PRFAQ when you are already sure of your concept and nothing will sway you"*

> 原文（PRFAQ SKILL.md）：*"**This is hardcore mode.** ... stress-tests every claim, challenges vague thinking, and refuses to let weak ideas pass unchallenged"* / *"write the press release announcing the finished product before building it. If you can't write a compelling press release, the product isn't ready."*

一句话：**Brief 是「把想清楚的写清楚」（温和协作、软门）；PRFAQ 是「借写作把没想清楚的想清楚」（硬核压测、强制客户视角+双 FAQ+判决，断言须联网核证）**。概念已定选 Brief；概念没被压测过、要回答「值不值得做」选 PRFAQ。

### 3. PRFAQ（新闻稿式立项挑战）

> 原文（`bmad-prfaq/assets/prfaq-template.md`）：*"Working Backwards guided experience to forge and stress-test your product concept"*（bmad-help.csv 描述）

> 原文（模板结构）：*"# {Headline}... **{City, Date}** — {announce the product...}* → *## Customer FAQ* → *## Internal FAQ* → *## The Verdict: Concept strength assessment — what's forged in steel, what needs more heat, what has cracks in the foundation."*

通俗解释：亚马逊「逆向工作法」——假装产品已经发布，先写新闻稿和最难回答的客户/内部问答，最后给「判决」：概念哪里是钢、哪里还欠火、哪里地基有裂缝。与 Product Brief 二选一，作为 PRD 的替代前身；比 Brief 更严苛，适合概念还没被压测过的场景。

### 4. PRD（Product Requirements Document，产品需求文档）

> 原文（bmad-help.csv）：*"Facilitated PRD workflow — create a new PRD via coached discovery..."*，required=true，phase=2-planning

> 原文（`bmad-create-prd/steps-c/` 步骤文件名序列）：*init → discovery → vision → executive-summary → success → journeys → domain → innovation → project-type → scoping → functional → nonfunctional → polish → complete*

通俗解释：BMAD 的核心需求产物，由引导式对话逐节建出来。v6 安装版的节序是：

| PRD 节 | 步骤文件 | 内容 |
|---|---|---|
| Executive Summary | step-02c | 执行摘要 |
| Success Criteria | step-03 | 成功判据（见 §5 名词） |
| User Journeys | step-04 | 用户旅程（用户类型在这里出现） |
| Domain Requirements | step-05 | 领域/合规要求 |
| Innovation Patterns | step-06 | 创新模式 |
| Project-Type Requirements | step-07 | 项目类型要求 |
| MVP Scope | step-08 | 范围划定（做什么/明说不做什么） |
| Functional Requirements | step-09 | 功能需求 FR（见 §6） |
| Non-Functional Requirements | step-10 | 非功能需求 NFR（见 §7） |

注意：安装版 PRD 模板（`templates/prd-template.md`）只是个空壳，真实结构由上述步骤逐步追加生成。

### 5. Success Criteria（成功判据）

> 原文（step-03-success.md）：*"Define comprehensive success criteria that cover user success, business success, and technical success"* / *"Focus on measurable, specific success criteria"*

通俗解释：回答「怎么算赢」——用户成功（用户何时觉得值）、业务成功、技术成功三层，必须可度量。这就是 diy 侧 `goals[]`（目标+度量）对应的概念源头。

### 6. FR（Functional Requirement，功能需求）

> 原文（step-09-functional.md）：*"FRs define WHAT capabilities the product must have. They are the complete inventory of user-facing and system capabilities that deliver the product vision."*

> 原文（格式）：*"FR#: [Actor] can [capability] [context/constraint if needed]" — "Number sequentially (FR1, FR2, FR3...)" — "Aim for 20-50 FRs for typical projects"*

> 原文（地位，加粗原文）：*"This is THE CAPABILITY CONTRACT for all downstream work"* / *"If a capability is missing from FRs, it will NOT exist in the final product"*

通俗解释：FR 是「谁可以做什么」的能力清单——只说 WHAT 不说 HOW（不写 UI 细节、不写性能数字、不写技术选型）。它被称作下游一切工作的「能力契约」：UX 只为清单里的能力做设计、架构只支撑清单里的能力、拆解只实现清单里的能力；清单外的能力等于不存在。

### 7. NFR（Non-Functional Requirement，非功能需求）

> 原文（step-10-nonfunctional.md）：*"NFRs define HOW WELL the system must perform, not WHAT it must do. They specify quality attributes like performance, security, scalability, etc."*

> 原文（候选类别）：*"Performance / Security / Scalability / Accessibility / Integration / Reliability"*

通俗解释：NFR 管「做得有多好」而不是「做什么」——快不快、安不安全、能不能扩、无障碍、集成、可靠性等质量属性。且是按需取舍：*"We only document NFRs that matter for THIS product"*（只记对这个产品真正要紧的，防需求膨胀）。

### 8. UX Design Specification（UX 设计规范）

> 原文（bmad-help.csv）：*"Guidance through realizing the plan for your UX, strongly recommended if a UI is a primary piece"*，phase=2-planning，preceded-by=bmad-product-brief

> 原文（`bmad-create-ux-design/steps/` 步骤名）：*discovery → core-experience → emotional-response → inspiration → design-system → defining-experience → visual-foundation → design-directions → user-journeys → component-strategy → ux-patterns → responsive-accessibility*

通俗解释：界面为主的产品在 PRD 之后、架构之前产出的体验设计文档——核心体验、情绪响应、设计系统、视觉基础、组件策略、响应式与无障碍等。它是可选产物（strongly recommended，非 required）。

### 9. Architecture（架构决策文档）

> 原文（`bmad-create-architecture/architecture-decision-template.md`）：*"# Architecture Decision Document — This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together."*

> 原文（steps 文件名）：*context → starter → decisions → patterns → structure → validation*

> 原文（step-04-decisions.md 小节名）：*"Core Architectural Decisions / Decision Priority Analysis / Data Architecture / ..."*

通俗解释：不是一次性画架构图，而是把每条技术决策逐条「选了什么、为什么、影响哪些需求」谈出来再落文档——核心决策按优先级排序、含数据架构等分类，外加模式、结构、starter（项目脚手架）。目的（bmad-help.csv）：让 AI 实现者对「项目如何组织」保持一致。

### 10. OpenAPI 契约（openapi.yaml）

> 原文（bmad-help.csv）：*"Generate OpenAPI interface documentation from architecture with iterative user review."*

通俗解释：从架构文档推导出的接口契约（OpenAPI 3.1 格式），多轮评审后定稿。注意：安装版 `bmad-generate-openapi` 的步骤里**没有任何 FR 追溯机制**（生成步骤 grep 不到 FR/traceability 字样）——接口与需求之间在 BMAD 原生流程里没有正式链接。

### 11. Epics 文档（Epic Breakdown）

> 原文（`bmad-create-epics-and-stories/templates/epics-template.md`）：*"This document provides the complete epic and story breakdown for {{project_name}}, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories."*

> 原文（Requirements Inventory 各节）：*"### Functional Requirements {{fr_list}} / ### NonFunctional Requirements {{nfr_list}} / ### Additional Requirements / ### UX Design Requirements / ### FR Coverage Map {{requirements_coverage_map}}"*

> 原文（故事格式）：*"### Story {{N}}.{{M}}: As a {{user_type}}, I want {{capability}}, So that {{value_benefit}}."*

> 原文（验收标准格式）：*"**Given** {{precondition}} **When** {{action}} **Then** {{expected_outcome}} **And** {{additional_criteria}}"*

通俗解释：把 PRD 的 FR/NFR、UX 设计要求、架构要求拆成可实施的故事全集。文档开头先抄录一遍「需求清单」（FR 列表/NFR 列表/追加要求/UX 要求），再放一张 **FR Coverage Map**（FR 覆盖映射表），然后按 Epic → Story 分组展开。这一步同时定义了两个关键名词：

- **Epic**：一组相关故事的大节（Epic 1、Epic 2...），带目标陈述。
- **Story（用户故事）**：`作为〈某类用户〉，我想要〈某种能力〉，以便〈得到某种价值〉`。
- **AC（Acceptance Criteria，验收标准）**：Given/When/Then 三段式（BDD 行为驱动格式）——给定前提、当某动作发生、则应看到某结果。

### 12. Story 文件（单个故事的施工单）

> 原文（`bmad-create-story/template.md`，⚠️ 本文件含本地定制痕迹——中文注记、Interactive States、自动化可行性报告等节为定制扩展）：*"Status: ready-for-dev"* / *"## Story / ## Acceptance Criteria / ## Tasks / Subtasks / ## Test Cases / ## Dev Notes / ## Dev Agent Record"*

> 原文（任务与 AC 的挂钩）：*"- [ ] Task 1 (AC: #)"*

> 原文（测试用例与 AC 的挂钩）：*"**Maps to:** AC#[n], Task #[m]"* / *"**Type:** unit / integration / e2e"*

通俗解释：sprint 排期后、编码前，为「下一个要做的故事」单独立一份文件，装入实现所需的全部上下文：故事陈述、验收标准、任务清单（每个任务标注服务哪条 AC）、测试用例 TC（每条标注映射到哪条 AC、什么类型、能否自动化）、开发备注（架构约束、要动的源码树位置）、以及开发代理的执行记录区。状态从 `ready-for-dev` 起步。

### 13. TC（Test Case，测试用例）

> 原文（story 模板定制版）：*"#### TC-001: ... **Method:** [等价类划分/边界值分析/判定表/场景法] / **Type:** unit / integration / e2e / **Automation:** FULL | SEMI | MANUAL / **AAA:** Arrange / Act / Assert"*

通俗解释：一条可执行的验证——用例编号、映射到哪条 AC、设计方法（等价类/边界值/判定表/场景法）、层级（单元/集成/端到端）、自动化级别（全自动/半自动/纯手工）、AAA 三段（准备-执行-断言）。TEA 模块（Test Architecture Enterprise）还有自己的产物：test design（风险驱动的测试设计）、ATDD 红相位测试、traceability matrix（追溯矩阵）等。

### 14. sprint-status.yaml（冲刺状态表）

> 原文（`bmad-sprint-planning/sprint-status-template.yaml`）：*"Epic Status: backlog / in-progress / done"* / *"Story Status: backlog / ready-for-dev / in-progress / review / done"*

> 原文（WORKFLOW NOTES）：*"Developer typically creates next story ONLY after previous one is 'done' to incorporate learnings"* / *"Dev moves story to 'review', then Dev runs code-review (fresh context, ideally different LLM)"*

通俗解释：把 Epics 文档里全部故事压平成一张带状态的清单（epic-N 一行、每个故事一行），是实施期的唯一进度真相。状态机：backlog（只在 epic 文档里）→ ready-for-dev（story 文件已建）→ in-progress（开发中）→ review（实现完等审）→ done。开发节奏强制串行：上一个故事 done 了才建下一个，好吸收上一个的经验。

### 15. 实施期其余产物（简）

> 原文（bmad-help.csv）：*code review（"adversarial review layers"）/ retrospective（"lessons learned and next epic"）/ QA e2e tests（"automated API and E2E tests"）/ readiness report（"Ensure PRD UX Architecture and Epics Stories are aligned"）*

通俗解释：
- **就绪报告**：进入实施前的四件套对齐检查（PRD/UX/架构/Epics）。
- **代码审查报告**：对故事实现的对抗式分层评审。
- **回顾（Retrospective）**：一个 epic 做完后的经验总结，反哺下一个 epic。
- **QA 测试套件**：为已实现功能补的 API/E2E 自动化测试。

### 16. WDS（Web Design Studio）产物（简）

> 原文（bmad-help.csv wds 段）：*Project Brief → Trigger Mapping（personas + feature-impact-analysis）→ Outline Scenarios（scenario-overview）→ Conceptual Specs（page-specs）→ Functional Components → Visual Design（html-prototypes）→ Design System（components + design-tokens）→ Design Delivery（delivery-package + acceptance-criteria）*

通俗解释：面向 Web 设计的独立模块产物链——产品简报、触发映射（商业目标↔用户心理，产出人物角色）、场景大纲、概念规格（逐页面逐元素的设计决定，开发者直接照它建）、功能组件、视觉设计（HTML 原型）、设计系统（组件库+设计令牌）、交付包（DD yaml + 验收标准）。与主流程的 UX 设计规范是两套并行体系。

---

## 三、关系：谁导致谁产出（逐边引原文）

1. **调研/头脑风暴 → Brief/PRFAQ**：step-03 原文 *"Analyze product brief, research, and brainstorming documents for success criteria already mentioned"*——PRD 各步反复回读这些输入。
2. **Brief/PRFAQ → PRD**：PRD frontmatter 原文 *"inputDocuments: []"*——输入文档登记在文档头；bmad-help.csv 中 bmad-prd 的 preceded-by 即 product-brief。v6 另有 **distillate**（蒸馏摘要）作为交出面：Brief 可选带、PRFAQ 标配（*"A complete PRFAQ document + PRD distillate for downstream pipeline consumption"*）；diy 把它定形为五字段机器契约（附录 A2）。
3. **PRD(FR) → UX 设计**：step-09 原文 *"UX Designer reads FRs → designs interactions for each capability"*。
4. **PRD(FR) → Architecture**：step-09 原文 *"Architect reads FRs → designs systems to support each capability"*。
5. **Architecture → OpenAPI**：bmad-help.csv 原文 *"Generate OpenAPI interface documentation from architecture"*。
6. **PRD + UX + Architecture → Epics 文档**：epics-template 原文 *"decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories"*。
7. **四件套 → 就绪报告 → sprint**：readiness（required）→ sprint-planning（required，读 epics）。
8. **Epics → sprint-status.yaml**：模板注释原文 *"The actual file will be generated with all epics/stories from your epic files"*。
9. **sprint 状态机驱动 story 文件创建**：sprint 模板注释原文 *"Developer typically creates next story ONLY after previous one is 'done'"*。
10. **story 文件 → 编码 → 审查 → 回顾**：dev-story（读 story）→ code review → retrospective → 下一个 epic。

---

## 四、BMAD 原生的追溯边与缺口

原生有的追溯机制（仅两处半）：

1. **FR Coverage Map**（epics 文档内）：FR ↔ Epic/Story 的覆盖映射表——这是 BMAD 唯一正式的「需求→拆解」追溯边。
2. **AC ↔ TC、Task ↔ AC**（story 文件内）：`Maps to: AC#`、`Task 1 (AC: #)`。
3. **inputDocuments**（frontmatter，算半处）：文档头列输入文件名，无结构化内容、无编号、不可反查。

原生**没有**的边（后续裁断的讨论对象）：

- 目标（Success Criteria）→ FR：没有正式链接。
- FR → UX 设计页面 / FR → OpenAPI 端点：没有（OpenAPI 生成步骤无 FR 追溯，已 grep 验证）。
- 需求 → 调研材料（哪条需求来自哪份调研/对话）：没有——材料只在文档头留个文件名。

> 接点说明：以上缺口正是 diy 迁移中「需求编号链」前伸后延的依据，也是 C·14 溯源链批次要讨论的范围；本档只记 BMAD 原状，不作裁断。

---

## 附：diy 体系对应与升级（2026-10-03 补）

> 迁移后对应关系。diy 把 BMAD 的 markdown 散文产物全部升级为 **YAML 单一源 + 编号 + 机械终门**（check --final，exit 0 唯一放行）。

### A1. 上游三产物与编号体系

| BMAD 产物 | diy 技能 | diy 产物 | diy 编号/结构名词（BMAD 没有的） |
|---|---|---|---|
| Product Brief | diy-product-brief | `brief.yaml` | `BD-###` 决策日志（决策/变更/推翻即记）；`addendum`（装不下的进附录带 why_separate）；`ER-###` review_refs；引擎 brief.py |
| PRFAQ | diy-prfaq | `prfaq.yaml` | **无文档级 ID**（单文档产物，靠文件名识别）；唯一内部 ID = `PQ-###`（客户/内部双 FAQ 共用一条序列，问题编号≠需求编号）；`stage: 1-5` 断点续跑锚点；`concept_type`（商业|内部|开源|社区）；引擎 prfaq.py |
| Research 报告 | diy-research | `research.yaml` | 见 A3 |

坑位登记：**`stakes` 同名不同物**——`brief.yaml` 的 `stakes` 是项目侧风险档位（个人兴趣|内部|投资人|公开）；`prfaq.yaml` 的 `essentials.stakes` 是客户侧利害（对客户为何重要、代价与后果）。

**先后与衔接（2026-10-03 补，原文对读）**：Product Brief 在 diy 里仍是 PRD **产生前**的上游产物——方向与 BMAD 相同，交接从「整份文档/可选摘要」升级为结构化交出面。证据链：

> 原文（`diy-product-brief/SKILL.md` frontmatter）：*`phase: 1-analysis` / `required: false` / `outputs: brief.yaml`*
> 原文（`diy-prd/SKILL.md` frontmatter）：*`phase: 2-planning` / `required: true` / `outputs: prd.yaml`*
> （阶段同构 BMAD：分析期出简报、规划期出 PRD；且 Brief **可选**、PRD **必经**——无 Brief 可直做 PRD。）

> 原文（diy-product-brief 规则1）：*「绝不碰 `prd.yaml`、其他产物或源码文件——**简报是 diy-prd 的上游输入，不是它的替代品**」*
> 原文（brief 工作流步骤3）：*「交付并点名路由（diy-prd；其余由 diy-help 分派）」*
> （brief 侧自认上游身份，收尾直接把下一步路由到 diy-prd。）

> 原文（brief.yaml `distillate` 段注释）：*「交出面：交给 diy-prd 的下游契约（字段级映射定义在 diy-prd 侧，本技能只声明交什么）」*
> 原文（diy-prd 输入清单表）：*「product-brief | `{output_dir}/brief.yaml` 的 `distillate` 段 | 按下表字段级映射」*＋*「**摄取规则唯一出处就是本表**；上游技能只负责交出自己的字段」*
> （BMAD 的 inputDocuments+distillate 半结构化交接在此被定形为机器契约；字段映射见 A2。）

> 原文（diy-prd）：*「上游产物缺席即跳过该源，不因此阻塞」*
> 原文（diy-prd `project.strictness` 注释）：*「深度档位，与 brief 的 stakes 同一枚举」*
> （PRD 探索永远从「口述背景 → 利害档位 → 工作模式」起步，Brief 只是可选输入之一——继承 BMAD 里 Brief/PRFAQ/调研多源并列的设计；另有一条隐式传递：brief 的 `stakes` 利害档位以同一枚举落 PRD 的 `strictness`。）

### A2. 上游 → PRD 的唯一通道：distillate 五字段（摄取，不是编号承接）

> 原文（`diy-prd/SKILL.md` 输入清单——摄取规则唯一出处）：brief / prfaq / research 三源的 `distillate` 同一形状：
> *`problem → purpose` / `target_users → users[]` / `value_props → features[] 的能力候选` / `constraints → out_of_scope`（含拒绝项形态「Not \<X\>: because \<Y\>」，PRD 不得重新提议）/ `open_questions → open_questions[]`（追加不覆盖）*

**编号不承接**：PRD 的 G/U/F/FR/NFR 编号由 diy-prd 在 Create 时新铸（FR-1.1 约定编号一旦定下永不改变）；上游编号里 PQ 是 FAQ 问题编号（问题≠需求）、BD 是决策编号，都不映射进 PRD。且 brief/prfaq 均为**单文档产物、无文档级 ID**（靠文件名识别）——与集合形态的 research.yaml（每记录一个 `RS-###`）相对。唯一被裁定可挂进 prd 的上游编号是 **RS**（2026-10-03 用户裁定，C·14 任务书 §0-5：RS-### 进 prd 做关联，其余溯源方向搁置）。

### A3. diy 调研产物名词（research.yaml，BMAD 无对应结构）

> 原文（`diy-research/SKILL.md` 结构节）：
> *`researches: [{id: RS-001, dimension: 市场|技术|领域, topic, goals, scope, date, status: 草稿|已定稿, findings: [{area, claim, sources: [{title, url, accessed}], confidence: 高|中|低}], synthesis: {executive_summary, key_points, open_questions}}]`* + `distillate` + `revisions`

名词表：`RS-###` 调研记录 ID（稳定永不复用）；`dimension` 三维度；`findings[].area` 分析步句柄；`findings[].claim` 断言；`findings[].sources` **逐断言来源数组**（title+url+accessed）——这是 BMAD 行内引用所没有的结构化挂钩；`confidence` 置信档；`synthesis` 单记录综述；`distillate` 跨记录交出面。引用纪律原文：*"每条断言至少一个来源…冲突的来源要摆出来，不许平均掉；无出处的说法不进 findings[]"*。

### A4. prfaq 挂载单元设计分析（2026-10-03 会话讨论，**待裁未定案**）

**问题**：prfaq 是 prd 的前沿产物，其内容要与 prd 的 FR 建立关系；但 prfaq.yaml 无文档级 ID，唯一内部编号 PQ 只覆盖 FAQ 问题（问题≠需求），press_release/essentials 为纯叙述（见 A1/A2 的「编号不承接」）。

**方案方向（用户提法：每个固定部分铸 ID——键位锚与编号链的合流）**：

| 家族 | 数量 | 对应键位（ID↔键冻结映射） |
|---|---|---|
| `ES-1..ES-4` | 4 | essentials.customer / problem / stakes / solution |
| `PR-1..PR-9` | 9 | press_release.headline / subheadline / opening / problem / solution / leader_quote / how_it_works / customer_quote / getting_started |
| `PQ-###` | 既有 | 双 FAQ 条目（internal_faq 是 NFR/out_of_scope 的常见源头） |
| `VD-1`（可选） | 1 | verdict |

**不可挂**：`notes`（过程叙事）、`distillate`（摘要面每次定稿重生成，挂了会漂）、`revisions`。
**粒度定性**：溯源到节、不到句——多条 FR 共指一个 `PR-x` 是常态（`PR-5 solution`/`PR-7 how_it_works` 是 FR 种子最密集处）；要到「每条承诺」级别须另铸主张级编号（PC-### 类）——成本高，本方向不采纳。
**语义注**：`ES-3 stakes` 是客户侧利害，更常作 G（目标）的源头而非 FR 的。

**实现分岔（待裁）**：

| | 甲：隐式覆盖（推荐倾向） | 乙：显式落盘 |
|---|---|---|
| 做法 | prfaq.yaml **零改动**；ID↔键位映射表作为冻结契约（键位本就冻结，ID 即键位的规范名） | schema 改（叙述转列表或平行 id 面），ID 物理在场 |
| 代价 | 违反 diy「ID 物理在场」惯例（grep `PR-7` 在 prfaq.yaml 搜不到） | schema/steps/prfaq.py check/viewer 标签全动；叙述改列表伤可读性 |
| 悬空校验 | viewer 查被引用键位是否在场（旧版缺键=悬空），复用 FR-4.4 | viewer 查 ID 存在性（与 RS 同构） |

**连带理顺（随本方向成立）**：
1. prd 侧挂载键：原拟 `research_refs` 升级为**统一键 `source_refs: [RS-001, PR-7, PQ-012]`**——一个键吃全部材料家族，将来 brief 接入不加键。
2. 挂载层级：G/F/FR/NFR 全层可选挂。
3. brief 侧**不同构、不动**：`users[]`/`value[]` 是列表条目、位次不稳定（会重排），要挂须铸真序列号（BV-### 类）——与 prfaq 冻结键位是两套机制，留待将来。
4. 时序：并入 C·14 溯源面待裁表；C·14 开工仍排 C·13 之后。
