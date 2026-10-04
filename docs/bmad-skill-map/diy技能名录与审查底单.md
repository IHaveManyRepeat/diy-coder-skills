# diy 技能审查底单

> 快照 2026-10-03，基数 50（2026-10-03 diy-selfcheck 固化随批补行）。事实源：各 SKILL.md frontmatter + `diy-help/registry.yaml`（守卫：test_help_registry.py）；本文档为派生快照，链序变更后作废重生成。
> 审 = 提示词审查，用 = 实际使用，勾选直接改本文件。★ = required 硬门禁（9）。[] = 链上可选节点。用途一句摘自各技能 description。

## 链序

```
前置  [research] → [product-brief] → [prfaq]（1-analysis，可选，无依赖边，不入链）
      ＋ [brainstorm] / [cis-method]（anytime·line: any，产物可喂 prd）
主线  prd ★ → architecture ★ → [openapi] → [design·双源] → epics-stories ★ → test-design ★
      → sprint ★ → create-story → test-author → dev → review → retrospective
分叉  dev → e2e-tests ｜ review → augment → test-review → test-gate
      ｜ sprint → build-loop（链后执行面）｜ epics-stories → readiness-check ★（链外挂）
WDS   wds-brief ★ → wds-trigger ★ → wds-scenarios ★ → [system] → [assets] → [evolution]
      → dev（WDS 模式）→ review（WDS 路径）
```

双模式三技：design（双源）/ dev / review——审查与使用各跑两遍。

## A 主线（22＋语义前置 2）

| 审 | 用 | 技能 | 用途 | 行 | 依赖 |
| --- | --- | --- | --- | --- | --- |
| ☐ | ☐ | diy-research | 市场/技术/领域三维联网调研，断言带核验来源 | 80 | — |
| ☐ | ☐ | diy-product-brief | 对话式陪跑产出产品简报＋BD 决策日志 | 89 | — |
| ☐ | ☐ | diy-prfaq | Working Backwards 五阶段拷问锻造产品概念 | 81 | — |
| ☐ | ☐ | diy-brainstorm | 多样创意技术主持交互式头脑风暴，结论落 brainstorm.yaml（line: any，产物可喂 prd） | 88 | — |
| ☐ | ☐ | diy-cis-method | 创意方法四选一引导（创新策略/问题求解/设计思维/叙事），落 cis-method.yaml（line: any，产物可喂 prd） | 81 | — |
| ☐ | ☐ | diy-prd ★ | 创建/更新 PRD 单一源，需求 ID 稳定 | 121 | — |
| ☐ | ☐ | diy-architecture ★ | 决策式架构，每条决策链需求 ID＋可测性/运维评审 | 94 | prd |
| ☐ | ☐ | diy-openapi | 从 prd＋architecture 推 OpenAPI 3.1 契约，接口先行评审 | 77 | architecture |
| ☐ | ☐ | diy-design（双源） | 设计单一源（方向/token/逐页四态）＋三段交付至框架代码 | 106 | prd |
| ☐ | ☐ | diy-epics-stories ★ | 从 prd feature 派生 epics/stories，AC 用 given/when/then 引 FR ID | 99 | architecture |
| ☐ | ☐ | diy-readiness-check ★ | 开工前校验 PRD/UX/架构/史诗齐备性，出判定 | 79 | epics-stories |
| ☐ | ☐ | diy-test-design ★ | 故障驱动从 AC 推 test-plan，每用例声明 kill_target | 102 | epics-stories |
| ☐ | ☐ | diy-test-framework | 搭测试框架＋CI 流水线，模板逐字节渲染 | 87 | — |
| ☐ | ☐ | diy-sprint ★ | stories＋test-plan 生成任务状态机（一故事一任务五态） | 97 | test-design |
| ☐ | ☐ | diy-create-story | 为一条故事产实施上下文包（AC/用例/决策/文件现状，按 ID 引用） | 92 | sprint |
| ☐ | ☐ | diy-test-author | test-plan TC 转红相测试脚手架（全 skip＋TC 锚，不执行） | 59 | test-design |
| ☐ | ☐ | diy-dev（双模式） | 严格 TDD 执行任务（红→绿→证据回写）；WDS 逐页过浏览器门 | 88 | create-story, test-author |
| ☐ | ☐ | diy-review（双模式） | 分层审查 L1–L4＋判决路由，通过原子写回送已完成 | 79 | dev |
| ☐ | ☐ | diy-e2e-tests | 对已实现特性生成并实跑 E2E/API 用例，追加进 test-plan | 75 | dev |
| ☐ | ☐ | diy-augment | 编码后按覆盖率补测（含变异杀伤），判定落 sprint.augment | 79 | — |
| ☐ | ☐ | diy-test-review | 32 规则审计测试代码质量＋三向走查覆盖缺口 | 88 | augment |
| ☐ | ☐ | diy-test-gate | AC×TC×证据追溯矩阵＋NFR/合规审计，裁 PASS/CONCERNS/FAIL | 92 | augment |
| ☐ | ☐ | diy-build-loop | 一次调用把任务推到终态（dev 环＋审查＋有界返工，HALT 写回） | 91 | sprint |
| ☐ | ☐ | diy-retrospective | epic 收尾回顾，提炼教训评估成败 | 93 | review |

## B WDS 线（6）

| 审 | 用 | 技能 | 用途 | 行 | 依赖 |
| --- | --- | --- | --- | --- | --- |
| ☐ | ☐ | diy-wds-brief ★ | WDS 入口：分诊→可选对齐签核→战略简报 | 86 | — |
| ☐ | ☐ | diy-wds-trigger ★ | Effect Mapping 工作坊，业务目标映射用户心理触发图 | 89 | wds-brief |
| ☐ | ☐ | diy-wds-scenarios ★ | 触发图→场景大纲＋页面树（SC-<nn>/.P<n>） | 88 | wds-trigger |
| ☐ | ☐ | diy-wds-system | 从页面用法长组件库＋token（建库/导入/预览/编辑/一致性） | 89 | wds-scenarios |
| ☐ | ☐ | diy-wds-assets | 资产工厂：规格＋系统→线框/页面稿/图标/动效/文案/演示，零外部服务 | 89 | wds-scenarios |
| ☐ | ☐ | diy-wds-evolution | 棕地 Kaizen 一轮迭代（分析→范围→设计→实现→验证→交付） | 88 | — |

## C 横向（20，独立可用）

| 审 | 用 | 技能 | 用途 | 行 |
| --- | --- | --- | --- | --- |
| ☐ | ☐ | diy-help | 动态导航：扫产物存在性＋status，给下一个技能/点名卡住文件（先审） | 79 |
| ☐ | ☐ | diy-viewer | YAML 产物渲染人类友好 HTML（C·14 重启将动聚合树） | 42 |
| ☐ | ☐ | diy-tools | 内部确定性 CLI diyc.py，宿主技能共用的检查/写回引擎，非用户直调 | 66 |
| ☐ | ☐ | diy-project-context | 为棕地项目建 AI 语境档＋代理必须遵守的规则 | 76 |
| ☐ | ☐ | diy-eval-runner | 技能评测四模式真跑（baseline/variant/quality/trigger） | 67 |
| ☐ | ☐ | diy-teach-me-testing | 7 节结构化测试课程＋跨会话进度跟踪 | 92 |
| ☐ | ☐ | diy-elicit | 从 69 方法库选 5 个深挖增强当前内容，零写面交还调用方（横切，被多技能挂载） | 73 |
| ☐ | ☐ | diy-party-mode | 动态派生 2-4 视角真子代理圆桌，逐字呈现不合成，零产物（横切，被多技能挂载） | 65 |
| ☐ | ☐ | diy-spec | 任意意图蒸馏成 SPEC 内核机器契约，保真校验 | 84 |
| ☐ | ☐ | diy-spec-scan | 扮演实现者预演规格暴露歧义，只读出中文歧义清单 | 90 |
| ☐ | ☐ | diy-selfcheck | 任务书自检编排者：冻结→三机制扫描→D 表处置→复扫两轮→B 部分机制评价（预演片调 diy-spec-scan，B3 §13 固化） | 55 |
| ☐ | ☐ | diy-editorial-review | 文风＋结构双透镜文稿评审，建议制不代改 | 87 |
| ☐ | ☐ | diy-quick-dev | 故事环外轻量通道：意图→计划→实现→审查→呈现一条 spec 记录 | 92 |
| ☐ | ☐ | diy-investigate | 取证调查：证据分级＋假设不删＋缺失记账 | 93 |
| ☐ | ☐ | diy-checkpoint-preview | LLM 辅助带看变更＋人裁（批准/返工/讨论），只读不改码 | 86 |
| ☐ | ☐ | diy-correct-course | 执行期重大变更导航：影响分析＋old→new 提案 | 90 |
| ☐ | ☐ | diy-analyze | 就一个具体问题分析既有代码库，只记事实不决策（独立入口，不入链） | 78 |
| ☐ | ☐ | diy-reverse | 外部网站/截图逆向成初始 design.yaml＋逐页结构稿（独立入口，不入链） | 83 |
| ☐ | ☐ | diy-bmb-builder | 技能工厂：造/改/评技能，产可安装技能目录树 | 65 |
| ☐ | ☐ | diy-bmb-module | 批次规划器：只规划不造，module-plan＋frontmatter 校验，零写面 | 81 |

## 顺序

help 先行 → 主线按链序（审查与使用同场跑一个真实项目）→ WDS 同法 → 横向插空。

## 审查进度

### 一审（提示词审查）

| 技能 | 状态 | 完成日 | 发现 → 处置 |
| --- | --- | --- | --- |
| diy-help | 完毕 | 2026-10-03 | ①「精准简练」句游离（零产物无适用对象）→ 随母本注入批删；② 逆向线未登记（规则 5 承诺随 B7）→ 随 B7/审查批；③ 结构段 WDS「下游待登记」滞后 → 随逐项化批 0；④ 激活头第 2 行零产物变体（:20「本技能零产物，`document_output_language` 不适用」）——母本 §3 只定义产物技能形态＋变量槽，未定义零产物形态 → 随母本注入批裁定（与①同性质） |
| diy-research | 完毕 | 2026-10-03 | ① 激活头与 diy-help 逐字一致（母本 §1/§3 管辖、测试 12 绿）→ 无动作；② §6「精准简练」＋§2「写作纪律」两块合并（套件级、文案借鉴 caveman 待拟）→ 随母本注入批（待办③条款重组）；核查牵出 diy-selfcheck §1 台账漏网 → 已记待办③封闭世界强制归类 |
| diy-product-brief | 完毕 | 2026-10-03 | 激活头（变量槽 title/problem/solution/pitch/decisions/addendum）＋§6/§2 纪律块与已审技能同构——均在母本 §1/§3/§2/§6 管辖，§6/§2 合并已裁（待办③条款重组）→ 随 YAML 迁移整体收编；另发现 §5 规则段指涉式变体（全库 8 处）→ 已记待办③ discover 预发现样本 |
| diy-prfaq | 完毕 | 2026-10-03 | 激活头（变量槽 问题/回答/引语/叙事/distillate 条目）＋§6/§2 纪律块母本管辖同构 → 随 YAML 迁移整体收编；§5 规则段指涉式变体（:76）属全库 8 处样本之一 → 已记待办③ |
| diy-brainstorm | 完毕 | 2026-10-03 | §1/§2/§3（无槽原形）/§4（有 steps/）/§5/§6 全在场逐字 → 母本管辖同构，无新动作，随 YAML 迁移整体收编 |
| diy-cis-method | 完毕 | 2026-10-04 | 纪律块逐字同构（§6/:79·§2/:81，全库 48 技能同款）→ 随 YAML 迁移整体收编；SKILL.md:73「无下游 ID 消费」字面属实、语义误导（「产物可喂 prd」＋04-design.md:210 概念路由 diy-design 均纯内容喂入）→ 已裁「下游认 ID」判据，prd 前置批＋cis-method→design 两待办段；四分支收尾「交付摘要」句 4 处近似变体 → 母本批预发现样本②，统一与否后面裁断 |

### 二审

| 技能 | 状态 | 完成日 | 发现 → 处置 |
| --- | --- | --- | --- |

## 待办分级总览（2026-10-03）

| 级 | 待办 | 影响面 |
| --- | --- | --- |
| 全库级（旧技能都要改） | 去 `.claude` 路径硬编码（安装器待办·①） | 155 文件近全员 |
| 全库级 | 50 技能正文逐项化 | 50 SKILL.md＋steps/ |
| 新机制 | 安装器向导化（安装器待办·②） | install.py＋diy-coder.yaml |
| 新机制 | 公共句式母本注入（方案 A 已拍板，discover 先行） | discover_texts.py＋sync_texts.py＋suite-texts.yaml＋test 改造 |
| 新机制 | prd 前置机制化（判据：下游认源 ID；brainstorm 细化至条目级三级锚） | registry＋7 技能 frontmatter＋prd 喂入面＋brainstorm.py |
| 单独技能 | cis-method→design 喂入认 ID（判据同 prd 前置） | 04-design.md:210＋diy-design 输入面 |
| 单独技能 | 新增 bug 分析技能（cis-method 问题求解编排·五段产物） | 新技能全套＋衔接 investigate/retrospective/bug-log |
| 单独技能 | 新增 prd→开发前编排工作流 | bmb-module＋bmb-builder 造＋链上各技能交互面 |
| 单独技能 | diy-help 聚合导航·版本演进 | help.py＋SKILL.md＋tests |
| 单独技能 | diy-help 游离「精准简练」句＋§3 零产物变体 | SKILL.md:79/:20，随母本注入批 |
| 单独技能 | diy-lab 实测缺陷修复批（①~⑥ 全定档：①走母本·②重·③root归一·④入本批·⑤检测·⑥轻） | cis-method/brief/research/prfaq/viewer/prd＋各引擎脚本 |

## 待办：prd 前置机制化（攒批，审查出结论后一并处理，现在不动）

裁定（2026-10-03）：语义上可喂 prd 的技能要在**机制上**成为 prd 前置，攒一批一起改，不逐个零改。

判据补充（2026-10-04 用户裁定）：**下游认 ID**——机制化时 prd 喂入须按源稳定 ID 引用，非裸内容喂入。记录级 ID：cis-method `CM-###` / brainstorm `BS-###` / research `RS-###`；单文档型以文档＋条目 ID 为锚（brief `BD-###` / prfaq `PQ-###`）；analyze / project-context 届时核。源侧边界句（例 diy-cis-method SKILL.md:73「本技能无下游 ID 消费」——现况属实）随机制化同步修正，现不动。

判据细化（2026-10-04 用户裁定，diy-lab 实测后）：brainstorm 的下游锚从记录级 `BS-###` 下沉到**条目级三级**——想法 / 主题聚类 / 行动计划都铸稳定 ID。理由：真正影响 prd 的素材单元不可预知（可能取自任一级），下游溯源须精确到素材单元；仅引 `BS-###` 太粗糙。**ID 形态（2026-10-04 已裁）**：前缀 `BI-###`（想法）/ `BT-###`（主题）/ `BA-###`（行动）；文件内**全局唯一**（引用免 `BS-###` 双锚，单写 `BI-008` 自带定位）；ID **取代** `no`（不并存）。改动面：`brainstorm.py`（ID 铸造/唯一性/引用完整性校验；规则 8「想法 no 不铸 ID 免 `--previous`」的豁免面随之重审）＋ SKILL.md 结构段（`ideas[].no`→`id`，`themes[].ideas` / `priorities` 三键 / `actions[].idea` 全部改引 ID）＋ `steps/04-organize.md` ＋ **viewer 展示调整（已裁必动）**（与修复批 ④ 枚举注册同批动）；diy-lab 现存 BS-001 产物随批迁移（代答草稿）。

判据细化②（约束链，2026-10-04 用户裁定登记，diy-lab 实测发现双重断链）：约束语义上必然被下游消费（CM-001「禁做清单随 ADR 立档」、design 守「自写 CSS」类禁做），但现状：① `distillate.constraints`（三源）与 prd `out_of_scope` 均为纯字符串＋内联文本锚，不在 ID 家族；② diy-architecture / diy-design 输入面**零提及** out_of_scope——约束无下游正面摄取通道，只活在「PRD 不得重新提议」负面纪律里。动作：**prd `out_of_scope[]` 铸 `OS-###`**（与 G/U/F/FR/NFR/Q 同族，每条带源锚，ID 链硬契约段扩入 `OS-*`）；**architecture / design 输入面新增摄取声明**——读 prd out_of_scope 按 `OS-###` 引用（architecture 的 ADR 关联禁做项落位、design 守实现类禁做）。**已裁（2026-10-04，重档）**：三源 `distillate.constraints` 条目改 `{text, src}` 结构——src 为独立字段可机械校验（本产物内 ID 须真实在场；跨产物引用如 `CM-001` 的校验规则随批核），brief.py / prfaq.py / research.py 引擎＋三源 SKILL.md 结构段＋steps 联动改；prd 摄取时直接拿结构铸 `OS-###`，零文本解析。依据：distillate 自证为「diy-prd 消费的机器契约」，机器契约内锚须为结构字段而非文本约定。

判据细化③（弱关联根治路径，2026-10-04 用户裁定）：brainstorm / cis-method 喂 prd 的弱关联问题（须点名·其他材料通道·无结构化摄取）**由本批机制化根治**，不单独改注——前置处理完、prd 关联前置的东西之后，「产物可喂 prd」自然成真。落地时底单三处标注同步对齐为本批后的真实通道表述：链序段（:10）＋主表 brainstorm / cis-method 两行（:28/:29）；此前不动。

判据细化④（research 条目级锚，2026-10-04 用户裁定，diy-lab 实测触发）：research 的下游锚从记录级 `RS-###` 下沉条目级——**findings / synthesis.key_points / open_questions 都铸稳定 ID**：`RF-###`（发现）/ `RK-###`（要点）/ `RO-###`（待决），文件内全局唯一（三前缀已查全库零冲突）；executive_summary 与 sources[] 不铸（前者零结构化消费，后者 url 即锚）。**为细化②的地基**：`distillate.{constraints, value_props}` 的 `src` 对 research 源可精确锚到 RF/RK（src 混指 RF/RK 规则与在场校验随批核）；prd 的 Q 溯源经 `RO` 精确到条目。改动面：research.py（ID 铸造/唯一性/校验）＋ SKILL.md 结构段＋ steps（findings 落盘步＋06-synthesis）＋ viewer 展示；diy-lab 现存 RS-001 产物随批迁移。

判据细化⑤（distillate 统一锚模型＋继承条目零复制，2026-10-04 用户裁定）：分界原则＝**提炼有增值→可写文本；零增值搬运→纯引用**。实测 prd out_of_scope 10 条中 8 条与 prfaq constraints 逐字同——映射表的内容搬家违反「不复述上游（引用 ID）」纪律，双源必漂移。三动作：
1. **修正②的 prd 侧形态**：`out_of_scope[]` 改两形态——**继承条目纯引用** `{src: <上游条目/母体锚>}` 不复制文本；仅 **prd 自产**约束铸 `OS-###`＋完整 statement；「PRD 不得重新提议」纪律不变。
2. **三源 distillate 全列表字段条目化 `{text, src}`**（②的 constraints 方案推广到 value_props / open_questions / target_users）：distillate.text 是上游提炼增值，合法；下游再抄 distillate.text 即零增值搬运，禁止。
3. **母体锚补齐**：prfaq 母体锚基本齐（`PQ-###`＋press_release 固定节键＋verdict）；brief 的 `value[]`/`users[]` 无条目锚——补铸（建议 `VD-###`，与①④同构，待裁）或 src 允许结构级段位。
联动：prd 摄取规则（SKILL.md 输入清单表）随两形态重写；viewer 支持继承条目按 src 展开渲染母体文本（与修复批⑧同批核）；diy-lab 产物随批迁移。

| 技能 | 产物 | 现状 | 机制化动作（待裁） |
| --- | --- | --- | --- |
| diy-research | research.yaml | line: mainline / phase: 1-analysis，链上无位 | registry 前置段或链位 |
| diy-product-brief | brief.yaml | 同上 | 同上 |
| diy-prfaq | prfaq.yaml（distillate 段自证为 PRD 输入） | 同上 | 同上 |
| diy-brainstorm | brainstorm.yaml | line: any / anytime | frontmatter 改线或仅挂 registry 前置段 |
| diy-cis-method | cis-method.yaml | line: any / anytime | 同上 |
| diy-analyze | analysis.yaml（棕地现状） | line: any（候选，待裁） | 同上 |
| diy-project-context | project-context.yaml（棕地语境） | line: any（候选，待裁） | 同上 |

约束：frontmatter 六字段与 registry 链序受 test_help_registry.py 双向守卫 + diy-bmb-module 镜像校验，改动须先裁后动（feedback-test-change-ruling-first）。
约束补充（2026-10-04 用户裁定）：**前置＝可选输入通道，非必须完成的门槛**——机制化不得要求前置产物全部在场才准跑 prd；保持 prd 现行语义「上游产物缺席即跳过该源，不因此阻塞」。本批改的是通道注册与 ID 认源，不加任何在场门禁。

## 待办：cis-method→design 喂入认 ID（同判据：下游认源 ID）

登记（2026-10-04 用户裁定）：`diy-cis-method/steps/04-design.md:210` 路由句「要把验证过的概念落成 UI / 接口契约 → `diy-design`」现为纯内容喂入（概念不带 `CM-###`）；机制化时改为 **ID 关联**——diy-design 消费设计思维分支产物须按源 `CM-###` 引用（design.yaml 引用位 / 输入面具体挂法待裁）。与 prd 前置批同判据（下游认 ID），是否同批实施待裁；现不动。

## 待办：新增 bug 分析技能（编排 cis-method 问题求解）

登记（2026-10-04 用户裁定立项；查证无对口技能）：现有面 = diy-investigate（取证调查，止于诊断报告，无机制消灭与经验沉淀）/ cis-method 问题求解（通用 9 步含根因·方案·经验教训，不面向 bug、无代码取证）/ retrospective（epic 级复盘）；BMAD 源 `bmad-analyze-bug` 未迁。

- 规格：调用 diy-cis-method **问题求解分支**分析 bug 成因；产物五段——**表面原因 / 复现办法 / 根本原因 / 机制性消灭根本原因的方案 / 经验教训**。
- 判据（下游认 ID，2026-10-04）：产物铸稳定 ID（如 `BG-###`），喂 `bug-log.yaml` / experience_repo 时按 ID 关联。
- 待裁：技能名与产物文件名；挂法 A（独立 bug 专有产物，cis-method 当方法引擎）vs B（薄模板特化走 cis-method 记录）；与 diy-investigate 分工（代码取证 vs 方法流分析，是否吃 `IV-###`）；phase / line。

## 待办：新增 prd→开发前编排工作流技能

登记（2026-10-04 用户裁定立项；查证底单 50 技能无编排类——test-framework 是 CI 模板、selfcheck 是任务书自检）：编排 prd 之后至 dev 之前的链段（architecture → [openapi] → design → epics-stories → test-design → sprint → create-story → test-author），推进到开发就绪。

- 硬约束（用户 2026-10-04）：**用 diy 已有技能创建机制造**——`diy-bmb-module`（批次规划）＋ `diy-bmb-builder`（技能工厂）——不手搓。
- 判据（下游认 ID）：编排器对各环节的交接按稳定 ID（prd 需求 ID / epics / stories / sprint 任务等）。
- 待裁：可选环节（openapi / design）的处理；推进模式（HALT 检查点 vs 无头续推）；零产物 vs 编排状态文件；与 `diy-build-loop` 交接锚（它管 dev 侧单任务循环，本技能管 dev 前链段）。

## 待办：安装器向导化 + 去 `.claude` 路径硬编码·多工具化（攒批，机制定案后一并改，现在不动）

登记（2026-10-03）：

**① 路径硬编码**：技能文本写死 `{project-root}/.claude/skills/...`（例：diy-analyze 激活第 1 步调 diyc.py resolve）。`.claude` 是 Claude Code 宿主特定约定——换宿主安装根不同，路径全断。
- 影响面：155 个文件（SKILL.md／steps／scripts，50 技能近全员）。
- 机制方向（待裁）：安装根由安装器写进 diy-coder.yaml；技能文本统一改宿主无关口径（复用已有表述「裸 `steps/*.md` 路径从本技能安装目录解析」），脚本调用改读配置或安装根相对解析。

**② 安装器升级（对齐 `npx bmad-method install`）**：现 install.py 三件事=拷贝→首次拷 yaml→冒烟；无交互、硬编码 `.claude/skills`（install.py:24）、yaml 是静态模板非安装答案。BMAD 参照（`_bmad/config.toml` 头注释）：交互问答案+重装记住旧答案作默认。
- 安装时应设通用项：宿主选择（定安装根，②①的接点）／communication_language／document_output_language／output_dir／experience_repo／viewer.auto_open。
- 机制（用户 2026-10-03 拍板）：安装器是设置项**唯一写入口**——yaml 每项在安装器有对应配置；升级新增设置项须同步进安装器（老项目升级时新项给默认并让用户过目）；重装/升级=**读已有 yaml 值作默认 → 逐项让用户确认或改**（不静默保留、不静默覆盖）。不照搬 BMAD 三层治理（单层即可，custom 层 YAGNI）。
- 实施时同步改口径：`README.md:16` 与 `install.py:44` 的「仅首次安装创建，重装不覆盖」→ 新机制描述（现不改——机制未落地前改 README 成假文档）。

约束：改动经 sync.sh 源↔副本两侧同步，md5 须全同；先裁后动。

## 待办：公共句式母本注入机械化（攒批，方案 A 已拍板，实施时一并动）

登记（2026-10-03）：现状=母本（`.analysis/2026-09-16-skill-remediation/suite-texts.md`）+ `test_suite_texts.py` 抓漂移，但**落地是手工逐文件改**——公共条款每加一条要改所有成员技能。旧理由 NFR-4 已证伪（47 技能调 diyc.py，分发单元事实上=整套 skills 目录；详版见讨论结论文档）。

- **方案 A 拍板（2026-10-03，引擎/数据分离）**：`diy-coder/sync_texts.py`（引擎，不随条款变）＋ `diy-coder/suite-texts.yaml`（唯一事实源）。均构建期资产，不随 install 分发；旧 markdown 母本退役（notes 迁 YAML，裁定史在 git history）。
- 单条先行否决（2026-10-03 用户裁定）：不提前单建 suite-texts.yaml——单条先行=新旧双源（正是本方案要消灭的）；YAML 随本批开工整体迁移 §1-§8 时建。
- YAML schema（每片段）：key=片段 ID（YAML/标记对/测试三方共用锚）/ `text`=逐字内联文本 / `members`=必含技能短名（去 diy- 前缀）/ `banned`=必不含（防误插，承测试 C 组）/ `notes`=放置＋禁改面（人读，脚本不消费）。**封闭世界**：members ∪ banned == 全部技能，漏归即红（同 EXPECTED_SKILL_COUNT 型）。
- **标记对即锚**：`<!-- suite:§N begin/end -->`，位置固化在成员文件上、YAML 不存位置（SKILL.md 是自然文档非机器结构，位置规则必碎）。脚本只替换标记对内内容；标记对缺失=显式报错，不静默跳过。
- **调用与回执**：`python diy-coder/sync_texts.py`（同步＋终端摘要）；`--check` 只校验；`--json` 机器回执（逐片段×技能 ok/replaced/missing-marker/banned-violation＋失败原因＋counts＋覆盖缺口）；`--report <path>` 生成**自包含单文件 HTML**（成功/失败/原因/缺口分组，内联 CSS 零依赖，浏览器直开）；退出码非 0=有失败（CI 可用）。
- `test_suite_texts.py` 改造：删自持 frozenset（INSTANCE_MEMBERS/CONVERTED_*/NON_MEMBERS），改为读同一 YAML；头注释 NFR-4 旧理由一并修正。
- **首次落地=AI 插空标记对＋人审位置＋测试兜底**：人只审标记对位置（diff 上下文行），内容逐字一致由测试断言。流程：定稿 YAML → AI 按 notes 逐技能插标记对 → 跑脚本填充 → 跑测试 → 人过目 diff → sync.sh 两份 md5 全同。
- 首批应用：**§9 回复纪律**（精简、名词准确；§6 管产物内容、§9 管回复文字；diy-help「10 行上限」并入）＋**产物精简条款**（并入 §2；中文禁词表/句长上限随批拟呈核）。
- 条款重组：§6「精准简练」并入 §2「写作纪律」（**2026-10-03 用户裁定合并成立**，文案待拟）：§2 成为产物内容＋形式唯一纪律块；新产物精简条款并入同块。文案预计多于两块简单拼接（拼接版仅底稿），**借鉴 caveman 技能写作纪律**（`C:/Users/93559/.claude/skills/caveman/SKILL.md` Rules 段：砍填充词/hedging/客套、短同义词、片段句、箭头表因果、一词够则一词、技术名词/代码/错误串逐字、不发明读者解不开的缩写、`[thing][action][reason]` 句型），与中文禁词表/句长上限一并拟呈核。数据面：两块交集 46；只有 §6 的 4 技能＝build-loop（写产物却无 §2，入块待裁）＋help/tools/viewer（零产物，随批删——与 diy-help 游离句处置合流）。测试面：ANCHOR_PRECISE 并入 §2 断言；§9 措辞「§6 管产物内容」改「§2」。不单技能先行改（锚串断言即红，随母本批整体动）。
- 公共条款处置判据（2026-10-03 两轮讨论定稿）：**保证只来自「必经引擎关卡」**——关卡必经＋自行计算＋显式拒绝不代建（diyc_lib.py:369-376 MISSING_FILE 防呆；init 铸骨架、终门 exit 0 唯一放行）。提示词层只降摩擦不供保证；处置序：能下沉关卡者优先下沉（产物行数/禁词 grep 可断言），无关卡可设的（废话判定/回复风格）承认概率区，靠在场＋抽查。
- 配套下沉项：`diyc.py resolve` 回执扩 `communication_language` / `document_output_language` 两键（diyc_lib.py:198）；母本 §3「读 yaml 自解析」改「跑回执取值」。随本批一并改。
- 封闭世界强制归类（2026-10-03 核查 diy-research↔diy-help 激活头一致性时发现）：`diy-selfcheck` 不在 §1 任何台账（members / converted / non-members 皆缺；现测试无「全部技能必须归类」断言，静默跳过）——其激活头为自declared 变体（「本技能不解析实例目录、不碰 `{output_dir}`」）。YAML 迁移时归 banned（写明理由）或补配，不得再漏。
- 协调：前置=待办②安装根口径（§1 句宿主无关化，避免定稿改两次）；与待办④逐项化同为 50 文件级改动，实施定先后，且逐项化规范加「标记对内内容冻结不改」。
- **discover 先行（2026-10-03 用户拍板，实施序变更）**：建主动普查工具——独立脚本 `discover_texts.py`（与 sync_texts.py 同级构建期资产）——**先普查、再建母本**：普查清单与旧母本 §1-§8 合并裁定后定稿 YAML（避免先迁完又发现新片段改两遍）。
  - 扫描面：50 技能 SKILL.md＋`steps/*.md`；行规范化（去首尾空白）后分组。
  - 排除：纯机器行（命令串/路径/表格分隔符/frontmatter）＋已收编行（首跑靠旧母本文本标注「已管据」，标记对插入后改靠标记对）。
  - 输出两组：**逐字重复组**（阈值 ≥2 技能，已定）＋**近似变体组**（算法已定 2026-10-03：`difflib.SequenceMatcher` 标准库、中文按字符；锚定分组缩比对面——行内机器锚点相同者组内两两比、无锚点纯中文行按行首 6 字；阈值分层 0.95 高/0.80 中/0.75 低＝初值，真实语料首跑按噪声率调（调参=重跑，可迭代）；首版限定含机器锚点行——§1-§8 条款全含锚点、纯中文行噪声高，首跑噪声明朗后再放开）。
  - 近似变体处置流：清单呈核 → 人裁「适合统一/不适合统一」→ 适合者定稿统一文案进 YAML；不适合者进 banned/技能自定并写明理由（spec-scan §2 自定短块先例）。
  - 人工预发现样本（2026-10-03 审 diy-product-brief 时发现）：§5 的**规则段指涉式伴生句**全库 8 处——product-brief / create-story / prfaq / research / investigate / project-context / quick-dev / readiness-check，各措辞微异（照/按…执行/照 Workflow；「打开浏览器／报告路径等待查看／阻塞等待」列举三种粒度），纯漂移型；完整 §5 句（工作流段）41 技能在场、锚串测试绿。统一与否随近似组一并人裁。
  - 人工预发现样本②（2026-10-04 用户发现）：cis-method 四分支收尾**「交付摘要」句** 4 处——`steps/02-innovation.md:265` / `03-problem.md:285` / `04-design.md:209` / `05-story.md:272`，骨架逐字同构「5. 交付摘要：一句话给「…」，附未决问题（无则写「无」）」，仅分支要素串不同（近似变体，锚定「交付摘要」）；`03-problem.md:251` 另有指涉式引用。**与 §9 回复纪律 / diy-help 游离「精准简练」句同精神**——「一句话给」即收尾播报简练纪律的实例化。统一与否随近似组一并人裁；若统一，归 §9（管回复文字）还是分支自定（要素串分支专有）待裁；其他技能收尾播报句（research / brainstorm 等）由 discover 普查覆盖。
  - 保证面：逐字重复组−已收编=空 可作断言；近似组语义判定归人裁（保证=引擎关卡唯一，不变）。

## 待办：50 技能正文逐项化（攒批，待办任务 #1~#8 已建，任务书缓建——与其他攒批合并排期，现在不动）

裁定（2026-10-03）：SKILL.md 正文＋steps/ 厚子文件**全部**逐项化——编号列表、一条一个步骤（最小语义单元）、连续行不空行、机器锚点（ID/枚举值/文件名）逐字保留；四段结构与 frontmatter 不动；行数上限 90 → 250。样例＝diy-help「激活时」10 条版（用户认可）。

- 上限落点：`bmb_builder.py:102` SKILL_MD_MAX_LINES（源/装两份）＋:52/:1438 帮助文本＋bmb-builder SKILL.md:47/:54 范式句；测试面无行数断言；fidelity 报告的 ≤90 为历史留档不改。存量超限 5 技能（prd 121／design 106／test-design 102／epics-stories 99／sprint 97）放宽后一并合规。
- 分批（#1 裁定已完成）：批 0＝上限放宽＋逐项化规范句固化进 bmb-builder P1 范式＋bmb-builder 自身改写（规范载体先自洽）→ 批 1＝prd＋help 样板呈核（须含 steps/ 文件实改）→ 批 2/3/4＝A 主线／B WDS／C 横向铺开（批内并行、逐技能用户过目）→ 每批收尾＝底单补行＋全量测试（基线 1621 绿）＋渲染自证＋sync 同步＋迁移计划登记。
- 协调：与「安装器向导化」①路径硬编码（155 文件近全员）同为全库级文本改动，实施时定先后或并面，避免同一文件改两遍。

约束：开工前建任务书（影子仓 diy-coder/.analysis/）＋diy-spec-scan 自扫＋过用户审核门（任务书立完≠开工授权）。

## 待办：diy-help 多实例聚合导航·版本演进模式（攒批，方案已裁，实施随攒批窗口，现在不动）

裁定（2026-10-03）：

**① 隔离单元＝版本，非功能**（用户拍板）：一个产品不可能一份 PRD 做完，现实按版本演进——一版本含多功能（版本级 prd.yaml 多需求 + epics/stories 按功能分组 + 一个 sprint.yaml 装版本内全部 story），每版本一条完整链住 `{output_dir}/{version}/`（机制上即现行 `--instance` 目录隔离，help.py:186）。按功能拆链否决（架构逐功能复制、漂移无界）。

**② 聚合导航＝A1 改 help.py**（A2 新技能否决——基数 50 是 selfcheck EXPECTED_SKILL_COUNT／底单／逐项化的共同锚点，不为聚合视图新增技能）：
- 触发：不带 `--instance` 且平铺根无链产物、output_dir 下存在含链产物的合规子目录 → 自动聚合（现状此时报「零起点」是误导，变更为纯增强）；显式 `--all-instances` 兜底。
- 实现：枚举合规子目录（INSTANCE_RE，help.py:36）且含链产物，逐个复用 scan_chain／scan_sprint，零新判定逻辑；阻塞项置顶。
- 输出：总览表（版本｜线｜位置｜下一步｜阻塞），`--json` 扩 `instances[]` 数组。
- 影响面：help.py main()＋render_human＋diy-help SKILL.md 工作流段＋对应 tests；registry／其他技能不动；runner 无头侧聚合调度本期不做。

- 配套措辞：diy-prd description 预设「product PRD」产品级单一源——版本模式下每版本一份版本级 prd.yaml，措辞适配（改 description 还是仅用法文档）随本批裁。
- 遗留（记录不阻塞）：版本间共享事实（技术栈／整体分层）在各版本 architecture.yaml 重复、漂移无机制发现——版本模式下属增量演进，暂接受，机制后议。

约束：help.py 测试面先裁后动（本条即裁定记录）；源↔装两份 sync 同步（md5 全同）。

## 待办：diy-help 游离「精准简练」句移除（单独技能级，随母本注入批）

登记（2026-10-03）：`diy-coder/skills/diy-help/SKILL.md:79` 孤行——「**精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。」游离在规则段编号条目之外。

- 不合适原因：diy-help 是**零产物技能**（规则 1「零写回。只读导航」），「写进产物的每条内容」在本技能无适用对象；该句实为产物纪律（母本 §2／新增产物精简条款管辖），不应以单技能孤行变体存在。
- 处置：**母本机制（suite-texts.yaml＋sync_texts.py）重建后随批删**——产物精简条款由母本统一注入真正写产物的技能（diy-help 不在其 members）；不提前单独改（避免同文件改两遍）。

## 待办：diy-help 逆向线登记 + 结构段滞后文本（登记 2026-10-03，审查发现，随 B7/逐项化批处置，现在不动）

登记（2026-10-03，审查 diy-help 时发现）：

**① 逆向线未登记**：SKILL.md 规则 5 已承诺三向分叉（产品/应用 → 主线；官网/营销站 → WDS；分析/迁移现有系统 → 逆向入口「随 B7 登记」），registry.yaml 仅 mainline/wds 两线——逆向场景下 branches 无第三选项。
- 动作：registry 加逆向线（entry/chain 形状待裁：diy-analyze / diy-reverse 均 line: any 独立入口，reverse 产物是否衔接主线链下游待裁）＋ help.py branches 文案 ＋ 相关技能 frontmatter 联动 ＋ test_help_registry.py 测试面。

**② diy-help 结构段滞后**：SKILL.md:52 注释 WDS 线写「（下游待登记）」，registry 已登记 6 节点至 wds-evolution（help.py:8-9 头注释亦全）。
- 动作：结构段 WDS 行对齐 registry，或改指 registry 为唯一源不复制链序（防再漂移）。可随逐项化批 0（help 是样板技能）一并动。

约束：registry 受 test_help_registry.py 双向守卫 + bmb-module 镜像校验；先裁后动。

## 待办：diy-lab 实测缺陷修复批（登记 2026-10-04，部分已定档；C·14 最后处理，本批先于 C·14）

登记（2026-10-04 用户裁定）：来源 = diy-lab 六技能实测（代答模式 agent team 跑 cis-method/brainstorm/research/brief/prfaq/prd，全链终门绿），完整发现见 `D:/mycode/diy-lab/EXPERIMENT-REPORT.md` 与 memory `project-diy-lab-experiment`。同批坐实两条既有判据：下游认源 ID 实测成立（prd 通篇 BS/CM/BD/RS/PQ 锚，自由通道零复制）；三源 distillate 结构化通道、brainstorm/cis-method 走「其他材料」须点名（底单行改注另裁）。

| # | 面 | 缺陷 | 修法（档位） |
| --- | --- | --- | --- |
| ① | cis-method `steps/03-problem.md` | 类目指错：「问题陈述精炼」「是/不是分析」指为`分析`类，库实在`诊断`类，按字面 `--category` 过滤找不到 | 一行改（已裁）。**steps 文本在母本面内**：改走母本机制；母本未落地前不动，须提前则报备直改并纳入 discover 普查面 |
| ② | diy-product-brief / diy-research | distillate 交出面无落点无校验：brief.py＋steps/01~03＋check 全零提（research 06-synthesis 同），按「步骤 Read/Write 唯一权威」执行会产无交出面定稿且门放行 | **重档（已裁）**：brief.py / research.py `check --final` 加 distillate 存在＋五字段非空校验；prfaq steps/05 已有指令，校验对称补否随批核；steps 补 Write 指令与否随批核 |
| ③ | diy-prfaq `prfaq.py` | `check --output-dir` 相对路径按进程 cwd 解析非 project-root（实测误报 MISSING_FILE 指向源码仓；有同名文件时静默校验错文档） | root 归一，照 `--previous` 分支既有先例（已裁） |
| ④ | diy-viewer | brainstorm 61 技术枚举（brain-methods.csv）未注册进值标签表，渲染报 unmapped——零裸键纪律漏网 | **入本批（已裁）**：照 C·11 W3 §5.1 先例逐条取引擎值域注册（采集口径同 R3，中文值同名标签）；测试面枚举断言若动先报备 |
| ⑤ | 各技能引擎脚本 | YAML 重复键静默覆盖（PyYAML 后值覆盖）：实测 cis-method.yaml `open_questions` 重复键丢 3 条、终门未拦 | load 加 duplicate key 检测（已裁）；检测报什么违规码（新码 vs 复用 UNPARSABLE_YAML）随批核 |
| ⑥ | diy-prd | Create 首跑门必失败：终门 PENDING_DECISION 要求全部 Q 有 answer，而映射规则强制追加上游 open_questions——首跑必回退草稿批复一轮，SKILL.md 未提示 | **轻档（已裁）**：SKILL.md 落盘收尾段明示「定稿前逐条批复 Q（含上游继承项）属必经，Create 首跑门回退属预期」；独有流程句非公共句面，直改不涉母本，discover 普查若见近似变体再并 |
| ⑦ | diy-brainstorm | 条目级锚面缺失：想法/主题聚类/行动计划无稳定 ID，下游只能引 `BS-###` 记录级——粒度太粗（素材单元不可预知，可能取自任一级） | 三级铸稳定 ID（已裁）——锚面判据本体，**归 prd 前置机制化批实施**（见该批「判据细化」段）；ID 形态等待裁项见彼处；viewer 展示与本批 ④ 同批动 |
| ⑧ | diy-viewer | cis-method 键标签漏网：四分支 deliverable 键＋`sessions`/`deliverable` 顶层键未注册 `KEY_LABELS`，渲染直出英文键名（实测问题求解分支至少 13 键缺，创新策略/设计思维/叙事三分支待普查）——零裸键纪律漏网，与 ④ 同族 | 补注册四分支全键（键表逐条取自 steps/02~05「本分支结构」节）＋顶层键；键名是 schema 机器锚点，产物保留英文、仅展示层译名（C·11 W3 先例）；随批核：零裸键验收断言面为何未覆盖 cis-method／brainstorm（④ 同问） |

另（实测通过项，不立待办）：安装器 install.py 冒烟过；brief→prfaq→prd 链路 stakes 消歧有效、constraints 被拒项两跳传播完整；editorial-review 嵌套调用走通（调用无标准命令属别扭级，未登）。
