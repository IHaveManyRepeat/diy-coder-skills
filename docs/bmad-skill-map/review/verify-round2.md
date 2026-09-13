# V2 第二轮验证报告：抽样溯源取证

- 生成时间：2026-09-13
- 执行：w-verify2（第二轮独立验证子代理）
- 校验对象（快照）：`F:/code2/bmad-tool/docs/bmad-skill-map/raw/` 下 7 份模块 JSON + `catalog-baseline.json` + `skill-map.json`
- 基准口径：`catalog-baseline.json` 的 `skillDir`（全部 `location=project`，即 `F:/code2/bmad-tool/.claude/skills/<canonicalId>`）；help 目录以 `F:/code2/bmad-tool/_bmad/_config/bmad-help.csv` 为准
- 方法：逐条打开实体源文件核对（不采信提取物自述）；复算 sourceFiles 存在性；与 CSV 逐字段比对；以防写方式干跑 `scripts/assemble.py`（验证装配行为但不落盘）
- 快照说明：raw 文件时间戳集中在 2026-09-13 10:44–10:55，其中 `module-bmm-b.json` 10:55 被重写、`skill-map.json` 10:53 生成 —— 见问题 D2。本报告只反映该快照，不修改任何产物文件。

## 1. 结论摘要

**不通过。** 核心事实：`module-bmm-b.json` 的 13 个技能步骤与 sourceFiles 取自**全局副本**（`C:/Users/93559/.claude/skills/`）而非基线指定的项目 skillDir，导致 `workflow.md` 幽灵引用与实质内容偏差（dev-story 多出项目里不存在的 RED/GREEN/REFACTOR 步骤）；且已生成的 `skill-map.json` 滞后于 10:55 的源修订，其中的 document-project 行仍是旧的错误版本。一轮报告的三项阻断（assemble 崩溃、3 技能缺失、2 组重复）在当前快照中已分别修复，但引入了 3 条新重复。

| 维度 | 结果 |
|------|------|
| 抽样溯源（23 条，覆盖 7 个模块组） | 属实 18 / 部分属实 4 / 失实 2（create-story、dev-story） |
| TEA 依赖链闭合 | ✓（6 条抽样与 CSV 逐字段一致） |
| WDS idMapping 双向覆盖 | ✓（15 实体 ⇄ 18 目录行全部有去向） |
| 装配可运行性（干跑） | ✓（86/86 覆盖、0 缺失、3 重复） |
| 产物与源同步 | ✗（skill-map.json 陈旧，见 D2） |
| 可选路径标注 | 6/8 已标注，2 条缺失 |
| 命名登记错位 | 32 实体未入目录（14 命名错位 + 18 真未登记）；18 目录行无同名实体（17 语义可映射 + 1 纯残留） |

## 2. 抽样溯源明细表

| # | 技能ID | 模块 | 核对项 | 结论 | 证据 |
|---|--------|------|--------|------|------|
| 1 | bmad-shard-doc | core | menu / steps | 部分属实 | menu `d/m/k` 属实（`SKILL.md:74` "Your choice (d/m/k)"）；提取 `steps=null`，但源文件 `SKILL.md:19-61` 有 Step 1–6 明确执行流 |
| 2 | bmad-brainstorming | core | steps / sourceFiles | 属实 | 提取 8 步；8 个 sourceFiles（含 `workflow.md`、`steps/step-01-session-setup.md` … `step-04-idea-organization.md`）全部存在 |
| 3 | bmad-customize | core | evidenceLevel | 部分属实 | `local-source` 与实际有 `SKILL.md` 一致；但源文件含 Step 1–6，提取 `steps=null`（与 #1 同一模式，core 共 8 例） |
| 4 | bmad-agent-tech-writer | bmm | menu / sourceFiles | 属实 | 提取菜单 `DP/WD/MG/VD/EC` 与 `customize.toml:59/64/69/74/79` 五码一致；6 个 sourceFiles 全部存在 |
| 5 | bmad-document-project | bmm | steps / sourceFiles | 属实（A 版） | 提取 14 步 = `workflows/full-scan-instructions.md` 的 14 个 `<step>`；7 个 sourceFiles 全部存在；menu 4 项为真实交互选项 |
| 6 | bmad-prfaq | bmm | 依赖 / 可选语义 | 部分属实 | notes 记录 manifest 与 CSV 依赖不一致（属实）；但 CSV "alternative to product brief" 语义在产物中完全缺失（见 D6） |
| 7 | bmad-create-story | bmm | steps | **失实** | 提取 8 步含 `3.5 从验收标准生成测试用例`、`3.6 评估测试自动化可行性`；项目 `SKILL.md` 仅 6 步（行 91/248/286/319/341/394），3.5/3.6 仅存在于全局 `C:/Users/93559/.claude/skills/bmad-create-story/workflow.md:271,314` |
| 8 | bmad-dev-story | bmm | steps / sourceFiles | **失实** | 提取 12 步（5–9 为 TDD 模式/RED/GREEN/REFACTOR/路径覆盖 100%）；项目 `SKILL.md` 10 步（行 88–462，step5 为 "Implement task following red-green-refactor cycle"）；RED/GREEN 版仅存在于全局 `workflow.md:307-451`；`sourceFiles` 的 `workflow.md` 在项目目录不存在 |
| 9 | bmad-retrospective | bmm | steps | 部分属实 | 提取 12 步；源文件 `SKILL.md:228` 的 `<step n="0.5" goal="Discover and load project documents">` 未收录（源共 13 步） |
| 10 | bmad-agent-architect | bmm | steps / 重复 | 属实（内容） | 8 步与 SKILL.md 激活序一致；sourceFiles 存在；但与 `module-bmm-missing.json` 重复（见 D3） |
| 11 | bmad-investigate | bmm | steps | 属实 | `module-bmm-missing.json` 版 14 步 = 7 激活步 + Outcome 0–5 + Follow-up，与 SKILL.md 章节一一对应；`module-bmm-b.json` 版只有 13 步（缺 Follow-up） |
| 12 | bmad-agent-dev | bmm | steps / menu | 属实 | 8 步激活序 + 8 项菜单；sourceFiles 存在；同样存在重复问题 |
| 13 | bmad-agent-builder | bmb | menu / sourceFiles | 属实 | 提取 `BA/AA` 与 CSV 行（`bmad-agent-builder | BA/AA | anytime`）一致，entry 明确声明来源为 bmad-help 菜单；`references/build-process.md`、`references/quality-analysis.md` 存在 |
| 14 | bmad-story-automator | automator | steps | 属实 | 10 步与 `steps-c/` 下 10 个文件一一对应（step-01-init … step-04-wrapup） |
| 15 | bmad-tea | tea | menu | 属实 | 提取 10 项与 `customize.toml` 的 10 个 `[[agent.menu]]`（TMT/TD/TF/CI/AT/TA/GATE/RV/NR/TR）一致 |
| 16 | bmad-testarch-test-design → framework → ci | tea | 依赖链 | 属实 | 提取 phase/precededBy/followedBy 与 CSV 逐字段一致：test-design(followed framework) → framework(preceded test-design, followed ci) → ci(preceded framework)，链闭合 |
| 17 | bmad-testarch-atdd / automate / trace | tea | 依赖链 | 属实 | 与 CSV 一致：atdd(preceded `bmad-create-story:create`, followed `bmad-dev-story`) → automate(preceded atdd)；trace(preceded test-review) |
| 18 | bmad-cis-storytelling | cis | steps / menu | 属实 | 10 步；检查点菜单 `a/c/p/y` 与 `SKILL.md:77` 一致 |
| 19 | bmad-cis-agent-storyteller | cis | menu | 属实 | 提取 `ST` 与 `customize.toml:55-56`（`code = "ST"`）一致 |
| 20 | wds-5-agentic-development | wds | menu / steps | 部分属实 | menu `P/D/F/E/A/R/T` 与 `workflow.md:53-59` 一致；但 `steps=null`，而目录下有 `steps-a/d/e/f/p/r/t` 及 7 个 `workflow-*.md` |
| 21 | wds-7-design-system | wds | menu / steps | 属实 | menu `C/I/V/E/B` 与 `workflow.md:53-57` 一致；提取 3 步 |
| 22 | wds-0-alignment-signoff | wds | 可选标注 | 属实 | CSV AS 行 "Skip if building your own product"；实体 summaryZh/notes 含 Skip/可选语义 |
| 23 | bmad-wds-platform-requirements | wds | 目录条目吸收 | 属实 | catalogOnlySkills 记录并入 wds-1 项目简报步骤 27–32，sourceFiles 指向真实 `step-10a-platform-strategy.md` |

## 3. 跨模块一致性问题清单

### D1【阻断】module-bmm-b.json 的 13 条技能取自全局副本，非基线 skillDir
- 13 条：create-story、dev-story、code-review、sprint-planning、sprint-status、correct-course、retrospective、qa-generate-e2e-tests、check-implementation-readiness、create-architecture、create-epics-and-stories、generate-project-context、quick-dev。
- 证据链：
  1. 这 13 条的 `sourceFiles` 均引用 `workflow.md`，该文件在项目目录**不存在**（`ls .claude/skills/bmad-dev-story/` = checklist.md/customize.toml/SKILL.md），而全局副本均有；
  2. create-story 提取含 3.5/3.6 两步，只存在于全局 `workflow.md:271,314`；
  3. dev-story 提取的 5–9 步（TDD/RED/GREEN/REFACTOR/路径覆盖）只存在于全局 `workflow.md:307-451`，项目副本是另一套（implement/tests/validate）；
  4. 同文件内 architect/dev/investigate 三条又用项目式 sourceFiles（SKILL.md/customize.toml）——即**同一文件混用两种来源**。
- 影响：下游 Markdown/HTML 会把项目里不存在的流程展示为"当前安装事实"。

### D2【阻断】skill-map.json 与 raw 源不同步（10:53 生成 vs bmm-b 10:55 重写）
- 现象一：`skill-map.json` 中 `bmad-document-project` 仍是旧的 B 版（16 步、菜单 initial_scan/full_rescan/deep_dive/resume、sourceFiles 含不存在的 `workflow.md`）；当前源中该 ID 只剩 A 版（14 步、菜单 resume/full-rescan/deep-dive/cancel、7 个 sourceFiles 全部存在）。
- 现象二：`stats.duplicates` 仍记录 2 条已不复存在的重复（document-project、tech-writer）。
- 干跑验证（不落盘）：以当前源重跑 assemble 得到 baselineCovered=86、missing=[]、duplicates=3（D3 的 3 条），与盘上 skill-map.json 不一致。

### D3【重要】新增 3 条跨文件重复：module-bmm-b.json vs module-bmm-missing.json
- `bmad-agent-architect` / `bmad-agent-dev` / `bmad-investigate` 在两个文件各出现一次，措辞不同。干跑 assemble 按评分选择 `module-bmm-missing.json` 版。
- 保留建议：**保留 module-bmm-missing.json 版**（investigate 含 Follow-up 步，14 步 vs 13 步；评分也更高），从 `module-bmm-b.json` 删除这 3 条。反之若想以 bmm-b 为准，则从 `scripts/assemble.py` 的 SOURCES 移除 `module-bmm-missing.json`。二选一，避免每次装配产生噪声 duplicates。

### D4【重要】assemble.py 重复记账标签错误
- 定位：`docs/bmad-skill-map/scripts/assemble.py:121-129`。`dupes.append` 在评分比较**之前**执行，标签写死 `kept=当前源 / dropped=既有源`，与实际保留结果可能相反。
- 证据：盘上 `skill-map.json` 的 `stats.duplicates` 声称 tech-writer `kept=module-bmm-b.json`，但同一文件 `modules` 中该行 `_source=module-bmm-a.json`。
- 改法：先做 score 比较、确定胜者后再 append，并写真实 kept/dropped。

### D5 结构口径漂移（装配层已兼容，raw 层不统一）【提示】
- kind 两套：`X 型`（core / bmb-automator / tea-cis / bmm-missing）vs 裸值 `agent/workflow/utility`（bmm-a / bmm-b / wds）；`bmad-party-mode` 为自由文本 `utility 型（多 agent 编排）`。
- steps 键三套：`{name,descZh,optional}` / `{id,titleZh,summaryZh,optional,source}`（bmm-a 110 条）/ `{name,file,descZh}`（core 仅 bmad-brainstorming 8 条）。
- dependencies 两套：dict（core / bmm-b / tea-cis / wds / bmm-missing）vs list（bmm-a 15 条中 9 条非空、bmb-automator 7 条中 6 条非空）。
- sourceFiles 三种路径约定：`.claude/skills/` 前缀 / `<canonicalId>/相对路径` / 裸相对路径。
- 说明：`normalize_kind/normalize_step/normalize_deps` 已在装配时归一，不阻断出图；但 raw 层不统一会让后续维护者误读，建议统一或在文件头 `schemaNotes` 声明。

### D6 TEA 依赖链闭合性：通过
- 抽查 6 条（test-design/framework/ci/atdd/automate/trace）与 CSV 的 phase、preceded-by、followed-by 全部一致，无断链、无循环。

### D7 kind 字段滥用检查：未发现错分类
- 除 D5 的枚举漂移外，未发现 agent/workflow/utility 的实质错标；唯一自由文本 `bmad-party-mode` 的括号说明建议移入 notes。

## 4. 可选路径标注核查结果

关键词扫描 `_bmad/_config/bmad-help.csv` 全文，命中 "Skip / Optional / alternative" 的目录行共 8 条：

| CSV 行 | 关键词原文 | 产物标注 | 结论 |
|--------|-----------|----------|------|
| bmad-prfaq (WB) | "alternative to product brief" | `module-bmm-a.json` 的 entry/summaryZh/notes 均无替代语义 | **✗ 未标注** |
| bmad-retrospective (ER) | "Optional at epic end" | 仅 `dependencies.required=false` 隐含，summaryZh/notes 未说明"epic 结束时可选" | **✗ 未显式标注** |
| bmad-wds-alignment (AS) | "Skip if building your own product" | 实体 `wds-0-alignment-signoff` 标注 ✓ | ✓ |
| bmad-wds-platform-requirements (PR) | "Skip for simple landing pages" | `catalogOnlySkills` summaryZh 标注 ✓ | ✓ |
| bmad-wds-conceptual-sketching (CS) | "Skip for straightforward scenarios" | summaryZh 标注 ✓ | ✓ |
| bmad-wds-storyboarding (SB) | "Skip for simple scenarios" | summaryZh 标注 ✓ | ✓ |
| bmad-wds-functional-components (FI) | "Skip if Design System Mode None" | summaryZh 标注 ✓ | ✓ |
| bmad-wds-design-system (DS) | "Skip if Design System Mode None" | 实体 `wds-7-design-system` 标注 ✓ | ✓ |

WDS 侧 6/6 已标注，缺失的是 BMM 侧 2 条（范围说明：仅关键词扫描，未含"可跳过"的同义改写）。

## 5. 命名登记错位清单（完整列举）

### 5A. 实体存在但 inHelpCatalog=false（32 条）

**A-1 命名错位（目录有语义对应行，字符串不匹配，14 条）**
- WDS 11 条：`wds-agent-saga-analyst`↔bmad-wds-saga(SAGA)、`wds-agent-freya-ux`↔bmad-wds-freya(FREYA)、`wds-0-alignment-signoff`↔bmad-wds-alignment(AS)、`wds-1-project-brief`↔PB、`wds-2-trigger-mapping`↔TM、`wds-3-scenarios`↔bmad-wds-outline-scenarios(OS)、`wds-6-asset-generation`↔bmad-wds-visual-design(VD)、`wds-7-design-system`↔bmad-wds-design-system(DS)、`wds-5-agentic-development`↔bmad-wds-agentic-development(AD)、`wds-8-product-evolution`↔PE，共 10 条 1:1；`wds-4-ux-design` 经 4 条 absorbed 目录行命中。
- BMM 3 条：`bmad-create-prd` / `bmad-edit-prd` / `bmad-validate-prd` ↔ 单条目录行 `bmad-prd`(PRD)，1:N 基数错位。

**A-2 真未登记（目录无任何对应行，18 条）**
- core：`bmad-advanced-elicitation`（1）
- bmm：`bmad-agent-analyst`、`bmad-agent-pm`、`bmad-agent-ux-designer`、`bmad-agent-architect`、`bmad-agent-dev`（5 个 agent）
- tea：`bmad-tea`（agent；其 10 个工作流子技能均已登记）
- bmb：`bmad-eval-runner`（1）
- cis：`bmad-cis-agent-brainstorming-coach`、`-creative-problem-solver`、`-design-thinking-coach`、`-innovation-strategist`、`-presentation-master`、`-storyteller`（6 个 agent）
- wds：`wds-0-project-setup`、`wds-agent-mimir-builder`、`memory`、`sync`（4；后两者为辅助目录，装配层已排除）

不对称观察：同为 agent 型，`bmad-agent-tech-writer` 已登记目录（WD 等 5 行），而上述 5 个 bmm agent 与 6 个 cis agent 均无目录行——登记口径不一致，需裁决"agent 是否入目录"。

### 5B. 目录条目无同名实体（18 条，均为 WDS 的 `bmad-wds-*` 字符串）
- 17 条语义可落位：10 条 1:1 映射到 `wds-*` 实体；7 条无独立实体、功能被吸收（platform-requirements→wds-1；conceptual-sketching、storyboarding、conceptual-specs、design-delivery→wds-4；functional-components、usability-testing→wds-5/7），已在 `module-wds.json` 的 `catalogOnlySkills` 记录去向。
- 1 条纯残留：`bmad-wds-idun`——目录有行、manifest 无、本地无实现。

### 5C. WDS idMapping 完整性：通过
- 15 实体 ⇄ 18 目录行双向核对全部有去向：10 条 1:1 + 7 条 absorbed + 1 条 catalog-only + 4 条 manifest-only（wds-0-project-setup、wds-agent-mimir-builder、memory、sync）。
- 遗留：该映射仅以 `module-wds.json` 的 `idMappingSummary` **自然语言文本**承载，未结构化（机器不可读）；建议落为 `canonicalId ↔ menuCode ↔ matchStatus` 结构化字段供合成与展示使用。

## 6. 必须修复项清单（按严重度排序）

| 级别 | 问题 | 文件 + 定位 | 建议改法 |
|------|------|-------------|----------|
| 阻断 | D1 bmm-b 13 条取自全局副本 | `docs/bmad-skill-map/raw/module-bmm-b.json` 全 13 条（create-story/dev-story/code-review/sprint-planning/sprint-status/correct-course/retrospective/qa-generate-e2e-tests/check-implementation-readiness/create-architecture/create-epics-and-stories/generate-project-context/quick-dev）的 sourceFiles 与 steps | 以基线 `skillDir`（项目副本）重提取：sourceFiles 改为真实文件（SKILL.md/customize.toml/step-*.md 等），steps 按项目副本重算。若团队有意以全局定制版为准，需整体改基线口径并明示，不可混用 |
| 阻断 | D2 skill-map.json 陈旧 | `docs/bmad-skill-map/raw/skill-map.json`（10:53）vs `module-bmm-b.json`（10:55） | raw 冻结后重跑 `scripts/assemble.py`；下游 Markdown/HTML 一律以重跑结果为准 |
| 阻断 | D3 新增 3 条重复 | `module-bmm-b.json` 与 `module-bmm-missing.json` 的 `bmad-agent-architect` / `bmad-agent-dev` / `bmad-investigate` | 保留 `module-bmm-missing.json` 版（investigate 含 Follow-up），从 bmm-b 删除这 3 条 |
| 重要 | D4 重复记账标签错误 | `docs/bmad-skill-map/scripts/assemble.py:121-129` | 先比较 score 再 append，并写真实 kept/dropped |
| 重要 | D5-retrospective 漏步骤 0.5 | `module-bmm-b.json` 的 `bmad-retrospective.steps`（12 条）vs 源 `SKILL.md:228` | 补 `<step n="0.5">` 对应条目（项目/全局副本均有） |
| 重要 | D6-prfaq 未标注可选路径 | `module-bmm-a.json` 的 `bmad-prfaq`（entry/summaryZh/notes） | 补一句"产品简报的替代路径（CSV: alternative to product brief）" |
| 重要 | D6-retrospective 未显式标注可选 | `module-bmm-b.json` 的 `bmad-retrospective`（summaryZh/notes） | 补"epic 结束时可选（CSV: Optional at epic end）" |
| 提示 | D5 结构口径漂移 | 7 个模块 JSON 的 kind/steps/dependencies/sourceFiles | 统一为裸值 kind + `{name,descZh,optional}` + dict deps + 单一路径约定；暂不统一则在文件头 `schemaNotes` 声明 |
| 提示 | core 8 条 utility 丢真实步骤 | `module-core.json`：shard-doc、index-docs、customize、editorial-review-prose、editorial-review-structure、review-adversarial-general、review-edge-case-hunter、advanced-elicitation | 至少补有明确执行流的（如 shard-doc 6 步，`SKILL.md:19-61`）；或统一声明"utility 型不展开" |
| 提示 | wds-5 步骤缺失 | `module-wds.json` 的 `wds-5-agentic-development.steps=null` | 补 steps（对齐 steps-a/d/e/f/p/r/t），或写明"步骤拆分在 7 个 workflow-*.md，未合并" |
| 提示 | WDS idMapping 未结构化 | `module-wds.json` 的 `idMappingSummary`（自然语言） | 增结构化映射字段（canonicalId/menuCode/matchStatus）供机器消费 |
