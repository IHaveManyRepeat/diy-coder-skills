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

## 待办：prd 前置机制化（攒批，审查出结论后一并处理，现在不动）

裁定（2026-10-03）：语义上可喂 prd 的技能要在**机制上**成为 prd 前置，攒一批一起改，不逐个零改。

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
- YAML schema（每片段）：key=片段 ID（YAML/标记对/测试三方共用锚）/ `text`=逐字内联文本 / `members`=必含技能短名（去 diy- 前缀）/ `banned`=必不含（防误插，承测试 C 组）/ `notes`=放置＋禁改面（人读，脚本不消费）。**封闭世界**：members ∪ banned == 全部技能，漏归即红（同 EXPECTED_SKILL_COUNT 型）。
- **标记对即锚**：`<!-- suite:§N begin/end -->`，位置固化在成员文件上、YAML 不存位置（SKILL.md 是自然文档非机器结构，位置规则必碎）。脚本只替换标记对内内容；标记对缺失=显式报错，不静默跳过。
- **调用与回执**：`python diy-coder/sync_texts.py`（同步＋终端摘要）；`--check` 只校验；`--json` 机器回执（逐片段×技能 ok/replaced/missing-marker/banned-violation＋失败原因＋counts＋覆盖缺口）；`--report <path>` 生成**自包含单文件 HTML**（成功/失败/原因/缺口分组，内联 CSS 零依赖，浏览器直开）；退出码非 0=有失败（CI 可用）。
- `test_suite_texts.py` 改造：删自持 frozenset（INSTANCE_MEMBERS/CONVERTED_*/NON_MEMBERS），改为读同一 YAML；头注释 NFR-4 旧理由一并修正。
- **首次落地=AI 插空标记对＋人审位置＋测试兜底**：人只审标记对位置（diff 上下文行），内容逐字一致由测试断言。流程：定稿 YAML → AI 按 notes 逐技能插标记对 → 跑脚本填充 → 跑测试 → 人过目 diff → sync.sh 两份 md5 全同。
- 首批应用：**§9 回复纪律**（精简、名词准确；§6 管产物内容、§9 管回复文字；diy-help「10 行上限」并入）＋**产物精简条款**（并入 §2；中文禁词表/句长上限随批拟呈核）。
- 公共条款处置判据（2026-10-03 两轮讨论定稿）：**保证只来自「必经引擎关卡」**——关卡必经＋自行计算＋显式拒绝不代建（diyc_lib.py:369-376 MISSING_FILE 防呆；init 铸骨架、终门 exit 0 唯一放行）。提示词层只降摩擦不供保证；处置序：能下沉关卡者优先下沉（产物行数/禁词 grep 可断言），无关卡可设的（废话判定/回复风格）承认概率区，靠在场＋抽查。
- 配套下沉项：`diyc.py resolve` 回执扩 `communication_language` / `document_output_language` 两键（diyc_lib.py:198）；母本 §3「读 yaml 自解析」改「跑回执取值」。随本批一并改。
- 协调：前置=待办②安装根口径（§1 句宿主无关化，避免定稿改两次）；与待办④逐项化同为 50 文件级改动，实施定先后，且逐项化规范加「标记对内内容冻结不改」。

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
