# diy 技能审查底单

> 快照 2026-10-03，基数 50（2026-10-03 diy-selfcheck 固化随批补行）。事实源：各 SKILL.md frontmatter + `diy-help/registry.yaml`（守卫：test_help_registry.py）；本文档为派生快照，链序变更后作废重生成。
> 审 = 提示词审查，用 = 实际使用，勾选直接改本文件。★ = required 硬门禁（9）。[] = 链上可选节点。用途一句摘自各技能 description。
> 纪律：登记在案 ≠ 开工令——任何待办/发现/批次的动工须用户明示点头（多窗口并行，未点头的开工＝撞车）。

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
| diy-help | 完毕 | 2026-10-03 | ①「精准简练」句游离（零产物无适用对象）→ 已删（2026-10-05 §6 适用面批，test_help 断言同步退役）；② 逆向线未登记（规则 5 承诺随 B7）→ 随 B7/审查批；③ 结构段 WDS「下游待登记」滞后 → 随逐项化批 0；④ 激活头第 2 行零产物变体（:20「本技能零产物，`document_output_language` 不适用」）——母本 §3 只定义产物技能形态＋变量槽，未定义零产物形态 → 随母本注入批裁定（与①同性质） |
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
| diy-test-framework | 完毕 | 2026-10-04 | 激活头同构（含预载预算变体）、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；「未建」滞后两处（:83 规则 8 例子过期＋06-finish.md:35 条件分支，test-author 早已建成）→ 已登待办段（含全库普查分流：wds-system 三处真未建归去源锚批）；模板逐字节渲染＋同模板同 plan 同字节＋CI 对齐重扫不采信台账＝「保证=引擎关卡」正面样板；引用式 `static_check_alignment`（以 order 引用禁抄录命令）＝下游认 ID 正面细节；TF-### 稳定、副作用三档纪律（自动/环境分档/保留确认＋defer-add 入队）完备；行数 87 不超限 |
| diy-sprint | 完毕 | 2026-10-04 | 激活头逐字同构、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；ID 锚全在场（`story` 引 S-x／`test_refs` 引 TC，check --type sprint 机械核对双向）＝正面样板；reconcile 干跑/apply 原子落盘＋「任务纪律只是共享规则的人读表述，门由 reconcile 机械计算」＝「保证=引擎关卡」正面样板；augment 正交字段定义归 diy-augment 唯一出处（此处只引用）＝认源纪律；重开两入口一不变量（清旧 verdict）；五态×TDD 门×零 TC 合法记录口径机制完备，无新发现；逐项化存量超限（97 行） |
| diy-create-story | 完毕 | 2026-10-04 | 激活头同构（含预载预算变体）、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；引用纪律即灵魂（规则 2「跨文档每个事实都是 ID 或路径，绝不转述复制」＝下游认 ID 正面样板）；collect 确定性开场（AC/TC/决策/前序事实一律取回执绝不重读）＋check --final＝引擎关卡正面样板；`decisions: [D-x]`（:63）证实架构决策消费点在本层——为 epics-stories 一审「precededBy 零消费」待裁项补证据（支持澄清链序语义方案）；§5 指涉式变体（规则 7 照 Workflow 句）属全库 8 处样本 → 已记母本批；五轴段已裁本技能 `api_refs` 上下文包提升；行数 92 不超限，无新发现 |
| diy-test-author | 完毕 | 2026-10-04 | 激活头同构（含预载预算变体）、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；零 YAML 写面技能（产物＝测试代码，:43/:54 明写「无渲染步骤、母本 §5 不适用」）——零产物/零 YAML 形态变体又一面（与 diy-help:20 同族）→ 随母本批一并裁定条款注记；TC 锚设计好（每用例上方 `TC:` 锚、C 族 `//` 与 dev `# trace:` 形态区分＝认锚纪律）；author.py audit 终门＋全 skip 交付门＋无待处理 TC 不静默空跑＝引擎关卡正面样板；「消费 TC vs 三者生产 TC（test-design/augment/e2e）」边界完备；五轴段改动面已含（执行时核实 scripts/steps）；行数 59 不超限，无新发现 |
| diy-dev | 完毕 | 2026-10-04 | 激活头同构（含预载预算＋模式判定门禁/零产出变体）、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；TDD 门（test_refs 逐条解析＋双向拒绝＋零 TC 合法口径）＋规则 6 真源回填（`green` 原子双写 sprint evidence＋test-plan 状态·BUG-012 机制化）＋规则 2 先摘 skip 骨架（与 test-author 红相脚手架精确衔接·「激活是 dev 的第一动作不是作者的」）＝引擎关卡正面样板；浏览器门裁定 21 双禁（不静默降级/不无条件硬停）＋副作用①②档分层＋跳过留名不另立键；「门不过不许写待验收（写了=假事实）」＋已移除 `--reason` 必填＋悬空 AC 只读路由＋不代批＝写权边界完备；`# trace:` 双形态（主线 S/AC/TC vs WDS 页ID+态名、C 族 `//`）＝认锚纪律；三处「裁撤与归位（源侧台账）」块（wds-implement:39/wds-accept:44/wds-fix:33）→ 随去源路径锚专批迁 dev-only 台账（§326 已补登 18 处/16 文件）；行数 89 不超限，无其他新发现 |
| diy-e2e-tests | 完毕 | 2026-10-04 | 激活头同构（含预载预算变体）、纪律块 §6/§2 同款在场（:73/:75）→ 随 YAML 迁移整体收编；核心发现＝openapi 契约零关联（全目录零提及 openapi.yaml/operationId/api_refs；`03-generate-api.md:5` 输入面只有「API 实现」、`:30` 契约不清即跳过；augment 同族零提及）→ 已裁四项＋补裁（A＋B 双源·TC 新字段 `api_refs` 复合锚·在场必做/缺席零提及·01 步第三上游产物·augment 并入），专段待执行；BMAD 溯源注记 6 处/4 文件（steps/02:10·03:14·04:10/:15/:17/:29·05:48）→ 归去源路径锚批（旁形态）；「只追加从不建文件/从不改写既有条目」＋record 终门 exit 0 唯一放行＋层轴（api\|e2e）与 `type` 脱钩＝引擎关卡/边界正面样板；行数 75 不超限 |
| diy-augment | 完毕 | 2026-10-04 | 激活头同构、纪律块 §6/§2 同款在场 → 随 YAML 迁移整体收编；核心发现＝变异借位配置（寄生 static_checks＋会话确认、无显式配置面、默认关）→ 已登「变异配置显式化」待办段（`mutation:{enabled,tool?}` 段·默认开日常任务级·任务级/发版级 override·借位条款退役）；`diyc mutate` 沙箱建销＋永不跑在工作区＋score 保守口径（等价体不白送分、裁定唯一落点 gate waivers）＝引擎关卡正面样板；「判定必落」＋「失败只出判定不重开」（重开=用户裁断 runner --reopen-failed）＋证据交接点（evidence 归下一周期 green 写、EVIDENCE_MISSING 是信号非豁免）＝写权边界完备；重跑对账永不重复追加；五轴批 2 与 e2e 认 ID 批已含本技能（dimension 义务＋API 补测锚定）；行数 79 不超限 |
| diy-test-review | 完毕 | 2026-10-05 | 激活头同构（含预载预算变体）、纪律块 §6/§2 同款在场（:86/:88）→ 随 YAML 迁移整体收编；账本引擎唯一权威（severity/维度分/recommendation 全复算·LLM 只判命中·手写数字被 check 打回）＋convention 三类门（新现降一档 floor LOW·缺失/未知不成立·class 与 baseline 对表独立复测）＋「匹配不到任何规则的 100 不是 100」（excluded 不评分＋全空 scope 走拒绝零产出）＝引擎关卡正面样板；空/极简文件 R-3（空→excluded·零断言→C4「No meaningful tests」）＋pact 附加上报 R-4（无行缺陷走 recommendations 散文·配置不可验证 L4 记账给两出路）＝表外情形完备；walkthrough 委派不重写（diyc trace/check·rc∈{0,1} 正常·异常降级不阻塞）＋SET_MISMATCH 跨目录护栏＋全量零 trace 整类跳过；四命令 --output-dir 全 required（永不默认）＋check --final exit 0 唯一放行＋机械项可扩不可缩（误报丢弃须摘要说明）＝写权边界完备；与 diy-review/diy-test-gate 边界规则 1 单侧声明（家族惯例不立案）；BMAD 溯源注记归去源路径锚批（旁形态：criteria.yaml 头部迁移裁定注释块＋`source:` 键＋steps 泛指 3 处 02:10·03:24/:33——数据资产非 SKILL 正文，处置面随批核）；引擎测试 33 绿＋中央契约 test_suite_texts 在场；行数 88 不超限，无其他新发现 |
| diy-test-gate | 完毕 | 2026-10-05 | 激活头同构（含预载预算变体；无 scope 问询变体——scope 即 story 定位）、纪律块 §6/§2 同款在场（:90/:92）→ 随 YAML 迁移整体收编；引擎关卡正面样板：覆盖数字/totals/by_level/overall_risk/adr.rows 全引擎重算对账（SET_MISMATCH/CRITERION_STALE）＋decision 规则树 check 重算（DECISION_INCONSISTENT）＋拒绝 exit 1 零产出（拒绝永不成为门记录）＋HALT 无「无法评估」档（半份记录比没有更坏）；阈值禁猜（THRESHOLD_UNSOURCED/UNKNOWN_THRESHOLD_PASS·source 只认用户会话）＋豁免只由人开（8 键契约·安全域不可豁免·`mutant:` 须命中候选集防假豁免）＋变异裁定分重算（批准即出分母取代保守分·与 augment「裁定唯一落点 gate waivers」契约互认）＝写权边界完备；四条走查义务全有机械落点与违规码（EVIDENCE_STALE>7 天二选一不许静默/合规五行聚合 FAIL>PARTIAL>PASS/CROSS_DOMAIN_UNRECORDED/duplicates 逐条判定——「静默丢弃=伪造绿灯」×3 处明文）；duplicates 口径收窄可读数据面＋盲区只读产物不读源码（与 test-review walkthrough 分工明确）；无 P1 记 100% 口径＋无台账通过的合法来源三分（e2e/augment 合法·dev 异常须查）；47 测试绿（含 SKILL 契约冒烟）；发现两项：dev 仓引用 6 处/4 文件（迁移计划 §十三:459×4·§二验收×1·SKILL.md:67 裸节号——原普查 4 处漏网，已补登）＋06-finish:33 viewer 滞后句（「通用降级渲染·标签缺口」——C·2 2026-09-21 已补齐 test-gate 标签，已登清理批）；BMAD 溯源注记旁形态（adr-checklist.yaml :3/:4/:39 路径与源注＋steps 源泛指约 8 处）归去源锚批；行数 92 不超限（上限 250） |
| diy-retrospective | 完毕 | 2026-10-05 | 激活头同构（含预载预算变体＋collect 确定性开场变体）、纪律块 §6/§2 同款在场（:91/:93）→ 随 YAML 迁移整体收编；引擎关卡正面样板：collect 门禁 exit 1 零产出（拒绝永不变成记录）＋metrics 照抄回执（SET_MISMATCH 与 collect 同函数互证·绝不重读 sprint 重推）＋check --final exit 0 唯一放行（零 [假设]/readiness 五键非空/零带 owner 行动项＝门失败/引用全可解析）；「一个 epic 一条记录」不变量（partial 补做原地更新·revisions 追加·无 --previous 轮）＝台账纪律；写权边界：只写 retrospective.yaml，需改上游才能落地的结论一律 significant_changes＋owning skill 名落 recommended_action（不新增字段）＝「上游不动、不代写」；交接契约**双侧互认**（correct-course SKILL:28 明文收 retro 整批一条 proposal·impacts[]＋trigger 记 RT id——罕见双边合同）；锚定纪律：每断言可溯源（ID 锚或 user-read 标记·不加 [假设] 前缀）＋不追责（系统视角）＋全文零工期估计（轮次计数做速度代理）；pattern ≥2 故事门槛＋归并先 route 分桶再语义细分＋「零 pattern 合法不注水」；就绪度五维「问不假设·不许乐观缺省·两头都不落的担忧不算担忧·一切正常是有效结论」；交互点显式列举（第 1/4/6 步）＝Front-load 例外纪律；路由分界精确（缺用例按任务态分 test-design/augment——augment 硬门只收已完成任务即分界线；账本不对先 diyc check 定位再按归属路由）；27 测试绿含 SKILL 契约冒烟（薄主文件 ≤93 行断言在测）；BMAD 溯源注记旁形态归去源锚批（泛指「源技能/源 step-N」最重一族：7 个 steps 全带＋引擎头注约 20 处/8 文件·无路径锚）；行数 93 不超限（自测断言线），无其他新发现 |
| diy-build-loop | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋TDD 门继承 dev 模式判定/零产出变体）、纪律块 §6 在场（:91）；§2 缺席＝写产物却无 §2——待办③既有登记（入块待裁）非新发现；零 steps/零自有脚本＝「只编排不复制」极简形态（dev/review 纪律按名引用＋diyc transition/green/done/static 命令面）；HALT 协议＝每次迁移即时写回＋done 原子批次三面真源回填（BUG-012 机制化·sprint＋stories＋test-plan＋bump updated；已阻塞不写真源——故事未交付什么也不算通过）＝引擎关卡正面样板；轮次封顶 2 跨运行续算不重置＋幂等恢复（中断盘上即真实状态）＋歧义转已阻塞点名理由绝不空转＋自动模式不跑证伪轮＋调度归 runner（本技能绝不挑任务·post 三连 e2e→test-review→test-gate 落草稿待人核）＝无头纪律完备；渲染尽力而为永不阻断终态写；test_runner 121 绿覆盖 runner 面；零源锚零 dev 引用（全库罕见干净）——唯任务书编号旁形态 4 处（AC-9.1/AC-9.2/FR-3.6/R-4·FR-4.5/D-9 属全族激活头模板句归母本批）归去源锚批普查（含口径补记：同族 R-3/R-4 等先例散见 test-review/test-gate，一审时未单列）；行数 91 不超限，无其他新发现 |
| diy-viewer | 完毕 | 2026-10-05 | 薄启动器两段式变体（运行＋规则·无激活头模板——零产物形态条款注记随母本批，同 diy-help:20 族）；§6 已删（2026-10-05 §6 适用面批）、§2 无（零产物族——待办③ help/tools/viewer 随批删范围）；规则面完备：PyYAML 缺失报错不静默回落＋空目录点名扫描目录不编造＋`--open` 仅用户显式/`--no-open` 一票否决＋自动化/无头静默旁路不报路径＋外壳固定中文设计句（document_output_language 管源产物不管 viewer 外壳）＝边界自律正面；零裸键纪律由 test_viewer_labels 断言守卫（121 绿含 open/robust/runner）；实例形态同命令行加 `--instance` 绝不静默回落主线（调用方义务条款在场）；发现：viewer.py dev 引用 +2（:669 迁移计划 §已定补充·:165 §五 C·8 裸节号——原普查仅记 :666）＋`# trace:`/批次码出处注约 70 处（旁形态·处置面随批核）→ 已补登普查至真 12 处/8 文件；底单主表 42→41 系今日 §6 删除后快照漂移（快照性质·不单独立案）；行数 41 不超限，无其他新发现 |
| diy-tools | 完毕 | 2026-10-05 | 内部工具封皮形态（调用/命令表/独立脚本/回执/规则五段——非用户直调、无激活头，形态正确）；命令面 14 子命令完备（resolve／check×9 类型／trace／static／mutate 沙箱／transition／green／done／bug-add／defer-add／defer-set／reconcile／baseline-add）＝「全部规则活在脚本里·提示词只声明命令面」正面样板；mutate 沙箱不解析工具输出（rc＋output_tail 原样回执·解释归 augment＝职责分工）＋transition 拒绝 `待审查→已完成`（唯一入口 done）＋defer-set 单向终态 ILLEGAL_TRANSITION＝状态机纪律；基线台账四护（DUPLICATE／INVALID／STALE 只减不增／降级只在判定层·明细照旧呈现观察事实）＋「baseline-add 唯一写入者·用户拍板才入册」＋`--strict` 忽略台账供 CI＝欠债管理正面样板；INTERNAL_ERROR 兜底（回执形状完好·绝不静默留空·不残留 .tmp）；232 测试绿（check/cli/lib/writeback/mutate/baseline/exp-sync）；发现两项：§6 在场（:66）＝零产物技能带精准简练——**用户点名记全库级待办**（今日适用面批已删 viewer/help/elicit/party-mode，余本技能）；dev 引用 +4 处/2 文件（diyc_mutate.py:2·diyc_writeback.py:67/:563/:629）→ 普查补登至真 16 处/10 文件，另 SKILL.md:31 `C·9` 批次码 1 处归普查编号旁形态；行数 66 不超限 |
| diy-project-context | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋模式判定三选项变体：重扫/深挖/Cancel）、纪律块 §6/§2 同款在场（:74/:76）→ 随 YAML 迁移整体收编；单文件产物纪律（绝不产 markdown 文档集/零散状态文件）＋边界声明（只记录既有事实·prd/architecture 读它当棕地输入）＝正面样板；重写纪律闭环＝`.prev` 快照＋`check --previous` 抓 ID_UNSTABLE（静默丢规则）＋通过才删——重扫/深挖两模式的 PC-### 保护门；「人确认后的 part 清单是权威」（引擎未解析交用户·绝不发明·version 留空 notes 注明人确认）＝人机分工正面；规则准入「不显然细节」检验（称职代理不被告知会做错吗）＋缺省从简（长度即成本）；`[假设]` 前缀只写值不新增键·headless 转 open_questions 不删不猜·引擎递归全扫 ASSUMPTION_PRESENT；深挖逐文件实读禁抽样·读不了的点名记未读不静默丢；条件扫描按部件类型折叠＋三档读面纪律（快速不读源/深入 critical_dirs/穷尽排排除清单）；elicit/party-mode 挂载点（03:39 深拷问承接·不改规则形状）＝横向技能挂载先例；scan 确定性只读（MANIFEST_UNPARSED＝拒绝猜测交人裁）＋check --final exit 0 唯一放行（--output-dir 必填）；23 测试绿；零源锚零 dev 引用（唯 FR-4.5/D-9 全族模板句）；行数 76 不超限，无新发现 |
| diy-eval-runner | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋硬门四条件零产出变体）、纪律块 §6/§2 同款在场（:65/:67）→ 随 YAML 迁移整体收编；**零 YAML 主产物**形态（run 目录全 JSON）→ 零渲染条款（:61 母本 §5 不适用——与 test-author 零渲染变体同族但更彻底）＋viewer 零集成自洽；**反自欺硬规则两条**＝trigger 只认 `tool_use`（init 事件列技能名会令子串匹配恒 100%——作弊机理写成规则·`load_signal` 子串式直接拒跑）＋grader 三纪律（不给部分分/举证责任在通过方/反向批评 rubric）＝评测诚实面正面样板；清场环境契约（子进程环境从零构建绝不继承·空 HOME·`auth_env` 仅宿主非空才传——传空串毁凭据回落的坑写明）；run 目录永不删除覆盖轮转＋同名未完成 run 只提示不续跑＋追加式无定稿态（无 `--final`——形态正确：评测产物无定稿语义）；降级两路不入队（确认是当场决策·队列语义归 defer-add——与 diy-tools 分工精确）；`aggregate` 贝塞尔校正＋`--self-test` 固定夹具验公式＋「均值是信号不是结论·方差大先加 runs」；「打不过裸模型就该退休不是打补丁」决策路由＋自改进 opt-in 先问用户；边界四对（vs test-review/test-gate/review/runner.py）；22 测试绿＋中央契约在场；零源锚零 dev 引用（唯 FR-4.5/D-9 模板句）；行数 67 不超限，无新发现 |
| diy-teach-me-testing | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`status` 五分支唯一入口表变体·与回执 `entry_step` 同源）、纪律块 §6/§2 同款在场（:90/:92）→ 随 YAML 迁移整体收编；Hub-and-spoke 形态（任何节入口都在 Hub·不直接跳节·中断恢复先进 Hub）；定义态/运行态分离（curriculum.yaml 定义态唯一源 vs learning-progress.yaml 运行态·整数 session id 对齐）＝正面样板；引擎关卡：派生三键禁手写（SET_MISMATCH）＋单一写通道（init/update/check·手改 YAML 连带触派生字段）＋损坏恢复走 `init --recover`（引擎备份再重建·禁手改）＋check --final exit 0 唯一放行；quiz 70 分线数值边界写明（`round(答对*100/3)`·2/3=67 未达线·未达停下让用户选 R/C 不自动通过）；学员隔离（一个 output_dir 一份·多学员靠实例机制）；教学纪律不夹带源平台品牌字样与外部 URL＋引用 ID 禁复制＝去品牌/引用纪律；notes md 不进渲染面（viewer 只扫 `*.yaml`·notes 字段唯一引用点·不得增交互点）；无 `--previous`（幂等 upsert 无收缩面）；29 测试绿＋viewer learning-progress 专项＋中央契约在场；旁形态归去源锚批（curriculum.yaml 头部迁移裁定注释块＋逐行「源: 英文名」留档注——数据资产面；SKILL.md:88 B3 批次码＋:87「源纪律」泛指）；行数 92 不超限，无其他新发现 |
| diy-analyze | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋list 六字段续接三选项变体＋门禁「代码库可读」零产出变体）、纪律块 §6/§2 同款在场（:76/:78）→ 随 YAML 迁移整体收编；「只记现状不做决策」＋**边界六对**（vs architecture 方向相反决策式/文献式·vs 用户级 arch-analyze 边界句在激活段·vs spec-scan 扫文本/扫结构·vs project-context 语境档/单问·vs investigate 缺陷取证/架构取证·vs elicit/party-mode 是调用非竞争）＝边界最密技能之一；检查点四选项六拍纪律（[a]elicit/[p]party-mode 零写面返回重落盘/[c]进/[y]跳选项；无头全程 [y] 明示·**不入 deferred-actions 队列**）＝交互点显式族；`AN-<nn>` ID 体系（init 铸骨架·引擎核唯一性与顺序性·重号/跳号/非法各判违规）；取证纪律 `已核实|待核实`——绝不把推断写成事实＋规则 10 不可机械部分写明（定级排序人工·引擎只核枚举必填顺序）＝诚实分工正面样板；内容型产物写权归会话（question/architecture/四清单直编）·骨架与校验归引擎＝写权分工变体；终门 check --final exit 0 唯一放行＋不得改用 diyc check --type（主线 8 型封闭集）＋零新增违规码（复用冻结集）；Mermaid 住字符串字段不落散文件·定稿前至少一张；只增不减无 --previous；26 测试绿＋viewer analysis 专项在场；零源锚零 dev 引用（唯 FR-4.5/D-9 模板句）；行数 78 不超限，无新发现 |
| diy-elicit | 完毕 | 2026-10-05 | 激活头同构（含三档定位变体＋硬门「对象 ≥1 句」零产出）＋**无 steps 变体**（:31 母本 §4「无 steps 永久不适用」分支——源即单文件短流程，又一形态变体）；§6 已删（2026-10-05 适用面批·零产物族）·§2 在场（:72）；**零产物零写面**＝交还块唯一交付形态·落盘归产物持有者（`revisions` 由持有者记）＋**无终门**（无产物可校验·引擎只读 methods/--random/--category/--all·ENUM_INVALID）——形态正确；菜单交互纪律（每次执行后重现同一菜单·应用必问 y/n·仅 y 接受·换对象先交还再重开）；智能选 5 主体是 LLM 非引擎（`--random 5` 是抽样兜底面）；方法库 methods.csv 69 方法/12 类数据资产（引擎读不预读全文）；多视角方法立场与 party-mode 视角制同源；边界三对（vs editorial-review 建议制/就地增强·party-mode·brainstorm 深挖入口调用本技能）；被多技能挂载先例（project-context 03:39·analyze `[a]`）；9 测试绿（今日 §6 断言退役后）；零源锚零 dev 引用（唯 FR-4.5/D-9 模板句）；行数 72 不超限（主表 73 系快照漂移），无新发现 |
| diy-party-mode | 完毕 | 2026-10-05 | 激活头同构（含参数解析/子代理探测降级/门禁变体）＋无 steps 变体（:28/:58——引 2026-09-19「无 steps 技能 §4 永久不适用」裁定＋test-author 零产物判例＝判例引用在场）；§6 已删（2026-10-05 适用面批）·§2 在场（:64）；**真子代理独立推理**（绝不自生成发言·`--solo` 唯一例外且开场一行明示·自动降级探测两判据·用户拒绝 solo 即停）＋逐字呈现不合成（禁合成/转述/压缩/框语·编排者注短且标注）＝反趋同机制正面样板；视角动态派生（无名册无剧本·反面义务必设·轮次轮换）＋上下文管理（讨论摘要 ≤400 词非全量转录·每 2-3 轮更新）；零写面（对话即交付·理由写明「落盘只会制造写权边界问题」）＋无渲染（§5 不适用）；副作用与确认档（>4 视角或 `--model` 覆盖先问·无头按 4 上限截断·不入 deferred-actions 且写明为何无落点）＝与 diy-tools 队列语义分工；异常处置四情形（趋同引反方/绕圈汇总反问/失焦直接问/弱响应不重试交用户）；边界（vs diy-review 结构化检出/讨论形态·不互替不互读产物）；9 测试绿（今日 §6 断言退役后）；发现：SKILL.md:15「裁自源技能：…」句＝裁剪说明嵌入正文段——迁移决策记录漏网（「裁自」形态不在标记词口径）→ 已补登去源锚批迁移痕迹普查；行数 64 不超限（主表 65 系快照漂移），无其他新发现 |
| diy-spec | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋输入判定三拒绝路径零产出变体＋slug 同键就地更新变体）、纪律块 §6/§2 同款在场（:82/:84）→ 随 YAML 迁移整体收编；**两遍自校验**（Pass 1 Coherence → Pass 2 Preservation·不许静默丢弃·仅包装性内容落 `verdict.preservation.dropped`）＋**CAP 纪律**（退役保留条目标 `retired: true`——「痕迹的价值在于退役的是什么」·绝不删条目·`--previous` ID_UNSTABLE 防丢）＝保真校验正面样板；slug＝记录唯一键（同 slug 更新既有记录不新建）；边界**双向声明**（vs quick-dev `spec.yaml` 不同名不同生命周期互不读写·≠ diy-prd 轻内核不替代 PRD）；稀疏输入二选一 express/guided（无头默认 express 并把选择记在 `verdict.coherence` 段末——决策留痕）；companions 双轨（adopted 只引用不改 / sources 已完全吸收仅审计·下游不读）；引用式纪律（CAP-N / path 禁复制）；内容面直编 YAML（内容型产物·引擎骨架与校验——同 analyze 写权分工变体）；零 `[假设]` --final 义务；29 测试绿（spec＋spec_kernel 两件）；零源锚零 dev 引用（唯 FR-4.5/D-9 模板句）；行数 84 不超限，无新发现 |
| diy-spec-scan | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋定位目标三选项 HALT＋硬门「有要照做的事」零产出变体——纯参考资料/纯数据停）、纪律块 §6 在场（:88）·§2 变体（:90 带 `quote` 豁免条款——引文里 `[假设]` 等禁字面量照抄·终门对 quote 豁免）；核心原理写透（「歧义只在遇到具体决策时暴露」＋预演不是读后感·执行计划留对话·落盘只有卡点清单·不为过程叙事扩 schema）；方法论六规则硬核：**只读规格禁读实现**（「读了就能从实现反推意图·这是本技能失效的头号原因」——失效模式写成规则）＋禁读后感句式＋**`would_guess` 是命根子**（空值引擎判违规）＋零改写＋不评论质量＋不确定标 `建议` 别升 `阻断`（阻断只留给两种理解导致完全不同实现）＝诚实分级正面样板；findings 八类型枚举＋五问字段（read_as/stuck/would_guess/impact/suggestion）；`units[]` 覆盖凭证（证明扫了什么）；交叉验证换视角复扫补漏去误报；SS-0nn-nn 号段空缺允许绝不重编号；28 测试绿；旁形态 1 处（:27 示例文案含 B3 批次码——归普查编号口径）；行数 90 不超限，无其他新发现 |
| diy-selfcheck | 完毕 | 2026-10-05 | 编排者形态（零 YAML 写面·预演片机器台账归 diy-spec-scan——SS-### 由片承担铸号＋`check --final` 初跑；边界双向声明 :19）；三机制读取边界各异按片分治（预演禁读实现／引用核对与对抗必读实现＋git——「不按最严纪律自我设限」）；分片隔离纪律（互不通气＋片指令必含「不复用写作侧结论」——反 self-preference 是并行形态核心价值）；交叉置信度（2-3 片独立命中＝最高·B3-B7 实证注「三片同中条全是阻断或高」）；D 表闭环（无处置记录＝扫描未闭环·驳回写理由不是忽略·观察记去向）＋增量补扫＋**旧值复扫两轮**（B6 强制道「逐条处置≠逐处改透」·零命中才准收口）＝机制正面样板；用户拍板贯通三问（B7b：受影响技能/条款要改/读写面）；版本锚冻结/解冻（md5＋commit·锚一变全废·git 仅做锚点）；B 部分必出（「只出 A 是普通审查·出 B 才算 dogfood」）；单执行者降级形态（C·7·四轮换视角不带前轮结论）；`outputs: —` 但写报告散文→§6 在场正确（「写产物散文」判据正面例证·不在零产物删除名单）；10 测试绿；发现三项：①主产物 md 违 YAML 单一源（全库唯一例外）→ 已裁四项入专段待办（用户点名·落 output_dir/分片同 YAML 化/SC-###/自带终门）；②批次码 B3/B6/B7/C·7/§13 共 10 处＝普查编号旁形态；③「B7b 截断教训」条款随 YAML 化批改写（待办段已录）；行数 55 不超限，无其他新发现 |
| diy-editorial-review | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`stats` 门禁四拒绝路径零产出变体——target 缺席/空/<3 词/枚举越界皆拒绝非记录）、纪律块 §6/§2 同款在场（:85/:87）→ 随 YAML 迁移整体收编；**建议制不代改**（CONTENT IS SACROSANCT 只改怎么说不改说什么）＋「findings 归本技能·施加归调用方」两方分工（brief 三遍施加顺序点名）——与 diy-elicit 边界互认＝写权边界正面样板；**结构先行**（结构建议可能淘汰段落·先做文风会白做）；被调用形态例外条款（product-brief 调用→两透镜全跑不问直接定稿——「每个交互点都问」纪律的**明示例外**）＝交互纪律变体登记清晰；「无问题也是合法完成·绝不编造发现凑数」；双透镜分槽（结构六类 CUT|MERGE|MOVE|CONDENSE|QUESTION|PRESERVE＋`estimated_reduction_words`／文风三列修订）；style_guide 覆盖一切＋唯一例外 CONTENT IS SACROSANCT＋project-context 引用提及不硬接；记录只追加无 `--previous`；9 测试绿＋viewer editorial 专项在场；旁形态微量（:17「源文自述」1 处泛指归去源锚批）；行数 87 不超限，无新发现 |
| diy-quick-dev | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋断点路由六值变体——按 SP `status` 路由·断点恢复不得跳过路由判定）、纪律块 §6/§2 同款在场（:90/:92）→ 随 YAML 迁移整体收编；边界三面（vs diy-dev 故事环外不进 sprint 不立 TC·vs diy-review 审查层 L1-L3 绝不另立第二套每条 finding 恰好路由一次·vs diy-spec 双向互认 :77 两产物不同名不同生命周期互不读写）；**L4 边界条款**（:19——`acceptance` 无 `design_ref` 故 (a)/(b) 无法键控·改跑 (c)+(d) 等价只读命令不新增写权·跳过须用户明示）＝层适配精细；TDD 差别明说（无红绿台账·每条验收判据带命令级 `verification` 必须真跑·空则 `审查中` 被 EMPTY_FIELD 拒）；**`project.status` 文件水位线**（全部 SP 已完成才 `已定稿`·新增/重开先回 `草稿`）＝新颖设计；`intent` 一经人批准即冻结＋`change_log` 只追加；审查轮次上限 5→HALT；`review_order` 按关注点不按文件·已完成必填；SCOPE STANDARD 只给建议永不设门；一次成型早期出口（step 6 零爆炸半径通道三种处置）；`baseline` 先记（commit-sha\|NO_VCS）；绝不 commit/push/开编辑器；上游 `investigation.yaml` 引用式消费（绝不转抄·分级口径归 investigate）；18 测试绿＋viewer spec 专项；发现：BMAD 裁改对照注记 6 处/4 文件（SKILL:58 源语汇/:86 裁改对应关系＋01:21/:22＋03:18＋06:31 源做法 vs diy 做法对照——同 party-mode:15 族）→ 已补登迁移痕迹普查；行数 92 不超限，无其他新发现 |
| diy-investigate | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`collect` 采集器变体——NO_VCS warning 降级绝不致命·行数即子代理成本依据）、纪律块 §6/§2 同款在场（:91/:93）→ 随 YAML 迁移整体收编；**证据三级分级是核心纪律**（已确证引 path:line/时间戳/commit·已推断给链·假设中写证伪条件·「级永不注水——诚实的级就是交付物」）＝诚实面正面样板；据点先行（先锚一条已确证再外扩·绝不从理论出发找支持·**用户描述是假设不是事实**——problem_statement 原话永保、证据可反驳不改写）；**假设永不删除**（status＋resolution·错路留在案卷·无 resolution 终门拒放行）＋每次向已确证移动**先跑证伪轮**（主动找反证记进 resolution）；缺失证据也是发现（`missing_evidence` 三键·`availability: 缺失` 只标已有条目跑丢·`evidence_light` 案件合法不静默）；委派闸值单一定义源（>10K 单文件/≥5 文件/类别 >10K→派·子代理只返 JSON 父上下文不重读）；边界：调查止于诊断不修不成故事不写冲刺＋缺陷入库「给命令」而非「写文件」（bug-add·source: 用户·确认后就地执行）；**下游消费双边合同**（quick-dev:29 引用式消费 handoff_brief/conclusion/evidence·绝不转抄）；slug 续案键＋follow_ups 同日多条也照记；ID 三层作用域（IV 文件级/EV/H case 内）；side_findings 切向观察三态区分（≠backlog≠evidence）；19 测试绿＋viewer investigation 专项；零源锚零 dev 引用（唯 FR-4.5/D-9 模板句）；行数 93 不超限，无新发现 |
| diy-checkpoint-preview | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`target` 三层级联定位变体——显式 ref→`待审查` 任务→git diff·PR 线索由会话层先解析成本地 ref·三层全空 exit 1 零写入）、纪律块 §6/§2 同款在场（:84/:86）→ 随 YAML 迁移整体收编；边界（vs diy-review：人的理解与拍板 vs 机器分诊与状态迁移——不补丁不动状态不写 stories）；**按关注点带看不按文件排布**（连贯设计意图·理解顺序·`path:line` 停靠点）；风险点 2-5 个**按爆炸半径排序＋枚举标签**——「绝不按 diff 顺序·绝不用数值严重度」＝今日爆炸半径批判据（④纪律句）的本源样板；亲手验证 2-5 条纯体验面·绝不复述 CI/测试套件；**人的话就是证据**（`reason`/`next` 引述或贴近转述·绝不替人编结论）；`讨论` 永不收口（回决策点循环）；`target.inferred` 只为 true 而写（缺席是常态绝不无中生有）；mode 死值诚实标注（:57「全程轨迹——本生态不适用」）；无风险明说不编造；「在此批准不发版＝记录一次人工拍板」；22 测试绿＋viewer checkpoint 专项（7 处）；零源锚零 dev 引用（唯 FR-4.5/D-9 模板句）；行数 86 不超限，无新发现 |
| diy-correct-course | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`collect` 确定性开场变体——硬门三件套已定稿·exit 1 拒绝永不变成记录）、纪律块 §6/§2 同款在场（:88/:90）→ 随 YAML 迁移整体收编；**只出提案不改真源**（八产物逐一点名·`handoff.route` 点名谁执行·「整篇改写是产物所有者技能的活」）＝写权边界正面样板；输入面两路＋上游调查（retro 交接**一条 proposal 承载整批**·trigger 写 RT-id＋change 摘句——retro 双边合同对侧；investigation.yaml 引用式消费绝不转抄——第二个消费方）；**只引用不复制**（`impacts`/`edits` target 带稳定 ID 或 `path:<relative>`·`old`/`new` 最小决定性取值绝不粘贴整段）；**scope×route 门强制配对**且真判据＝被改产物唯一所有者（`轻微`→所有者落实/`中等`→重组 backlog/`重大`→规划层重规划·allow-list 只是粗筛）＝认源纪律；「已驳回」终门永不放行的例外（改跑不带 `--final` 的 check 收口——终门变体诚实处理）；批准先于路由（未批准绝不交接）；触发不清就停·绝不虚构影响；25 测试绿＋viewer proposal 专项；零源锚零 dev 引用（唯 FR-4.5/D-9 模板句）；行数 90 不超限，无新发现 |
| diy-reverse | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`list` 六字段续接＋门禁两轨零产出＋写权分支变体）、纪律块 §6/§2 同款在场（:81/:83）→ 随 YAML 迁移整体收编；**生成权/演进权分离（裁定 13）**＝`design.yaml` 只在初始生成时写·已存在 `init` 判 `OVERWRITE_REFUSED` 零写入·`revisions` 建议＋路由 `diy-design`——写权边界正面样板；纪律三条（先观察后提取/尊重知识产权/抓规则不抄像素）＋**「不抄像素」判据机械化**（同值 ≥2 次才可作 token·与 `design.py audit` 的 `one-off-*` 同判据＝跨引擎判据复用）；既有 schema 逐字沿用（不新增字段不自造 ID·`P-<n>` 不用 WDS 记录形态·`SET_MISMATCH` 核结构稿名）；**双终门交叉核对**（本引擎 `check --final` ＋ `design.py validate/check` 双 exit 0·不一致以设计域引擎为准「schema 与易用性权威」）＝跨域权威让渡正面；新增两码（`TARGET_UNREACHABLE`/`OVERWRITE_REFUSED`）；提取来源无承载位→结构稿头部注释承载＋登记 C·3 schema 扩充项（债有主）；检查点四选项六拍（同 analyze 族）＋「路由≠技能间调用：调用先例只给零写面增强技能」纪律澄清；只读外访（联网不可用即中止不排队）；边界六对；C·12 欠账两键（form_factor/modes）在场核验✓；35 测试绿；旁形态：批次码与裁定号注记约 8 处（C·3×5·C·12×1·裁定 11/13——归普查编号口径）；行数 83 不超限，无其他新发现 |
| diy-bmb-builder | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋build-logs 续接＋硬门三条零产出变体）、纪律块 §6/§2 同款在场（:63/:65）→ 随 YAML 迁移整体收编；**零 YAML 主产物形态**（三写面＝母本 §1「唯一读写根」**有据例外**·理由「产物是技能树不是文档」；§8 产物状态口径不适用——零 YAML 形态变体登记清晰）；判据「这一行值不值得留：称职模型不被告知也会做的事就是摩擦」＝leanness 哲学贯穿；单循环构建流（目标驱动非固定阶段·硬化优先于生成·「你就是你教的那个形状」）；lint gate 三件（prepass＋scan＋check --final·三次修不好即停并上报）＋eval beat **不 fork**（调 diy-eval-runner·「产出归它、施加归本技能」）；防覆盖 `FILE_CONFLICT`＋Edit 破坏性确认＋无头 `defer-add` 入队（队列语义正面使用）＋`--force` 硬护栏（套件已建技能名/禁改面即使 --force 也拒）；自足可分发（拷贝即用·自足判据在内容面·套件工具豁免）；Analyze 十二件全落（少落失去可比性）；边界三对（vs spec-scan 歧义≠质量·editorial-review 提示词工艺≠行文·spec 技能树≠机器契约）；25 测试绿；:47/:54「≤90 行」滞后于 2026-10-03 上限放宽（90→250）＝逐项化批 0 既有登记（含 bmb_builder.py:102 落点）非新发现；零源锚零 BMAD 注记；行数 65 不超限 |
| diy-bmb-module | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋议题 HALT＋「只有一串名字」拒绝变体——「计划的价值在愿景与 brief 不在名录」）、纪律块 §6/§2 同款在场（:79/:81）→ 随 YAML 迁移整体收编；**只规划不造**（造物归 builder·按 `build_order` 交棒）＋**零写面**（校验全程只读·frontmatter 亦然——「frontmatter 是 diy-help 的读面·写入权不在本技能」＝认源纪律）；价值定位清晰（:17「注册面散在各自 frontmatter·批次一致性没有任何单技能能看见」）；校验**三档处置**（对端计划内→判/已装→warning/两边都不是→违规）＋`--previous` 留痕（收缩须标 `dropped: true` 不静默丢）；slug 身份键同款（同 slug 就地更新）＋MP-### 引擎铸造；`skills[].name` 完整名含 `diy-` 前缀「零前缀算术」＝引用形态同一空间；`new`/`dropped` 双标记（六字段判定面/收缩判据）；:49 单记录 vs 多记录产物的 status 口径区分说明＝形态知识正面；与 builder 交棒双边合同（builder 01:37 按 `build_order` 逐个造·未定稿停——对侧在场核验✓）；28 测试绿；零源锚零 dev 引用（唯 FR-4.5/D-9 模板句）；行数 81 不超限，无新发现。**至此 C 横向 20 技能一审全部完毕** |
| diy-openapi | 完毕 | 2026-10-05（2026-10-04 已审出接口契约/鉴权面发现入待办·本轮按当日标准收口补行） | 激活头同构（含预载预算＋双上游预警问询变体＋接口面判定门「没有接口的 openapi 是虚构」零产出＋Create/Update 判意图）、无 steps 变体（工作流六条内联·单文件短流程族）、纪律块 §6/§2 在场（:75/:77）→ 随 YAML 迁移整体收编；**合法 OpenAPI 3.1 高于一切**（元数据住 `x-project` 扩展·revisions 落点在扩展块内「裸根键违反合法 3.1」）；ID 链硬契约＝`x-fr` 只引用绝不复制（下游认源 ID 正面·operationId 即身份已裁·e2e `api_refs` 批即消费此锚待执行）；**Update 安全网三档**（`.prev`＋`ID_UNSTABLE` 找回补进重跑／`MISSING_FILE` 快照失效停手告知／非 0 一律不删）；范围＝FR 集合（不臆造 CRUD 不做没人要的版本机制）；`[假设]` 写 YAML 值上不在对话里；终门走 `diyc check --type openapi --final`（主线 8 型复用·无自有引擎正确）＋门失败回退草稿＋`known[]`＝已认可基线非待修违规；viewer 专项渲染（render_openapi_section）＋审阅发生在接口总览表非裸 YAML；test_diyc_check 16 处 openapi 断言；零源锚零 BMAD 注记；行数 77 不超限。2026-10-04 既有发现（鉴权/通用错误/tags·三层联动触发）已裁入接口契约批待执行，本轮无新增 |
| diy-review | 完毕 | 2026-10-05（C·12 已做机制面＋2026-10-04 steps 深化发现入待办·本轮按当日标准收口补行） | 激活头同构（含预载预算＋硬门状态机变体＋`--falsify` 例外＋WDS 线判定分支）、纪律块 §6/§2 在场（:77/:79）→ 随 YAML 迁移整体收编；步骤薄件×7（C·12 拆 steps 后主文件 79 行——steps 集合==磁盘实况由 test_review_skill 契约守卫·每件 Read/Write 行）；四层+双透镜可选（批判式/边界穷举收编自 bmad 同名技能）；**每条 finding 恰好一路由**（四路由表主线/WDS 双落点同表同词表）；判决规则完备（`规格缺陷`→已阻塞·其余失败打回·`后置` 唯一落点 sprint findings **不入 deferred-actions「语义不同」**＝队列分工精确）；**BUG-012 真源回填**（`done` 原子批次·已阻塞不写真源——与 build-loop 同口径互认）；状态写入权封闭四边（`transition` 拒 `待审查→已完成`·证伪命中重开清旧判定·批量 reopen 归 sprint）；bug-add 缺陷入库喂经验环（三级分类·`type` 自由扩展标签「现象吻合复用·真新才铸」＝词汇漂移防治）；实现面 diff 口径（trace 回执引用文件集＋git porcelain 未跟踪·开场声明采样面）；WDS 线（`待验收` 页按 `states[].signals` 独立复验·**批准始终归用户不由审查者代劳**·回修边）；L4 设计采用四核＋C·7 顶层两键消费＋C·13 触控分档消费（「以 diy-design 引擎为唯一权威不另立解释」＝认源纪律·引用回执按 code 点名不写维度计数）；经验上行 exp-sync 由人手动执行（投影/真源分清）；investigation 引用式消费（第三消费方）；48 测试绿（skill 契约＋contract＋WDS 三件）；旁形态：L4 批次码 C·7/C·13/FR-3.7/D-10（归普查编号）；steps 深化批（L1 untraced/L2 推导规程/falsify 探针）系 2026-10-04 既有登记属一审范围——本轮收口不新增；行数 79 不超限 |
| diy-wds-brief | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`list` 五字段续接按 `stage` 七态分流 HALT＋WDS 起点无上游门禁变体——门禁＝分诊问答完成·拒答零产出可路由 prfaq）、纪律块 §6/§2 同款在场（:84/:86）→ 随 YAML 迁移整体收编；**三方唯一契约**（:70 下游 trigger 按 `project.status: 已定稿` 门禁读 brief 四组键——「键名＝跨技能读契约·改键名须同步 W2/W3」）＝下游认 ID 正面；`intake.stage` 七态续接锚点（续接粒度细）；检查点四选项六拍＋YOLO 首选明示＋不入 deferred-actions（家族同款）；档位决定键表·键表由 `check --final` 机械核对（simplified 收窄键表）；WDS 型自带终门（不得改用 diyc 8 型——同 analyze/reverse 先例）＋零新增码＋`SET_MISMATCH` 承载分诊改判（「分诊结论是整链路由的根·改判走 revisions 经用户确认」）；边界五对含 **WDS 线拓扑写清**（vs product-brief 两线在 design 交汇·prd 起手分叉·design/dev 双源——brief→trigger→scenarios 独立短链）；规则 9 本线风格 HARM/HELP（源 Saga 归位＋「产出看着完整却不按键表走比没有更糟」）；单记录多段顶层设 `project.status`（母本 §8 直接适用）；36 测试绿＋schema 模板数据资产；发现：steps 溯源注记**重灾区**（7 步全带「源侧/源 step-N/源 03b」泛指＋裁改对照约 15+ 处·:37 补齐注记）→ 归去源锚批；03:144 系原普查真 4 处 dev 引用之一·所在块＝迁移决策记录嵌正文（「不在 DOC_LABELS」句面已滞后——标签实落 viewer.py:48/:400·随批迁台账消解不另立清理项）；行数 86 不超限，无其他新发现。**WDS 线开审：45/50** |
| diy-wds-trigger | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`list` 八字段续接按 `stage` 七态 HALT＋上游 `wds-brief` 已定稿门禁＋**模式必须用户显式选择禁代选**）、纪律块 §6/§2 同款在场（:87/:89）→ 随 YAML 迁移整体收编；**三方唯一契约**（:73 下游 scenarios 按 `已定稿` 门禁读三组键·**数组按优先级降序前 3 即其 Top 3**——读取语义钉死）；**0 基/1 基映射纪律**（图内节点 ID 保源侧 0 基·产物 ID 1 基·换算式写明＝认锚纪律）；**规则 4 诚实登记缺陷面**（W 默认完整·S/D 降级自审·第 1 层 Learn WDS Form 标不可用＋源侧 5 条学习材料路径失效实况——2 条实存 saga 1687 行·3 条确不存在·「不得伪造方法层文档」·已登记能力损失）——**Layer 1 方法本体迁入待办在册（2026-10-05 已裁·未开工·本轮无新增**）；effect_map 派生视图（mermaid 构图纪律「收编的唯一定义」·**连接数公式＝目标数＋2×人物数可机械核**）；`SET_MISMATCH` 三兼作（mode 不符/评分重算/驱动 ID 序号）；随身体检 `metrics` 越界只 warning 不阻断；边界四对（vs research 联网调研/结构化驱动力 不联网不产来源）；规则 9 头韵名等 saga 风格＋HARM/HELP；38 测试绿＋模板数据资产；发现：steps 溯源注记重灾区（42 处「源侧/bmad」——同 wds-brief 族）＋SKILL:80 引用 `_bmad` 安装布局外路径（Layer 1 迁入批处理）→ 均归去源锚批（任务批名词口径已整类覆盖）；行数 89 不超限，无其他新发现。46/50 |
| diy-wds-scenarios | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`list` 六字段续接三选项 HALT＋上游已定稿门禁双拒绝＋按门禁**只读三组键**）、纪律块 §6/§2 同款在场（:86/:88）→ 随 YAML 迁移整体收编；**三条骨律全保**（源 step-05：阳光路径零分支/场景名含人物名/**每页恰属一条战略链**——漏配/重复分配/清单外各判违规＝覆盖完整性机械化）；**ID 体系（裁定 8）**：`SC-<nn>.P<n>` 复合锚（废止独立 `P-*`）＋slug 展示名须与 ID 同源（引擎核）＝认锚纪律；两个用户关卡不得省（规模分析/场景计划呈批）；**design_intent 交接契约**（K\|C\|S\|D\|L——design 按它预选活动·`design_status` 只设初值推进归设计线＝写权分离）；上游只读（要修正走 `revisions` 建议或路由上游重跑）；只产本 YAML（裁定 12——不建目录树/Sketches·产物位归 C·3 design）；`SET_MISMATCH` 承载四类（ID 跳号/页号不连续/slug 不同源/覆盖矩阵）；与 epics-stories **不互译不互替**（`SC-*` vs `S-*`/`AC-*` 两线词表隔离）；HARM/HELP 源 Freya 归位（「规格必须完整——不完整规格到设计阶段一定返工」）；44 测试绿；steps 溯源注记 33 处（重灾区族）→ 归去源锚批整类口径；行数 88 不超限，无新发现。47/50 |
| diy-wds-system | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`list` 六字段续接活动菜单 HALT＋上游已定稿门禁双拒绝＋`design.yaml` 可选读降级记 warning 不阻断）、纪律块 §6/§2 同款在场（:87/:89）→ 随 YAML 迁移整体收编；**token 派生（裁定 5）**＝tokens 只存名与指向·值回 `design.yaml.tokens` 取·「同一 token 位的两半」（design 唯一风格源·要改值回 design）＝引用不复述正面样板；**重复检测边界诚实（规则 7）**：聚合段可机械交引擎（权重 30/30/25/15·六级）·输入段不可机械「源侧只有散文示例无字段级规则·故由你判定＋用户确认·**不得假装全自动**」＝诚实分工样板；四套源词汇表归一为一套 `space-*`（10 个）＋唯一渐进阈值「二次使用才提取」（裁定 17·间距提取问题消灭＝KISS）；组件十五键＋逐前缀独立计数＋废弃不删走 `status`；V+B 合一静态 HTML（localhost 四路由裁＝平台耦合）·Figma 通道整块裁·零外部服务·零 git 写操作（源自动提交已裁）；用法一致性校验取 `[M]` 版＋复杂度路由 842 行收编为 data 资产；HARM「库看起来很齐但 `used_in[]` 全空＝凭空造的」＝从使用中长出原则的证伪面；65 测试绿（WDS 线最大）；既有登记联动：`data/complexity-router.md:5` 系迁移痕迹普查在册项＋「未建」滞后 3 处（test-framework 审时已归去源锚批）；steps 溯源注记 28 处＋裁定号密集（裁定 2/4/5/6/17/19·计划 §四:232）→ 归去源锚批整类口径；行数 89 不超限，无新发现。48/50 |
| diy-wds-assets | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`list` 六字段续接三选项 HALT＋上游已定稿门禁双拒绝＋design-system 可选读降级）、纪律块 §6/§2 同款在场（:87/:89）→ 随 YAML 迁移整体收编；**零外部服务（裁定 6·用户拍板原话在案）**＝产物直出（HTML/SVG/CSS）·提示词导出＝照片类通道＋可选项·不产二进制；**规则 6 可机械 vs 不可机械清单化（不得假装全自动）**＋「注意」诚实段（引擎只核路径形态不核文件存在——会话按 09 双向对表自证：YAML 有路径必有文件·目录有产物必有条目）＝诚实分工＋自证义务样板；**链条终点定位（规则 11）**：「反向回填 design.yaml 的口在 diy 侧不存在（源侧 E-Assets 消费者为零·普查实测）」＝消费面为零诚实登记；已知缺口诚实登记（:70 viewer 只扫顶层 yaml→assets/ 渲染不到·C2 面缺口在册）；AS ID 体系（8 活动按 code 序固定＋条目父 ID 必须存在＋**prompts 复用来源 ID＝派生索引不另铸号**）；`SET_MISMATCH` 承载五类；数据资产最富（风格库 16 卡＋presentation-formats 7＋迭代精修/红旗两条纪律件）；HARM「产物与提示词都缺规格锚的清单回不来也改不动」＋浏览器实际打开核对（mimir 行为规格句）；68 测试绿（WDS 线最大）；发现：**风格库 16 卡未汉化**→ 已登待办（用户点名 content-styles＋design-styles·卡名引用键保留只汉化叙述）；既有登记联动：presentation-formats/index.md:25 系 dev 引用原普查真 4 处之一在册；steps 溯源 73 处（最重族）→ 归去源锚批整类口径；行数 89 不超限，无其他新发现。49/50 |
| diy-wds-evolution | 完毕 | 2026-10-05 | 激活头同构（含预载预算＋`list` 四字段续接三选项 HALT＋**入口门禁变体**「既有产物任一在场·**本技能自己的产物不算**」——防自续接假棕地＝防自噬门禁）、纪律块 §6/§2 同款在场（:86/:88）→ 随 YAML 迁移整体收编；**入口形态（`precededBy: []`·裁定 9）**：门禁＝既有产物任一在场（design/sprint/wds-\*）·新建项目路由 brief/prd；**差异化定位诚实（:15）**：「六个活动本身与 diy-dev 同构·**方法论不同构**」＝不可替代内容＝Kaizen 方法论（data 两件：Priority=Impact×Effort×Learning 三因子 5/3/1＋Kaizen vs Kaikaku＋四原则＋暂停三情形）；**一次只做一条**（未选中目标进 `candidates[]` 作下轮原料）＋判定理由进 `rationale`（「框架只保证排序自洽·不保证判定正确」＝人工判定诚实）；HARM「一轮塞三条改进范围悄悄膨胀＋判据泛化成大致符合——下轮无从分辨哪条起作用」＝增量纪律证伪面；副作用三档（自动档含 `git add`+`commit`·保留确认档 `push --force`/删分支/越界写盘 defer-add 入队·零外部服务）＋非 git 仓库**不替 `git init`**；边界四面（本轮增量实现归 dev WDS 模式·全量验收归 dev B7b 裁定 10·`[T]` **只验本轮增量**·互不代写互不调用；design 只读演进对象；correct-course 变更提案 vs 已定路线小步改进）；「每个数字都带出处——答不出的先别写进产物」（源原则盯过程）；46 测试绿＋27 子测；steps＋data 溯源注记约 33 处（含 data 两件 9 处）→ 归去源锚批整类口径；行数 88 不超限，无新发现。**50/50——一审表全库收口** |

### 二审

| 技能 | 状态 | 完成日 | 发现 → 处置 |
| --- | --- | --- | --- |

## 待办分级总览（2026-10-03）

| 级 | 待办 | 影响面 |
| --- | --- | --- |
| 全库级（旧技能都要改） | 去 `.claude` 路径硬编码（安装器待办·①） | 155 文件近全员 |
| 全库级 | 50 技能正文逐项化 | 50 SKILL.md＋steps/ |
| 全库级 | 去源路径锚＋任务批名词（「源 `X`」悬空锚＋批次码/裁定号/「本批·已批」句/用户日期拍板引语等出处注迁 dev-only 台账·**技能正文不放**〔2026-10-05 用户裁定整类禁入·拍板引语当日裁并入〕） | 72 文件＋预扫 99 文件 314 处（扩口径后更多） |
| 全库级 | 零产物技能删「精准简练」块——§6 适用面＝写产物散文的技能（2026-10-05 用户点名全库级；适用面批已删 viewer/help/elicit/party-mode＋diy-tools:66 同批收口·断言退役 58 绿——**零产物带 §6 清零**；dev/review/augment/build-loop/selfcheck 虽 `outputs: —` 但写产物内容＝适用保留——判据「是否写产物散文」，范围随批终核） | 零产物 SKILL.md＋对应 test 断言 |
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
| 单独技能 | diy-test-gate viewer 滞后句清理（06-finish:33「走通用降级渲染·标签缺口由主 agent 登记」——C·2 2026-09-21 已补齐 test-gate 标签，句面失实） | diy-test-gate steps/06-finish.md |
| 单独技能 | diy-test-gate dev 仓引用漏网 6 处清理（迁移计划 §十三:459×4·§二验收×1·SKILL.md:67 裸节号；普查标记词未命中 §形态——与既有 4 处同族合计 10 处/8 文件，**随去源锚专批一起改**，待用户点头开工） | diy-test-gate SKILL＋steps/05＋scripts/gate.py＋gate_check.py |
| 单独技能 | 变异配置显式化（test-plan `mutation:{enabled,tool?}` 段·默认开日常任务级·任务级/发版级 override·借位条款退役） | test-design/augment SKILL＋diyc 校验＋tests |
| 单独技能 | wds-assets 风格库汉化（2026-10-05 用户点名 content-styles＋design-styles 两目录；实测：content-styles 10 件全英文、design-styles 6 件全英文、presentation-formats 7 件标题已中文正文疑英文待核、styles/index.md 已中文。**卡名与文件名是引用键**（SKILL:59 `style:{design,content,format 卡名}`＋steps 02/05 消费）——只汉化叙述、键逐字保留，steps 零改动。待用户点头开工）〔v4·汉化插队已销 2026-10-13〕 | diy-wds-assets data/styles＋presentation-formats |
| 单独技能 | diy-spec-scan 加方法驱动分支穷举（ECH 化·2026-10-05 用户裁定「卡点法还不够」＋**方案全定 1A+3B·无待裁项**：①穷举独立成 step（如 02b-exhaustive）不并入 03——与 diy-review 双透镜并列同构·两法 findings 去重复用 02「同一处只报一次」·判据参考 diy-review lenses.md「边界类从内容自身推·不套固定清单」；②**穷举默认跑（opt-out·2026-10-05 裁）**——除非用户明示不用穷举·对齐 editorial-review 两透镜默认全跑 `--lens` 收窄先例；③**载体已裁＝`source: 卡点\|穷举` 字段**——type 保持八类·引擎 FINDING_TYPES 零改·summary 分法计数（selfcheck B 部分机制评价原料）。**未开工·待用户点头**）〔v4·批2a 已销 2026-10-11〕 | diy-spec-scan SKILL＋steps＋引擎＋tests |
| 单独技能 | diy-selfcheck 硬门放开「要照做的事」→ 任意文档可审（2026-10-05 用户点名 prd/架构/epic/story/任意文档；BMAD AR/ECH 文档面能力补缺·Story 2.1 实用过 AR 定稿兜底；**方案已裁 2A+4a**：spec-scan 硬门同步放开为「可读非空」·两技能形态统一·selfcheck 预演片对纯文档不降级；纯文档时 spec-scan 跳过 02 预演只跑穷举+03+04（依赖 1A）；kind 扩「任务书\|技能\|规格\|文档」——引擎不校验语义 kind·仅改 SKILL.md 文案零引擎改动。**未开工·待用户点头**）〔v4·批2b 已销 2026-10-11·引擎零改＝4a 收窄——改动面列之『引擎』在册未触〕 | diy-selfcheck SKILL＋steps＋diy-spec-scan SKILL＋steps＋引擎＋tests |
| 单独技能 | 爆炸半径分析注入 diy-review＋测试设计族（四项全闭合：1b 独立面/2b FH 排序/三技能范围/定制标签＋漂移防治已核·**未开工·待用户点头**） | diy-review＋test-design/e2e/augment＋引擎＋viewer＋tests |
| 单独技能 | diy-analyze 吸收 arch-analyze 职能（方向已裁：arch-analyze 退役不装·套件内 4 处路由句改写·取代形态/产物面待裁·**未开工·待用户点头**） | diy-analyze SKILL＋steps＋引擎＋viewer＋tests＋底单 C 表 |
| 单独技能 | diy-reverse 补「参考用法」引导（2026-10-05 会话实测：用户想先逆向别站做参考再做自己的 design.yaml——instance 隔离机制在场可解（`--instance` 落 `<output_dir>/<instance>/` 不占主线位）但 SKILL.md 只有「初始设计单源」一种叙事，参考用法入口不显性；拟补引导：参考目的→带 `--instance` 跑＋主线生成权不受扰＋design `[C]`/`[K]` 只读消费参考；挂法/文案/是否动 diy-design 输入面待裁，预期零引擎改动·**未开工·待用户点头**） | diy-reverse SKILL.md（或＋diy-design 输入面） |
| 单独技能 | diy-wds-trigger Layer 1 方法本体迁入（2026-10-05 用户裁定「要迁移就都迁移完」：2 份实存 saga 文档 1,687 行（trigger-mapping 653＋dream-up-approach 1,034）迁入 diy——**安装 diy 不装 bmad·技能不得依赖 `_bmad` 路径**·裁定 9「不可用」随之解封；迁入形态/落点待裁·**开工先普查全库同类**（运行时输入依赖安装布局外路径·功能依赖型）·**未开工·待用户点头**） | diy-wds-trigger SKILL＋steps＋新迁文件 |

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

## 待办：architecture stack 全 kind 表态＋下游取值＋help 按值推荐（2026-10-22 用户裁定，待任务书）

登记来源：审 Q-107（3476d19）时提出——现校验只保「写了合法」（枚举/唯一/形态），不保「该有就有」；无前端的项目不该推荐 design，无接口面的不该推荐 openapi。

裁定：
1. **7 类 kind 逐类表态**（照规则 4 安全类先例）：适用写 choice 值；不适用落 `choice: null` 并在 why 写理由。存量缺表态 → warning 不阻塞；新写由 SKILL 文本强制。
2. **下游取值恒在**：消费方按 kind 取 choice，空＝该项目不适用（非「取不到/追问用户」）。
3. **help 按值推荐**：diy-help 读架构适用性值决定可选节点推荐——frontend 空不推 design，接口面空不推 openapi；推荐归导航层，不散落各下游自行 SKIP。

待裁（任务书呈裁门）：
- 多值 kind（language/test/lint/typecheck/build）与「必表态」的表示法：多条＋不适用一条 null，还是每组一条汇总。
- 空值形态：`null` vs 空串。
- 接口面表态落点：stack 扩第 8 类 kind（Q-107 已裁「扩展另立待办」）vs architecture 新顶层块 vs 沿用 components/decisions 推导。
- help 数据接口：registry.yaml 扩适用性键 vs help 直读 architecture.yaml。
- 拆批：architecture 侧 / 下游五消费方 / help 三件，是否分三批入夜跑。
- 存量缺表态 warning 口径确认（沿用 Q-107）。

改动面（草案）：`diyc_check_docs_upstream.py`＋`diyc_check_docs_lib.py`（全 kind 表态断言）／`diy-architecture/SKILL.md`（结构＋规则）／design、readiness-check、test-design、dev、augment 输入面／`diy-help`（registry.yaml＋help.py／help_lib.py＋SKILL）／`diy-openapi`（若接口面判据改）／viewer（null 渲染）／相关 tests。

## 待办：新增 bug 分析技能（编排 cis-method 问题求解）

登记（2026-10-04 用户裁定立项；查证无对口技能）：现有面 = diy-investigate（取证调查，止于诊断报告，无机制消灭与经验沉淀）/ cis-method 问题求解（通用 9 步含根因·方案·经验教训，不面向 bug、无代码取证）/ retrospective（epic 级复盘）；BMAD 源 `bmad-analyze-bug` 未迁。

- 规格：调用 diy-cis-method **问题求解分支**分析 bug 成因；产物五段——**表面原因 / 复现办法 / 根本原因 / 机制性消灭根本原因的方案 / 经验教训**。
- 判据（下游认 ID，2026-10-04）：产物铸稳定 ID——**前缀已裁（2026-10-04）：`BUG-A-0xx`**（原示例 `BG-###` 被 diy-wds-trigger 占用、`BA-###` 被 brainstorm 占用，查证后弃）；喂 `bug-log.yaml` / experience_repo 时按 ID 关联。
- 输入面（2026-10-04 用户裁定）：照 diy-test-design:90 同款经验源挖法——experience_repo `taxonomy.yaml` 骨架＋`bugs/<subclass>.yaml` 逐桶全读＋本项目 `bug-log.yaml`；相关性判据同款（`trigger`/`prevention` 能否落在分析对象上）。
- **写面（2026-10-04 用户裁定）：能写输出文件**——① 分析结果经 `bug-add` 入 `bug-log.yaml`（五段→字段映射：表面→`symptom`／复现→`trigger`／根因→`root_cause`／机制消灭→`fix`＋`prevention`；`source` 值域现四值 `开发|审查发现|证伪轮|用户`，扩「bug 分析」类值随批核）——直写非「给命令」（有异于 investigate 零写面先例）；② experience_repo 投影（`bugs/<subclass>.yaml`＋`taxonomy.yaml`）——补 diy 体系零写方缺口（查证：diyc 无投影命令、retro 仅提醒不同步），直写 vs 新引擎命令待裁。
- **衔接机制（2026-10-04 用户裁定）：diy-review 发现真缺陷 → 自动调用本技能**——bug 分析技能做好后，review 经 `bug-add` 入库的真缺陷自动触发本技能生成分析内容（预填 `BUG-0xx` 上下文）＝BMAD 机制 (a) 的 diy 化；调用形态（挂载式内部调用照 elicit/party-mode 先例 vs 收尾路由移交）随批核。
- **BMAD 源阶段参考（2026-10-04，`bmad-analyze-bug`）**：五阶段＝① 信息收集 ② 代码图生成（调用图＋依赖可视化）③ 根因分析（**工作流级＋实现级两层**）④ 修复提案（**双产物**：自动化验证方案＋工作流变更提案）⑤ 完备校验＋归档——报告增量构建（每步 verify 前步＋append 本节，零占位符）。四个可借鉴机制：(a) review 自动衔接——**已裁 diy 化（见上条）**；(b) 代码图阶段（diy 对应物：`diyc trace` 分析面，是否独立阶段待裁）；(c) ④的双产物面——validation plan（防复发测试）与 diy「机制性消灭方案」的测试面交集待定；(d) **⑤引擎自动归档**（源用 `bug-archive.js` 归档 bug registry＋commit＋distribute）——经验库投影「引擎化」的 BMAD 先例，支持写面②选新引擎命令。
- 待裁：技能名与产物文件名；挂法 A（独立 bug 专有产物，cis-method 当方法引擎）vs B（薄模板特化走 cis-method 记录）；与 diy-investigate 分工（代码取证 vs 方法流分析，是否吃 `IV-###`）〔2026-10-18 分工与 IV-### 已裁·见下〕；BMAD 机制 (b)(c)(d) 取舍；phase / line。

**〔2026-10-18 用户裁定·分工重画＋`IV-###` 喂案卷〕**：
- **入口分两条，investigate 只在 runner 路径进场**——① review 路径：diy-review 发现真缺陷 → **直接调 bug 分析技能**（investigate 不参与；输入＝bug-log 条目＋`BUG-0xx` 预填，无案卷裸跑）；② runner 路径：三连失败结论 → **先 investigate 归因**（四分法定性·10-17 案 A 既定）→ 判「③产品代码错」确认为 bug → **调 bug 分析技能分析并修复**。
- **「是否吃 `IV-###`」＝吃**：runner 路径在场必接——归因案卷（证据/复现/因果链）供根因深挖复用、不重查；review 路径缺席不阻塞。原「代码取证 vs 方法流分析」接力式分工表述作废（该分工框定系 10-04 记录时 AI 注解非用户裁定——「有异于 investigate 零写面先例」括注同批同性质，不作依据）；改判＝investigate 退守失败定性/探索/悬案，bug 技能为已确认 bug 的分析执行者。
- **连带两点**：① 吃案卷形态（随任务书定形）——bug 技能输入面加 `investigation.yaml` 可选输入源，按 ID 引用、缺席不阻塞；② 与 10-17 修复路由③衔接顺序＝**位置 A＋分析完才重开〔2026-10-18 用户裁定〕**——归因③ → bug 技能分析（五段落 bug-log·吃 IV-### 案卷）→ **分析产物（investigation 案卷＋五段）作为重开前置产物** → sprint 重开回 dev 按消灭方案修 → 全量三连重跑；重开时机与五段写入节奏（一次性入 vs 分段追加）等 schema 细节随任务书。

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

补登（2026-10-11，bug 分析技能调研裁点 3 连带·批 9 收编面，依据＝`research-bmad-analyze-bug-mechanisms.md` §③-3 裁定）：
- 安装通用项在既有 `experience_repo` 外扩两键：**归档开关**（用户决定 bug 记录是否归档）／**默认上传与否**（决定投影后是否自动 git push）；`experience_repo` 语义完善＝本地 clone 路径＋git 仓库地址（`exp-sync init [repo-url]` 绑远端写回配置先例在案）。
- **diy-help 增修改配置入口**（装后随时改 yaml 不必重跑安装器）；与 10-03「安装器是设置项唯一写入口」拍板的兼容口径（help 写入是否算破例）随批 9 任务书呈裁。
- **键名与形状归批 9 任务书呈裁**（安装器须落键，批 9 早于 bug 技能立项；bug 技能任务书只消费）；投影 FIELDS 形态随 bug 技能 §③-2 schema 窗口。

约束：改动经 sync.sh 源↔副本两侧同步，md5 须全同；先裁后动。

## 待办：公共句式母本注入机械化（攒批，方案 A 已拍板，实施时一并动）

登记（2026-10-03）：现状=母本（`.analysis/2026-09-16-skill-remediation/suite-texts.md`）+ `test_suite_texts.py` 抓漂移，但**落地是手工逐文件改**——公共条款每加一条要改所有成员技能。旧理由 NFR-4 已证伪（47 技能调 diyc.py，分发单元事实上=整套 skills 目录；详版见 `docs/bmad-skill-map/讨论结论-公共内容与保证模型-2026-10-03.md`——含保证模型两轮讨论定稿与方案 A 推导链）。

- **方案 A 拍板（2026-10-03，引擎/数据分离）**：`diy-coder/sync_texts.py`（引擎，不随条款变）＋ `diy-coder/suite-texts.yaml`（唯一事实源）。均构建期资产，不随 install 分发；旧 markdown 母本退役（notes 迁 YAML，裁定史在 git history）。
- 单条先行否决（2026-10-03 用户裁定）：不提前单建 suite-texts.yaml——单条先行=新旧双源（正是本方案要消灭的）；YAML 随本批开工整体迁移 §1-§8 时建。
- YAML schema（每片段）：key=片段 ID（YAML/标记对/测试三方共用锚）/ `text`=逐字内联文本 / `members`=必含技能短名（去 diy- 前缀）/ `banned`=必不含（防误插，承测试 C 组）/ `notes`=放置＋禁改面（人读，脚本不消费）。**封闭世界**：members ∪ banned == 全部技能，漏归即红（同 EXPECTED_SKILL_COUNT 型）。
- **标记对即锚**：`<!-- suite:§N begin/end -->`，位置固化在成员文件上、YAML 不存位置（SKILL.md 是自然文档非机器结构，位置规则必碎）。脚本只替换标记对内内容；标记对缺失=显式报错，不静默跳过。
- **调用与回执**：`python diy-coder/sync_texts.py`（同步＋终端摘要）；`--check` 只校验；`--json` 机器回执（逐片段×技能 ok/replaced/missing-marker/banned-violation＋失败原因＋counts＋覆盖缺口）；`--report <path>` 生成**自包含单文件 HTML**（成功/失败/原因/缺口分组，内联 CSS 零依赖，浏览器直开）；退出码非 0=有失败（CI 可用）。
- `test_suite_texts.py` 改造：删自持 frozenset（INSTANCE_MEMBERS/CONVERTED_*/NON_MEMBERS），改为读同一 YAML；头注释 NFR-4 旧理由一并修正。
- **首次落地=AI 插空标记对＋人审位置＋测试兜底**：人只审标记对位置（diff 上下文行），内容逐字一致由测试断言。流程：定稿 YAML → AI 按 notes 逐技能插标记对 → 跑脚本填充 → 跑测试 → 人过目 diff → sync.sh 两份 md5 全同。
- 首批应用：**§9 回复纪律**（精简、名词准确；§6 管产物内容、§9 管回复文字；diy-help「10 行上限」并入）＋**产物精简条款**（并入 §2；中文禁词表/句长上限随批拟呈核）。
- 条款重组：§6「精准简练」并入 §2「写作纪律」（**2026-10-03 用户裁定合并成立**，文案待拟）：§2 成为产物内容＋形式唯一纪律块；新产物精简条款并入同块。文案预计多于两块简单拼接（拼接版仅底稿），**借鉴 caveman 技能写作纪律**（`C:/Users/93559/.claude/skills/caveman/SKILL.md` Rules 段：砍填充词/hedging/客套、短同义词、片段句、箭头表因果、一词够则一词、技术名词/代码/错误串逐字、不发明读者解不开的缩写、`[thing][action][reason]` 句型），与中文禁词表/句长上限一并拟呈核。数据面：两块交集 46；只有 §6 的 4 技能＝build-loop（写产物却无 §2，入块待裁）＋help/tools/viewer（零产物，**已删 2026-10-05 §6 适用面批**——elicit/party-mode 同批共 5 家，台账落地 `PRECISE_NON_MEMBERS`）。测试面：ANCHOR_PRECISE 并入 §2 断言；§9 措辞「§6 管产物内容」改「§2」。不单技能先行改（锚串断言即红，随母本批整体动）。
- **ASD-STE100（简化技术英语）纳入 §2 候选条款**（2026-10-05 用户点名，随条款重组一起处理，具体文案后定）：AI 产物**可遵循其规则面**——约 57 条写作规则（一句只讲一事/短句/主动语态/现在时/禁成语比喻/一词一义/程序一步一句等）作为 §2 候选条款，与禁词表/句长上限/caveman 借鉴同拟呈核；**词典面不可机械内置**——约 900 受控词表系 ASD 版权，不可打进技能包做引擎门。**随批裁定三点**：①适用语言范围（STE 只定义英语受控语言；`document_output_language=英文` 时全套适用？中文产物取精神不取词表？）；②规则子集取舍（57 条全量 vs 挑与产物相关的子集）；③句长上限数值与 STE 程序句 ≤20 词的关系。
- **〔2026-10-17 扩围裁定·单源多通道〕**（窗口输出落点销入本批）：
  - **生效通道三条**：A＝既有 SKILL.md 标记对注入（产物面）；B＝新增注入目标＝项目 CLAUDE.md 标记对段（回复面·全会话自动加载·任何会话的 AI 回复都生效）；C＝可机械件下沉引擎关卡（产物面禁词/句长 grep 进 diyc check；中文全角宽度算列宽函数等——有消费者才落）。
  - **配置型**：注入目标列表（SKILL 集＋CLAUDE.md 路径）读配置不写死；将来 diy 用户由 init 技能/安装器写入其项目 CLAUDE.md；生成物＝普通 markdown 段落＋标准 HTML 注释标记对，换 agent 兼容（不绑宿主专有机制）。
  - **条款源扩三块**（拟稿逐条呈审·用户已核方向合适）：caveman 借鉴（caveman SKILL.md 全文 2026-10-17 已核）＋STE100 精神子集＋载体判据（并列 ≥3 项→表格/流程架构→图（mermaid）/多产物长文档→viewer 页/结论先行先一句话再展开）。
  - **〔2026-10-17 条款范围二裁〕**：**caveman＝全部吸收**（含 Auto-Clarity 四类降级例外/分档思想/代码·commit·PR 边界正常写/技术名词错误串逐字红线/语言保持/不自夸——全条款进条款源，§2 vs §9 分家归拟稿）；**STE100＝全家族精神收编、词表面不收**——家族 1（一词一义）/2（一句一事短句）/3（主动语态现在时）系用户先前点名（2026-10-17 前讯），家族 4（禁弱动词 perform/carry out/名词化——「进行+动词」句式砍）/6（用语一致不轮换同义词）/7（结构件：复杂指令配图/列表代长句/步骤编号/禁双重否定禁 etc.）本次裁收，家族 5（禁词表）既有计划在场（中文禁词表随批拟）；推导链＝三来源合计覆盖规则八家族中全部可收面，不收面唯版权词表。
  - **STE100 三点闭合**：①适用语言＝中文取精神不取词表（900 词表系 ASD 版权＋英语受控语言，内置即违）；②子集＝挑与输出理解效率直接相关的约 10 条（不全量 57）；③句长上限＝初值拟稿呈审（中文可初拟 40 字/句）、真实语料首跑后按噪声率迭代调参（同 discover 调参先例）。
  - **hook 路线不做**（窗口输出段同日裁定）。
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

- 上限落点：`bmb_builder.py:102` SKILL_MD_MAX_LINES（源/装两份）＋:52/:1438 帮助文本＋bmb-builder SKILL.md:47/:54 范式句＋steps 三处（`03-analyze.md:41`·`04-gate.md:18/:20`·`05-finish.md:24`——2026-10-07 滞后表述普查补登）；测试面无行数断言；fidelity 报告的 ≤90 为历史留档不改。存量超限 5 技能（prd 121／design 106／test-design 102／epics-stories 99／sprint 97）放宽后一并合规。
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

**〔v4·help 聚合提前批 已销 2026-10-20〕**：自动聚合（平铺根空＋含链产物合规子目录）＋`--all-instances` 强制（含平铺根 `(root)` 行）＋总览表（版本｜线｜位置｜下一步｜阻塞·阻塞置顶）＋`--json instances[]`；`--line` 限实例内选线（聚合给 `--line` 报错）；混合态 notes 提示；diy-prd description 改「product or version PRD」。help.py 拆 help_lib.py（332 行）＋help.py（160 行·≤400 红线）。全量 1772＋248 绿·sync 源装 md5 全同。遗留句保留：版本间共享事实（技术栈／整体分层）在各版本 architecture.yaml 重复、漂移无机制发现——暂接受，机制后议。

## 待办：diy-help 游离「精准简练」句移除（单独技能级，随母本注入批）

**已处置（2026-10-05）**：随 §6 适用面收窄批删句，test_help 断言同步退役——见「§6 适用面收窄」已执行段。

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

## 待办：diy-lab 实测缺陷修复批（登记 2026-10-04·2026-10-21 部分销项：②~⑥⑧ 已落地；余 ① 随母本批、⑦ 随 Q-112）

登记（2026-10-04 用户裁定）：来源 = diy-lab 六技能实测（代答模式 agent team 跑 cis-method/brainstorm/research/brief/prfaq/prd，全链终门绿），完整发现见 `D:/mycode/diy-lab/EXPERIMENT-REPORT.md` 与 memory `project-diy-lab-experiment`。同批坐实两条既有判据：下游认源 ID 实测成立（prd 通篇 BS/CM/BD/RS/PQ 锚，自由通道零复制）；三源 distillate 结构化通道、brainstorm/cis-method 走「其他材料」须点名（底单行改注另裁）。

| # | 面 | 缺陷 | 修法（档位） |
| --- | --- | --- | --- |
| ① | cis-method `steps/03-problem.md` | 类目指错：「问题陈述精炼」「是/不是分析」指为`分析`类，库实在`诊断`类，按字面 `--category` 过滤找不到 | 一行改（已裁）。**steps 文本在母本面内**：改走母本机制；母本未落地前不动，须提前则报备直改并纳入 discover 普查面。2026-10-08 用户裁定 C·14 不会提前→报备直改分支不触发，①定走挂序 9 随母本批 |
| ② | diy-product-brief / diy-research | distillate 交出面无落点无校验：brief.py＋steps/01~03＋check 全零提（research 06-synthesis 同），按「步骤 Read/Write 唯一权威」执行会产无交出面定稿且门放行 | **重档（已裁）**：brief.py / research.py `check --final` 加 distillate 存在＋五字段非空校验；prfaq `check --final` 校验对称补（2026-10-19 已裁）；brief steps/01~03 补交出面 Write 指令（2026-10-19 已裁） |
| ③ | diy-prfaq `prfaq.py` | `check --output-dir` 相对路径按进程 cwd 解析非 project-root（实测误报 MISSING_FILE 指向源码仓；有同名文件时静默校验错文档） | root 归一，照 `--previous` 分支既有先例（已裁） |
| ④ | diy-viewer | brainstorm 61 技术枚举（brain-methods.csv）未注册进值标签表，渲染报 unmapped——零裸键纪律漏网 | **入本批（已裁）**：照 C·11 W3 §5.1 先例逐条取引擎值域注册（采集口径同 R3，中文值同名标签）；测试面枚举断言若动先报备 |
| ⑤ | 各技能引擎脚本 | YAML 重复键静默覆盖（PyYAML 后值覆盖）：实测 cis-method.yaml `open_questions` 重复键丢 3 条、终门未拦 | load 加 duplicate key 检测（已裁）；违规码＝新码 `DUPLICATE_KEY`（2026-10-19 已裁，与 UNPARSABLE_YAML 性质区分） |
| ⑥ | diy-prd | Create 首跑门必失败：终门 PENDING_DECISION 要求全部 Q 有 answer，而映射规则强制追加上游 open_questions——首跑必回退草稿批复一轮，SKILL.md 未提示 | **轻档（已裁）**：SKILL.md 落盘收尾段明示「定稿前逐条批复 Q（含上游继承项）属必经，Create 首跑门回退属预期」；独有流程句非公共句面，直改不涉母本，discover 普查若见近似变体再并 |
| ⑦ | diy-brainstorm | 条目级锚面缺失：想法/主题聚类/行动计划无稳定 ID，下游只能引 `BS-###` 记录级——粒度太粗（素材单元不可预知，可能取自任一级） | 三级铸稳定 ID（已裁）——锚面判据本体，**归 prd 前置机制化批实施**（见该批「判据细化」段）；ID 形态等待裁项见彼处；viewer 展示与本批 ④ 同批动 |
| ⑧ | diy-viewer | cis-method 键标签漏网：四分支 deliverable 键＋`sessions`/`deliverable` 顶层键未注册 `KEY_LABELS`，渲染直出英文键名（实测问题求解分支至少 13 键缺，创新策略/设计思维/叙事三分支待普查）——零裸键纪律漏网，与 ④ 同族 | 补注册四分支全键（键表逐条取自 steps/02~05「本分支结构」节）＋顶层键；键名是 schema 机器锚点，产物保留英文、仅展示层译名（C·11 W3 先例）；随批核：零裸键验收断言面为何未覆盖 cis-method／brainstorm（④ 同问） |

另（实测通过项，不立待办）：安装器 install.py 冒烟过；brief→prfaq→prd 链路 stakes 消歧有效、constraints 被拒项两跳传播完整；editorial-review 嵌套调用走通（调用无标准命令属别扭级，未登）。

**〔2026-10-21 部分销项·核验〕**：②~⑥⑧ 已完成——Q-103 `3b74ea2`/merge `ba3f67c`（② brief/research/prfaq `--final` distillate 五字段＋brief 三步骤交出面 Write；③ prfaq root 归一）、Q-104 `049d074`（⑤ DUPLICATE_KEY）、Q-105 `53e9090`/merge `90fa9f1`（④ brainstorm 61 枚举入值表；⑧ cis-method 四分支全键标签）、Q-001 `404a5e6`（⑥ diy-prd 首跑门提示，`SKILL.md:69`）。**余①（cis-method 类目指错）未修**——`steps/03-problem.md:77/:96` 仍写「`分析` 类」，原裁走母本批（批 8）不提前直改；**余⑦（想法三级 ID）随夜队列 Q-112**（2026-10-21 已裁三级一体 BI/BT/BA）。

## 待办：接口契约通用设计与架构鉴权面（2026-10-04 用户裁定，攒批随既有批次一起处理，现在不动）

登记来源：审 diy-openapi 时用户提出；跨技能双查属实——两技能正式面对 security/鉴权/通用错误结构零提及，BMAD 源均有先例（`bmad-generate-openapi` step-02 `securitySchemes`＋step-03b Error Response Format；`bmad-create-architecture` step-04 Category 2 Authentication & Security），属迁移瘦身丢面。

- **通用状态码（重档已裁）**：`components/responses` 定义通用状态码；**每个 operation 必挂通用错误 `$ref`**——`check --type openapi` 门校验面联动扩，测试面先裁后动。
- **错误结构（已裁）**：统一错误响应 schema 用 **RFC 9457 problem details**。
- **触发机制（已裁，三层联动）**：前后端分离（接口面存在）→ architecture **必答**鉴权类安全决策（触发落点：规则 4 改写 / 评审维度 / 新规则，随批拟）→ openapi **必须**设计 `securitySchemes`＋`security`，引用架构侧 `D-*` 决策 ID（下游认源 ID 判据）。
- **无鉴权显式留痕（已裁）**：鉴权选「无」＝显式决策落盘（照 BMAD `None` 选项先例），不裸奔。
- **功能分组（2026-10-04 已裁，组合＋重档）**：现状按资源平铺、prd `F-x` 零消费（工作流「逐资源推导」；`paths` 无功能维度锚）。裁：① operation **必挂**功能 `tags`（tag 名含锚，`F-x 功能名` 形态）＋顶层 `tags:` 声明——生态工具原生按 tag 分组；② 引擎校验每个 tag 的 `F-x` 须在 prd.yaml 解析到（同 `x-fr` 校验模式）；③ 推导流同改——走查批次单位从资源改**功能**（一功能内全部端点一批走查）；④ 跨功能共享资源**单归属**（归主功能，他功能仅经 `x-fr` 关联）。
- 排期：随攒批一起处理，与逐项化/母本批同面协调先后（两技能均在 50 文件面内，避免同文件改两遍）。

改动面：diy-architecture SKILL.md（触发落点＋评审面）＋ diy-openapi SKILL.md（结构段 `responses`/`securitySchemes`/`tags`＋工作流走查单位＋DRY 规则扩 `components/responses`）＋ diyc_lib.py 校验面（通用错误 `$ref`·`F-x` tag 解析）＋ viewer 展示层词汇＋相关 tests。

**〔v4·批4a 已销 2026-10-19〕**：①通用错误结构——RFC 9457 problem details＋`components/responses` 通用状态码（默认清单 400/401/403/404/409/500 按需）＋每 operation 必挂通用错误 `$ref`（终门断言）；②鉴权三层联动——architecture 规则 4 改写（问用户形态·安全默认考虑、opt-out 答复落盘）＋安全类四类必答＋规则 8 保留重定位接口面联动；openapi `securitySchemes`＋顶层 `security`（`security: []`＝显式无鉴权留痕）入终门硬门；③功能分组数据面——operation 必挂 `F-x 功能名` tags＋顶层 `tags:` 声明＋F-x 解析到 prd.yaml（prd 缺席/损坏硬 violation exit 1）＋走查单位资源→功能＋跨功能共享资源单归属；④viewer KEY_LABELS 补 securitySchemes/tags 等键（零裸键）。夜队列 Q-106 施工（分支 overnight/2026-10-19/Q-106·合入 `a903268`），全量 1737 passed＋248 subtests 绿·sync 过；展示重组＋行锚归 4b。

## 待办：openapi 接口总览行锚（2026-10-04 用户裁定，待执行）

登记来源：用户看 diy-lab 实测渲染的 openapi.html 接口总览提出「接口没有 id，要增加 id」。

事实（2026-10-04 核实）：
- viewer 接口总览已有「操作 ID」列且值在（viewer.py `render_openapi_section`）；引擎已校验 operationId 必填＋查重（diyc_check_docs.py:396/:412）。
- 全体系实体均有「前缀-编号」锚 ID（FR-x.y / D-x / BS-### / TC-x.y.z / FH-x.y.z），唯接口无——现行接口身份＝operationId＋path＋method 复合锚（五轴段已裁 C 方案）。
- viewer 接口总览行无 HTML 行锚（render_table 行锚取 `item["id"]`，openapi 行字典无该键）——跨页无法深链到具体接口行。

裁定（2026-10-04）：**不铸新 ID**——operationId 即接口唯一身份（复合锚裁定不变、零下游联动）；仅补 viewer 展示：接口总览行加 HTML 行锚（锚值＝operationId，引擎查重保证唯一），供跨页深链（如将来 stories 页 `api_refs` 渲染跳转）。

改动面：viewer.py `render_openapi_section`（行锚；注意 `render_table` 行锚机制取 `item["id"]` 会同步渲染成列——实施时避免「操作 ID」列重复，row-id 参数或本函数自拼，实施时定）＋viewer tests（新增断言，本裁定直接后果同源可逆，按三条件报备）。与「接口契约通用设计与架构鉴权面」批同文件（viewer.py），排先后实施避免改两遍。

**〔2026-10-13 用户裁定〕**：撤 v4·批3a 任务书（taskbook-batch3a.md 转留档），本段**改归批 4 一体落形**——openapi 展示重组（功能分组＋详情表格）后行锚随形落地；锚值＝operationId（2026-10-04 已裁）不变；「row-id 参数 vs 自拼」实现方式随重组后表格形态重定、不单独裁。

**〔2026-10-16 用户裁定〕裁点 B/C 提前闭合**（原随批 4b 任务书呈裁，批 4a 讲解时提前裁）：**B＝是**——requestBody/responses 等详情聚合表格**归批 4 扩面**，4b 一体落形（功能分组＋详情表格＋行锚）；**C＝保留中文**——「操作 ID」列标签**不**弃中文改 operationId 原文（viewer.py KEY_LABELS `"operationId": "操作 ID"` 现状维持）。4b 立书直接引用本两裁、不重呈。

## 待办：viewer index 产物卡片按生成时间排序（2026-10-04 用户提出，登记待裁，现在不动）

登记来源：用户看 diy-lab 实测 index.html 提出「产物按生成时间排，不然眼睛看花了」。

事实（2026-10-04 核实）：
- 现状卡片按**文件名字母序**（viewer.py main: `sorted(out_dir.glob("*.yaml"))` 原序进 `build_index`）——diy-lab 实测 17 份产物，字母序与生成序完全对不上。
- 排序键可用性：全部产物均有 `created`（project/x-project 块，实测 17/17 在场）；但**粒度止于日期**（YYYY-MM-DD）无时分——同日跑完多产物并列分不出先后；产物内无更细时间源；文件 mtime 不可靠（clone/同步刷新）。`created` 无引擎强制校验（diyc_check_docs.py 零提及），漏写可能存在。

裁定（2026-10-04 用户三项）：
- **排序键扩时分秒**：`created` 从 `YYYY-MM-DD` 扩为带时分秒——根治「粒度止于日期、同日并列分不出先后」；落库面随批核（全库产物 schema 结构段 `created:` 行＋diyc 校验是否新增格式断言＋viewer 展示），存量旧值（纯日期）不回填、按当日零点参与排序。
- **兜底次序＝链序（逻辑生成序）**：时分秒仍并列（或值不可比）时按链序排；链序表**来源仍待裁**（viewer 内置照 `DOC_LABELS` 硬编码先例 vs 读 registry 跨包依赖，倾向前者）；非链产物链序表无位 → 排链产物之后（机械推论，不另裁）。
- **缺 `created` 的产物排最后**。

改动面：viewer.py（排序落点：main 渲染序或 build_index 内排序——注意渲染文件循环也用同一序，页内「其他产物」导航链接顺序随之变，属同题一并动）＋viewer tests＋**created 时分秒的 schema 面（随批核）**。与「openapi 接口总览行锚」「接口契约」批同文件（viewer.py），可同批施工。

**〔v4·批3 已销 2026-10-13〕**：viewer.py 三桶全局序（created 升序·并列/不可比走 23 键内置链序兜底·缺 created 殿后；editorial-review/selfcheck 动态挂——读最新记录 target 匹配在场产物挂紧后·匹配不上按非链处理）＋DOC_LABELS 补 wds-brief/wds-trigger/wds-scenarios 三键；created 时分秒落库收口（§7-3 一/二/三裁演进）：A 组 15＋1 引擎铸点 now() 秒级（wds_system 漏铸点照 SS-006-08 同构漏网先例补入）·**created/updated 同铸同改**〔e 裁附记：推翻「updated 不扩」默认，写回刷值一并 now()〕·diyc stamp 新子命令（C 组 10 家「时间键留空＋跑 stamp」·AI 填时指示全部退役·定位照写回族 type/instance 法·CHECK_TYPES 封闭集零扩）·brief.py DATE_RE＋diyc_check_docs 通用 project 时间键断言两格式兼容（存量纯日期合法·空串＝未盖章红）——全量 1718＋248 零红·sync 源装 md5 43/43。
**〔批 3 追裁五项落地 2026-10-15〕**：①清单外 10 家（investigate/project-context/quick-dev/readiness-check/research/retrospective/checkpoint-preview/correct-course/create-story/selfcheck）纳入 stamp 面——STAMP_TYPES 11→21 型（新键 investigation/project-context/spec/readiness/research/retrospective/checkpoint/change-proposal/story-context/selfcheck；spec 键供 quick-dev 与 diy-spec 共写 spec.yaml 用）＋10 SKILL＋9 steps 建文件指示改「留空＋跑 stamp」；②brief.py＋prfaq.py 补 project 时间键非空门（留空＝未盖章红）——prfaq.py DATE_RE 随批两格式扩秒（批 3 §7-3b「凡涉时间格式校验处同步含秒」漏网处一并补）；③test_framework.py today() 死定义删除（含 import datetime）；④回执参数 updated 6 处（analyze×2/reverse/diyc baseline-add/wds_evolution×2）today()→now() 统一秒级；⑤wds_system 局部变量 day→stamp（名实对齐）。施工副产：test_diyc_writeback 13 处「updated==now() 相等断言」跨秒竞态改 NOW_RE 格式断言（模块级单源）；新增用例 3（stamp 新类型走查/brief 非空红/prfaq 非空红＋秒级合法）。

## 待办：viewer 产物页左侧章节目录（TOC）（2026-10-13 用户提出，登记待裁，现在不动）

登记来源：用户提出——viewer 渲染 HTML 时左侧展示章节目录（如 prd 章节多，左侧见目录、点击跳转对应位置）。

事实（2026-10-13 核实）：
- 页面骨架（viewer_pages.py `page()`）＝顶栏（h1＋`nav` 页间导航）＋单栏 `<main>` 正文＋`refpane` 引用详情侧板——**无页内目录**；`nav` 是产物间导航非章节目录，section 标题无锚点跳转入口。
- 产物页按 section 顺序渲染（viewer_pages.py `render_doc_page`）——prd 等长文档页内定位只能滚动。

待裁项：TOC 深度（仅一级 section 标题 vs 含嵌套子节）；形态与响应式（左侧固定边栏 vs 窄屏折叠/隐藏阈值）；覆盖面（全部产物页 vs 章节数达阈值的页才显示）；锚点实现（section 标题铸 id，是否复用既有行锚机制——openapi 行锚批先例）。

裁定（2026-10-16 用户）：②形态/窄屏＝**窄屏隐藏**（隐藏阈值实施时定）；③覆盖面＝**全部产物页显示**（不设章节数阈值）；①TOC 深度＝方向裁「按不同产物分别列」、具体层数待定；④锚点实现＝方向裁「按每个产物各自定」、不搞统一机制；**落位（排哪批）未裁**、本段继续悬置。

改动面：viewer.py（`page()` 骨架＋CSS＋section 渲染加锚）＋viewer tests。与「index 产物排序」「openapi 行锚」批同文件（viewer.py），可同批施工。

## 待办：BMAD 记忆文件实存细看（2026-10-13 用户提出，登记待查，现在不动）

登记来源：用户——想看 BMAD 的记忆文件里到底存了什么、用户强调的东西为何它能记住；当初技能迁移没迁记忆，这个部分需要细致看。

事实（2026-10-13 核实）：
- BMAD 记忆机制在册：agent 记忆实位＝`_bmad/_memory/<agent>-sidecar/`（`_bmad/bmm/module-help.csv:8` 注册 tech-writer `update-standards` 动作写 documentation-standards.md）；**本仓 `_bmad/` 下无 `_memory/` 目录**——用户实际使用时的记忆实存待寻（本仓外项目/全局位置）。
- diy 侧对位物＝experience_repo 经验库（`diy-coder.yaml:10`，全局 `~/.diy-coder/experience`）——与 BMAD agent-sidecar 记忆（用户偏好/标准类）非同物；迁移未覆盖此面。

待办动作：细看 BMAD 记忆体系（存储内容/写入触发/读取时机），产出「存了什么、强调为何能记住」事实清单；再裁 diy 是否补记忆面及形态。**〔2026-10-13 调研已完成〕**报告＝`docs/bmad-skill-map/调研结论-BMAD记忆机制-2026-10-13.md`。核心结论：BMAD 记住强调＝「偏好固化进 `_bmad/custom/` 的 `persistent_facts`＋技能激活时自动读入」（非模型记忆）；四层机制（custom 偏好／agent MEMORY／bmm sidecar／wds 会话状态）中本机仅 custom 层有实存（本仓 20 toml＋doc-style.md＋eng-defaults.md）；diy 零对位面，现状靠宿主 CLAUDE.md 兜底。待裁三项（是否补 persistent_facts 同构面／补则形态／层②③要不要）见报告末节，**未裁不动**。**〔2026-10-17 方向已裁＋设计呈审〕**方向＝「机制要加·按产物/技能挂」；设计方案＝`docs/bmad-skill-map/设计方案-偏好记忆机制-2026-10-17.md`（载体＝`preferences.yaml`、读入＝`resolve` 扩键、写入＝AI 直写 append、保证＝写面 check＋读面概率区、排期＝句搭批 8 随窗）——**五裁点待裁未开工**，原三项随方向裁定收敛于设计五裁点。

## 待办：全库去源路径锚（2026-10-04 用户裁定，专批，现在不动）

登记来源：用户实测——安装后的 diy 体系内 `p-specify.md` 表格引用的 `steps-p/` 9 文件找不到（源在 BMAD wds-4-ux-design，dev 仓 `.claude/skills/` 可解析，1,323 行核对吻合）。裁定：技能文件受众是 AI，正文路径即行为输入——读到即可能去开文件，终端环境（不装 BMAD）读不到 → 轻则空转工具调用，重则困惑后即兴补「源内容」；悬空锚全库清理。

- 方法（已裁·2026-10-04 补）：**逐技能实测**——覆盖技能**全部文本面**（SKILL.md、steps/、data/、templates/、scripts 注释与输出提示等一切随包文本），所写路径逐条实际解析打开，跑不通的统计成清单，针对性修复；实测清单为修复依据。正则普查只作预扫参考：精确口径「源 `含路径串`」180 处/72 文件，抽样 40 条全为注释性溯源、显式读取指令未见——180 是下界，以实测为准（实测天然覆盖无反引号裸路径、「收编自/出处」引导等正则漏网形态）。
- 方案（已裁）：正文去锚自包含——引文/判据值留、路径删；扩查出的显式读取指令改指 diy 自带文件。不随附源文件（第二份源违单一源；AI 回读 BMAD 原文＝迁移改写白做）；不发布时机械剥离（锚多嵌句中，剥不成句）。
- 溯源落点（已裁 dev-only）：行级锚（路径＋行号＋裁定号）集中迁 `docs/bmad-skill-map/` 新台账（文件名落地时定），发布包正文彻底无源路径；dev 仓 BMAD/wds 源文件本体不动。
- 源侧缺陷登记保留条件（已裁·2026-10-04 补）：**正确路径可寻得**（缺陷＝源笔误、文件本体在）→ 错误登记**不保留**；**真幽灵**（正确路径亦不存在）→ 保留「裁/改道」处置事实，源路径细节进 dev-only 台账。实测两例：D12 `object-router.md` 实存于源 `data/object-types/`（笔误，登记可删）；D13 `design-system-router.md` 全库未寻得（幽灵，保留裁的事实）。
- 迁移痕迹零正文（已裁·2026-10-04 补）：裁撤登记/改写说明/净损失登记/归属裁定等**迁移决策记录整块迁 dev-only 台账专门记录，技能正文不留**——不只去路径锚，记录块本身退出正文。技能正文是可执行内容，迁移决策记录属变更台账，载体分离。台账载体可与 迁移计划.md「能力损失台账」合并，落地时定。普查（标记词口径）：真 16 处/14 文件（diy-design 13 处全族＋`diy-dev/steps/wds-accept.md:44` 整节＋`diy-wds-system/data/complexity-router.md:5`；party-mode 2 处系误报——「缺陷台账」指 diy-review 产物非迁移记录）；2026-10-04 用户点名补登 `diy-dev/steps/wds-implement.md:39` / `wds-fix.md:33` 两整节（同族「裁撤与归位（源侧台账）」，原普查时点后新增）→ 计 18 处/16 文件；一审 party-mode 预发现（2026-10-05）：`diy-party-mode/SKILL.md:15`「裁自源技能：…」句＝裁剪说明嵌入正文段（非独立块），「裁自」形态不在标记词口径 → 计 19 处/17 文件；一审 quick-dev 预发现（2026-10-05）：「源技能做法 vs diy 做法」裁改对照注记 6 处/4 文件（SKILL.md:58/:86＋steps/01:21/:22·03:18·06:31——同「裁自」族嵌入正文段）→ 计 25 处/21 文件；「收编自/出处/按裁定 N/普查编号」等旁形态随逐技能实测覆盖（一审 e2e 预发现：BMAD 溯源注记 6 处/4 文件——steps/02-targets:10·03-generate-api:14·04-generate-e2e:10/:15/:17/:29·05-record:48，归本批；一审 test-review 预发现：criteria.yaml 头部迁移裁定注释块＋`source:` 键＋steps 泛指 3 处（02:10·03:24/:33）——数据资产面非 SKILL 正文，归本批、处置随批核；一审 test-gate 预发现：adr-checklist.yaml 路径与源注（:3/:4/:39）＋steps 源泛指约 8 处（02:15 源四级·03:47 源时效线·04:52/:61/:67·05:16/:46/:50/:51），同归本批；一审 retrospective 预发现：泛指形态最重一族——「源技能/源 step-N/源主持纪律」遍布 7 个 steps 文件＋引擎头注约 20 处/8 文件（无路径锚），同归本批；一审 viewer 预发现：viewer.py `# trace:`/批次码出处注约 70 处（C·2/B3/W2/R-x——出处类旁形态，处置面随批核）；口径补记（2026-10-05）：任务书编号（AC-9.x/FR-3.x/R-x/§五 C·N 等）散见 build-loop SKILL.md（4 处）、test-review steps/引擎（R-3/R-4）等——同归「普查编号」旁形态，此前一审未单列，此处补口径；一审 teach-me-testing 预发现：curriculum.yaml 头部迁移裁定注释块＋逐行「源: 英文名」留档注——数据资产面，同 criteria.yaml 先例，归本批；一审 party-mode 预发现（2026-10-05 用户裁定）：SKILL.md:15 尾句「裁自源技能：BMAD 的 agent 名册与人设剧本整段不迁，留的是『多视角独立推理』的方法本体」＝迁移归属裁定正文化——信息搬日志（dev-only 台账）、正文删句，归本批；selfcheck 讲解时用户裁定（2026-10-05·一审前点名）：`diy-selfcheck/SKILL.md:17`「底子」整句（B3 §13 固化的编排＋融合 B4 机器台账/B6 旧值复扫/B7 片间交叉置信度/C·7 单执行者降级形态）＝批次码出处说明——出处类旁形态，正文删句（已裁可去·待本批执行，信息进台账）→ 计 20 处/18 文件）。
- **任务批名词整类禁入正文（2026-10-05 用户裁定·WDS 线一审点名）**：「B6 的已批码 `TOKEN_UNRESOLVED`（本批不新增码）」同款句在 WDS 四技能 SKILL.md 违规码段在场（`diy-wds-brief/SKILL.md:80`·`diy-wds-scenarios/SKILL.md:81`·`diy-wds-system/SKILL.md:82`·`diy-wds-assets/SKILL.md:81`）＝批次码出处注嵌规则正文。裁定：任务批名词（批次码 B3/B6/B7b·裁定号·C·N·SS-###·§N·「本批/同批/移交/已批」句）**全面普查、全量迁 dev-only 台账，技能正文不放**；行为内容（码表、承载语义、判据值）改写自包含留正文，出处句删。预扫（2026-10-05·grep 已批码/本批/`B\d`/`C·\d`/裁定 \d/`SS-###`·.analysis 外）：约 **314 处/99 文件**，遍布 SKILL/steps/scripts 注释/data 资产头注/templates——远超窄口径已计数（20 处/18 文件系标记词口径）；精确清单随批逐技能实测出（正则预扫只作参考·本批既有纪律）。
- 批 2c 预发现（2026-10-12 用户点名·归本批，不动 2c 已呈审面）：用户点名 2 处＝`diy-selfcheck/SKILL.md:40`「B7b 口径：」领起句＋`steps/02-dispatch.md:11`「（B7b 截断教训）」尾注——均照本段已裁原则处置（行为内容「分片写短 YAML、主产物由编排者写」自包含留正文，出处标记删）；同批 2c 新写同族 2 处＝`SKILL.md:48/:55`「照 spec-scan 先例」；原有批次码句余 9 处（SKILL:17〔已点名〕/:72/:74/:75·01:16/:24·03:14·04:24）预扫口径在场零净新。全部补入批 6 实测清单，随逐处呈审定去留。
- **dev 仓内部文档引用同属迁移痕迹**（已裁·2026-10-04 补）：`迁移计划.md:行号`、`*-fidelity.md §节`、`docs/bmad-skill-map/` 路径等 dev 私有管理文档引用**不得出现在技能正文**——发布包必无该文件，且行号/章节号随文档漂移，比 BMAD 源锚更不可解析（例：`prototype-loop.md:12` 的「源侧 `迁移计划.md:210`」）。普查：真 4 处/4 文件（`diy-design/steps/prototype-loop.md:12`、`diy-wds-brief/steps/03-signoff.md:144`、`diy-viewer/scripts/viewer.py:666`、`diy-wds-assets/data/presentation-formats/index.md:25`；`c-discuss.md:6` 系「讨论结论」产物字段名误报）。处置同总则：行为事实改写自包含留正文，出处/行号/编号进台账。一审 test-gate 补登（2026-10-05，原普查漏网）：6 处/4 文件——`diy-test-gate/SKILL.md:67`（裸节号 §十三:459）＋`steps/05-gate.md:17`＋`scripts/gate.py:60/:73`（§十三:459／§二验收 #3·#4·#12）＋`scripts/gate_check.py:13/:665`，皆「迁移计划 §节」形 → 计真 10 处/8 文件；一审 viewer 再补 +2（2026-10-05）：viewer.py:669（迁移计划 §已定补充）＋:165（§五 C·8 裸节号——原普查仅记 :666）→ 计真 12 处/8 文件；一审 diy-tools 补 +4（2026-10-05）：`diyc_mutate.py:2`（迁移计划 §五 阶段 C 第 9 项）＋`diyc_writeback.py:67/:563/:629`（§五 C·8②·迁移计划 §十三）→ 计真 16 处/10 文件（`diyc.py:302` 系 FR-4.5/D-9 全族模板句，归母本批不在此计）。
- 范围（已裁）：整个技能包。排期（已裁）：专批；与逐项化/母本批协调先后（同为 50 文件级正文改动，避免同文件改两遍）。

改动面：diy-coder/skills 72+ 文件正文＋docs/bmad-skill-map 溯源台账新建＋批尾保真走查（b*/c*-fidelity 惯例）。

## 待办：diy-test-design 五轴矩阵＋故障假设落盘（2026-10-04 用户裁定，攒批，现在不动）

**〔v4·批1 已销 2026-10-10〕**：dimension/dimension_audit/fault_hypotheses 段＋kill_target 引 FH ID＋api_refs 铸造面（epics-stories·create-story·story_context）＋diyc 三组规则＋e2e.py record 联动＋viewer 标签＋教学材料三处同步——全量 1648 绿。

登记来源：用户裁定现行「一个 AC 至少一条用例（五态穷举）」（SKILL.md:89）只是完备性下限、标准太小；提高为五轴矩阵＋故障假设（FH）双向闭合；用例量涨 3~5 倍属预期。

- **五轴矩阵（已裁）**：每条非 `已完成` AC × {正向, 边界, 异常, 安全, 性能} 逐轴审过——适用→≥1 TC，不适用→一行理由登记；**审过≠每轴全用例**（硬铺必造装饰品，违 kill_target 纪律）。适用判据（机械可判）：正向恒适用；边界＝AC 含数值/长度/次数/枚举约束；异常＝含拒绝/失败语义或实现面碰外部资源；安全＝涉及输入解析/跨产物引用/证据声明（锚 :82「伪造证据类」）；性能＝AC 或 nfrs 含时限/量级声明。**性能轴限层**：性能用例 `type∈{集成,端到端}`，单元层不出现。
- **异常轴含环境故障注入子类**（已裁）：文件缺席/依赖回执异常/exit≠0/YAML 损坏——不单独立轴；幂等/重入并进属性测试挖掘提示（不立轴）。
- **落盘 A（已裁）**：TC 加 `dimension`（5 值枚举）；顶层 `dimension_audit` 段（每 AC×5 轴：TC 列表或 not_applicable 理由，二选一）；门判双向一致（audit 列的 TC 须真绑该 AC 且 dimension 对应；TC.dimension 须出现在其 AC 对应轴）。`已完成` 故事整段豁免（同现行 ≥1 TC 豁免口径）。
- **一条用例一个轴（已裁）**：跨轴拆用例（矩阵可判前提，涨量主要来源）。
- **FH 落盘（已裁）**：顶层 `fault_hypotheses` 段，每条 {id: FH-x.y.z, ac, text}；`kill_target` 从自由文本改为引用 FH ID（允许列表＝一杀多）；门判「每条 FH 被 ≥1 TC 杀」（封「列 5 条假设只写 1 条用例」洞）；:90 经验挖掘与相关性判据不动，只是产物落盘。diy-augment / diy-e2e-tests 获 FH 追加权（编码后发现新故障先落 FH 再写 TC）。
- **FH 删除权在用户（已裁·2026-10-04 补）**：AI 不得自行删 FH。杀不掉的 FH 照 coverage_gaps 模式记 `[FH-GAP]` reason、`decision: 待办` 交用户当轮裁决——裁「删」→ 删 FH＋`revisions` 留痕（change 引 FH-x.y.z，revisions 用法自 TC 扩及 FH）；裁「不删」→ **必须补 TC**（无「不杀也不删」第三态）；两出口均删 gap 条目；`--final` 禁 `[FH-GAP]` 待办（复用现有禁令）。
- **「砍掉」处置权统一归用户（已裁·2026-10-04 两轮补）**：SKILL.md 三处同族——① :92 逐对体检两层无净关系→重排或砍；② :92 末无独立 kill 的工具→砍；③ :90 装饰品用例→砍或重新瞄准。三处 AI 均只摆证据交用户裁决，不自行删改产物。
- **Update 迁移**：存量自由文本 kill_target 逐条转 FH 条目；kill_target 不入 ID 稳定门（SKILL.md:98），存量 TC 原样保留可对账。
- **openapi 在场→接口用例设计必做（2026-10-04 补裁·当轮闭合）**：`{output_dir}/openapi.yaml` 在场（已定稿）时接口面纳入设计；缺席照旧零提及。登记来源：审 test-design 输入面（SKILL.md:25 不含 openapi.yaml）发现接口用例无据可推、契约↔用例无机械桥。
- **锚定＝AC 侧复合锚（已裁·C 方案）**：epics-stories 铸 AC 时挂 `api_refs`——**operationId＋path+method 复合锚**；与 `design_ref` 同构（同级产物锚·可选·须可解析），合「下游认源 ID」判据（operationId 在 diy-openapi 已按稳定 ID 管理）。多对多归属在铸造期走查落盘、非推导期解链——A（FR 链不可机判）、B（openapi 侧挂 x-ac 时序倒挂：主线 openapi 先于 epics+stories）均否；diy-openapi 零改动。
- **门联动（已裁·强门）**：带 api_refs 的 AC → 接口用例（`type: 集成`、点名锚）必做、照五轴审；被引 operation ≥1 TC；反向悬空 operation（契约有端点、无 AC 引）→ **skip line 式显式登记**（照 epics-stories SKILL.md:70 `<FR-x.y>: <为什么>` 先例），不静默。
- **漂移同步（已裁）**：openapi.updated 晚于 stories.updated → 漂移提示（照 test-design SKILL.md:28 同款）；悬空锚照 UNKNOWN_ID 报。排批：入本段待办（改动面见下）。
- **create-story 上下文包提升（已裁）**：story-context.yaml 的 SC 记录加可选 `api_refs`——聚合该故事全部 AC 的复合锚、去重平铺（照 `design_ref`/`tc_refs` 引用面平铺先例，dev 一跳可达端点清单）；快照口径同 tc_refs（原位重写刷新，不另立同步机制）；story_context.py collect 回执透传。
- 分批：批 1（核心）＝SKILL.md＋diyc_check_docs.py（`tc_declarations` kill_target 改引 ID＋`check_test_plan` 加 dimension/audit/FH 三组规则）＋源↔装两份 sync＋夹具与 9 测试文件 → 全量绿；批 2（下游）＝augment/e2e SKILL.md 补 dimension 写入义务＋viewer.py 渲染两新段（新字段全带中文标签·零裸键）＋author/gate 轻引面核实；批 3（登记）＝底单补行＋教学材料同步（已裁·2026-10-04：curriculum:23/:38 与 quiz:32 三处条目微调至 FH 引用口径，quiz:55 题保留、可加 1 道 FH 门规则新题——不同步则学员按旧口径填自由文字、入门即被 kill_target 引用不可解析拦下）。
- 测试面报备：夹具/测试改动系本裁定直接后果（同源）、git 可逆——按「测试面改动先裁后动」三条件登记。

待裁：无（2026-10-04 openapi 输入面当轮全闭合：锚定 C 方案复合锚／强门联动＋skip line 登记／漂移提示／排批入本段）。

改动面：diy-test-design SKILL.md＋**diy-epics-stories SKILL.md（api_refs schema＋输入面扩 openapi＋悬空 operation 登记）**＋**diy-create-story SKILL.md＋steps/01-target.md·02-artifacts.md（Write 面字段清单／回执 acs 子字段加 api_refs／起草 schema 示例／第 2 步补挂口径照 design_ref 先例；03-05 执行时核实）＋scripts/story_context.py（collect 透传）**＋diy-tools/scripts/diyc_check_docs.py（含 `.claude` 装副本）＋**diyc 校验面（api_refs 可解析·operation 覆盖门，落点执行时核实）**＋tests/diyc_fixture.py＋9 测试文件（test_diyc_check/test_augment/test_e2e/test_author/test_gate/test_test_review/test_story_context/test_retrospective/test_change_proposal）＋diy-augment·diy-e2e-tests SKILL.md＋diy-viewer/scripts/viewer.py＋（执行时核实）diy-test-author·diy-test-gate scripts/steps。

协调：与逐项化/母本/去源路径锚批同为 SKILL.md 正文改动面（test-design 在逐项化超限名单：102 行），实施定先后，避免同文件改两遍。

## 待办：test-author「未建」滞后表述清理（2026-10-04 审 diy-test-framework 发现，随批，现在不动）

登记：diy-test-author 已建成（A 表在列、B3 早已收口），test-framework 两处「未建」条件分支系批次期滞后文本——
- `diy-test-framework/SKILL.md:83` 规则 8「路由与未建技能」：「下游 `diy-test-author` 属 B3 同批（未建成前只在摘要给路由行，不当作可调用技能）」例子过期；修法随批拟（删例子句保留通用纪律「只把已建的 diy 技能当可调用对象」vs 整条改写）。
- `diy-test-framework/steps/06-finish.md:35`：「下一步读 `diy-test-author/SKILL.md`（若已建；未建则以摘要中的路由行交接）」——条件分支删，改直连。

普查分流（全库 grep「未建」5 处/4 文件）：diy-wds-system 三处（SKILL.md:80＋`complexity-router.md:6/:64`）系 `object-types/workflow.md` 真未建的事实登记（非滞后），归「去源路径锚·迁移痕迹零正文」批处置；diy-bmb-module `03-validate.md:29` 是引擎 warning 违规码语义说明（活机制文本），不动。

## 已执行：滞后表述全库普查（2026-10-07，用户点名「语句有问题/多余文字」类跨技能普查，只读）

词族四组：`未建|若已建`·`待登记|下游待`·`≤90/90 行/上限 90`·`标签缺口|降级渲染|通用降级`。**净新增仅 1 处**：diy-bmb-builder steps 三处「≤90 行」（`03-analyze.md:41`·`04-gate.md:18/:20`·`05-finish.md:24`）→ 已补登逐项化批上限落点行。其余命中均在案或活机制：help.py:387「下游待登记」＝链走完分支的运行时枚举（活机制非滞后）；bmb_module.py:388 与 wds_brief/scenarios/trigger 三引擎「尚未建立」＝MISSING_FILE warning 语义（活机制）；wds-brief `03-signoff.md:146`「缺口 2」句面滞后已在一审行裁定归去源锚批（标签实落 viewer.py:48/:400）；wds_brief.py:90 / wds_scenarios.py:101 头注释「viewer 标签缺口登记」＝出处注旁形态（去源锚批口径内）。

## 待办：diy-review steps 步骤深化（2026-10-04 用户提出，2026-10-11 三候选均立项·②③实施子项待裁，现在不动）

登记来源：用户看 `diy-review/steps/` 觉单薄，问补充可能。

裁定（2026-10-11 用户）：**三候选均立项（①②③全做）**。②③实施子项仍待裁——②方法定义识别规则（lambda/嵌套/装饰器）＋扫面口径声明；③形态三选（A 撤/B 降级改写/C 坚持原案＋实证）与 leanness-4 处置；利弊见调研 `diy-coder/.analysis/2026-10-07-execution-plan/research-review-steps-deepen.md` §⑤，推荐 ② 照旧建议落、③ 降级改写。施工排批 7 后（同文件协调在案）。

**〔2026-10-17 用户二裁·②③实施子项闭合〕**：**②＝A 照落**（引擎补齐 untraced 检测，`diyc.py trace` 扩「扫面内方法定义缺 trace 行」报告）；**方法定义识别判据＝写了名字的方法定义才算方法**（匿名如 lambda 不入扫描面——用户原话「写了方法名的算一个方法」，嵌套/装饰器随此判据归类：有名字即入）；diff→扫面口径声明随正文。**③＝B 降级改写，且加内容必落实**——六维每维打法**必须真写出来**落到 bug-log pattern 的 subclass 弹药条目（按 subclass 归档与六维天然对位），falsify.md 正文不增厚（最多末行指针）；「留指针不写打法」不算完成（用户原话「加内容还是要做」）。leanness-4 方向不违、subclass 重叠经弹药落点消解。原三选（A/B/C）作废留档。至此本段②③无待裁项，剩任务书落地，施工仍排批 7 后。

事实（2026-10-04 核实）：
- 抓手盘点：L1/L3/L4 各有机械抓手（`diyc.py trace`／`check --type review`／`design.py audit+check`），**L2 零抓手**——仅一句口诀（坏输入/空None/并发/错误路径/静默兜底＋「真会咬人」），无推导方法无判据；falsify 非功能六维只有名字、「跑临时攻击」零打法；lenses（HALT/空数组合法/归一）与 wds-review（零产出/不采信自述/写权）纪律齐备，不补。
- 规模对比：兄弟技能 steps 单文件 20~82 行（dev 32~50／test-author 20~52／investigate 29~57／retrospective 27~82），diy-review 全部 6~9 行——steps/ 系单文件 SKILL.md 拆分产物，未按步骤展开规程。
- `diyc.py trace` 只解析已有 trace 行 ID（diyc.py:45 `TRACE_LINE_RE`→references/unresolved），不报「方法定义缺 trace 行」——l1 正文自认「整行缺席仍属目读」；旧分析（.analysis/2026-09-13 determinism-1）建议的 untraced 类半截未落。

候选（①方向自洽；②③ 2026-10-11 立项，实施子项待裁）：
- ① **L2 补推导规程**：AC→边界怎么推（输入等价类/域边界／状态字段非法迁移／错误路径静默兜底识别）＋「真会咬人」判据——补推导方法而非固定清单（守 lenses「边界类从内容自身推，不套固定清单」）；须写明与边界穷举透镜分层：L2＝必跑层高危快扫、透镜＝可选全量枚举（防透镜被架空）。
- ② **L1 untraced 机械检测**：`diyc.py trace` 扩「扫面内方法定义缺 trace 行」报告——方法定义识别有误报面（lambda/嵌套函数/扫面口径），先裁后动（测试面纪律）。
- ③ **falsify 六维最小探针**（每维一行打法）：与旧分析 leanness-4「证伪轮向更简」方向相抵、无产出差实证——待裁。

改动面：①③＝diy-review `steps/l2-boundary.md`·`falsify.md`；②＝diy-tools diyc.py＋tests。协调：与逐项化批同文件（diy-review SKILL.md 正文），排先后避免改两遍；本条发现属 diy-review 一审范围（技能逐个审查行动线），一审行待审完由用户勾。

## 待办：diy-e2e-tests 关联 openapi 契约认 ID（2026-10-04 用户裁定，攒批待执行，现在不动）

**〔v4·批1 已销 2026-10-10〕**：A+B 双源＋01-detect 第三上游产物＋TC api_refs 复合锚（record 实核）＋augment 并入同款义务。

登记来源：用户点名 diy-e2e-tests 要关联 openapi 文档、用里面的 ID。

事实（2026-10-04 核实）：
- diy-e2e-tests 全目录（SKILL.md＋steps/）零提及 openapi.yaml / operationId / api_refs；diy-augment 同族零提及（grep 证实）。
- `steps/03-generate-api.md:5` 输入面只有「API 实现（路由、处理器、schema）」；`:30` 契约不清（无 schema、无成文错误码）→ 报出来跳过——openapi.yaml 在场（成文契约）未被消费。
- ID 形态已有裁定根基：operationId 即接口唯一身份（见「openapi 接口总览行锚」段）；五轴批已裁 AC 侧 `api_refs` 复合锚（operationId＋path+method），但本技能不在五轴批改动面（批 2 仅补 dimension 写入义务）。

裁定（2026-10-04 四项全闭合）：
- **通路＝A＋B 双源**：A＝直接读 openapi.yaml，按 operationId 取契约做 oracle（状态码/响应结构/错误码——契约在场不再按「契约不清」跳过）；B＝步骤 2 绑 AC 时顺带取 AC `api_refs` 锚定端点。
- **TC 落锚＝新字段落复合锚**：TC 加可选 `api_refs`（照五轴段 create-story 同名先例；形态＝operationId＋path+method 复合锚，path 即 URL 路径、method 即 get/post）；schema 动 → e2e.py record 校验（锚可解析）＋viewer 渲染联动。
- **在场口径照五轴先例**：openapi.yaml 在场 → API 用例锚定必做；缺席零提及（不加硬门）。
- **openapi 在场＝第三件上游产物（补裁·同日）**：`steps/01-detect.md` 硬门段「上游产物优先」清单加可选第三件——openapi.yaml 在场才算上游产物，随门禁段识别并交接后续步消费；缺席不阻塞、不加硬门（硬门仍只 test-plan.yaml＋stories.yaml 两件）。
- **diy-augment 并入本条**：同族义务同款——API 补测用例同锚定、同在场口径。

改动面：diy-e2e-tests SKILL.md＋steps/01-detect.md·02-targets.md·03-generate-api.md＋diy-augment SKILL.md（＋steps·引擎面，执行时核实）＋TC schema 新字段＋scripts/e2e.py（record 校验）＋viewer＋tests。协调：B 通路依赖五轴批的 AC `api_refs` 字段先行（A 通路不依赖）；与五轴批 2 同文件（两技能 SKILL.md），排先后避免改两遍。

## 待办：变异配置显式化——默认开＋可关（2026-10-04 审 diy-augment 用户裁定，攒批，现在不动）

**〔v4·批1 已销 2026-10-10〕**：mutation 段落 schema（唯一出处 diy-test-design）＋借位载体退役＋diyc 形状校验；「随批核」override 落点已定＝会话显式指令按次开关＋持久改写走 Update 改段＋revisions 留痕。

登记来源：审 diy-augment 规则 5 发现变异系**借位配置**——无自己的配置面：载体＝① test-plan `static_checks[].tool` 中用户会话确认为变异工具的条目（寄生在静态检查滤网上、靠人肉确认）② 会话临时命令；皆无＝未配置＝不跑（**默认关**）。test-design 侧无变异开/关设计位。

裁定（2026-10-04 三项）：
- **配置段形态**：test-plan 顶层加 **`mutation: {enabled: true, tool?}`** 段（schema 归 diy-test-design 唯一出处，augment 只消费——合既有分工；enabled 默认 true，tool 可选缺省走既有「按栈选」：Python→cosmic-ray、JS→stryker）。
- **默认开＝日常任务级**：每任务 done 后 `--scope` 档默认跑变异（接受 runner 循环成本上升；发版 `--full` 档不变）。
- **关闭粒度**：全局开关＋**任务级/发版级 override**（关默认、单任务开；开默认、单任务关——override 落点随批核）。
- 借位条款退役：augment 规则 5 的①②载体删除，改读 `mutation` 段。

改动面：diy-test-design SKILL.md（schema 段）＋diy-augment SKILL.md（规则 5 改写）＋diyc 校验面（mutation 段格式/枚举，随批核）＋tests。协调：augment SKILL 已在五轴批 2 与 e2e 认 ID 批改动面——三批同文件，排先后或并面施工。

## 已执行：§6「精准简练」适用面收窄——只有有产物的技能（2026-10-05 用户裁定，当日执行完毕）

裁定：「精准简练」是**产物纪律**，只有有产物的技能才需要；「适用面=全部技能不设非成员」（2026-09-19 旧裁定）作废。

- 判据：**正文零写回自述**（零写回/零写面/不改任何文件）；frontmatter `outputs: —` 不作判据——selfcheck 同为 — 但产 dogfood 人读报告（:38-40）故保留；dev/augment/build-loop/review 写代码或写回 sprint/stories/bug-log 均保留。
- 已删 5 家：viewer／elicit／help／party-mode／tools（`tests/test_suite_texts.py` 的 `PRECISE_NON_MEMBERS` 台账五员；tools 2026-10-05 用户裁定入删除类——借 baseline-add 写 reason 但自身零散文产出）；连带退役：test_elicit / test_help / test_party_mode 各自的 PRECISE 在场断言与「§6→§2 顺序」断言。
- 联动：diy-help 游离句条（2026-10-03 段）已随本批处置；待办③ suite-texts.yaml 的 members 字段以本批台账为起点。

## 已执行：runner 冲刺末三连——e2e → test-review → test-gate 自动调用（2026-10-05 用户裁定，当批已施工）

裁定（2026-10-05 用户四点＋两裁点）：
- **自动连跑**：主循环全终态后依次 spawn diy-e2e-tests → diy-test-review → diy-test-gate（顺序使 e2e 落的测试代码与 TC 进后两者审计面）；三技能全 report-only——结论落各自产物、不重开任务、不阻塞退出，汇入收尾汇总由人裁断。
- **旗标**：`--skip-post` 关三连／`--post-only` 只跑三连不驱动主循环（服务人装完 e2e 框架后补跑与裁断修复后复核）；`--post-only` 要求任务全终态（半程面的矩阵分母不完整）；与 `--skip-post`/`--augment-only`/`--reopen-failed` 互斥；WDS 线对两旗标显式拒绝（与 augment 面同款）。
- **e2e 无头处置（不破硬门）**：跑不起来先查 test-plan 前层 TC status 鉴别归属——前层已过而 e2e 层起不来＝e2e 面问题，按技能「失败当场修」处理；修不动（含无框架——技能硬门「绝不安装任何东西」）零用例收场给一行诊断，人装框架后 `--post-only` 补跑。
- **review/gate 无头落草稿**：记录 `status: 草稿` 待人核定稿（定稿＝人审，与 sprint「已定稿」硬门同哲学）；runner note 行以产物最新记录为准（自报≠已处置），e2e note＝退出码＋会话摘要首行。

改动面（已落）：`diy-coder/runner.py`（三 spawn＋note 判读＋旗标＋`_spawn` 增返 result）／三技能 SKILL.md description 补自动调用声明／diy-build-loop 规则 9 签名行／README 工作流链条／`tests/stub_claude.py`（post 会话路由）＋`tests/test_runner.py`（TC_Post_Face 七用例；`run_runner` 缺省注入 `--skip-post` 隔离既有测试，`--line wds` 不注入）；install.py 已同步安装形态。

遗留待办（YAGNI 后补）：`--reopen-failed` 现只认 `augment:失败`；e2e/gate 发现的实现缺陷重开＝人手改 sprint.yaml 对应任务回 `进行中` 后重跑 runner。若实际冲刺中 e2e 失败量大，再裁扩展 reopen 认「关联端到端失败 TC 的任务」（需 TC→AC→story 映射解析）。〔2026-10-17 升格：开关扩展框架作废留档——真实需求＝失败归因分叉＋分路修复的工作流，见「待办：runner 三连失败处置工作流」〕

## 待办：test_pending_precise_brief 跨窗口中间态红——检查任务（2026-10-05 发现并查明，现在不动）

**〔v4·批0 已销 2026-10-09〕**：全量 1628 passed＋248 subtests（含本测试）零红，检查任务完结。

现象：2026-10-05 三连批全量跑时 `tests/test_suite_texts.py::PendingLandingTests::test_pending_precise_brief` 间歇红一次（单跑过、复跑全绿，当时误判 flaky）。

查明：非 flaky——§6 批两半（`PRECISE_NON_MEMBERS` 台账改判 vs elicit/help/party-mode 删句）在两个窗口非原子落盘，对账断言跨越中间态窗口即红；两半齐后稳定绿。

检查任务（随 §6 批闭合执行，不动手改）：§6 批收口时确认该测试在全量下稳定绿即可；若再红，先查是否又是并行批中间态（台账先行/正文后至），不要直接改断言。

## 待办：diy-selfcheck 产物 YAML 化（2026-10-05 用户裁定，待用户点头开工）

**〔v4·批2c 已销 2026-10-11〕**：四项方案施工完毕——主产物 `{output_dir}/selfcheck.yaml` 集合形态（SC-###/status 草稿|已定稿/anchor·target·findings 三源·disposals·rescans·b_review·revisions 区块）＋分片 `selfcheck/part-<片名>.yaml` 化＋自带引擎 `selfcheck.py check --final` 六义务终门＋viewer 标签（零裸键）；全量 1702 passed＋248 subtests 零红。⑦「PRECISE_NON_MEMBERS 同步退出」系登记笔误已勘正零动作（台账从未含 selfcheck）。

登记来源：用户审查 diy-selfcheck 产物节——主产物 md（`dogfood-scan-<日期>.md` 落目标同目录、不碰 `{output_dir}`、`outputs: —`）违背家族「YAML 单一源＋viewer 渲染」原则，全库 50 技能唯一例外。

裁定（2026-10-05 四项）：
- **主产物改 `{output_dir}/selfcheck.yaml`**（集合形态、`SC-###` 记录、`status: 草稿|已定稿`）；md 人读报告退役，人读视图走 viewer 渲染（viewer 补 selfcheck.yaml 标签——零裸键纪律）。
- **区块**：`anchor`（md5＋commit＋执行形态＋分片数——现 md 首行版本锚转正为字段）/ `target` / `findings[]`（三源合一，`source: 预演|引用核对|对抗` 区分；预演片条目**引 SS-### 不复制**——机器台账仍归 diy-spec-scan、边界不动；引用核对/对抗片 findings 从「只进人读报告」改落此处，自有字段不撑破预演八类枚举）/ `disposals[]`（D 表）/ `rescans`（两轮复扫·旧值清零凭证）/ `b_review`（B 部分必出）/ `revisions`。
- **分片 part 文件同批 YAML 化**（`part-<片名>.yaml`）；B7b 截断教训口径收窄为「子代理不写长结构化」——分片写短 YAML、主产物由编排者写（教训本义防子代理长产物截断，条款随批改写）。
- **新增终门 `selfcheck.py check --final`**（自带引擎，同 analyze/teach 先例——不进 diyc 主线 8 型封闭集）：必出 B 部分、引用核对必报总数、每条 finding 有处置记录、复扫两轮在场、零 `[假设]`、SS 引用可解析。

场景口径：dogfood 主场景随落点扩为**任意产物自检**（不再限任务书——`target.kind` 枚举随批核）。

连锁：frontmatter `outputs` 改 `selfcheck.yaml`；SKILL.md:23「不解析实例目录、不碰 {output_dir}」条款改写；**§6 加回**（YAML 化后重新成为写产物技能——今日适用面清零后的回流首例，`PRECISE_NON_MEMBERS` 台账同步退出）；测试面新断言。

改动面：diy-selfcheck SKILL.md＋steps×5＋新 `scripts/selfcheck.py`＋viewer 标签＋tests。协调：与逐项化批同为 SKILL.md 改动面（现 55 行距上限远，冲突小）。

## 待办：爆炸半径分析注入 diy-review 与测试用例设计技能族（2026-10-05 用户提出，登记待裁，现在不动）

**〔v4·批1 已销 2026-10-10〕**：review findings radius 标注/按半径排序（禁数值严重度）＋FH/TC radius 字段（枚举 局部|模块|跨模块|系统|外部）＋test-design/e2e/augment 三技能定制标签＋值域收口引擎校验＋viewer 中文标签注册。

登记来源：用户问爆炸半径分析能否用于测试用例设计堵漏，结论可（覆盖优先级判据＋故障假设排序轴·非用例生成方法），点名 diy-review 与其他测试用例设计技能增加此类内容。

事实（2026-10-05 核实）：
- 全库「爆炸半径」仅在 4 技能且均为改动影响评估：checkpoint-preview（SKILL.md:77＋steps/03——风险按半径排序＋禁数值严重度＋枚举标签）、quick-dev（SKILL.md＋steps/01·06）、create-story（steps/03）、correct-course（steps/02）。
- diy-review 全目录零提及爆炸半径/风险/影响面——findings 只按路由（意图缺口/规格缺陷/小修/后置）分类，无影响排序维度。
- 测试用例设计面零提及：test-design 五轴枚举（正向/边界/异常/安全/性能）无此轴；e2e-tests、augment 同零。

裁定（2026-10-05 四项）：
- **1b 独立面**：diy-review findings 加影响标注/排序（不动「steps 深化」批·两批独立）；判决规则不联动——维持「后置永不阻断」纪律，要联动另裁。
- **2b FH 排序判据**：不动五轴枚举与 audit 门；FH 条目标半径、按半径排序——先为炸得最广的假设设计攻击用例。**依赖五轴批先行**（FH 段系其新增），排期随之。
- **3 范围＝test-design＋e2e＋augment 三技能**；test-author/review/gate 不动。与五轴批 2（同动 e2e/augment SKILL）**同批施工一并排期**，避免同文件改两遍。
- **4 各技能定制标签＋词汇漂移防治**（已核·2026-10-05 用户同意）：①结构统一——跨技能字段形态统一（字段名一致·具体名随批拟）；②值域收口引擎——各技能标签枚举活在各自引擎终门校验（改标签须过引擎·漂移被机械拦住）；③viewer 照值域注册中文标签（C·11 W3 先例·零裸键）；④「按半径排序＋禁数值严重度」纪律句若判公共，随 discover 普查归 suite-texts 家族裁，不提前单建。

协调：diy-review 与「steps 深化」批＋逐项化批同文件；test-design 与五轴批＋逐项化批同文件；e2e/augment 与五轴批 2＋e2e 认 ID 批同文件——多批同文件，施工前统一排期。改动面：diy-review SKILL.md（findings 半径标注/排序）＋test-design/e2e/augment SKILL.md＋各自引擎校验面（FH/TC 半径字段·枚举）＋viewer＋tests。

## 待办：diy-analyze 吸收 arch-analyze 职能（2026-10-05 用户提出，方向已裁·实施待裁，现在不动）

**〔2026-10-17 方向推翻·本段作废〕**：用户裁定 arch-analyze **不迁移**——核实用面＝体系内零功能使用（仅 4 句边界路由文本指向它，无任何链/引擎消费）＋`analysis.yaml` 单文件形态不适合文档集体检（形态错配）；10-05「职能由 diy-analyze 取代」系未核使用面所拍，翻案有据。原三待裁（形态 A/B／产物面／边界句）全部作废；处置并入新段「diy-analyze 定位收口与产物依赖缺席总则」。arch-analyze 留作用户全局私有工具、不进套件。

登记来源：用户裁定——用户级全局技能 `arch-analyze` 将不再安装，职能由 diy-analyze 取代；套件内不得再路由到套件外技能。

事实（2026-10-05 核实）：
- 套件内 arch-analyze 引用 4 处/3 文件：`diy-analyze/SKILL.md:27`（门禁边界句「要体检任意项目的代码库架构 → 用你的 arch-analyze」）＋`:73`（规则 9 vs 边界条）＋`steps/01-define.md:55`（--codebase 不可读时路由句）＋`tests/test_diy_analyze.py:365`（断言边界句在场）。
- 技术面 diy-analyze 已支持任意路径（`init --codebase <path>`，无 diy 限定）——缺的是定位与路由句，不是能力。
- 形态差异（取代的实质缺口）：arch-analyze＝全维度体检（结构/质量/模式/依赖/扩展性/安全/性能）＋markdown 文档集落 `docs/arch/`（架构化文件清单＋工程级概述＋文件夹级文档）；diy-analyze＝单问取证＋`analysis.yaml` 单文件＋AN 锚＋引擎终门。

待裁：
- 取代形态：A. diy-analyze 加「全库体检」模式分支（question 合法形态放宽 or 新模式）vs B. 保持单问形态、多条单问覆盖体检（零模式改动）vs C. 其他。
- 产物面：体检规模是否撑爆 analysis.yaml 单文件；arch-analyze 的「文件夹级文档集」形态是否还有需求（保留进产物 vs 弃——弃则功能净损失要留痕）。
- 边界句改写：4 处引用处置（删路由句/改「套件内自理」口径）；:365 测试断言随改——测试面先裁后动。
- 底单联动：C 表 diy-analyze 用途列与一审行边界描述随批对齐。

改动面：diy-analyze SKILL.md（:27/:73）＋steps/01-define.md:55＋analyze.py（若模式/字段变）＋viewer（若产物扩）＋tests（:365 断言＋新面）＋底单 C 表行。协调：与逐项化批同文件（现 76 行不超限·冲突小）。

## 待办：diy-wds-trigger Layer 1 方法本体迁入（2026-10-05 用户裁定，未开工·待用户点头，现在不动）

登记来源：用户审 diy-wds-trigger 发现并裁定——裁定 9 称「源侧 5 条学习材料引用路径失效」并把 Layer 1「Learn WDS Form」标为不可用，但其中 2 条的方法本体实存于本仓 `_bmad/wds/data/agent-guides/saga/`；**安装 diy 不会安装 bmad**，技能不得依赖 `_bmad` 路径——「要迁移就都迁移完」。

事实（2026-10-05 核实）：
- 裁定 9 落点两处：`diy-wds-trigger/SKILL.md:80`＋`steps/01-mode.md:34`（含原 5 条引用清单、「不伪造方法层文档」「能力损失不登记为偏离」口径）。
- 两份文件实存且行数已核：`saga/trigger-mapping.md` 653 行＋`saga/dream-up-approach.md` 1,034 行＝1,687 行（Layer 1 方法本体）；其余 3 条原引用确不存在（无源可迁）。
- 同目录共享面已有两先例、体量级不同：wds-brief `05-content.md:75/:89` 将 `seo-strategy-guide.md`／`content-structure-principles.md` **内联进步骤正文**（口径「该文件在 diy 侧不存在→本批内联」·条目级精要）；diy-design `p-specify.md:57` 将 freya `meta-content-guide` 判据值定案内联（SS-030-08）。本件是第三例但是**整层方法本体**（1,687 行），内联＝方法折损，故用户裁向整迁。
- 测试面无钉住裁定 9 措辞的断言（test_wds_trigger.py 零命中「第 1 层/不可用/Learn WDS」·已核）。

待裁（开工前须点头）：
- 迁入形态与落点：A. 整文件迁入技能目录（如 `references/`·保 1,687 行方法本体·Layer 1 学习材料完整复活）vs B. 内联精要（wds-brief 先例·正文预算压力小）。用户裁定句「都迁移完」倾向 A，落点目录名待定。
- 裁定 9 解封范围：Layer 1 从「不可用」改「可用」后，S/D 降级模式第 1 层是否随之恢复；「不得伪造方法层文档」句随迁入失效回改两处。
- 权威双轨：迁入文档 vs 既有自审基准（键表＋06-finish 质检）谁为 Layer 1 权威；01-mode.md:34「对照见 layer1 调研报告」注记随改。
- 3 条确不存在材料维持「能力损失」口径不变（无源可迁）。

改动面：diy-wds-trigger SKILL.md:80＋steps/01-mode.md:34（＋02~06 若第 1 层贯通）＋新迁文件＋tests（回归）。协调：与逐项化批同文件；属 WDS 线一审范围（45/50·trigger 审查中）——一审完毕行随批引用本段。

开工时先普查全库同类（用户点名 2026-10-05）：判据＝技能正文引用 **diy 安装布局外路径**（`_bmad/`·源仓 `docs/`/`src/`）作**运行时输入**，非纯溯源注记。已核在案三处：本件（功能依赖·真缺）；wds-brief `05-content.md:75/:89`（内容已内联·`_bmad` 句面残留＝溯源注记型·归去源锚批）；diy-design `p-specify.md:57`（判据已内联·同前）。普查找「功能依赖型」漏网——`_bmad|agent-guides` 全库 grep 已跑（.analysis 外仅上述命中），源仓 `docs/`/`src/` 形态需借去源锚批普查台账交叉分类（两批判据分工：功能依赖归本批·溯源注记归去源锚批）。

## 待办：技能正文拍板/裁定注记迁日志（2026-10-05 用户提出·当日四项全裁，并入去源锚批，现在不动）

登记来源：用户点名 `diy-wds-assets/SKILL.md:16`「（用户 2026-09-21 拍板：『我直接出 html 就行了』）」——拍板内容属本仓决策史，应记日志/台账，不应写进技能正文（安装面随技能分发，读者是使用方非迁移方）。

事实（2026-10-05 预扫）：
- 带日期拍板注记 7 处/7 文件（`.analysis/` 各批任务书/裁定录＝日志本体，合规不计；tests 零钉住已核）：
  - diy-wds-assets：SKILL.md:16＋steps/01-wireframes.md:69（「我直接出 html 就行了」）
  - diy-wds-system：steps/02-import.md:10＋steps/04-edit.md:12＋data/token-vocabulary.yaml:3＋scripts/wds_system.py:21（裁定 5/6 溯源句）
  - diy-viewer/scripts/viewer_refs.py FOLDED_KEYS 注释（revisions 留痕裁定）
- 同族更广变体：无日期「裁定 N」编号锚 297 处/97 文件（wds 线＋design＋reverse 密集；编号指向 `.analysis` 裁定表，安装面内无解析对象）。
- 与去源锚批预扫（314 处/99 文件）重合为主：该批 grep 口径已含 `裁定 \d`——本段 297 处几乎全在场内；净新增＝「用户 <日期> 拍板」引语句式（7 处中 6 处因带裁定号/迁移计划引用已在场，唯 SKILL.md:16 纯引语句净新）。

已裁（2026-10-05）：
- 范围＝宽口径：连「裁定 N」整类一起清；**逐处清单先呈审**——每处具体去留由用户过目后定，不整类盲删。
- 落点＝统一位置：底单待办日志需求盘点——需迁移日志的只有去源锚批一族（:401 已裁 dev-only 台账·落 `docs/bmad-skill-map/` 新台账·文件名落地时定；:403 载体可与迁移计划「能力损失台账」合并）；其余「留痕/台账」字样（无鉴权留痕、PRECISE_NON_MEMBERS、baseline 台账等）系技能行为语义非迁移日志，不立第二载体——拍板类信息同管道收。
- 并批＝并入去源锚批一次扫完（两批 grep 口径已证重合；本段为该批子项，「用户日期拍板」句式补入其标记词族）。
- 处置＝删＋改写成自足句（非纯删，规则本体不靠拍板句支撑）。

执行门（两道·均须用户点头）：① 逐处去留清单先呈审；② 删除＋改写后的句面效果呈审，过目后才动手改文件。

改动面：随去源锚批（其台账新建＋正文清理一体执行）；tests 无钉住已核。

## 第二批待办（2026-10-10 起·v4 批 1 审核中发现，与上方第一批待办〔2026-10-03~05 登记〕区分）

### 待办：test-plan 终门「FH 被杀」口径——引用与实测结果脱钩（2026-10-10 v4 批 1 审核发现·2026-10-16 已裁双口径分时点·2026-10-21 已销：夜队列 Q-102 `d1879b3`）

登记来源：用户审核批 1 产物（diy-test-design/SKILL.md，提交 `5183546`）时问「新故障先落 FH 再写 TC，是否有编码/测试/结果回写字段」——核实回写机制后点出终门缺口。

事实（2026-10-10 核实）：
- 回写机制已闭环、非缺口：`TC.status: 待办|通过|失败` 由 diy-dev / diy-build-loop 经 `diyc.py green` 机械写回；diy-augment / diy-e2e-tests 只追加跑过的用例（天生带实测 status）。FH 不存「已杀」字段＝设计选择（派生状态：被 ≥1 条 `status: 通过` TC 引用即被杀——单一事实源，避免在 FH 上维护第二份状态）。
- 缺口本体：`diyc_check_docs.py` `check_test_plan` final 段「每条 FH 被 ≥1 TC 杀」（:944-958·批 1 工作树版）只收 `kill_target` 引用、不看 `TC.status`——引用某 FH 的 TC `status: 失败`（故障为真未修完）甚至 `待办`（未跑），门照样判「被杀」。
- 时点分裂：设计期跑 `--final` 全待办，核引用是唯一可行口径（自洽）；实现期（green 回写 / augment·e2e 追加后）再跑 `--final`，「被杀」与实测结果脱钩。

已裁（2026-10-16·双口径分时点，推翻三选项框架）：
- **判时点**＝任务书的状态＋测试是否编写完 → 设计期 / 编码期；
- **编码期＝收紧**（原②）：FH 须被 ≥1 条 `status: 通过` 的 TC 引用；
- **设计期＝引用口径**（＝原①现状）：只查每条 FH 有无 ≥1 TC 引用、不看 `status`——保住设计期结构把关；设计期红不算有问题；
- 原三选项（①②③）作废留档：①维持现状——「被杀」＝被引用，实测结果归 diy-test-gate 管；②收紧——final 时 FH 须被 ≥1 条 `status: 通过` 的 TC 引用；③折中——`status: 失败` TC 的 kill_target 引用不计数（`待办` 仍计）；
- 判据的机械定义（任务书取哪个状态字段／「测试编写完」如何算）随任务书呈裁。

改动面：`diyc_check_docs.py` final 段＋`tests/test_diyc_check.py`（测试面系本裁定直接后果·同源）；另动 diy-test-design SKILL.md 终门口径句（双口径分时点须与提示词同口径）。

**〔已销 2026-10-21·核验〕**：双口径已落地——`diyc_check_docs_testplan.py` final 段按 `coding_phase`（任一 TC.status ≠ 待办）分设计期引用口径／编码期收紧；`tests/test_diyc_check.py:615`（设计期）／`:623`（编码期）断言在案；`diy-test-design/SKILL.md:40` 终门口径句已同源。落地提交 `d1879b3`（夜队列 Q-102）。注：原改动面所指 `diyc_check_docs.py` 已拆分，FH 段现位于 `diyc_check_docs_testplan.py`。

### 待办：枚举值跨技能一致性——回查关卡先行，方案 A 注入后并（2026-10-11 用户认可两步路径，登记排期，现在不动）

登记来源：用户问「同一枚举 a 处 5 个值、b 处 4 个值」如何防止（各使用点各自手维护）。核实后给出两步路径，用户认可、登第二批待办。

事实：
- 单点已有：`diyc_check_docs.py:31-39` 九个枚举常量（RADII/DIMENSIONS/TC_STATUSES 等，`# rule:` 注释锚回 SKILL.md 规则位），已用于**产物数据**校验（值非法=红）。
- 缺口=文档面：SKILL.md schema 行（diy-test-design:52 radius、diy-review findings 同族）、viewer 中文标签各自手维护、无引擎回查——漂移只发生在这一层。
- 方案 A 引擎（sync_texts.py＋suite-texts.yaml）未开工（库内无文件），公共条款待办③仍开放。

方案（已认可·两步）：
①查而不写——每个枚举常量登记「出现面清单」（封闭世界），check 引擎逐面提取枚举文本、与常量断言集合相等；漂移/缺值/新面私加=红。viewer 标签值域读同一常量。
②引擎升级——方案 A 开工后枚举并入 YAML 单点派发；①回查降为兜底关卡，不撤。

改动面（做①时）：`diyc_check_docs.py`（面清单＋extract＋断言）＋`tests/test_diyc_check.py`；viewer 标签接线随①范围定。

### 待办：spec-scan kind 判据规则表（2026-10-11 批 2c 立书调研发现·2026-10-16 已裁闭合·2026-10-21 已销：夜队列 Q-108 `36a780c`）

登记来源：批 2c 裁⑤讨论——`target.kind` 现由执行者（AI）现场判定（`01-collect.md:20`「由你判定（引擎不给）」），四条定义是唯一判据、无规则表＝非确定性；每轮问人＝低效。用户裁定登底单，两技能规则表**同批同文一次立**。

事实：
- 四选一枚举在案（`01-collect.md:20-25`＝任务书|技能|规格|文档）；边界弹性（prd/epic/story/架构）2b① 裁「判法在执行者」＝归 AI 裁量，无兜底规则。
- selfcheck 侧同源：2c 裁⑤拟三阶判据链，规则表写 selfcheck 01＝2c 面内（经派发指令传片 A 照录，两账同源不依赖本段动工）。
- 不造通用共享文档（安装自包含模型＋两技能读取纪律开洞）；公共内容方案 A（sync_texts）落地后收编候选。

方案（2026-10-11 讨论共识·待正式裁）：
- 三阶判据链：① 用户明示 kind 照录 → ② 规则表机械判（`SKILL.md+steps`→技能；名字含 prd/epic/story/架构→规格；带分工施工指令→任务书；无执行结构→文档）→ ③ 模糊档 AI 判＋播报纠错（或先问一次，形态待裁）。
- spec-scan 侧动工前与 selfcheck 侧（2c 裁⑤回填件）对表同文；2b「判法在执行者」运行态维持至规则表落地。

已裁（2026-10-16·部分）：
- **模糊档形态＝乙**（先问一次）——三阶链走完仍模糊，AI 不代判、停下来问用户；原③「AI 判＋播报纠错」作废。
- **方案不照原样整体裁可**——三阶链（①明示照录②机械判③模糊问人）保留，但缺一块：须补**「整个 diy 体系产物→类型」对照表**（封闭世界：体系全部产物——prd/architecture/sprint/design/test-plan/SKILL/steps/任务书……逐个归 任务书|技能|规格|文档 四类；判据从「名字含 prd/epic/story/架构」启发式升级为查表定归）。补块后方案整体重呈裁。
- **第二补块（2026-10-16 用户裁「并进」）：文档路由 03 步补「消费向轻扫」口径**——文档不整篇预演，只扫两类：①规范性语句（「须／禁止／唯一／优先／才算」等 AI 会照着行动的句子）逐句查两读；②指涉可解析性（引用 ID／文件／术语落盘是否存在、唯一）。判据表述修正：风险轴＝「谁以什么方式消费它」（机械消费靠引擎断言／语义消费靠扫＋写作纪律），「文档＝无防护」作废；与对照表并列为方案第二补块，同随整体重呈裁。深审互补面＝diy-editorial-review 已有 `--reader-type 人类|LLM` 档（单篇深审·建议制），轻扫是流水线点查、editorial-review 是重点文稿深审，不互代。
- **整体裁可（2026-10-16）**：三阶链（①用户明示照录→②体系内查表定归／体系外结构判兜底→③模糊档问人＝乙）＋对照表（规格从紧＝prd/brief/prfaq/epics/stories/architecture/openapi/design/test-plan/spec/story-context/change-proposal＋WDS 四产物 trigger/scenarios/system/brief；技能＝SKILL.md/steps/模板与教学资产；任务书＝taskbook*；文档＝sprint/review/mutation-report/selfcheck/spec-scan/investigation/research/retrospective/checkpoint/editorial-review/readiness/WDS assets 清单/evolution；⚠ 四行 prfaq/story-context/change-proposal/project-context 从紧归规格）＋第二补块文档轻扫口径，整体裁可。两键核实结论＝产物真名 test-plan.yaml、STAMP 键 test-design 错位（缺陷另立新待办段）。
- 排期待定。现成盘点素材（动工时核）：STAMP_TYPES 21 型＋diyc check CHECK_TYPES 9 类型。

改动面（做时）：`diy-spec-scan/steps/01-collect.md:20-25` 定目标类型节＋`tests/test_spec_scan.py` kind 断言面（2b 落）随之扩＝测试面先裁后动。

**〔2026-10-21 已销·核验〕**：Q-108 已合入 dev（实施 `36a780c`·merge `832eb55`）——`diy-spec-scan/steps/01-collect.md` 与 `diy-selfcheck/steps/01-freeze.md` 同文落三阶链＋体系产物对照表＋文档轻扫口径；`tests/test_spec_scan.py` 两处 kind 断言在场。后续「kind 判据表引擎化」另登本底单第二批待办（Q-113 待跑）。

### 待办：wds-assets 提示词（Prompt Keywords / Prompt Recipe）翻译（2026-10-13 用户提出并两裁执行，已销）

登记来源：汉化插队批呈审时用户指示「提示词也要翻译」——该批按裁断保留英文未翻，补登待办。

一裁（2026-10-13）：标题下加中文行，词行不动——随审核四裁 `9eb64e2` 落地、`7c6e9c5` 销项。

二裁（2026-10-13，推翻一裁「词行不动」）：**英文行保留，下行加中文对照**；注行「提示词关键词」改「**提示词**」；英文标题与 steps/模板引用面不动；**Prompt Recipe（presentation 7 卡）入范围**——配方英文段后加中文对照段，导语补「段后中文对照仅供理解」。事实更正：`## Prompt Keywords` 实存 16 卡（content 10＋design 6），presentation 7 卡仅 Recipe 节——首登「23 个数据文件 Keywords 节」计数不准。〔已销 2026-10-13·16 卡词行对照＋7 卡配方对照落地，随批呈审〕

### 待办：architecture 规则 4「安全类决策只在需求要求时才成型」说法有误——架构必须要有安全类决策（2026-10-16 用户提出，登记待裁，现在不动）

登记来源：批 4a 任务书讲解中用户裁定——任务书 §2-2 记述规则 4 与「鉴权必答」存在字面张力，用户点出前提本身有误：**架构必须要有安全类决策**；安全类决策属必答面，不是「需求要求时才成型」的可选横切关切。

事实（2026-10-16 核实）：
- 规则 4 原文（`diy-architecture/SKILL.md:87`）：「**决策只为需求存在。** 持久化 / 安全 / 性能这类横切关切，也只在某条 FR/NFR（或 WDS 线的 `SC-<nn>` / `SC-<nn>.P<n>`）要求时才成型——不臆造架构。」——安全类被列在「需求要求时才成型」的横切关切内。
- 批 4a 已裁丙＝新规则 8 只盖**鉴权**一类；安全类决策**整体**必答与规则 4 现句面直接冲突，批 4a 未覆盖。
- 批 4a 任务书 §2-2「字面张力」系按规则 4 现句面如实记述；本待办只登记不动任务书（登记不动手）。

待裁项：
- 修订落点：规则 4 改写（安全移出横切关切或加必答例外）vs 扩批 4a 规则 8 为「安全类决策必答」并与规则 4 对表。
- 与批 4a 排次：随批 4a 一并施工 vs 独立后批；随批则任务书 §3 改动面须补 architecture 面（先裁后动）。
- 安全类覆盖面：全类必答（鉴权/加密/输入校验…）vs 限指定子类——判据待定。

**〔2026-10-17 用户三裁〕三待裁项全闭合**：**落点＝A 规则 4 改写**（安全移出横切关切「需求要求时才成型」名单、改为必答面——推翻 10-15 批 4a 裁丙「规则 4 不动」之前提，甲的实质经三裁吸收）；**覆盖面＝全类必答**（鉴权/加密/输入校验等全类显式作答·含显式选「无」＝决策落盘）；**排次＝随批 4a 一并施工**（同文件规则区一次动完；批 4a 任务书已随裁回填 `taskbook-batch4a.md` 头部裁断回填行＋§1-2/§2-2/§3/§7-1 四处·开工重锚时行号重核）。规则 4 新句式、原丙「新规则 8」保留与否、触发判据与子类清单＝**拟案随批 4a 审核门过目**。本段并入批 4a 范围、不独立排批。

**〔2026-10-17 审核门拟案三项裁断〕**：①规则 4 新句式＝**问用户形态**——激活时问用户一次「持久化 / 安全 / 性能哪些需要在架构设计时考虑」，安全默认考虑、除非用户明确答「只自己用、不对外」才移出，opt-out 答复本身落盘留痕；持久化 / 性能按用户当场回答与需求要求定；②原丙「新规则 8」＝**保留**，重定位「接口面联动」条（`securitySchemes` 每 scheme 以 `x-decision: D-*` 引架构决策·下游认源 ID）；③触发＝**需求面默认＋显式 opt-out**（「只自己用不对外」＝不适用唯一出口、仍须落盘不沉默；子类封闭四类＝鉴权/加密（传输＋存储）/输入校验/敏感数据处理（含日志红线））。两草稿（规则 4／规则 8）在批 4a 任务书 §7-1 拟案裁断段，施工照写、终稿随开工审核门过目；任务书已随裁回填（头部⑧⑨⑩＋§2-2/§3/§7-1）。

改动面（做时）：`diy-architecture/SKILL.md` 规则区（:84-:90）＋tests 文本守卫面（若有断言依赖）。

### 待办：STAMP_TYPES `test-design` 键与产物文件名错位——stamp 对 test-plan 盖章 MISSING_FILE（2026-10-16 核实 spec-scan 对照表时发现·2026-10-21 已销：修法①落地，夜队列 Q-101 `88e3f7d`）

事实（2026-10-16 证据链三步）：
- 产物真名＝`test-plan.yaml`（diy-test-design frontmatter `outputs: test-plan.yaml`·description 原文「Derive test-plan.yaml」）。
- 引擎定位＝output_dir 平铺 `<type>.yaml`、无别名（`diyc_writeback.py:94` `_doc_path`＋`_load` 实读）。
- ⇒ `check --type test-plan`／green／done 回填写 test-plan.yaml 正确；**`stamp --type test-design` 找 test-design.yaml → MISSING_FILE**——盖章对本产物实际不可用。成因推测＝批 3 扩面 STAMP_TYPES 11→21 时键沿用技能名而非产物名；测试夹具疑按错名建文件把错位锁绿（施工时核实）。

待裁项：
- 修法：①键改 `test-plan`（与 check/writeback 对齐·KISS）vs ②`_doc_path` 加别名映射（保键名·多一层转接）。
- 指示面跟改：批 3 追裁①改过 10 SKILL＋9 steps「留空＋跑 stamp」句——句中若点名 `--type test-design` 须同源跟改（做时 grep 全库核）。
- 测试面：stamp 用例是否按错名 fixture（须核）；测试面先裁后动。

改动面（做时）：`diyc.py` STAMP_TYPES＋可能 `diyc_writeback.py`＋指示面 grep 命中处＋`tests/test_diyc_writeback.py`。

**〔2026-10-16 用户裁定〕**：修法＝**①键改 `test-plan`**（与 check/writeback 对齐·②别名映射弃）；调查（指示面 grep 全库核＋测试夹具错名核实）**执行时间＝批 4 开工前**——届时随调查同窗施工落地，测试面照「先裁后动」随窗呈裁。

**〔已销 2026-10-21·核验〕**：修法①已落地——`diyc.py` STAMP_TYPES 键为 `test-plan`、`test-design` 不在集合；`tests/test_diyc_writeback.py:576-580` 断言在案（`test_stamp_type_key_is_test_plan`）；技能/测试指示面 grep 无 `--type test-design` 残留（仅历史注释）。落地提交 `88e3f7d`（夜队列 Q-101）。

### 待办：窗口输出通用内容统一——通用行同源跟改＋输出 UX 原则（2026-10-16 组7 裁定②登记·2026-10-21 通用行已销：夜队列 Q-110 `7cbb83c`；UX 原则文案随母本批）

登记来源：组7 emit 族呈核后用户两裁（提交 `a40a8b4`）——①emit_via＋violation_line/warn_line 入库、14 家接库＝**已随组7 落地**；②**原则单源方向照准，先记录、另立批**；追加提出：窗口输出统一**先说结论**、再用表格等展示友好型内容输出（含中文全角宽度设计）；并点名**穴居人（caveman）技能**部分内容适合写入统一输出通用内容。

事实（组7 当批状态）：
- 回调内通用行仍本地逐字拼（14 家 `CODE where: msg`／`WARN` 前缀行本批行为保持，未换小工具调用）；表格输出现无消费者＝YAGNI。
- 影子仓 status.md 组7 行已记「登记待办另立批」，但底单本段此前漏登——本次补登（含 caveman 来源）。

待办内容（做时一体）：
- **通用行同源跟改**：14 家回调内逐字同款违规/警告行机械换 `violation_line()`／`warn_line()` 调用（格式单源改单处；定制行 OK/PASS/汇总原封不动）。
- **输出 UX 原则文案**：窗口输出结论先行→表格等友好展示→中文全角宽度设计；拟稿借鉴 caveman（`C:/Users/93559/.claude/skills/caveman/SKILL.md`）写作纪律——与既有 §6/§2 条款重组的 caveman 借鉴（:279）同源参考、各管各面（此处管回复输出，彼处管产物内容）。
- **指令复述（2026-10-16 用户追加）**：AI 每次接到指令，先用自己的话解释一遍对指令的理解再动手，避免误解。
  - 当日已写入项目 CLAUDE.md 三要素版（目标／动哪些文件／不做什么；平凡指令直做；复述防接错意不防做错事）——提示词层只降摩擦不供保证（:282 既判据）。
  - 机制讨论遗留（待后续仔细思考）：①机械门只能查复述"存在"查不了"对不对"，查存在必催生套话→hook 路线暂判不值得；②复述须可证伪（三要素具体到文件/范围，用户一眼可核）防展示功夫；③分层触发防仪式化；④兜底在批间停审门，复述价值=纠错从产物审核提前到开工前。
- ~~落点待裁：原则下沉 diyc_lib vs 指示面 SKILL/CLAUDE.md 文案。~~〔2026-10-17 已裁·见下〕

**〔2026-10-17 用户裁定·落点闭合，销入母本批〕**：**落点＝单源多通道**——原则文案统一落母本批 `suite-texts.yaml`（§9 回复纪律＋载体判据），`sync_texts.py` 增注入目标＝项目 CLAUDE.md 标记对段（全会话自动加载，任何会话回复都生效）；机械可下沉件（产物面禁词/句长 grep、中文全角宽度算列宽函数等）按判据「能下沉优先下沉＋消费者出现才落」处置（YAGNI）。**注入目标＝本项目 CLAUDE.md**（不动全局 `~/.claude/CLAUDE.md`）；**配置型设计**——注入目标列表（SKILL 集＋CLAUDE.md 路径）读配置不写死，将来 diy 用户装套件时由 init 技能/安装器写入其各项目 CLAUDE.md；换 agent 兼容＝生成物是普通 markdown 段落＋标准标记对注释，不绑 Claude Code 专有机制。**hook 路线不做**（「查存在必催生套话」教训在案，将来需要再议）。条款内容（caveman 借鉴＋STE100 子集＋载体判据）随母本批拟稿逐条呈审。本段落点问题销，通用行跟改/输出 UX 文案/复述机制讨论等其余内容不动。

改动面（做时）：14 家回调＋`diyc_lib.py`（若下沉）＋指示面；测试面若有行式样断言须同源核（先裁后动）。

**〔2026-10-21 部分销项·核验〕**：通用行同源跟改已完成（夜队列 Q-110 实施 `7cbb83c`·merge `732d841`）——14 家引擎回调接 `violation_line()`/`warn_line()`，输出同形、定制行未动。**余「输出 UX 原则文案」随母本注入批（批 8）**——落点已于 2026-10-17 裁入 `suite-texts.yaml` §9＋项目 CLAUDE.md 注入（见本段裁断行）。

### 待办：kind 判据表引擎化——规则入脚本、两技能去表（2026-10-21 用户裁定，登记排期，现在不动）

登记来源：Q-108 过审后用户指出「表格在两个技能里，需要合并到一个地方」（`diy-spec-scan/steps/01-collect.md` 与 `diy-selfcheck/steps/01-freeze.md` 同批同文副本）；讨论后裁定：能机械判的进脚本，不做提示词指定文件读取。

已裁（2026-10-21）：
- **判据下沉引擎**：体系产物对照表＋结构判（`SKILL.md`+`steps`→技能、`taskbook*`→任务书）入 `diy-tools` 新增判定模块，挂 `diyc.py kind --target <path> --json`，输出 `{kind, matched_by, ambiguous}`。
- **两技能 steps 去表**：只留三阶链与命令调用——①用户明示照录（提示词，引擎看不见对话）②引擎判定 ③`ambiguous: true` → 先问一次（提示词）。不可机械化两阶留提示词属正当分层，非复制残留。
- **母本不承载正文**：非全库重复块；母本在 `.analysis` 影子仓、不随安装分发，当不了运行时源。
- **偏好记忆不承载**：按记忆机制设计稿 §6 归属表，判据属「可机械规则」→ 引擎关卡；偏好管用户口味、随 output_dir 实例走。
- **步骤文件不整体脚本化**：指令层保留 Read（脚本不提升指令遵循度；Bash 输出有截断风险；步骤要可审可 diff）。可机械的只有数据与门禁。
- **落点 `diy-tools`**：50 技能共同依赖，两技能调用零新增耦合；不放 spec-scan（避免 selfcheck 跨技能调脚本）。

改动面（做时）：新增 `diy-coder/skills/diy-tools/scripts/diyc_kind.py`＋`diyc.py` 增 `kind` 子命令；`diy-spec-scan/steps/01-collect.md` 与 `diy-selfcheck/steps/01-freeze.md` 删表改命令；`tests/test_spec_scan.py` 两处 kind 断言改引擎输出断言＋新增引擎测试。测试面先裁后动（本段即裁）。

关联：Q-108 已按原裁定合入 dev（2026-10-21，merge commit）；本条落地时替换两处步骤文本。

### 待办：diy-brainstorm 规则 1/8 写范围张力——规则 1 未回指 `.prev` 例外（2026-10-21 Q-109 审查发现，登记待改，现在不动）

登记来源：Q-109 审查发现——规则 8 新增每轮 `snapshot` 写 `{output_dir}/brainstorm.yaml.prev`，并自称「规则 1 写范围的 `.prev` 具名例外」，但规则 1 原文仍是无例外的禁令。

事实（2026-10-21 引原文）：
- 规则 1：「写范围：只写 `{output_dir}/brainstorm.yaml`（记录与 `revisions`）；不碰 `prd.yaml` / `sprint.yaml` / `stories.yaml` / 源码，也不建任何状态散文件。」
- 规则 8：「……拍 `{output_dir}/brainstorm.yaml.prev`（规则 1 写范围的 `.prev` 具名例外）……」
- 两条互不指认，逐字执行时冲突；规则 8 更具体，实际多半按 8 走，但自检/审查会反复报。

改法（待执行）：规则 1 末尾补半句「（唯一例外＝规则 8 的 `.prev` 快照）」；只动 `diy-brainstorm/SKILL.md` 规则段，不动规则 8 与引擎。测试面已核：`tests/test_brainstorm.py` 未钉住规则 1 原文（SkillContractTests 无该句断言），改动零测试影响。

### 待办：diy-brainstorm 违规码清单补登 `TOOL_ERROR`（2026-10-21 Q-109 审查发现，登记待补，现在不动）

登记来源：Q-109 审查发现——`snapshot` 写盘失败报 `TOOL_ERROR`，但引擎 docstring 违规码段只列九码＋`ID_UNSTABLE`；该码在 `brainstorm_cmds.py:159`（init 写盘失败）早已使用，属本批之前既有遗漏，Q-109 沿用未扩大。

事实（2026-10-21 核实）：
- docstring 原文：「本引擎用到 …`ASSUMPTION_PRESENT` 共 9 个，**冻结九码一字不动**；本批技能级新增码 1 个：**`ID_UNSTABLE`**」——未列 `TOOL_ERROR`。
- 使用点两处：`brainstorm_cmds.py:159`（init 写盘失败，既有）；`brainstorm.py:124`（snapshot 写盘失败，Q-109 新增）。
- 先例：diy-correct-course「新增 `TOOL_MISSING` / `TOOL_ERROR`（diyc 委派降级专用，同 readiness 先例）」；diy-e2e-tests 码清单含 `TOOL_ERROR`；diy-readiness-check 同。

改法（待执行）：docstring 违规码段补登 `TOOL_ERROR`——「工具层写盘／子进程失败通用码（init 写盘失败、snapshot 写盘失败使用）」；只补文档登记，不改代码行为、不动冻结九码。测试面已核：`tests/test_brainstorm.py` 无 docstring 码清单文字断言，改动零测试影响。

### 待办：diy-brainstorm 想法铸稳定 ID `BI-###`（2026-10-21 用户指示登记，现在不动）

登记来源：Q-109 审查时用户确认「队列『不含三级 ID』与测试出现 BI-### 不矛盾」（Q-109 只做对账、不做铸造），并要求把「给每一个想法增加 BI id」正式登入待办。

既有裁定（2026-10-04，见本文件 :190）：brainstorm 下游锚从记录级 `BS-###` 下沉条目级三级——`BI-###`（想法）/ `BT-###`（主题）/ `BA-###`（行动）；文件内全局唯一、ID 取代 `no`（不并存）。改动面：`brainstorm.py`（铸造/唯一性/引用完整性）＋ SKILL.md 结构段（`ideas[].no`→`id`，`themes[].ideas` / `priorities` 三键 / `actions[].idea` 改引 ID）＋ `steps/04-organize.md` ＋ viewer 展示 ＋ diy-lab 存量产物迁移。

本次登记：把「每个想法铸 `BI-###`」单列为可执行待办。Q-109 已就位的前置：每轮 `snapshot` 快照＋`check --previous` 已支持 `ideas[].id` 对账与「迁移轮跳过」（旧无 id → 新有 id 当轮不误报）。

待裁点（做时）：
- 范围：只做 BI（想法），还是连同 `BT-###` / `BA-###` 一次做（:190 原裁定为三级一体）；
- ID 取代 `no` 的迁移形态、`themes[].ideas` / `priorities` / `actions[].idea` 引用切换；
- 与 prd 前置机制化（:184）的先后：BI 是 prd 外部锚，prd 侧摄取规则随该批核；本条可先落地铸造，不阻塞 prd 批；
- viewer 展示与测试面（先裁后动）。

### 待办：architecture stack `kind` 枚举扩展（2026-10-21 用户裁定，登记待扩，现在不动）

登记来源：Q-107 方案裁定——`kind` 初版只收有机械消费方的 7 类：`frontend` / `scaffold` / `language` / `test` / `lint` / `typecheck` / `build`；数据库、部署、包管理器等其余技术类目本次不进枚举，扩展时走本条。

扩展判据（沿用 Q-107 口径）：
- 有机械消费方才进枚举（下游有按 `kind` 取值的步骤点）；无消费者不写（YAGNI）。
- 新 `kind` 入枚举须同步四处：`diy-architecture` 结构段注释、`diyc check` 枚举常量与校验、对应消费方 steps、tests。
- 封闭世界：枚举外 `kind` 一律 `ENUM_INVALID`。

## 待办：runner 三连失败处置工作流（2026-10-17 用户裁定，登记待办，现在不动）

登记来源：runner 三连遗留待办（上段「reopen 只认 augment:失败」）讨论升格——用户点出「重开任务回进行中」框架装不下真实需求：失败须先归因分叉（用例/代码/上游），再分路修复，各自有校验门与重跑。原开关扩展框架作废留档。

裁定全集：

1. **归因四分法**：①用例设计错 ②测试代码写错 ③产品代码错 ④上游 AC 错。三份报告只给线索不给结论（e2e 落失败事实／test-review findings 排②嫌疑／gate 矩阵排①覆盖缺口＋④路由），归因须现场复现 debug（复现失败→对读 TC↔AC→查测试文件）。
2. **查明技能＝diy-investigate（案 A）**：归因结论落 `investigation.yaml`（TC ID＋①②③④判定＋证据链，证据分级/假设不删既有纪律适用）；**只写自己产物**，修复写入归各产物所有者技能（写权封闭零破例）。与已立项 bug 分析技能分工＝investigate 归因止于诊断，真缺陷（③）才转 bug 分析技能做根因深挖。
3. **修复路由（人裁断后按原生产技能执行）**：
   - **①用例设计错→test-plan**：废弃**不改写**——独立字段（不进 `status` 枚举，green 回写面隔离），承载废弃原因＋`replaced_by` 指向新用例；原生产技能补替代用例（正常追加）。**AI 只建议废弃，人裁落标**；**废弃 TC 不算覆盖**——补替代才放行（FH 被杀门联动：唯一杀 FH 的 TC 被废弃＝红到补上）。
   - **②测试代码错→修测试代码**（e2e 写的归 e2e）→全量三连重跑→test-review 新 RV 记录即对账面（实质＝乙案，不发明追加动作）。
   - **③产品代码错**→`bug-add` 入 bug-log＋sprint 重开回 dev 修→全量三连重跑。
   - **④上游 AC 错**→路由 `diy-epics-stories`（gate oracle HALT 现成路，不新设载体）。
4. **重跑边界＝全量三连**（复用 `--post-only`，不做局部补跑——gate 矩阵分母保完整）；**质量校验衔接＝强制门**（修完必过 test-review 及各引擎终门才准重跑）。
5. **viewer**：废弃条目**折叠区**渲染（零裸键中文标签）。

待裁（随任务书呈裁）→〔2026-10-18 用户三项全裁·见下，实施细节随任务书〕：
- **TC 生产者判据三选一**（TC 现无生产者字段：`type: 端到端`→e2e 可判；`单元/集成` 分不清 test-design 设计 vs augment 补测）——①TC 补生产者字段（动 schema＋三生产方落笔）②按类型粗判 ③放弃按生产者、按类型路由。
- investigate 触发形态（三连失败后人手动调 vs runner 自动路由）。
- 废弃字段 schema 形态与强制门机械落点（引擎拦位）。

**〔2026-10-18 用户三项裁定〕**（裁定本体不再重呈，实施细节随任务书）：
1. **TC 生产者判据＝①补生产者字段**——TC 加生产者字段，三生产方（test-design/augment/e2e）追加用例时落笔。字段名、枚举值、存量 TC 兼容口径（缺省不回填 vs 按 type 推断）随任务书。
2. **investigate 触发形态＝runner 自动路由**——三连失败汇总后 runner 自动 spawn investigate 归因（非人手动调）。spawn 点、旗标设计、与 `--post-only` 关系、无头成本随任务书。
3. **废弃字段 schema＋强制门落点（两半均裁）**：
   - **schema＝TC 可选嵌套键 `retired: {reason, replaced_by}`**——不进 `status` 枚举（green 回写面隔离；status＝执行结果、废弃＝生命周期裁决，两轴正交）；嵌套单键在场性即裁决开关（键缺席＝活跃、键在场＝已裁废弃；AI 只建议不写键、人裁落标＝键写入即人闸凭证）；键在则双键必填（缺一 EMPTY_FIELD）；`replaced_by` 按 UNKNOWN_ID 校验在场、禁自指（照 `kill_target`→FH 引用校验先例）；存量 TC 零改动天然合法（api_refs「缺席即整键省略」同款）。
   - **强制门＝三处改造＋一设计，复用现有门零新增违规码**：(a) 形状校验挂 `check_test_plan` TC 循环内（status 枚举后·任何 check 都跑——同 api_refs 形状/锚解析分层惯例）；(b) 覆盖类集合统一剔除 retired＝联动本体——FH 被杀门 `killed` 收集与接口锚门 `tc_anchor_hits` 收集跳过带 `retired` 键的 TC（「废弃不算覆盖＋FH 门联动」的机械本质＝覆盖类断言输入集合不收废料；FH 侧红走现有 SET_MISMATCH 零新码）；(c) counts 层（by_type/by_dimension/`covered`）同步剔除（虚报活跃数防护）；(d) 替代品**不继承** kill_target（KISS——补替代是完整生产动作须重新瞄准 FH；FH 杀伤＝活 TC 真引用，单一事实源零代理推理）。违规码复用 EMPTY_FIELD/UNKNOWN_ID/SET_MISMATCH（批 4a 封闭集零扩先例）。
   - **留任务书小尾巴**：green 对 retired TC 写回是否机械拒——倾向不动 green（YAGNI·提示词层禁跑废弃 TC），误操作实证再议。

改动面（做时）：test-plan schema（废弃字段）＋`diyc_check_docs.py` check_test_plan（覆盖门＋FH 门联动）＋e2e/augment/test-design 三生产方写入面＋viewer 折叠渲染＋diy-investigate SKILL（失败归因入口段）＋runner（若触发裁自动）＋tests（先裁后动）。

## 待办：diy-analyze 定位收口＋产物依赖缺席三档总则（2026-10-17 用户裁定，登记待办，现在不动）

登记来源：arch-analyze 吸收方向翻案讨论中连带裁出（同日三裁＝architecture 规则 4 批 4a 随批之后的第二件）。

**裁定三项**：

1. **arch-analyze 不迁移**（推翻 10-05 方向·详见该段作废注记）：处置＝4 句死路由改「套件内自理」口径——`diy-analyze/SKILL.md:27`/`:73`、`steps/01-define.md:55`（路由句删或改写）＋`tests/test_diy_analyze.py:365` 断言同源（测试面先裁后动）。
2. **evolution A/S 路由式接线**（历史依据：wds-[A] 扫库线在原流程喂 [S] 估范围/[I] 懂代码·迁移时拆断）：**调用方**＝`diy-wds-evolution` `01-analyze`（根因需代码库证据时路由）＋`02-scope`（估范围需组件/依赖底数时路由）；**消费方**＝同两相读 `analysis.yaml`——A 相补根因取证（`question`/`risks[]`）、S 相垫 `components_touched`/`data_changes`/`risk` 估算（`AN-<nn>` 为引用锚）；**消费＝硬消费**：一旦依赖（引锚/声明需底数）`analysis.yaml` 缺席即显式报错（依三档总则一档）；不依赖的轮次（改文案类）不受阻——依赖声明与缺席报错的机械落法（引擎校验 vs 步骤纪律）随任务书呈裁。`diy-reverse`→analyze 既有路由不动；diy-analyze 本体零改动、不改名（YAGNI）。
3. **产物依赖缺席三档总则**（新立·全库适用）：**一档**＝硬依赖（链序上游/职责承重）缺席→显式报错拒放行；**二档**＝可选源→明文声明「缺席不阻塞」；**环境依赖**（工具/git）→`TOOL_MISSING`/`NO_VCS` warning 降级（环境≠产物·brief 既有边界句）。三灰色件按影响判档处置：①`check_openapi`←prd：**一档改硬**——`x-fr` 解析遇 prd 缺席/损坏改硬 violation（exit 1），废 :466 warning 跳过；**批 4a 任务书 F-x 拟案同源跟改**（「prd 缺席 warning 跳过照 :466」改照硬口径·随批 4a 回填）；②a `create-story`←architecture：**一档改硬**（护栏面缺席拒跑或硬 violation·随任务书定形）；②b `create-story`←test-plan/sprint：**二档维持**（链序下游·创作时本就未生成）；③`readiness`←architecture：**一档甲式拒跑**——architecture 缺席→零产出 exit 1（源侧「Missing Documents (WARNING)」设计作废留痕；design.yaml 缺席维持现状）。总则立法落点（code-quality.md vs 各技能声明汇总）随任务书呈裁。

**改动面（做时）**：diy-analyze SKILL/steps＋`diy-wds-evolution` 两 step＋`diyc_check_docs.py`（check_openapi）＋`story_context.py`＋`readiness.py`＋批 4a 任务书一行＋各测试面（先裁后动）。协调：evolution 两 step 与逐项化批同文件；批 4a F-x 行随 4a 开工重锚回填。

## 待办：diy-overnight 开工权收紧——不明示不开工＋最后一步交提示词（2026-10-19 用户提出，登记待办，现在不动）

登记来源：用户要求——夜跑技能用户不明示开工，不准开工；该做的工作做完最后一步后，给用户提示词，让用户自己确定什么时候开工。

待办内容：

- **开工权只归用户**：技能激活、队列就绪、开工前置五步做完，均不构成开工依据；`run_queue.py start` 只在用户明示「开工」后调，不得自动进入执行循环。
- **最后一步＝交提示词**：准备工作（队列整肃／基线自证／五数值呈核）完成后停手，给用户一段可直接粘贴的开工提示词（技能名＋队列路径＋建议参数），由用户自行决定何时开工；每晚收尾（晨报）同理——停下交提示词，不自动续跑/开工。
- **落点**：`diy-coder/labs/diy-overnight/SKILL.md` 激活时（:43「开工门是唯一交互点」同方向，补「交提示词·不代开工」形态）＋开工前置第 5 步措辞。

改动面（做时）：SKILL.md 两处；`run_queue.py` 零改动（脚本无自动起跑入口）。现在不动。

**〔2026-10-19 已实施·待审〕**：SKILL.md 三处——激活时「开工权只归用户」（`start` 不得调用）／开工前置第 5 步停手交提示词（原第 5 步顺延为 6）／收尾第 4 条不自动续跑；`run_queue.py` 零改动。

## 待办：diy-overnight 晨报写入逐任务早审 diff 入口（2026-10-19 用户提出，登记待办，现在不动）

登记来源：用户要求——晨报的早审 diff 入口形如：

- `Q-001：git diff 2841e00..404a5e6（不改代码，仅 SKILL.md 补首跑门提示）`
- `Q-002：git diff 404a5e6..02e9550（prfaq.py 单行归一 + 3 用例）`
- `Q-003：git diff 02e9550..9551ed3（复制按钮 + COPY_JS + 6 用例，viewer_render.py 恰 400 行卡线）`

这类入口必须写入报告，防止用户清理上下文后不知道如何审核。现报告只有通用指引「`git diff <前支tip>..<本支tip>`」与表格内的分支/短 commit（run_queue.py:301-323），前支 tip 需用户自行推算。

待办内容：

- **新增「早审 diff 入口」段**：按队列序逐支一行 `<id>：git diff <前支tip>..<本支tip>`（短 sha）；首支前支＝`base`；括号内附一句变更摘要。
- **摘要来源待裁（随任务书呈核）**：①取任务 `title`（现数据即得，最粗）；②取完成提交 message 体（信息最实，需读 `git log`）；③`done` 回报增字段由调度员落笔（动队列格式）。用户示例括号内容接近②。
- **数据基础**：`prev_tip()`（run_queue.py:106-114）已能算前支 tip，完成条目 `result.commit` 在案——零新数据结构即可生成入口段。
- 未完成/跳过/阻塞条目无分支：不列入口或注明「无完成提交，见 reason」。

改动面（做时）：`run_queue.py` `cmd_report`＋（若选来源③）`done` 参数与队列格式＋晨报断言测试（先裁后动）。现在不动。

**〔2026-10-19 已实施·待审〕**：摘要来源取②（提交 message 体，剔除 `basis`/`测试` 尾段）；`cmd_report` 新增「早审 diff 入口（队列序）」段，`prev_tip()` 复用；py_compile＋真实队列重生成冒烟通过（三支入口与用户示例同形）；无测试面（labs 资产、run_queue 无既有测试）。

## 升级事项（可选·不排期·需要才做）

### object-types 参考层类型扩展（2026-10-04 登记）

- 候选：table（用户提出）及 select / checkbox·radio / toggle / modal / tabs / card / badge / progress。
- 事实：机制天然开放——引擎不消费该目录、k-sketch 通配引用、p-specify:28 开放枚举；源侧仅五件（button/heading-text/text-input/image/link），新类型属 diy 自产（按五件同构的规格项清单式）；正文 4 处「五件」写死需同步（SKILL.md:101、p-specify:30/:38、m-design-system:16/:45/:47）。
- 触发：实际使用中遇到该类型对象无参考层可读时再做。
- 若做：随去源路径锚批同文件处理（避免同文件改两遍）；新件不带改写说明头（无源即零迁移痕迹）。

### diy-init 工具安装技能（2026-10-11 登记）

- 候选：新技能把好用工具安装进项目——代码分析工具（如 ruff/rg/knip 类）、各技能运行必备的外部工具；一次巡检缺啥装啥。
- 触发：实际开新项目或技能报缺工具时再做。

### viewer HTML 任务复制按钮（2026-10-12 登记）

- 候选：viewer 渲染的 HTML 页面对任意任务加一个复制按钮——点击后把该任务内容复制到剪贴板，粘贴进 Claude Code 这类工具里继续处理；不限产物类型（不管是什么产物）。
- 事实：渲染脚本＝`diy-viewer/scripts/viewer.py`（产 index.html 等页）；按钮属纯前端交互。
- 已裁（2026-10-13，三项）：
  - **复制内容形态＝转成提示词文案**（不复制原文 YAML/JSON）——文案必带**产物文件路径＋条目 ID**，使 AI 据以打开对应文件、定位该 ID 对应内容，再按用户粘贴后口述的意图（解释/修改等）处理。
  - **按钮位置＝表格内每个 ID 旁**（非每任务卡一个）。
  - **交互＝单击复制**。
  - 文案具体措辞随任务书拟。
- 触发：需要把 viewer 里看到的任务直接喂给 AI 工具时再做。
