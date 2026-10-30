# 底单·已销归档（原「diy技能名录与审查底单.md」销账段原样迁出）

> 迁出 2026-10-25：源文件中销账完毕／已执行完毕的段落**原样**迁入本文件，内容零改写。
> 段名与迁出前一致（任务书「段名对表」引用口径不受影响）；历史行号锚以迁出前源文件为坐标。
> 未销／部分销段落仍在源文件 `diy技能名录与审查底单.md`；本文件只进不出（新销账段随迁移追加至此，不回改历史段）。

## 待办：prd 前置机制化〔v4·批5a 已销 2026-10-25〕

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
| diy-research | research.yaml | line: mainline / phase: 1-analysis，链上无位 | registry.prereq（已落 5a） |
| diy-product-brief | brief.yaml | 同上 | registry.prereq（已落 5a） |
| diy-prfaq | prfaq.yaml（distillate 段自证为 PRD 输入） | 同上 | registry.prereq（已落 5a） |
| diy-brainstorm | brainstorm.yaml | line: any / anytime | registry.prereq（已落 5a；BI/BT/BA 由 Q-112 铸） |
| diy-cis-method | cis-method.yaml | line: any / anytime | registry.prereq（已落 5a；prd 按 CM 摄取） |
| diy-analyze | analysis.yaml（棕地现状） | line: any（候选，待裁） | 不入本批（5a 裁定 analyze 不入） |
| diy-project-context | project-context.yaml（棕地语境） | line: any（候选，待裁） | registry.prereq（已落 5a；rules 按 PC-###） |

约束：frontmatter 六字段与 registry 链序受 test_help_registry.py 双向守卫 + diy-bmb-module 镜像校验，改动须先裁后动（feedback-test-change-ruling-first）。
约束补充（2026-10-04 用户裁定）：**前置＝可选输入通道，非必须完成的门槛**——机制化不得要求前置产物全部在场才准跑 prd；保持 prd 现行语义「上游产物缺席即跳过该源，不因此阻塞」。本批改的是通道注册与 ID 认源，不加任何在场门禁。

## 待办：cis-method→design 喂入认 ID（同判据：下游认源 ID）〔v4·批5b 已销 2026-10-25〕

登记（2026-10-04 用户裁定）：`diy-cis-method/steps/04-design.md:210` 路由句「要把验证过的概念落成 UI / 接口契约 → `diy-design`」现为纯内容喂入（概念不带 `CM-###`）；机制化时改为 **ID 关联**——diy-design 消费设计思维分支产物须按源 `CM-###` 引用（design.yaml 引用位 / 输入面具体挂法待裁）。与 prd 前置批同判据（下游认 ID），是否同批实施待裁；现不动。

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

**〔v4·批4b 已销 2026-10-22〕**：总览/详情两层落形——总览横表 7 列（方法/路径/操作 ID/摘要/功能组/x-fr/请求参数简略·操作 ID 行内链接跳详情）＋详情按顶层 tags 声明序分组、每接口一张两列竖表全字段、标题挂 `id=operationId` 行锚（一 operation 一锚）；未挂/不匹配 tags 落「未分组」殿后（存量不丢行）；多 tag 取首个匹配归组；openapi 页通用渲染跳过 paths 树与顶层 tags 表（其余顶层键保留兜底）；KEY_LABELS 补详情行键 7 条＋`("openapi", "format")` FREE_TEXT 例外（照 4a type 先例·diy-lab 零诊断）；拆 `viewer_openapi.py` 新件（viewer_pages 336 行不超线）。新增 `tests/test_viewer_openapi.py` 9 用例（7 列/分组序/兜底/锚唯一/无重复节/security 覆盖/存量形）；夜队列 Q-118 施工（分支 overnight/2026-10-22/Q-118）。

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

## 已执行：滞后表述全库普查（2026-10-07，用户点名「语句有问题/多余文字」类跨技能普查，只读）

词族四组：`未建|若已建`·`待登记|下游待`·`≤90/90 行/上限 90`·`标签缺口|降级渲染|通用降级`。**净新增仅 1 处**：diy-bmb-builder steps 三处「≤90 行」（`03-analyze.md:41`·`04-gate.md:18/:20`·`05-finish.md:24`）→ 已补登逐项化批上限落点行。其余命中均在案或活机制：help.py:387「下游待登记」＝链走完分支的运行时枚举（活机制非滞后）；bmb_module.py:388 与 wds_brief/scenarios/trigger 三引擎「尚未建立」＝MISSING_FILE warning 语义（活机制）；wds-brief `03-signoff.md:146`「缺口 2」句面滞后已在一审行裁定归去源锚批（标签实落 viewer.py:48/:400）；wds_brief.py:90 / wds_scenarios.py:101 头注释「viewer 标签缺口登记」＝出处注旁形态（去源锚批口径内）。

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

**〔2026-10-23 核实补注·已实施〕** 本条已由夜队列 Q-113 落地：`diyc_kind.py`＋`diyc.py` `kind` 子命令在场，两技能 steps 已去表改调命令（feat `13437cc`·merge `17b32ca` 合入 dev）。本段销项，勿重复排期。

### 待办：diy-brainstorm 规则 1/8 写范围张力——规则 1 未回指 `.prev` 例外（2026-10-21 Q-109 审查发现，登记待改，现在不动）

登记来源：Q-109 审查发现——规则 8 新增每轮 `snapshot` 写 `{output_dir}/brainstorm.yaml.prev`，并自称「规则 1 写范围的 `.prev` 具名例外」，但规则 1 原文仍是无例外的禁令。

事实（2026-10-21 引原文）：
- 规则 1：「写范围：只写 `{output_dir}/brainstorm.yaml`（记录与 `revisions`）；不碰 `prd.yaml` / `sprint.yaml` / `stories.yaml` / 源码，也不建任何状态散文件。」
- 规则 8：「……拍 `{output_dir}/brainstorm.yaml.prev`（规则 1 写范围的 `.prev` 具名例外）……」
- 两条互不指认，逐字执行时冲突；规则 8 更具体，实际多半按 8 走，但自检/审查会反复报。

改法（待执行）：规则 1 末尾补半句「（唯一例外＝规则 8 的 `.prev` 快照）」；只动 `diy-brainstorm/SKILL.md` 规则段，不动规则 8 与引擎。测试面已核：`tests/test_brainstorm.py` 未钉住规则 1 原文（SkillContractTests 无该句断言），改动零测试影响。

**〔2026-10-23 核实补注·已实施〕** 本条已由夜队列 Q-116 落地：规则 1 末尾「（唯一例外＝规则 8 的 `.prev` 快照）」已在场（`5eb386e` 合入 dev）。本段销项。

### 待办：diy-brainstorm 违规码清单补登 `TOOL_ERROR`（2026-10-21 Q-109 审查发现，登记待补，现在不动）

登记来源：Q-109 审查发现——`snapshot` 写盘失败报 `TOOL_ERROR`，但引擎 docstring 违规码段只列九码＋`ID_UNSTABLE`；该码在 `brainstorm_cmds.py:159`（init 写盘失败）早已使用，属本批之前既有遗漏，Q-109 沿用未扩大。

事实（2026-10-21 核实）：
- docstring 原文：「本引擎用到 …`ASSUMPTION_PRESENT` 共 9 个，**冻结九码一字不动**；本批技能级新增码 1 个：**`ID_UNSTABLE`**」——未列 `TOOL_ERROR`。
- 使用点两处：`brainstorm_cmds.py:159`（init 写盘失败，既有）；`brainstorm.py:124`（snapshot 写盘失败，Q-109 新增）。
- 先例：diy-correct-course「新增 `TOOL_MISSING` / `TOOL_ERROR`（diyc 委派降级专用，同 readiness 先例）」；diy-e2e-tests 码清单含 `TOOL_ERROR`；diy-readiness-check 同。

改法（待执行）：docstring 违规码段补登 `TOOL_ERROR`——「工具层写盘／子进程失败通用码（init 写盘失败、snapshot 写盘失败使用）」；只补文档登记，不改代码行为、不动冻结九码。测试面已核：`tests/test_brainstorm.py` 无 docstring 码清单文字断言，改动零测试影响。

**〔2026-10-22 Q-117 已销〕** docstring 已补登（`9385b76`·merge `b9c0bc9`）；代码两处真实抛出点：`brainstorm.py:130`（snapshot）、`brainstorm_cmds.py:159`（init）。

### 待办：diy-brainstorm 想法铸稳定 ID `BI-###`（2026-10-21 用户指示登记，现在不动）

登记来源：Q-109 审查时用户确认「队列『不含三级 ID』与测试出现 BI-### 不矛盾」（Q-109 只做对账、不做铸造），并要求把「给每一个想法增加 BI id」正式登入待办。

既有裁定（2026-10-04，见本文件 :190）：brainstorm 下游锚从记录级 `BS-###` 下沉条目级三级——`BI-###`（想法）/ `BT-###`（主题）/ `BA-###`（行动）；文件内全局唯一、ID 取代 `no`（不并存）。改动面：`brainstorm.py`（铸造/唯一性/引用完整性）＋ SKILL.md 结构段（`ideas[].no`→`id`，`themes[].ideas` / `priorities` 三键 / `actions[].idea` 改引 ID）＋ `steps/04-organize.md` ＋ viewer 展示 ＋ diy-lab 存量产物迁移。

本次登记：把「每个想法铸 `BI-###`」单列为可执行待办。Q-109 已就位的前置：每轮 `snapshot` 快照＋`check --previous` 已支持 `ideas[].id` 对账与「迁移轮跳过」（旧无 id → 新有 id 当轮不误报）。

待裁点（做时）：
- 范围：只做 BI（想法），还是连同 `BT-###` / `BA-###` 一次做（:190 原裁定为三级一体）；
- ID 取代 `no` 的迁移形态、`themes[].ideas` / `priorities` / `actions[].idea` 引用切换；
- 与 prd 前置机制化（:184）的先后：BI 是 prd 外部锚，prd 侧摄取规则随该批核；本条可先落地铸造，不阻塞 prd 批；
- viewer 展示与测试面（先裁后动）。

**〔2026-10-22 Q-112 已施工（68a7d0f）＋遗留登记〕** 三级 ID 引擎、SKILL、`steps/04-organize.md` 已落；遗留 `steps/03-facilitate.md`（:6 输出形状、:35 铸造口径、:38 格式模板、:43 已作废判据「`no` 连续性即存在凭证」）与 `steps/05-finish.md:38` 摘要模板仍为 no 制——照 03 执行会被新引擎拒收（`no` 在场 → `ENUM_INVALID`）。处置＝2026-10-22 夜队列 Q-119（纯文本 5 处，scope 两 steps 文件；前提 Q-112 已合并）。

**〔2026-10-22 用户裁·裁断不进技能文本〕** Q-112 引入的溯源句「ID 取代 `no` 不并存」及裁定日期锚须清除，SKILL／引擎只留可执行规则（`ideas[]` 用 `id`；`no` 字段出现即 `ENUM_INVALID`）。落点：`SKILL.md:73`、`brainstorm.py:27/:30/:63`、`brainstorm_checks.py:21/:22/:101`。并入 Q-119。

## 待办：rq_lib 中文路径 scope 比对误报——core.quotepath 八进制转义不解（2026-10-23 夜队列 Q-118 队列外发现，登记待修，现在不动）

登记来源：2026-10-22 夜跑 Q-118 首跑 done 被 scope 门误拦（晨报「队列外发现」段）。

缺陷：`rq_lib.py:201` `changed_rels` 用 `git status --porcelain` 取变更文件，默认 `core.quotepath=true` 时非 ASCII 路径输出为八进制转义形式（`diy\346\212\200...`），`.strip('"')` 不解转义 → 与任务 `scope` 比对时中文路径永不匹配，误报「scope 外」。

当夜绕法：进程级 `GIT_CONFIG_PARAMETERS='core.quotepath=false'`（零代码改动，全程带用）。

改法（二选一，随任务书呈裁）：

- **A（推荐）**：rq_lib 内 git 调用统一带 `-c core.quotepath=false`——从源头消除转义，零解析逻辑；
- B：保留默认输出、`.strip('"')` 后解八进制转义——多一段解析代码，且要防半转义边界。

补测：冒烟用例加「中文路径 scope 比对」（构造含中文文件名的 scope，断言不误报）。

改动面（做时）：`rq_lib.py` git 子进程调用处＋labs/diy-overnight 冒烟。现在不动。

**〔2026-10-23 用户裁·按 A〕** rq_lib 内 git 子进程调用统一带 `-c core.quotepath=false`。已裁待入夜跑队列，开工待请令。

**〔2026-10-24 已入队〕** 夜队列 `queue-2026-10-24-221738.yaml` 之 Q-124（队尾·小件超时自动顺延；与同队列 Q-122 批5a／Q-123 批5b 零文件交集）。


---

## 核证记录（2026-10-25）

拆分同日对本文件全部 26 段做销账核证：①声称的落地提交逐个验证为 dev 祖先；②对 HEAD 现文件做内容级抽查——销账声称的关键行为句逐条 grep 在场。**结论：26 段全部属实，零假销账，无需回移。**

| # | 段标题（本文件内原题） | 提交核 | 内容核（HEAD 实态） |
|---|---|---|---|
| 1 | 待办：prd 前置机制化〔v4·批5a 已销 2026-10-25〕 | bb0d0bc ✓ | `registry.yaml` `prereq:` 段在场 |
| 2 | 待办：cis-method→design 喂入认 ID〔v4·批5b 已销 2026-10-25〕 | 512c778 ✓ | `design_checks.py:38` `_validate_cm_refs` 在场 |
| 3 | 待办：diy-help 多实例聚合导航·版本演进模式 | ad9e505 ✓ | `help_lib.py` 拆分落地（help.py 421→160＋help_lib 332） |
| 4 | 待办：接口契约通用设计与架构鉴权面 | a903268 ✓ | `diy-openapi/SKILL.md` `securitySchemes`×3＋RFC 9457 |
| 5 | 待办：openapi 接口总览行锚 | 7798f9e ✓ | `viewer_openapi.py` 存在＋`id=operationId` 行锚句 |
| 6 | 待办：viewer index 产物卡片按生成时间排序 | 408e50f/5607d3a ✓ | `viewer.py:26` import `sort_docs`（三消费点序） |
| 7 | 待办：diy-test-design 五轴矩阵＋故障假设落盘 | 5183546 ✓ | `dimension`/`fault_hypotheses`/`kill_target` 在场 |
| 8 | 已执行：滞后表述全库普查（只读） | 无需提交 | 只读侦察无交付物声称——无假销账面 |
| 9 | 待办：diy-e2e-tests 关联 openapi 契约认 ID | 5183546 ✓ | `e2e/SKILL.md:60` `api_refs` schema＋双源通路句 |
| 10 | 待办：变异配置显式化——默认开＋可关 | 5183546 ✓ | `test-design/SKILL.md:74` `mutation: {enabled: true, tool?}` |
| 11 | 已执行：§6「精准简练」适用面收窄 | 历史批 | `test_suite_texts.py:214` `PRECISE_NON_MEMBERS` 五员在场 |
| 12 | 已执行：runner 冲刺末三连 | 历史批 | `runner.py` `--skip-post`/`--post-only` 旗标在场 |
| 13 | 待办：test_pending_precise_brief 跨窗口中间态红〔v4·批0 已销 2026-10-09〕 | 批0 完工 | 声称＝检查任务完结非代码交付；测试现稳定绿 |
| 14 | 待办：diy-selfcheck 产物 YAML 化〔v4·批2c 已销 2026-10-11〕 | c87328c ✓ | `selfcheck.py` 存在＋SKILL 主产物 `selfcheck.yaml` 句 |
| 15 | 待办：爆炸半径分析注入 diy-review 与测试用例设计技能族〔v4·批1 已销 2026-10-10〕 | 5183546 ✓ | `review/SKILL.md:49/:52/:64` `radius` 枚举＋按半径排序句 |
| 16 | 待办：diy-analyze 吸收 arch-analyze 职能〔2026-10-17 方向推翻·本段作废〕 | 声称＝作废 | 非交付声称；arch-analyze 路由句现存（批 5e 施工中处理） |
| 17 | 待办：test-plan 终门「FH 被杀」口径〔Q-102 已销 `d1879b3`〕 | d1879b3 ✓ | `diyc_check_docs_testplan.py:362` `coding_phase` 双口径分支 |
| 18 | 待办：spec-scan kind 判据规则表〔Q-108 已销 `36a780c`〕 | 36a780c/832eb55 ✓ | `01-collect.md:20-23` 三阶链＋调 `diyc.py kind`（selfcheck 同文） |
| 19 | 待办：wds-assets 提示词（Prompt Keywords / Prompt Recipe）翻译 | 83b50ad ✓ | `content-styles/3d-render.md` 等含「提示词」中文对照 |
| 20 | 待办：architecture 规则 4「安全类决策只在需求要求时才成型」说法有误 | a903268（随批 4a）✓ | `architecture/SKILL.md:89` 已改「安全默认考虑·问用户一次·封闭四类」 |
| 21 | 待办：STAMP_TYPES `test-design` 键与产物文件名错位〔Q-101 已销 `88e3f7d`〕 | 88e3f7d ✓ | `diyc.py:38` `STAMP_TYPES` 含 `test-plan`，全文零 `test-design` |
| 22 | 待办：kind 判据表引擎化〔2026-10-23 已实施 Q-113〕 | 13437cc ✓ | `diyc_kind.py` 存在＋两技能 steps 已去表改命令 |
| 23 | 待办：diy-brainstorm 规则 1/8 写范围张力〔2026-10-23 已实施 Q-116〕 | 5eb386e ✓ | `brainstorm/SKILL.md:77`「唯一例外＝规则 8 的 `.prev` 快照」在场 |
| 24 | 待办：diy-brainstorm 违规码清单补登 `TOOL_ERROR`〔Q-117 已销〕 | 9385b76 ✓ | docstring 补登句＋`brainstorm.py:130` 实抛点 |
| 25 | 待办：diy-brainstorm 想法铸稳定 ID `BI-###` | 68a7d0f＋Q-119 ✓ | `brainstorm.py` `BI/BT/BA` 铸造在场；steps/03 零 `.no` 残留 |
| 26 | 待办：rq_lib 中文路径 scope 比对误报——core.quotepath 八进制转义不解 | 40f7b82/65867d3 ✓ | `rq_lib.py:32` `git -c core.quotepath=false` 统一前置 |

核法说明：#8/#13 系侦察/检查类无代码交付物声称；#16 系作废声明（非交付）——三段天然无 git 面；其余 23 段提交＋内容双核全过。

## viewer HTML 任务复制按钮（2026-10-12 登记）〔Q-003 已销 2026-10-28 核实〕

（迁出 2026-10-28·原样自「升级事项」段·段名不变）

- 候选：viewer 渲染的 HTML 页面对任意任务加一个复制按钮——点击后把该任务内容复制到剪贴板，粘贴进 Claude Code 这类工具里继续处理；不限产物类型（不管是什么产物）。
- 事实：渲染脚本＝`diy-viewer/scripts/viewer.py`（产 index.html 等页）；按钮属纯前端交互。
- 已裁（2026-10-13，三项）：
  - **复制内容形态＝转成提示词文案**（不复制原文 YAML/JSON）——文案必带**产物文件路径＋条目 ID**，使 AI 据以打开对应文件、定位该 ID 对应内容，再按用户粘贴后口述的意图（解释/修改等）处理。
  - **按钮位置＝表格内每个 ID 旁**（非每任务卡一个）。
  - **交互＝单击复制**。
  - 文案具体措辞随任务书拟。
- 触发：需要把 viewer 里看到的任务直接喂给 AI 工具时再做。

**〔2026-10-28 核实已销·Q-003〕**：三项裁定＋措辞均已落地（2026-10-19 夜队列 Q-003）——文案＝提示词式含产物路径＋条目 ID（`viewer_render.py:390` 文案 A）·按钮＝表格 ID 旁（`:88-89`）·单击复制＋剪贴板双路兜底（`:385-404` COPY_JS）·trace 注在案（`:69`）。本节行滞后，勿再当待办。
