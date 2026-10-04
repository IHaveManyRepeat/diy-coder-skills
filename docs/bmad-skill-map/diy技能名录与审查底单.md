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
| diy-prd | 完毕 | 2026-10-04 | 激活头与已审技能逐字同构、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；diy-lab 实测发现三项：① Create 首跑门必失败（PENDING_DECISION×映射强制追加 open_questions）无提示 → 修复批⑥轻档；② 三源摄取为内容复制——out_of_scope 10 条中 8 条逐字抄 prfaq constraints，违反「不复述上游（引用 ID）」＋out_of_scope 无 ID、architecture/design 输入面零提及无下游通道 → 判据细化②⑤（两形态纯引用＋`OS-###`＋architecture/design 摄取声明）；③ brief/prfaq distillate 高度重叠无去重规则、research problem/value_props 选型形状与定位口径冲突无裁决规则 → 随前置批核 |
| diy-architecture | 完毕 | 2026-10-04 | 激活头逐字同构、纪律块同款在场 → 随 YAML 迁移整体收编；输入面零提及 prd `out_of_scope`（grep 证实）→ 已裁判据细化②（新增按 `OS-###` 摄取＋ADR 关联禁做项）；`affects` 只引 ID 绝不复制需求文本＝下游认 ID 正面样板；`stack[].choice` 被下游按值消费（SKILL.md:56 自证 diy-design 取前端框架 / diy-readiness-check 取脚手架）但无锚——值即锚够用 or 铸 `ST-###`，随判据家族批核 |
| diy-design | 完毕 | 2026-10-04 | 激活头逐字同构、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；三输入面缺陷均已对待办：① 零摄取 prd `out_of_scope` → 判据细化②（按 `OS-###` 守实现类禁做）；② cis-method 概念路由纯内容喂入（04-design.md:210）→ cis-method→design 认 ID 待办段；③ `frontend_framework` 按值消费 `stack[].choice`（B9·SKILL.md:99 逐字取值）→ ST-### 已裁改按 ID 引用；迁移痕迹全族最重（去源路径锚批：13 处＋D12 笔误／D13 幽灵＋dev 仓引用 prototype-loop:12）；object-types「五件」写死 4 处正文 → 升级事项段（使用触发）；WDS 源面（design_status 九值写回／SC 锚／九活动预选）无新发现 |
| diy-epics-stories | 完毕 | 2026-10-04 | 激活头逐字同构、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；ID 锚全在场（`feature_refs: [F-x]`／AC `refs` 引 FR/NFR／`design_ref` 引 P-x，终门机械复核解析）＝下游认 ID 正面样板；① frontmatter `precededBy: [diy-architecture]` 但正文零消费 architecture（硬门只读 prd，`D-*`/`C-*` 零引用，决策到 create-story 层才接入）——补摄取（story 按 `D-*` 认 ID）or 澄清依赖语义（仅链序非输入）→ 待裁；逐项化存量超限（99 行）→ 上限放宽批一并合规 |
| diy-readiness-check | 完毕 | 2026-10-04 | 激活头同构（含预载预算三段变体）、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；§5 指涉式变体（规则 5 指涉工作流静默旁路句）属全库 8 处样本 → 已记母本批预发现；确定性开场＋counts/coverage 照抄 collect 回执＋终门机械＝「保证=引擎关卡」正面样板；ST 待办段已含（输入面按 `ST-###` 取脚手架）；IR-### 自铸稳定、evidence 锚点纪律在场，无新发现 |
| diy-test-design | 完毕 | 2026-10-04 | 激活头同构、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；核心裁定＝「一个 AC 至少一条用例」完备性下限太小 → **五轴矩阵＋FH 落盘**已登专段（dimension/audit/FH 三组规则、kill_target 改引 FH ID、用例量涨 3~5 倍预期）；机械断言密度高（`ac` 悬空 UNKNOWN_ID／`kill_target` 非空／`technique` 枚举终门断言；TC＝AC 去前缀＋序号稳定）＝正面样板；新发现 `stack[].choice` **第三个**按值消费点（:92 静态检查链取技术栈，B9 同款）→ ST 待办段已补登；`kill_target` 纪律双面一致（用例层＋static_checks 层层声明 `kills`）；规格证伪扫与 review 证伪轮分工明确（攻击规格 vs 攻击实现）；自造检查器三条边界消解 TC 循环依赖；逐项化存量超限（102 行） |

### 二审

| 技能 | 状态 | 完成日 | 发现 → 处置 |
| --- | --- | --- | --- |

## 待办分级总览（2026-10-03）

| 级 | 待办 | 影响面 |
| --- | --- | --- |
| 全库级（旧技能都要改） | 去 `.claude` 路径硬编码（安装器待办·①） | 155 文件近全员 |
| 全库级 | 50 技能正文逐项化 | 50 SKILL.md＋steps/ |
| 全库级 | 去源路径锚（正文「源 `X`」180+ 处悬空引用迁 dev-only 台账） | 72 文件（扩口径后更多） |
| 新机制 | 安装器向导化（安装器待办·②） | install.py＋diy-coder.yaml |
| 新机制 | 公共句式母本注入（方案 A 已拍板，discover 先行） | discover_texts.py＋sync_texts.py＋suite-texts.yaml＋test 改造 |
| 新机制 | prd 前置机制化（判据：下游认源 ID；brainstorm 细化至条目级三级锚） | registry＋7 技能 frontmatter＋prd 喂入面＋brainstorm.py |
| 单独技能 | cis-method→design 喂入认 ID（判据同 prd 前置） | 04-design.md:210＋diy-design 输入面 |
| 单独技能 | architecture stack 铸 ST-###（判据同：下游认源 ID；三消费点 design/readiness-check/test-design） | diyc.py＋diy-architecture 结构段＋三消费方输入面 |
| 单独技能 | 新增 bug 分析技能（cis-method 问题求解编排·五段产物·review 自动调用衔接） | 新技能全套＋衔接 investigate/retrospective/bug-log＋diy-review 调用面 |
| 单独技能 | 新增 prd→开发前编排工作流 | bmb-module＋bmb-builder 造＋链上各技能交互面 |
| 单独技能 | diy-help 聚合导航·版本演进 | help.py＋SKILL.md＋tests |
| 单独技能 | diy-help 游离「精准简练」句＋§3 零产物变体 | SKILL.md:79/:20，随母本注入批 |
| 单独技能 | diy-lab 实测缺陷修复批（①~⑥ 全定档：①走母本·②重·③root归一·④入本批·⑤检测·⑥轻） | cis-method/brief/research/prfaq/viewer/prd＋各引擎脚本 |
| 单独技能 | 接口契约通用设计与架构鉴权面（重档·RFC 9457·前后端分离三层联动触发·无鉴权显式留痕·功能tags分组重档） | architecture/openapi SKILL＋diyc 校验面＋viewer＋tests |
| 单独技能 | test-author「未建」滞后表述清理（2 处条件分支；wds-system 三处真未建归去源锚批） | diy-test-framework SKILL＋steps |

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

## 待办：architecture stack 铸 ST-###（同判据：下游认源 ID）

登记（2026-10-04 用户裁定，一审 diy-architecture 牵出）：`stack[].choice` 被 diy-design（取前端框架）/ diy-readiness-check（取脚手架）**按值消费**（diy-architecture SKILL.md:56 自证），值为自由字符串、无锚——技术名写法漂移即断链。机制化（**已裁铸 ID**）：`stack[]` 条目铸稳定 ID **`ST-###`**（文件内全局唯一，前缀已查全库零冲突；`choice`/`why` 保持字段形态）；消费方 diy-design / diy-readiness-check 输入面改按 `ST-###` 引用取值，不再按值匹配。与 prd 前置批 / cis-method→design 同判据（下游认 ID）；是否同批实施随批核。改动面：diyc.py check（architecture 类型加 ST 域校验）＋ diy-architecture SKILL.md 结构段＋ diy-design / diy-readiness-check 输入面＋ viewer 展示。

补登（2026-10-04，一审 diy-test-design 发现）：**第三个按值消费点**——diy-test-design 静态检查链取技术栈（SKILL.md:92「从 `stack[].choice` 里找语言与检查工具链……逐字取技术名」，B9 同款）——消费方清单扩入；改动面同步补 diy-test-design 输入面。

## 待办：新增 bug 分析技能（编排 cis-method 问题求解）

登记（2026-10-04 用户裁定立项；查证无对口技能）：现有面 = diy-investigate（取证调查，止于诊断报告，无机制消灭与经验沉淀）/ cis-method 问题求解（通用 9 步含根因·方案·经验教训，不面向 bug、无代码取证）/ retrospective（epic 级复盘）；BMAD 源 `bmad-analyze-bug` 未迁。

- 规格：调用 diy-cis-method **问题求解分支**分析 bug 成因；产物五段——**表面原因 / 复现办法 / 根本原因 / 机制性消灭根本原因的方案 / 经验教训**。
- 判据（下游认 ID，2026-10-04）：产物铸稳定 ID——**前缀已裁（2026-10-04）：`BUG-A-0xx`**（原示例 `BG-###` 被 diy-wds-trigger 占用、`BA-###` 被 brainstorm 占用，查证后弃）；喂 `bug-log.yaml` / experience_repo 时按 ID 关联。
- 输入面（2026-10-04 用户裁定）：照 diy-test-design:90 同款经验源挖法——experience_repo `taxonomy.yaml` 骨架＋`bugs/<subclass>.yaml` 逐桶全读＋本项目 `bug-log.yaml`；相关性判据同款（`trigger`/`prevention` 能否落在分析对象上）。
- **写面（2026-10-04 用户裁定）：能写输出文件**——① 分析结果经 `bug-add` 入 `bug-log.yaml`（五段→字段映射：表面→`symptom`／复现→`trigger`／根因→`root_cause`／机制消灭→`fix`＋`prevention`；`source` 值域现四值 `开发|审查发现|证伪轮|用户`，扩「bug 分析」类值随批核）——直写非「给命令」（有异于 investigate 零写面先例）；② experience_repo 投影（`bugs/<subclass>.yaml`＋`taxonomy.yaml`）——补 diy 体系零写方缺口（查证：diyc 无投影命令、retro 仅提醒不同步），直写 vs 新引擎命令待裁。
- **衔接机制（2026-10-04 用户裁定）：diy-review 发现真缺陷 → 自动调用本技能**——bug 分析技能做好后，review 经 `bug-add` 入库的真缺陷自动触发本技能生成分析内容（预填 `BUG-0xx` 上下文）＝BMAD 机制 (a) 的 diy 化；调用形态（挂载式内部调用照 elicit/party-mode 先例 vs 收尾路由移交）随批核。
- **BMAD 源阶段参考（2026-10-04，`bmad-analyze-bug`）**：五阶段＝① 信息收集 ② 代码图生成（调用图＋依赖可视化）③ 根因分析（**工作流级＋实现级两层**）④ 修复提案（**双产物**：自动化验证方案＋工作流变更提案）⑤ 完备校验＋归档——报告增量构建（每步 verify 前步＋append 本节，零占位符）。四个可借鉴机制：(a) review 自动衔接——**已裁 diy 化（见上条）**；(b) 代码图阶段（diy 对应物：`diyc trace` 分析面，是否独立阶段待裁）；(c) ④的双产物面——validation plan（防复发测试）与 diy「机制性消灭方案」的测试面交集待定；(d) **⑤引擎自动归档**（源用 `bug-archive.js` 归档 bug registry＋commit＋distribute）——经验库投影「引擎化」的 BMAD 先例，支持写面②选新引擎命令。
- 待裁：技能名与产物文件名；挂法 A（独立 bug 专有产物，cis-method 当方法引擎）vs B（薄模板特化走 cis-method 记录）；与 diy-investigate 分工（代码取证 vs 方法流分析，是否吃 `IV-###`）；BMAD 机制 (b)(c)(d) 取舍；phase / line。

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

## 待办：接口契约通用设计与架构鉴权面（2026-10-04 用户裁定，攒批随既有批次一起处理，现在不动）

登记来源：审 diy-openapi 时用户提出；跨技能双查属实——两技能正式面对 security/鉴权/通用错误结构零提及，BMAD 源均有先例（`bmad-generate-openapi` step-02 `securitySchemes`＋step-03b Error Response Format；`bmad-create-architecture` step-04 Category 2 Authentication & Security），属迁移瘦身丢面。

- **通用状态码（重档已裁）**：`components/responses` 定义通用状态码；**每个 operation 必挂通用错误 `$ref`**——`check --type openapi` 门校验面联动扩，测试面先裁后动。
- **错误结构（已裁）**：统一错误响应 schema 用 **RFC 9457 problem details**。
- **触发机制（已裁，三层联动）**：前后端分离（接口面存在）→ architecture **必答**鉴权类安全决策（触发落点：规则 4 改写 / 评审维度 / 新规则，随批拟）→ openapi **必须**设计 `securitySchemes`＋`security`，引用架构侧 `D-*` 决策 ID（下游认源 ID 判据）。
- **无鉴权显式留痕（已裁）**：鉴权选「无」＝显式决策落盘（照 BMAD `None` 选项先例），不裸奔。
- **功能分组（2026-10-04 已裁，组合＋重档）**：现状按资源平铺、prd `F-x` 零消费（工作流「逐资源推导」；`paths` 无功能维度锚）。裁：① operation **必挂**功能 `tags`（tag 名含锚，`F-x 功能名` 形态）＋顶层 `tags:` 声明——生态工具原生按 tag 分组；② 引擎校验每个 tag 的 `F-x` 须在 prd.yaml 解析到（同 `x-fr` 校验模式）；③ 推导流同改——走查批次单位从资源改**功能**（一功能内全部端点一批走查）；④ 跨功能共享资源**单归属**（归主功能，他功能仅经 `x-fr` 关联）。
- 排期：随攒批一起处理，与逐项化/母本批同面协调先后（两技能均在 50 文件面内，避免同文件改两遍）。

改动面：diy-architecture SKILL.md（触发落点＋评审面）＋ diy-openapi SKILL.md（结构段 `responses`/`securitySchemes`/`tags`＋工作流走查单位＋DRY 规则扩 `components/responses`）＋ diyc_lib.py 校验面（通用错误 `$ref`·`F-x` tag 解析）＋ viewer 展示层词汇＋相关 tests。

## 待办：全库去源路径锚（2026-10-04 用户裁定，专批，现在不动）

登记来源：用户实测——安装后的 diy 体系内 `p-specify.md` 表格引用的 `steps-p/` 9 文件找不到（源在 BMAD wds-4-ux-design，dev 仓 `.claude/skills/` 可解析，1,323 行核对吻合）。裁定：技能文件受众是 AI，正文路径即行为输入——读到即可能去开文件，终端环境（不装 BMAD）读不到 → 轻则空转工具调用，重则困惑后即兴补「源内容」；悬空锚全库清理。

- 方法（已裁·2026-10-04 补）：**逐技能实测**——覆盖技能**全部文本面**（SKILL.md、steps/、data/、templates/、scripts 注释与输出提示等一切随包文本），所写路径逐条实际解析打开，跑不通的统计成清单，针对性修复；实测清单为修复依据。正则普查只作预扫参考：精确口径「源 `含路径串`」180 处/72 文件，抽样 40 条全为注释性溯源、显式读取指令未见——180 是下界，以实测为准（实测天然覆盖无反引号裸路径、「收编自/出处」引导等正则漏网形态）。
- 方案（已裁）：正文去锚自包含——引文/判据值留、路径删；扩查出的显式读取指令改指 diy 自带文件。不随附源文件（第二份源违单一源；AI 回读 BMAD 原文＝迁移改写白做）；不发布时机械剥离（锚多嵌句中，剥不成句）。
- 溯源落点（已裁 dev-only）：行级锚（路径＋行号＋裁定号）集中迁 `docs/bmad-skill-map/` 新台账（文件名落地时定），发布包正文彻底无源路径；dev 仓 BMAD/wds 源文件本体不动。
- 源侧缺陷登记保留条件（已裁·2026-10-04 补）：**正确路径可寻得**（缺陷＝源笔误、文件本体在）→ 错误登记**不保留**；**真幽灵**（正确路径亦不存在）→ 保留「裁/改道」处置事实，源路径细节进 dev-only 台账。实测两例：D12 `object-router.md` 实存于源 `data/object-types/`（笔误，登记可删）；D13 `design-system-router.md` 全库未寻得（幽灵，保留裁的事实）。
- 迁移痕迹零正文（已裁·2026-10-04 补）：裁撤登记/改写说明/净损失登记/归属裁定等**迁移决策记录整块迁 dev-only 台账专门记录，技能正文不留**——不只去路径锚，记录块本身退出正文。技能正文是可执行内容，迁移决策记录属变更台账，载体分离。台账载体可与 迁移计划.md「能力损失台账」合并，落地时定。普查（标记词口径）：真 16 处/14 文件（diy-design 13 处全族＋`diy-dev/steps/wds-accept.md:44` 整节＋`diy-wds-system/data/complexity-router.md:5`；party-mode 2 处系误报——「缺陷台账」指 diy-review 产物非迁移记录）；「收编自/出处/按裁定 N/普查编号」等旁形态随逐技能实测覆盖。
- **dev 仓内部文档引用同属迁移痕迹**（已裁·2026-10-04 补）：`迁移计划.md:行号`、`*-fidelity.md §节`、`docs/bmad-skill-map/` 路径等 dev 私有管理文档引用**不得出现在技能正文**——发布包必无该文件，且行号/章节号随文档漂移，比 BMAD 源锚更不可解析（例：`prototype-loop.md:12` 的「源侧 `迁移计划.md:210`」）。普查：真 4 处/4 文件（`diy-design/steps/prototype-loop.md:12`、`diy-wds-brief/steps/03-signoff.md:144`、`diy-viewer/scripts/viewer.py:666`、`diy-wds-assets/data/presentation-formats/index.md:25`；`c-discuss.md:6` 系「讨论结论」产物字段名误报）。处置同总则：行为事实改写自包含留正文，出处/行号/编号进台账。
- 范围（已裁）：整个技能包。排期（已裁）：专批；与逐项化/母本批协调先后（同为 50 文件级正文改动，避免同文件改两遍）。

改动面：diy-coder/skills 72+ 文件正文＋docs/bmad-skill-map 溯源台账新建＋批尾保真走查（b*/c*-fidelity 惯例）。

## 待办：diy-test-design 五轴矩阵＋故障假设落盘（2026-10-04 用户裁定，攒批，现在不动）

登记来源：用户裁定现行「一个 AC 至少一条用例（五态穷举）」（SKILL.md:89）只是完备性下限、标准太小；提高为五轴矩阵＋故障假设（FH）双向闭合；用例量涨 3~5 倍属预期。

- **五轴矩阵（已裁）**：每条非 `已完成` AC × {正向, 边界, 异常, 安全, 性能} 逐轴审过——适用→≥1 TC，不适用→一行理由登记；**审过≠每轴全用例**（硬铺必造装饰品，违 kill_target 纪律）。适用判据（机械可判）：正向恒适用；边界＝AC 含数值/长度/次数/枚举约束；异常＝含拒绝/失败语义或实现面碰外部资源；安全＝涉及输入解析/跨产物引用/证据声明（锚 :82「伪造证据类」）；性能＝AC 或 nfrs 含时限/量级声明。**性能轴限层**：性能用例 `type∈{集成,端到端}`，单元层不出现。
- **异常轴含环境故障注入子类**（已裁）：文件缺席/依赖回执异常/exit≠0/YAML 损坏——不单独立轴；幂等/重入并进属性测试挖掘提示（不立轴）。
- **落盘 A（已裁）**：TC 加 `dimension`（5 值枚举）；顶层 `dimension_audit` 段（每 AC×5 轴：TC 列表或 not_applicable 理由，二选一）；门判双向一致（audit 列的 TC 须真绑该 AC 且 dimension 对应；TC.dimension 须出现在其 AC 对应轴）。`已完成` 故事整段豁免（同现行 ≥1 TC 豁免口径）。
- **一条用例一个轴（已裁）**：跨轴拆用例（矩阵可判前提，涨量主要来源）。
- **FH 落盘（已裁）**：顶层 `fault_hypotheses` 段，每条 {id: FH-x.y.z, ac, text}；`kill_target` 从自由文本改为引用 FH ID（允许列表＝一杀多）；门判「每条 FH 被 ≥1 TC 杀」（封「列 5 条假设只写 1 条用例」洞）；:90 经验挖掘与相关性判据不动，只是产物落盘。diy-augment / diy-e2e-tests 获 FH 追加权（编码后发现新故障先落 FH 再写 TC）。
- **FH 删除权在用户（已裁·2026-10-04 补）**：AI 不得自行删 FH。杀不掉的 FH 照 coverage_gaps 模式记 `[FH-GAP]` reason、`decision: 待办` 交用户当轮裁决——裁「删」→ 删 FH＋`revisions` 留痕（change 引 FH-x.y.z，revisions 用法自 TC 扩及 FH）；裁「不删」→ **必须补 TC**（无「不杀也不删」第三态）；两出口均删 gap 条目；`--final` 禁 `[FH-GAP]` 待办（复用现有禁令）。
- **「砍掉」处置权统一归用户（已裁·2026-10-04 两轮补）**：SKILL.md 三处同族——① :92 逐对体检两层无净关系→重排或砍；② :92 末无独立 kill 的工具→砍；③ :90 装饰品用例→砍或重新瞄准。三处 AI 均只摆证据交用户裁决，不自行删改产物。
- **Update 迁移**：存量自由文本 kill_target 逐条转 FH 条目；kill_target 不入 ID 稳定门（SKILL.md:98），存量 TC 原样保留可对账。
- 分批：批 1（核心）＝SKILL.md＋diyc_check_docs.py（`tc_declarations` kill_target 改引 ID＋`check_test_plan` 加 dimension/audit/FH 三组规则）＋源↔装两份 sync＋夹具与 9 测试文件 → 全量绿；批 2（下游）＝augment/e2e SKILL.md 补 dimension 写入义务＋viewer.py 渲染两新段（新字段全带中文标签·零裸键）＋author/gate 轻引面核实；批 3（登记）＝底单补行＋教学材料同步（已裁·2026-10-04：curriculum:23/:38 与 quiz:32 三处条目微调至 FH 引用口径，quiz:55 题保留、可加 1 道 FH 门规则新题——不同步则学员按旧口径填自由文字、入门即被 kill_target 引用不可解析拦下）。
- 测试面报备：夹具/测试改动系本裁定直接后果（同源）、git 可逆——按「测试面改动先裁后动」三条件登记。

待裁：无（2026-10-04 全闭合）。

改动面：diy-test-design SKILL.md＋diy-tools/scripts/diyc_check_docs.py（含 `.claude` 装副本）＋tests/diyc_fixture.py＋9 测试文件（test_diyc_check/test_augment/test_e2e/test_author/test_gate/test_test_review/test_story_context/test_retrospective/test_change_proposal）＋diy-augment·diy-e2e-tests SKILL.md＋diy-viewer/scripts/viewer.py＋（执行时核实）diy-test-author·diy-test-gate scripts/steps。

协调：与逐项化/母本/去源路径锚批同为 SKILL.md 正文改动面（test-design 在逐项化超限名单：102 行），实施定先后，避免同文件改两遍。

## 待办：test-author「未建」滞后表述清理（2026-10-04 审 diy-test-framework 发现，随批，现在不动）

登记：diy-test-author 已建成（A 表在列、B3 早已收口），test-framework 两处「未建」条件分支系批次期滞后文本——
- `diy-test-framework/SKILL.md:83` 规则 8「路由与未建技能」：「下游 `diy-test-author` 属 B3 同批（未建成前只在摘要给路由行，不当作可调用技能）」例子过期；修法随批拟（删例子句保留通用纪律「只把已建的 diy 技能当可调用对象」vs 整条改写）。
- `diy-test-framework/steps/06-finish.md:35`：「下一步读 `diy-test-author/SKILL.md`（若已建；未建则以摘要中的路由行交接）」——条件分支删，改直连。

普查分流（全库 grep「未建」5 处/4 文件）：diy-wds-system 三处（SKILL.md:80＋`complexity-router.md:6/:64`）系 `object-types/workflow.md` 真未建的事实登记（非滞后），归「去源路径锚·迁移痕迹零正文」批处置；diy-bmb-module `03-validate.md:29` 是引擎 warning 违规码语义说明（活机制文本），不动。

## 升级事项（可选·不排期·需要才做）

### object-types 参考层类型扩展（2026-10-04 登记）

- 候选：table（用户提出）及 select / checkbox·radio / toggle / modal / tabs / card / badge / progress。
- 事实：机制天然开放——引擎不消费该目录、k-sketch 通配引用、p-specify:28 开放枚举；源侧仅五件（button/heading-text/text-input/image/link），新类型属 diy 自产（按五件同构的规格项清单式）；正文 4 处「五件」写死需同步（SKILL.md:101、p-specify:30/:38、m-design-system:16/:45/:47）。
- 触发：实际使用中遇到该类型对象无参考层可读时再做。
- 若做：随去源路径锚批同文件处理（避免同文件改两遍）；新件不带改写说明头（无源即零迁移痕迹）。
