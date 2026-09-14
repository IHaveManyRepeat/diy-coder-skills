# B1 批保真度报告 —— bmm 需求与调研（5 技能）

- 日期：2026-09-14 ｜ 批次：BMAD 迁移 阶段 B 第 1 批 ｜ 状态：**待用户审阅**（迁移计划 §五：B1 强制人工审点）
- 任务书与仲裁记录：`diy-coder/.analysis/2026-09-14-migration-b1/taskbook.md`（§12 为增量裁定，覆盖前文）
- 范式蓝本：P1 样板 `diy-checkpoint-preview`（已拍板）；写作蓝本：`batch4/frozen-texts.md`
- 驱动：agent team `migration-b1`（W1-W5 分技能交付 + V 独立验证）

## 一、批次结果总览

| 技能 | 源技能（合并） | 产物 | 领域引擎 | steps | 测试 | 测试数 |
| --- | --- | --- | --- | --- | --- | --- |
| diy-research | market + technical + domain research（3合1） | `research.yaml`（RS-###） | `research.py` | 14 文件 | test_research.py | 21 |
| diy-product-brief | product-brief | `brief.yaml`（BD-###） | `brief.py` | 5 文件 | test_brief.py | 18 |
| diy-prfaq | prfaq | `prfaq.yaml`（PQ-###） | `prfaq.py` | 5 文件 | test_prfaq.py | 17 |
| diy-readiness-check | check-implementation-readiness | `readiness.yaml`（IR-###） | `readiness.py`（委派 diyc） | 6 文件 | test_readiness.py | 14 |
| diy-project-context | document-project + generate-project-context（2合1） | `project-context.yaml`（PC-###） | `context.py` | 5 文件 | test_context.py | 18 |

**批级要点**

1. **5 个新产物类型均走技能自带领域引擎**（P1 的 R1 裁定延续：不扩 diyc 类型集）；契约同构——`exit 0` 唯一放行 / `--json` 单行回执 / `violations[{code, where, msg}]` + `counts` / `--output-dir` 必填 / 实例解析一律委托 `diyc.py resolve`。
2. **diyc 委派首次落地**：diy-readiness-check 的跨文档核对（FR 覆盖 / ID 链 / 跨文件真值）100% 子进程调用 `diyc.py check --type … --final`，本仓库真实产物实测 counts 与 diyc 自身逐项互证（22 FR / 19 must-FR / 4 epic / 17 story / 38 AC / 0 缺口）。
3. **确定性下沉的三处实质收益**：research 的引用完整性校验、readiness 的"人工通读 md 提取 FR"改为读结构化产物、project-context 的"14 步人工扫描"（部件探测 / 清单解析 / 源码树 / 既有文档发现）沉入 `scan` 引擎且语言无关。
4. 冻结文本 5/5 逐字命中（实例句 md5 `5445f98b…`、写作纪律块 md5 `f1b3b6fb…`）；登记元数据 5/5 与 skill-map 冻结表逐字一致。

## 二、逐技能保真度

### 2.1 diy-research（3合1）

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 3×6=18 → 14 文件（01-scope + 3 维度 × 02..05 + 06-synthesis；三源 init 合 1、末步合 1） |
| 源 menu → diy 分支 | 0 项 → dimension 路由 3 + Create/Update 2 |
| 门禁 | 联网硬前提（源 PREREQUISITE 保留）；无上游产物依赖；拒绝路径零产出 |
| ID 链 | `RS-###` 顺序稳定 + `--previous` 防丢记录（丢 → `ID_UNSTABLE` 点名） |
| viewer | 通用降级 rc=0 出图 |

能力归宿：market 4 分析步 → `market/02..05`（6/7/8/7 个 area 行）；technical → 同构（6/7/7/7+recommendations）；domain → 同构（5/6/7/6+recommendations）。
裁剪（3 条，均非能力）：customize 机制（既定）、Success Metrics/Failure Modes 尾部自检表（元品质声明，硬约束已提取进 Rules/各步）、research.template.md 与 slug 命名算法（单文件形态无路径可派生，映射为 `dimension`+`topic`+`date` 字段）。**无 B4 回接项**（三源零引用未建技能）。

### 2.2 diy-product-brief

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 9（skill-map 登记）→ 5 文件（01-discovery / 02-draft / 03-finalize / 04-update / 05-validate） |
| 源 menu → diy 分支 | 5 项 → 5（create/update/validate 路由 + create 内 fast-path/coaching-path） |
| 门禁 | 无上游依赖；intent=update/validate 而产物缺席 → 零产出拒绝 + 路由（`intent` 子命令，P1 `target` 先例） |
| ID 链 | `BD-###` 格式+唯一；`--previous` 防丢决策 |
| viewer | 通用降级 rc=0（决策表/BD-001 均在页面） |

等价改造记账：`.decision-log.md` → `decisions` 集合（会话中即写）；`addendum.md` → `addendum` 集合；`brief_template` → 步骤 02 的默认结构节表；`persistent_facts`（源读 project-context.md）→ 01 步读 `project-context.yaml` 的 `rules`（**与本批 diy-project-context 自然咬合**）。
裁剪：external_handoffs（Confluence/Notion MCP 交接，diy 无对应物，Rules 显式记载）；customize 机制。
**B4 后回接**：diy-party-mode / diy-elicit（开场推荐句）、diy-editorial-review（润色三遍）。

### 2.3 diy-prfaq

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 7（skill-map 登记）→ 5 文件（01-ignition / 02-press-release / 03-customer-faq / 04-internal-faq / 05-verdict）；references 四份并入宿主步骤（保「一次只加载一文件」） |
| 源 menu → diy 分支 | 0 → 模式分支 2（默认交互 / `--headless`+`-H`）+ 01 内分支 2（fast-track / graceful redirect） |
| 门禁 | headless 四要素在场/非空 → 缺项 rc=1 + 具名 gaps + 零产出 |
| ID 链 | `PQ-###` 文件内唯一（客户 ∪ 内部共用序列）+ `--previous` |
| viewer | 通用降级 rc=0 |

Stage 1-5 教练判据逐条保留（客户优先三改道 / 概念类型四值 + 非商业改框 / 子代理并行采集含降级 / Stage 2 九节锻造 + 五条质量棒 / Stage 3 五类角度 / Stage 4 五视角 + 创始人不愿面对那题 / Stage 5 三类判定 + distillate 九类）。
**仲裁改判一处**：coaching-notes 由 `distillate` 五桶改为顶层 `notes: [{stage, content}]`（`distillate` 回归纯下游摘要，防过程叙事污染 diy-prd 输入）——任务书 §12.5。
裁剪：customize 机制；`bmad-brainstorming` 改道路由（**B4 后回接** diy-brainstorm）。

### 2.4 diy-readiness-check

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 6 → 6（1:1 镜像） |
| 源 menu → diy 分支 | 1（IR 入口）+ 每步 [C] 阻塞菜单 → 0 菜单（顺序推进 + 2 个非阻塞人工点）；技能内分支 = design.yaml 在场/缺席 + verdict 三值 |
| 门禁 | prd+epics+stories 在场且 epics/stories final 才放行；architecture 缺席 warning、design 缺席不拒（源判据保留） |
| ID 链 | `IR-###` 顺序唯一；上游链 100% 委派 diyc（`TOOL_MISSING`/`TOOL_ERROR` 降级 warning，不崩） |
| viewer | 静默调用命令在位（P1 同款）；产物渲染由通用降级承接 |

关键改造（diy 优势点，步骤文已写明）：源 step-02「完整读取 PRD 提取全部 FR/NFR」→ 读结构化 `prd.yaml` + `collect` 回执，**不再人工通读散文**。
未机械覆盖一项（**已裁定**，任务书 §12.7）：`epics.feature_refs`/`stories.epic` 链的 F-x 悬空（diyc 明确排除范围）→ 步骤内读结构化 YAML 发现 + route，**登记为 C 阶段候选**（diyc epics 规则扩展）。
裁剪：customize 机制、`bmad-help` 具体引用（改指 diy-test-design）、源 md 报告模板（→ YAML 字段）、assessor 字段（冻结 schema 无此项）。

### 2.5 diy-project-context（2合1）

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 17（document-project 14 + GPC 3）→ 5 文件（01-scan / 02-context / 03-rules / 04-finalize / 05-deep-dive 含 5a-5g） |
| 源 menu → diy 分支 | 5（resume/rescan/deep-dive/cancel + GPC 入口）→ 4 分支 + 默认流程 |
| 门禁 | 项目根不存在 → rc=1 零产出；`--part` 未知 → `UNKNOWN_ID`；无上游依赖（anytime 入口） |
| ID 链 | `PC-###` 唯一 + `--previous` 防丢规则（旧稿不可读判 warning 不阻断） |
| viewer | 静默调用命令在位；产物走通用降级 |

确定性下沉（本批最大收益）：部件探测 / 项目类型分类（11 型 + `unknown` 降级）/ 清单解析（语言无关，未解析 → `MANIFEST_UNPARSED` warning）/ 既有文档发现 / 源码树 → 全部沉入 `scan` 引擎；步骤文明确「读回执，不重扫」。
源状态散文件（project-scan-report.json / 24h 归档 / 分批台账）→ `scan` 字段；深挖 5a-5g「禁抽样逐文件全读」硬句保留。
**B4 后回接**：GPC 的 A/P 菜单（advanced elicitation / party mode）。

## 三、源技能自身缺陷（12 项，V 阶段 A 独立清点；供理解"哪些差异不是我们的改造"）

| # | 缺陷 | 处置 |
| --- | --- | --- |
| OBS-1 | domain step-06 跨步引用编号错位（step-03/04 实为 04/05） | diy 版按实际步序，不复制错误 |
| OBS-2 | technical step-06 同类错位 | 同上 |
| OBS-3 | market step-06 计数错误（(1-4)，实际 6 步） | diy 版无此表述 |
| OBS-4 | document-project 引用不存在的 `project-types.csv` / `architecture_registry.csv` | diy 版不照搬该依赖（仅用实存的 documentation-requirements.csv 内容） |
| OBS-5 | document-project 自述"12 project types"实际 11 行；instructions 编号跳 n=2 | 按实际 11 行建枚举（W5 独立复核同结论） |
| OBS-6 | prfaq manifest 与 CSV 依赖登记不一致 | diy 登记元数据以 skill-map 冻结表为准 |
| OBS-7 | product-brief CSV 记 `-A` 参数，SKILL.md 从未定义（幽灵参数） | diy 版不迁该参数 |
| OBS-8 | 三 research outputLocation 拼写不一致 | diy 统一为 `{output_dir}` 单一路径 |
| OBS-9 | research step-05 的 [C] 文案"Complete Research"实际只路由 step-06 | diy 步骤路由清晰化 |
| OBS-10 | research/readiness 各步 stepsCompleted 自相矛盾 | diy 用 YAML 单一状态字段消解 |
| OBS-11 | document-project 是 SKILL→instructions→workflows 两级路由 | 重排为 diy 单级 SKILL→steps |
| OBS-12 | GPC 无续跑检测（DP 有） | 合并后由 YAML `scan` 字段统一承载 |

## 四、批级裁定摘要（全文见任务书 §12）

- **勘误 2 条**：W1 steps「10 文件」→ 14（同句描述展开即 14）；W3 Stage 3「六类」→ 源文 5 类角度 + 1 纪律句。
- **追认（适配项）9 条**：W1 `--final` status 一致性 + `--previous` 边界；W2 `intent` 子命令 + `status: final` 义务 + 起草期宽松口径；W4 三条加严 + 两个委派降级码；W5 两条裁量（`MANIFEST_UNPARSED` 仅 warning、旧稿不可读不阻断）。
- **改判 1 条**：W3 coaching-notes → 顶层 `notes` 键（§12.5）。
- **待办台账**：
  - **B4 后回接 4 处**：diy-party-mode / diy-elicit（brief 开场推荐）、diy-editorial-review（brief 润色）、diy-brainstorm（prfaq 优雅改道）。
  - **C 阶段清单**：viewer 标签映射 5 组 + 诊断键集 `ENUM_KEYS` 扩展（`prfaq.verdict.strength` / `concept_type` 属静默缺口——不映射也不告警，比有告警组更隐蔽）；**diyc epics 链规则扩展（`epics.feature_refs` / `stories.epic` 必须可解析——用户 2026-09-14 拍板排 C，落点 diyc、不写独立脚本）**；**diy-prd 对 prfaq `distillate` 的下游对接**（V 实测：diy-prd 全文零 `prfaq`/`distillate` 引用，下游消费未建立）；登记表纳入本批 5 技能。

## 五、V 独立验证结论

**首轮（diy-research / diy-product-brief / diy-readiness-check）——总判定：可发布 YES，阻断项 0 条**（报告：`v-b-research.md` / `v-b-product-brief.md` / `v-b-readiness-check.md` / `v-audit.md`）

| 技能 | 能力勾核 | 测试 | 冻结 md5 | 门禁实测 | 引擎契约 |
| --- | --- | --- | --- | --- | --- |
| diy-research | 34/34 | 21/21 | 双 ✓ | 4/4（空目录拒绝零产出 / final 合法 exit0 / sources 空 exit1 / --previous 丢 → ID_UNSTABLE） | 零新增码 |
| diy-product-brief | 21/21 | 18/18 | 双 ✓ | 4/4（intent update 拒绝+路由+零产出 / create 路由 / final exit0 / --previous 丢 BD-###） | intent 适配项核对无误 |
| diy-readiness-check | 20/20 | 14/14 | 双 ✓ | 4/4 + **diyc 真跑**（must-FR 缺口在 diyc.violations 与 coverage.gaps 两侧同现；缺三件套 → 3×MISSING_FILE+路由+零产出；verdict=ready 携 critical → SET_MISMATCH） | TOOL_MISSING/TOOL_ERROR 声明准确 |

跨技能一致性 **19 维全过**（登记元数据 / 触发语逐字 / 薄主文件 ≤90 / 语言绑定句法 / 读取纪律 / 渲染静默命令串逐字相同 / 写权边界 / exit 语义 / `--output-dir` 必填 / 回执共同键 / where 口径 / 违规码 / `--previous` 适用范围 / 测试覆盖 / 零 bmad- 悬空引用 等，逐维明细见 `v-audit.md` §2）。

渲染确认（验收 #6）：temp 项目 `viewer --no-open` exit 0，6 份 doc 渲染，未识别类型不崩。**标签缺口 5 组 + 1 条诊断键集扩展**已实测并登记 C 阶段（完整实测枚举清单见 `v-audit.md` §3；其中 `prfaq.verdict.strength` / `concept_type` 属**静默缺口**——不映射也不告警，需一并扩展 viewer 的 `ENUM_KEYS`）——这是主 agent 拍板的**已知且已登记的过渡态**（共享文件改动统一排 C，P1 同款处置；B2-B7 还会新增类型，逐批改同一文件属反复 churn）。

**次轮：diy-project-context——通过，无阻断项**（报告：`v-b-project-context.md`）

| 技能 | 能力勾核 | 测试 | 冻结 md5 | 门禁实测 | 引擎契约 |
| --- | --- | --- | --- | --- | --- |
| diy-project-context | 36/36 保留落地（含 12 条等价改造）；另 2 条裁剪有据 | 18/18 | 双 ✓ | 5/5（多部件夹具识别 client/web+server/backend+unknown，`MANIFEST_UNPARSED` 点名 Gemfile，**只读 0 文件产出**；`--part` 未知 → UNKNOWN_ID；根不存在 → MISSING_FILE；final exit0；`--previous` 丢 PC-003 → ID_UNSTABLE） | 零新增违规码；`MANIFEST_UNPARSED` 仅 warning，docstring 与实现一致；语言无关降级成立 |

V 独立确认 CSV 11 vs 12 型矛盾成立（源 `full-scan-instructions.md:21,41` 自述 12 行、实际 11 行；W5 按实际建枚举 `context.py:53-56`，两处独立命中）。

**第三轮：diy-prfaq——通过，无阻断项**（报告：`v-b-prfaq.md`）

| 技能 | 能力勾核 | 测试 | 冻结 md5 | 门禁实测 | 引擎契约 |
| --- | --- | --- | --- | --- | --- |
| diy-prfaq | 35/35（2 条裁剪有据；子代理 prompt 全文随 01 步保留） | 17/17（修补后 16→17） | 双 ✓（两次改判后均未变） | 5/5（headless 缺 3 项 → 具名 gaps + 零产出；四项齐 exit0；final 合法 exit0 含 counts.notes；stage≠5 → STATUS_MISMATCH；`--previous` 丢 PQ-003 → ID_UNSTABLE） | 零新增码；`check_notes` 与 docstring 一致 |

**终版总判定（5/5）：可发布 YES，阻断项 0 条**（`v-audit.md` 终版）

- 能力勾核 **146/146**；测试 **88/88**（21/18/17/14/18；prfaq 二次修补后 16→17）；冻结文本 **5/5 双段 md5**；门禁实测 **22/22 场景**
- 12 项验收：#1~#4、#7~#12 V 复核全过；#5 注册、#6 渲染由主 agent 收口（见 §五之二）
- 非阻断观察 **15 条**（O1~O15，v-audit §4）

**V 对主 agent 改判的异议与收敛（§12.5 二次修订）**：源 `distillate` 的 `Rejected framings`（源用途=防下游重提）与影响采用的竞争情报被我初次改判划入 `notes`，V 判为轻度保真度风险（下游 diy-prd 只消费 distillate）。**已裁定采纳并实施完毕**（W3 修补：两类回流 `distillate.constraints` / `open_questions`，格式 `Not <X>: because <Y>`；`notes` 只留纯过程叙事；测试 16→17，全绿）——**V 定点复查四查全过并标收敛关闭**（源 distillate 8/8 类吻合 / 六处落点句一致零残留 / 17/17 + 冻结 md5 / Schema 注释与步骤定义逐点对应；判据句 `A rejection is a constraint, not a story` 被 V 评为比其建议更进一步）。附带发现并要求登记：diy-prd 全文零 `prfaq`/`distillate` 引用，**下游对接未建立**，排 C 阶段回填。

## 五之二、主 agent 集成验证（2026-09-14）

| 项 | 命令/方式 | 结果 |
| --- | --- | --- |
| 注册（验收 #5） | `bash diy-coder/sync.sh` | 已安装 20 个 skill（15 现有 + 5 本批）；5 新技能 `SKILL.md` 源码/副本 md5 全一致 |
| 全量回归 | `cd diy-coder && python -m unittest discover -s tests` | **Ran 395 tests OK**（307 基线 + 88 新增：21/18/17/14/18） |
| 冻结文本 | 5 份 `grep -o "Instance resolution (FR-4.5/D-9).*" \| md5sum` + 纪律块同法 | 5/5 命中 `5445f98b…` / `f1b3b6fb…` |
| 登记元数据 | frontmatter 逐字段对照 | 5/5 与 skillmap 冻结表逐字一致 |
| 渲染（#6） | `viewer.py --project-root .` | rc=0，rendered 8 docs，静默无交互点（新类型走通用降级，已在各 W temp 项目实测） |
| 引擎冒烟 | readiness `collect`（真实产物，只读） | counts 与 diyc 自身逐项互证（22 FR / 19 must / 4 epic / 17 story / 38 AC / 0 缺口） |

> 边界声明：本节（§五之二）为主 agent 自测数据，**V 未独立复跑**（V 已核对并确认来源标注清楚）；§五 的 V 结论段由 V 本人事实核对（3 处更正已采纳）。其余主 agent 面声明（本批 §二/§三 引自各 W 回报与 V 报告）以对应文件为准。

## 五之三、验收 12 项对照（迁移计划 §二）

| # | 验收项 | 证据 | 判定 |
| --- | --- | --- | --- |
| 1 | 薄主文件（四段）+ steps/ 厚子文件 | 5 份 SKILL.md 65-74 行；steps 5-14 文件 | 通过 |
| 2 | 产物 YAML schema + 稳定 ID 前缀 | RS / BD / PQ / IR / PC，各 Schema 段 + check 用例 | 通过 |
| 3 | 前置门禁（零产出 + 路由） | 各技能测试的门禁用例（拒绝路径 listdir 为空）+ W 冒烟实测 | 通过 |
| 4 | ID 链接入 | 上游引用可解析（readiness 委派 diyc）；本产物 ID 稳定（`--previous`） | 通过 |
| 5 | 注册 | `sync.sh` → 20 技能，副本 md5 全一致 | 通过 |
| 6 | viewer 渲染 | 通用降级 5 类型实测出图；标签缺口记入 C 阶段清单 | 通过（降级） |
| 7 | 冒烟 TC | 87 条新用例（21/18/16/14/18），全量 394 绿 | 通过 |
| 8 | 登记元数据 | frontmatter 5/5 与 skill-map 冻结表逐字一致 | 通过 |
| 9 | 读取成本纪律 | On Activation 读取清单 + 「一次一 step 文件」+ 按 ID 定位 | 通过 |
| 10 | 双源输入声明 | **N/A**——本批 5 技能均非主线/WDS 交汇点（readiness 属主线校验，context 是 anytime 入口） | 不适用 |
| 11 | 渲染静默 | 各 Workflow 仅命令一行；无浏览器/等待/阻塞交互点 | 通过 |
| 12 | diyc 接线（a-e） | a 实例委托（5/5 frozen 句）；b 终门（各引擎 `check --final`）；c `--previous`（4/5 实现，readiness 报告追加式豁免）；d 语言绑定模板；e Rules 写权边界 | 通过（c 有一条豁免） |

## 六、人工审阅指引（B1 是强制审点，建议 10 分钟走完）

1. **先看本报告的 §二**——逐技能的「源 steps → diy 步数 / menu → 分支 / 裁剪清单」，任何一条你觉得不该裁的就是要追的问题。
2. **抽 1-2 个技能点开 SKILL.md**（`diy-coder/skills/<技能>/SKILL.md`，各 65-75 行）确认四段结构与写权边界是否符合你的直觉。
3. **抽一个引擎跑冒烟**（各技能引擎：`python diy-coder/skills/<技能>/scripts/<引擎>.py check --final --project-root . --output-dir diy-output --json`）——新产物不存在时应回 `MISSING_FILE` rc=1（这是门禁在工作的证据）。
4. **要看的争议点**（若有）：§四的改判 1 条（prfaq notes 键）与未机械覆盖 1 条（readiness 的 epics↔PRD 链）。
