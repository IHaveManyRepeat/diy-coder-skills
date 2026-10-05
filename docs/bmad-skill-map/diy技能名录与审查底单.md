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

### 二审

| 技能 | 状态 | 完成日 | 发现 → 处置 |
| --- | --- | --- | --- |

## 待办分级总览（2026-10-03）

| 级 | 待办 | 影响面 |
| --- | --- | --- |
| 全库级（旧技能都要改） | 去 `.claude` 路径硬编码（安装器待办·①） | 155 文件近全员 |
| 全库级 | 50 技能正文逐项化 | 50 SKILL.md＋steps/ |
| 全库级 | 去源路径锚（正文「源 `X`」180+ 处悬空引用迁 dev-only 台账） | 72 文件（扩口径后更多） |
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
| 单独技能 | diy-spec-scan 加方法驱动分支穷举（ECH 化·2026-10-05 用户裁定「卡点法还不够」＋**方案全定 1A+3B·无待裁项**：①穷举独立成 step（如 02b-exhaustive）不并入 03——与 diy-review 双透镜并列同构·两法 findings 去重复用 02「同一处只报一次」·判据参考 diy-review lenses.md「边界类从内容自身推·不套固定清单」；②**穷举默认跑（opt-out·2026-10-05 裁）**——除非用户明示不用穷举·对齐 editorial-review 两透镜默认全跑 `--lens` 收窄先例；③**载体已裁＝`source: 卡点\|穷举` 字段**——type 保持八类·引擎 FINDING_TYPES 零改·summary 分法计数（selfcheck B 部分机制评价原料）。**未开工·待用户点头**） | diy-spec-scan SKILL＋steps＋引擎＋tests |
| 单独技能 | diy-selfcheck 硬门放开「要照做的事」→ 任意文档可审（2026-10-05 用户点名 prd/架构/epic/story/任意文档；BMAD AR/ECH 文档面能力补缺·Story 2.1 实用过 AR 定稿兜底；**方案已裁 2A+4a**：spec-scan 硬门同步放开为「可读非空」·两技能形态统一·selfcheck 预演片对纯文档不降级；纯文档时 spec-scan 跳过 02 预演只跑穷举+03+04（依赖 1A）；kind 扩「任务书\|技能\|规格\|文档」——引擎不校验语义 kind·仅改 SKILL.md 文案零引擎改动。**未开工·待用户点头**） | diy-selfcheck SKILL＋steps＋diy-spec-scan SKILL＋steps＋引擎＋tests |
| 单独技能 | 爆炸半径分析注入 diy-review＋测试设计族（四项全闭合：1b 独立面/2b FH 排序/三技能范围/定制标签＋漂移防治已核·**未开工·待用户点头**） | diy-review＋test-design/e2e/augment＋引擎＋viewer＋tests |
| 单独技能 | diy-analyze 吸收 arch-analyze 职能（方向已裁：arch-analyze 退役不装·套件内 4 处路由句改写·取代形态/产物面待裁·**未开工·待用户点头**） | diy-analyze SKILL＋steps＋引擎＋viewer＋tests＋底单 C 表 |
| 单独技能 | diy-reverse 补「参考用法」引导（2026-10-05 会话实测：用户想先逆向别站做参考再做自己的 design.yaml——instance 隔离机制在场可解（`--instance` 落 `<output_dir>/<instance>/` 不占主线位）但 SKILL.md 只有「初始设计单源」一种叙事，参考用法入口不显性；拟补引导：参考目的→带 `--instance` 跑＋主线生成权不受扰＋design `[C]`/`[K]` 只读消费参考；挂法/文案/是否动 diy-design 输入面待裁，预期零引擎改动·**未开工·待用户点头**） | diy-reverse SKILL.md（或＋diy-design 输入面） |

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
- 条款重组：§6「精准简练」并入 §2「写作纪律」（**2026-10-03 用户裁定合并成立**，文案待拟）：§2 成为产物内容＋形式唯一纪律块；新产物精简条款并入同块。文案预计多于两块简单拼接（拼接版仅底稿），**借鉴 caveman 技能写作纪律**（`C:/Users/93559/.claude/skills/caveman/SKILL.md` Rules 段：砍填充词/hedging/客套、短同义词、片段句、箭头表因果、一词够则一词、技术名词/代码/错误串逐字、不发明读者解不开的缩写、`[thing][action][reason]` 句型），与中文禁词表/句长上限一并拟呈核。数据面：两块交集 46；只有 §6 的 4 技能＝build-loop（写产物却无 §2，入块待裁）＋help/tools/viewer（零产物，**已删 2026-10-05 §6 适用面批**——elicit/party-mode 同批共 5 家，台账落地 `PRECISE_NON_MEMBERS`）。测试面：ANCHOR_PRECISE 并入 §2 断言；§9 措辞「§6 管产物内容」改「§2」。不单技能先行改（锚串断言即红，随母本批整体动）。
- **ASD-STE100（简化技术英语）纳入 §2 候选条款**（2026-10-05 用户点名，随条款重组一起处理，具体文案后定）：AI 产物**可遵循其规则面**——约 57 条写作规则（一句只讲一事/短句/主动语态/现在时/禁成语比喻/一词一义/程序一步一句等）作为 §2 候选条款，与禁词表/句长上限/caveman 借鉴同拟呈核；**词典面不可机械内置**——约 900 受控词表系 ASD 版权，不可打进技能包做引擎门。**随批裁定三点**：①适用语言范围（STE 只定义英语受控语言；`document_output_language=英文` 时全套适用？中文产物取精神不取词表？）；②规则子集取舍（57 条全量 vs 挑与产物相关的子集）；③句长上限数值与 STE 程序句 ≤20 词的关系。
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

## 待办：openapi 接口总览行锚（2026-10-04 用户裁定，待执行）

登记来源：用户看 diy-lab 实测渲染的 openapi.html 接口总览提出「接口没有 id，要增加 id」。

事实（2026-10-04 核实）：
- viewer 接口总览已有「操作 ID」列且值在（viewer.py `render_openapi_section`）；引擎已校验 operationId 必填＋查重（diyc_check_docs.py:396/:412）。
- 全体系实体均有「前缀-编号」锚 ID（FR-x.y / D-x / BS-### / TC-x.y.z / FH-x.y.z），唯接口无——现行接口身份＝operationId＋path＋method 复合锚（五轴段已裁 C 方案）。
- viewer 接口总览行无 HTML 行锚（render_table 行锚取 `item["id"]`，openapi 行字典无该键）——跨页无法深链到具体接口行。

裁定（2026-10-04）：**不铸新 ID**——operationId 即接口唯一身份（复合锚裁定不变、零下游联动）；仅补 viewer 展示：接口总览行加 HTML 行锚（锚值＝operationId，引擎查重保证唯一），供跨页深链（如将来 stories 页 `api_refs` 渲染跳转）。

改动面：viewer.py `render_openapi_section`（行锚；注意 `render_table` 行锚机制取 `item["id"]` 会同步渲染成列——实施时避免「操作 ID」列重复，row-id 参数或本函数自拼，实施时定）＋viewer tests（新增断言，本裁定直接后果同源可逆，按三条件报备）。与「接口契约通用设计与架构鉴权面」批同文件（viewer.py），排先后实施避免改两遍。

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

## 待办：全库去源路径锚（2026-10-04 用户裁定，专批，现在不动）

登记来源：用户实测——安装后的 diy 体系内 `p-specify.md` 表格引用的 `steps-p/` 9 文件找不到（源在 BMAD wds-4-ux-design，dev 仓 `.claude/skills/` 可解析，1,323 行核对吻合）。裁定：技能文件受众是 AI，正文路径即行为输入——读到即可能去开文件，终端环境（不装 BMAD）读不到 → 轻则空转工具调用，重则困惑后即兴补「源内容」；悬空锚全库清理。

- 方法（已裁·2026-10-04 补）：**逐技能实测**——覆盖技能**全部文本面**（SKILL.md、steps/、data/、templates/、scripts 注释与输出提示等一切随包文本），所写路径逐条实际解析打开，跑不通的统计成清单，针对性修复；实测清单为修复依据。正则普查只作预扫参考：精确口径「源 `含路径串`」180 处/72 文件，抽样 40 条全为注释性溯源、显式读取指令未见——180 是下界，以实测为准（实测天然覆盖无反引号裸路径、「收编自/出处」引导等正则漏网形态）。
- 方案（已裁）：正文去锚自包含——引文/判据值留、路径删；扩查出的显式读取指令改指 diy 自带文件。不随附源文件（第二份源违单一源；AI 回读 BMAD 原文＝迁移改写白做）；不发布时机械剥离（锚多嵌句中，剥不成句）。
- 溯源落点（已裁 dev-only）：行级锚（路径＋行号＋裁定号）集中迁 `docs/bmad-skill-map/` 新台账（文件名落地时定），发布包正文彻底无源路径；dev 仓 BMAD/wds 源文件本体不动。
- 源侧缺陷登记保留条件（已裁·2026-10-04 补）：**正确路径可寻得**（缺陷＝源笔误、文件本体在）→ 错误登记**不保留**；**真幽灵**（正确路径亦不存在）→ 保留「裁/改道」处置事实，源路径细节进 dev-only 台账。实测两例：D12 `object-router.md` 实存于源 `data/object-types/`（笔误，登记可删）；D13 `design-system-router.md` 全库未寻得（幽灵，保留裁的事实）。
- 迁移痕迹零正文（已裁·2026-10-04 补）：裁撤登记/改写说明/净损失登记/归属裁定等**迁移决策记录整块迁 dev-only 台账专门记录，技能正文不留**——不只去路径锚，记录块本身退出正文。技能正文是可执行内容，迁移决策记录属变更台账，载体分离。台账载体可与 迁移计划.md「能力损失台账」合并，落地时定。普查（标记词口径）：真 16 处/14 文件（diy-design 13 处全族＋`diy-dev/steps/wds-accept.md:44` 整节＋`diy-wds-system/data/complexity-router.md:5`；party-mode 2 处系误报——「缺陷台账」指 diy-review 产物非迁移记录）；2026-10-04 用户点名补登 `diy-dev/steps/wds-implement.md:39` / `wds-fix.md:33` 两整节（同族「裁撤与归位（源侧台账）」，原普查时点后新增）→ 计 18 处/16 文件；一审 party-mode 预发现（2026-10-05）：`diy-party-mode/SKILL.md:15`「裁自源技能：…」句＝裁剪说明嵌入正文段（非独立块），「裁自」形态不在标记词口径 → 计 19 处/17 文件；一审 quick-dev 预发现（2026-10-05）：「源技能做法 vs diy 做法」裁改对照注记 6 处/4 文件（SKILL.md:58/:86＋steps/01:21/:22·03:18·06:31——同「裁自」族嵌入正文段）→ 计 25 处/21 文件；「收编自/出处/按裁定 N/普查编号」等旁形态随逐技能实测覆盖（一审 e2e 预发现：BMAD 溯源注记 6 处/4 文件——steps/02-targets:10·03-generate-api:14·04-generate-e2e:10/:15/:17/:29·05-record:48，归本批；一审 test-review 预发现：criteria.yaml 头部迁移裁定注释块＋`source:` 键＋steps 泛指 3 处（02:10·03:24/:33）——数据资产面非 SKILL 正文，归本批、处置随批核；一审 test-gate 预发现：adr-checklist.yaml 路径与源注（:3/:4/:39）＋steps 源泛指约 8 处（02:15 源四级·03:47 源时效线·04:52/:61/:67·05:16/:46/:50/:51），同归本批；一审 retrospective 预发现：泛指形态最重一族——「源技能/源 step-N/源主持纪律」遍布 7 个 steps 文件＋引擎头注约 20 处/8 文件（无路径锚），同归本批；一审 viewer 预发现：viewer.py `# trace:`/批次码出处注约 70 处（C·2/B3/W2/R-x——出处类旁形态，处置面随批核）；口径补记（2026-10-05）：任务书编号（AC-9.x/FR-3.x/R-x/§五 C·N 等）散见 build-loop SKILL.md（4 处）、test-review steps/引擎（R-3/R-4）等——同归「普查编号」旁形态，此前一审未单列，此处补口径；一审 teach-me-testing 预发现：curriculum.yaml 头部迁移裁定注释块＋逐行「源: 英文名」留档注——数据资产面，同 criteria.yaml 先例，归本批；一审 party-mode 预发现（2026-10-05 用户裁定）：SKILL.md:15 尾句「裁自源技能：BMAD 的 agent 名册与人设剧本整段不迁，留的是『多视角独立推理』的方法本体」＝迁移归属裁定正文化——信息搬日志（dev-only 台账）、正文删句，归本批；selfcheck 讲解时用户裁定（2026-10-05·一审前点名）：`diy-selfcheck/SKILL.md:17`「底子」整句（B3 §13 固化的编排＋融合 B4 机器台账/B6 旧值复扫/B7 片间交叉置信度/C·7 单执行者降级形态）＝批次码出处说明——出处类旁形态，正文删句（已裁可去·待本批执行，信息进台账）→ 计 20 处/18 文件）。
- **dev 仓内部文档引用同属迁移痕迹**（已裁·2026-10-04 补）：`迁移计划.md:行号`、`*-fidelity.md §节`、`docs/bmad-skill-map/` 路径等 dev 私有管理文档引用**不得出现在技能正文**——发布包必无该文件，且行号/章节号随文档漂移，比 BMAD 源锚更不可解析（例：`prototype-loop.md:12` 的「源侧 `迁移计划.md:210`」）。普查：真 4 处/4 文件（`diy-design/steps/prototype-loop.md:12`、`diy-wds-brief/steps/03-signoff.md:144`、`diy-viewer/scripts/viewer.py:666`、`diy-wds-assets/data/presentation-formats/index.md:25`；`c-discuss.md:6` 系「讨论结论」产物字段名误报）。处置同总则：行为事实改写自包含留正文，出处/行号/编号进台账。一审 test-gate 补登（2026-10-05，原普查漏网）：6 处/4 文件——`diy-test-gate/SKILL.md:67`（裸节号 §十三:459）＋`steps/05-gate.md:17`＋`scripts/gate.py:60/:73`（§十三:459／§二验收 #3·#4·#12）＋`scripts/gate_check.py:13/:665`，皆「迁移计划 §节」形 → 计真 10 处/8 文件；一审 viewer 再补 +2（2026-10-05）：viewer.py:669（迁移计划 §已定补充）＋:165（§五 C·8 裸节号——原普查仅记 :666）→ 计真 12 处/8 文件；一审 diy-tools 补 +4（2026-10-05）：`diyc_mutate.py:2`（迁移计划 §五 阶段 C 第 9 项）＋`diyc_writeback.py:67/:563/:629`（§五 C·8②·迁移计划 §十三）→ 计真 16 处/10 文件（`diyc.py:302` 系 FR-4.5/D-9 全族模板句，归母本批不在此计）。
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

## 待办：diy-review steps 步骤深化（2026-10-04 用户提出，登记待裁，现在不动）

登记来源：用户看 `diy-review/steps/` 觉单薄，问补充可能。

事实（2026-10-04 核实）：
- 抓手盘点：L1/L3/L4 各有机械抓手（`diyc.py trace`／`check --type review`／`design.py audit+check`），**L2 零抓手**——仅一句口诀（坏输入/空None/并发/错误路径/静默兜底＋「真会咬人」），无推导方法无判据；falsify 非功能六维只有名字、「跑临时攻击」零打法；lenses（HALT/空数组合法/归一）与 wds-review（零产出/不采信自述/写权）纪律齐备，不补。
- 规模对比：兄弟技能 steps 单文件 20~82 行（dev 32~50／test-author 20~52／investigate 29~57／retrospective 27~82），diy-review 全部 6~9 行——steps/ 系单文件 SKILL.md 拆分产物，未按步骤展开规程。
- `diyc.py trace` 只解析已有 trace 行 ID（diyc.py:45 `TRACE_LINE_RE`→references/unresolved），不报「方法定义缺 trace 行」——l1 正文自认「整行缺席仍属目读」；旧分析（.analysis/2026-09-13 determinism-1）建议的 untraced 类半截未落。

候选（①方向自洽，②③待裁）：
- ① **L2 补推导规程**：AC→边界怎么推（输入等价类/域边界／状态字段非法迁移／错误路径静默兜底识别）＋「真会咬人」判据——补推导方法而非固定清单（守 lenses「边界类从内容自身推，不套固定清单」）；须写明与边界穷举透镜分层：L2＝必跑层高危快扫、透镜＝可选全量枚举（防透镜被架空）。
- ② **L1 untraced 机械检测**：`diyc.py trace` 扩「扫面内方法定义缺 trace 行」报告——方法定义识别有误报面（lambda/嵌套函数/扫面口径），先裁后动（测试面纪律）。
- ③ **falsify 六维最小探针**（每维一行打法）：与旧分析 leanness-4「证伪轮向更简」方向相抵、无产出差实证——待裁。

改动面：①③＝diy-review `steps/l2-boundary.md`·`falsify.md`；②＝diy-tools diyc.py＋tests。协调：与逐项化批同文件（diy-review SKILL.md 正文），排先后避免改两遍；本条发现属 diy-review 一审范围（技能逐个审查行动线），一审行待审完由用户勾。

## 待办：diy-e2e-tests 关联 openapi 契约认 ID（2026-10-04 用户裁定，攒批待执行，现在不动）

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

遗留待办（YAGNI 后补）：`--reopen-failed` 现只认 `augment:失败`；e2e/gate 发现的实现缺陷重开＝人手改 sprint.yaml 对应任务回 `进行中` 后重跑 runner。若实际冲刺中 e2e 失败量大，再裁扩展 reopen 认「关联端到端失败 TC 的任务」（需 TC→AC→story 映射解析）。

## 待办：test_pending_precise_brief 跨窗口中间态红——检查任务（2026-10-05 发现并查明，现在不动）

现象：2026-10-05 三连批全量跑时 `tests/test_suite_texts.py::PendingLandingTests::test_pending_precise_brief` 间歇红一次（单跑过、复跑全绿，当时误判 flaky）。

查明：非 flaky——§6 批两半（`PRECISE_NON_MEMBERS` 台账改判 vs elicit/help/party-mode 删句）在两个窗口非原子落盘，对账断言跨越中间态窗口即红；两半齐后稳定绿。

检查任务（随 §6 批闭合执行，不动手改）：§6 批收口时确认该测试在全量下稳定绿即可；若再红，先查是否又是并行批中间态（台账先行/正文后至），不要直接改断言。

## 待办：diy-selfcheck 产物 YAML 化（2026-10-05 用户裁定，待用户点头开工）

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

## 升级事项（可选·不排期·需要才做）

### object-types 参考层类型扩展（2026-10-04 登记）

- 候选：table（用户提出）及 select / checkbox·radio / toggle / modal / tabs / card / badge / progress。
- 事实：机制天然开放——引擎不消费该目录、k-sketch 通配引用、p-specify:28 开放枚举；源侧仅五件（button/heading-text/text-input/image/link），新类型属 diy 自产（按五件同构的规格项清单式）；正文 4 处「五件」写死需同步（SKILL.md:101、p-specify:30/:38、m-design-system:16/:45/:47）。
- 触发：实际使用中遇到该类型对象无参考层可读时再做。
- 若做：随去源路径锚批同文件处理（避免同文件改两遍）；新件不带改写说明头（无源即零迁移痕迹）。
