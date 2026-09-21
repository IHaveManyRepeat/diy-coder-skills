# B7a 批保真度报告 —— wds 前置三段（3 技能）

- 批次：BMAD 迁移 阶段 B 第 7 批**前半**（B7 已按用户裁定拆为 **B7a / B7b**）｜ 完成日期：2026-09-21 ｜ 编制：主 agent
- 任务书：`diy-coder/.analysis/2026-09-21-migration-b7/taskbook-b7a.md`（影子仓自检后 `ec07782`，施工期再订正 2 处）
- 开工前自检：dogfood 扫描 **71 条**（阻断 6 / 高 19 / 中 37 / 低 9）逐条处置 + **两轮旧值复扫**封口（再抓 2 处漏改）
- 交付：`diy-wds-brief` / `diy-wds-trigger` / `diy-wds-scenarios` —— 套件从 41 → **44 技能**
- 本批三点特殊：① **WDS 线是独立产品线**（与 diy 主线并行不交汇），本批 3 技能自成一条可跑的短链（brief → trigger → scenarios）；② **源侧缺陷密度远高于前六批**（死链、断链、幽灵路径、互斥阈值成片）——「保真」在本批**不等于「照抄」**；③ **WDS 线在 C·3 前是断头路**（`diy-design` 硬门 `prd.yaml: 已定稿`）——本批产出的 `visual_direction` 等键**本批零消费者**，属既定排序（见 §七-3）

## 一、批次结果总览

| 技能 | 源 | 源规模 | 源步（主/校验/合计） | diy 交付 | 用例 |
| --- | --- | ---: | --- | --- | ---: |
| `diy-wds-brief` | `wds-0-project-setup` + `wds-0-alignment-signoff` + `wds-1-project-brief`（**3 合 1**） | 165 文件 / 20,615 行 | 2+6+40 / 6 / **54** | `SKILL.md` **86 行** · `steps/` **7 文件 57 小节** · 引擎 832 行 · 35 用例 | 35 |
| `diy-wds-trigger` | `wds-2-trigger-mapping` | 52 / 7,782 | 10 / 5 / **15** | **89 行** · `steps/` **6 文件 11 小节** · 引擎 1198 行 | 38 |
| `diy-wds-scenarios` | `wds-3-scenarios` | 21 / 3,449 | 9 / 5 / **14** | **88 行** · `steps/` **6 文件 16 小节** · 引擎 1003 行 | 44 |

**合计**：3 技能 · 5 源（20,615 + 7,782 + 3,449 = **31,846 行**）→ diy **19 个 `steps/` 文件 · 3 引擎 3,033 行 · 117 用例**。

**批级口径**：零阻断 · **能力损失 3 处**（全部显式登记，见 §二）· **源侧缺陷修复 9 条**（登记为「修复」非偏离）· 欠账见 §七。

## 二、逐技能保真度

### 2.1 `diy-wds-brief`（WDS 线入口：分诊 → 对齐 → 战略简报）

- **7 个步骤文件 / 57 小节**：`01-intake`(3) · `02-alignment`(12) · `03-signoff`(6) · `04-core`(12) · `05-content`(7) · `06-visual`(7) · `07-finish`(10)
- **产物** `wds-brief.yaml`：`intake` · `client_profile`(四域) · `brief.{core, content, visual, platform}` · `alignment`(十节) · `signoff`(三型) · 顶层 `project.status`（母本 §8 两值）
- **★ 裁定 13（用户拍板）签核全留**：三型并列（`external_contract` 11 节 / `service_agreement` 12 节 / `internal` 7 节）；**diy 无合同类产物载体** → 由 W1 设计段 schema 并回报三项（段结构 / 为何不另立产物 / viewer 标签需求）
- **源侧修复（4 条）**：① `service-agreement` **无构建步**（277 行模板从未被加载）→ **补齐 12 节构建步**；② `05f Availability` 写的节在合同模板中**不存在** → 补为合同第 6 节（**条件性**，仅长期聘用）；③ 术语表 11 处死链 → 词表内联；④ 简报档位读一个**从不被创建的文件** → 改由 `init --brief-level` 落 `intake.brief_level`
- **74 项校验去重结果**：**74 → 74，零删除**（逐对核对后确认三组疑似交叉均非重复，「视觉 45 项」在 wds-4/wds-7 面、不在本技能 74 项内）
- **能力损失（登记）**：源 `progress-tracker` 的「首次即确认 / 需纠正」反思统计不迁（diy 无承载位）；`_bmad/wds/data/agent-guides/saga/` 5 份 1,433 行 → **能力以引导问句内联**（非纯丢弃）

### 2.2 `diy-wds-trigger`（业务目标 ↔ 用户心理的 Effect Mapping）

- **6 个步骤文件 / 11 小节**；产物 `wds-trigger.yaml`：`business_goals[]` · `personas[]`(`TG-<n>`，**驱动因素内嵌** `DF-<n>.<m>+|-`) · `driver_patterns` · `priority` · `feature_impact[]` · `effect_map`
- **裁定 7（Effect Map 两形态）**：`yaml` 是单一源、Mermaid 是派生视图——源 `08a–08h` **8 微步骤的构图纪律收编为唯一定义**（配置 / 节点模板 / emoji 规则 / 连接数校验 = 目标数 + 2×人物数 / 4 类 classDef 逐字），`templates/trigger-map.template.md` **收编而非删除**（92 行可填骨架 + 必守十条）；`data/mermaid-formatting-guide.md`（262 行，无消费方且与步骤正文数字互斥）→ 裁
- **裁定 9（三模式降级）**：W 为默认完整路径；**S/D 保留 5 层管线的第 2–5 层为自审循环，第 1 层（Learn Form）标为不可用**——源侧该层依赖 **5 条不存在的文档**（幽灵路径）。**不新建方法层**（那是「造」不是「迁」）→ **登记为能力损失**
- **裁定 11（doc-synthesis 改写）**：替代入口从「用户往会话里塞文档」→ **读 diy 既有产物**（七维覆盖图 → `wds-brief.yaml` / `prd.yaml` / `research.yaml` / `prfaq.yaml` / `brainstorm.yaml` 的逐键映射表已落）
- **裁定 6（口径归一，两处）**：驱动因素 **3–5**（源采集端口径，展示端不再截断到 3）· 人物群 **2–4**（去掉「三级 TG0/1/2 + 5/3/3 加权」假设）
- **裁定 10（Feature Impact 保留）**：`06a–06e` 五微步骤 + 评分常量（Primary 5/3/1 / 其他 3/1/0 / Must-Have 阈值）全保——**与裁定 6 去掉的 `5/3/3` 是两组不同常量，不冲突**
- **`metrics` 子命令**（本技能独有）：人物群数 / 每人正负驱动条数 / Effect Map 连接数四条机械核对；越界 → warning（不阻断，保真源侧「展示端自适应」口径）

### 2.3 `diy-wds-scenarios`（场景大纲 + 页面树）

- **6 个步骤文件 / 16 小节**；产物 `wds-scenarios.yaml`：`scenarios[]`(`SC-<nn>`) → `pages[]`(`SC-<nn>.P<n>`)
- **裁定 12（只产 YAML）**：**不建 `C-UX-Scenarios/` 目录树、不建 `Sketches/`**——那是 C·3 `diy-design` 的产物位；源的「逐场景建文件夹 + 页面样板 md」→ 「写 `scenarios[]` 记录 + 其 `pages[]`」
- **裁定 8（ID 体系）**：`SC-<nn>` / `SC-<nn>.P<n>` / `TG-<n>`；**废止独立的 `P-*` 前缀**（源侧 0 处，且 `P-` 在 diy 命名空间是高危未占名）→ **属对已定稿计划的改判，已登记**（计划 §四 :214/:246 原写「引 `SC-*`/`P-*`」）
- **裁定 17（交接契约键）**：每条记录必携 `design_intent`(`[K|C|S|D|L]`) / `design_status`(初值 `not-started`) / `trigger_map_context`
- **裁定 15（validate 裁撤）**：源 `steps-v` 5 步 751 行 + `validation-report.md` 裁；**五维校验并入 `06-finish.md`**（36 项）。另：源 `workflow.xml` 450 行（32 个 `<gate>`，与 md 双写）——**先抽闸门清单再裁文件**（32 闸逐条落点表见 W3 回报 ⑧）
- **源侧修复（4 条）**：① 规模带 `<20/20–50/100+` 的 **50–99 空档** → `<20 / 20–50 / >50`；② 模式推荐的 **`Dialog` 幽灵值** → 归一本技能实装的 `对话/建议`；③ 避坑维度 **6 vs 7** → 取 checklist 权威版 **7**；④ 源页面样板首步三键与场景文件**重复存储** → 单一源
- **三条骨律全保**：阳光路径零分支 / 场景名必须含人物名 / 每页恰属一条战略链；两个用户关卡保留

## 三、批级裁定摘要（18 条 + 用户 3 项）

| 裁定 | 落点 |
| --- | --- |
| 1 三源融合 = 单技能 + 7 步骤文件 | **本批的「步数」= 文件内小节数（57/11/16），不是 `steps/` 文件数**（B6 已遇同类） |
| 2 产物 = 三技能各一个 YAML | **顶层 `project.status` 取母本 §8 两值**（★ 订正：首稿写「顶层不设 status」是从 B6 的 `sessions[]` 集合**误植**——三产物各是「一项目一份」的单记录） |
| 3 命名避让 | `wds-` 前缀为统一命名空间；记录 ID 见裁定 8 |
| 4 frontmatter 六字段 | ★ 订正两处（自检阻断）：`required` **三技能全 `true`**（首稿误填 false）· `phase` **逐技能取源实值**（`1-wds-strategy`×2 / `2-wds-design`，首稿自造 `wds`）；`line: wds` 首次引入 |
| 5 源侧缺陷处置 | **四类**（平台耦合→裁 / 冗余重复→裁到单一源 / **断链可修→修** / **断链不可修→裁+登记**）；判据 = **有没有落点**，不是「是不是断链」 |
| 6 号源侧互斥口径归一 | 驱动因素 3–5 · 人物群 2–4 · 避坑 7 项 |
| 7 Effect Map 两形态 | yaml 单一源 + Mermaid 派生视图（构图纪律收编为唯一定义） |
| 8 ID 体系 | `SC-<nn>` / `SC-<nn>.P<n>` / `TG-<n>`；**废止 `P-*`**（**对计划的改判，已登记**） |
| 9 三模式降级 | W 完整；S/D 第 1 层标不可用（**能力损失已登记**） |
| 10 Feature Impact 保留 | 评分常量全保（与裁定 6 是两组不同常量） |
| 11 doc-synthesis 改写 | 读 diy 既有产物 + 七维映射表 |
| 12 页面骨架归 `diy-design` | 本批只产 YAML（不建目录树） |
| **13 签核全留** | **用户 2026-09-21 拍板**；三型并列段 schema（W1 设计并回报三项） |
| 14 census 的 P2–P7 / C / K2 / K7 | 逐条裁定（主 agent，可推翻须列理由） |
| 15 `validate` 子流程裁撤 | 校验维度并入 finish 节；`validation-report.md` 产裁 |
| 16 `driving_forces` 归属键 | 嵌 `personas[]` 内 + 顶层 `driver_patterns` |
| 17 `scenarios[]` 交接契约键 | `design_intent` / `design_status` / `trigger_map_context` |
| 18 `--previous` 判 **no** | 三技能一致（单记录多段，无 ID 集合收缩面） |

**用户同日另拍板两项（不在本任务书内）**：① **B7 拆 B7a/B7b**；② `diy-analyze`（B7b）建且产物进 `diy-output/`、`presentation-master`（B7b）完整建第 9 活动。

**违规码**：三技能**零新增码**（复用冻结集；`wds-brief` 复用 `SET_MISMATCH` 承载「`init --project-type` 与既有产物不符」，已在 docstring 登记为语义复用）。
**★ 红线留存**：三技能全库 `check --type` 命中 **6 处，全是否定句**（无 `--previous` 后缀）——`diyc.py` 的 `CHECK_TYPES` 8 型封闭集未被污染。

## 四、V 独立验证结论（2026-09-21）

- **结论：审计通过，零阻断项。** 能力清点：census-1 真能力 A–I **9/9 承接**；census-2 T1–T11 **11/11 有归属**；能力损失 3 处全部登记到位
- **十一项重点验**：① 小节数 57/11/16（三处独立取数吻合）② 19 个 `steps/*.md` 引用**零 MISS**、与冻结表逐字一致 ③ **跨技能 schema 衔接 16 行对账表**（见下）④ 裁定 **11/11 全落** ⑤ 签核段三型并列真在场（实跑键转储）+ 服务协议构建步真补齐 ⑥ 红线零违规 ⑦ **跨技能门禁四种情形实跑全部零产出** ⑧ 三技能引擎冒烟 + `metrics` 四越界全 warning ⑨ **117 用例 V 亲手跑全 OK** ⑩ frontmatter 六字段与源实值逐字段一致（**开工前自检抓到的四个错处零回退**）⑪ 验收 12 过 / 1 未验（#5 注册属主 agent 面）
- **V 差异说明（比前批更强的三点）**：① 增了**跨窗口实测**——C·1 已落地并把 WDS 线登记为 `registry.yaml` 里的**独立一条线**（`entry: diy-wds-brief`、三节点、`exec_note`「本批止于 `diy-wds-scenarios`」），与 W3 的边界句**逐字一致** → 验收 #4 由「三技能自称不进 CHAIN」升级为**外部机制实证**；② 不止读文本，给了**引擎级实跑证据**（门禁四情形 / metrics 四越界 / 四型签核 `check --final` / 只读子命令 md5 不变）；③ 「未复现」项仅 1 条（W 回报是消息载体、未落盘，无法逐项对账）
- **V 发现 8 条**（1 高 3 中 4 低）→ **见 §七**

## 五、主 agent 集成验证（2026-09-21）

| # | 收口链项 | 命令 / 口径 | 结果 |
| --- | --- | --- | --- |
| 1 | ① 登记 | `test_suite_texts.py` 三处（`NEW_SKILLS` / `CONVERTED_INSTANCE` / `CONVERTED_DISCIPLINE`）+3 名 | **11 tests OK**（登记前三技能各报 2 红）——连带证明六节锚串逐字携带、零回改 |
| 2 | ② sync | `bash diy-coder/sync.sh` | **44 个 skill**（41 + 本批 3）；冒烟通过 |
| 3 | ③ 全量测试 | `python -m unittest discover -s diy-coder/tests` | **1116 tests OK**（含并行窗口 C·1/C·4 的改动）；**其中一次中间红见下** |
| 4 | ④ 渲染 | 三技能各 `init`（**tempdir**）→ `viewer.py` | `brief` rc 0 · **rendered 1 doc**；`trigger` rc 0 · **2 docs**；`scenarios` rc 0 · **2 docs**。**门禁独立复现**：上游缺失时 `trigger` / `scenarios` 的 `init` 分别 rc 1 —— 零产出 |
| 5 | ⑤ 本报告 | `render_fidelity.py`（复用 B5 渲染器） | `b7a-fidelity.{md,html}` |
| 6 | ⑥ 计划节 | `迁移计划.md` **§二十二**（§十七 B5 / §十八 C·2 / §十九 B6 / **§二十 C·4 / §二十一 C·1 均已占用**） | 见该节 |
| **7** | **收口期修复（主 agent）** | `precededBy` 缺 `diy-` 前缀 | **3 处 + 任务书源头 1 处**：`diy-wds-trigger` / `diy-wds-scenarios` 的 frontmatter 与 `test_wds_trigger.py:89` 的断言，从 `["wds-brief"]` / `["wds-trigger"]` 改为 `[diy-wds-brief]` / `[diy-wds-trigger]`。**根因**：裁定 4 按源侧「去 `bmad-` 前缀」推的短名——**库内约定是带 `diy-` 前缀的完整技能名**（`diy-architecture:6` 的 `precededBy: [diy-prd]`）。**由 C·1 的守卫 `test_help_registry.py::test_dependency_targets_are_installed` 抓出**（判 `dangling`），修后全量转绿 |

**★ 收口期的这条修复值得单独记一笔（机制面）**：本批是**第一次「新批次的 frontmatter 被另一个窗口的守卫抓到」**——C·1 建的 `test_help_registry.py` 在我拿到 V 审计结果之后落地，随即在全量测试里判出红。**它证明「登记表驱动」这条路已经形成自我校验**：新技能写错依赖名，不再只靠人工审、而是被机械守卫拦住。**B7b 编制时须把这条约定写进 §2.1 的 frontmatter 冻结表**（已在 B7a 任务书裁定 4 追订正二）。

## 六、验收 13 项对照（迁移计划 §二）

| # | 验收项 | 责任 | 证据 |
| --- | --- | --- | --- |
| 1 | 薄主文件 + steps/ 厚子文件 | W1/W2/W3 | **86 / 89 / 88 行**（≤90 硬阈值）+ steps **7 / 6 / 6 文件** |
| 2 | 产物 schema / 稳定 ID | 三 W | 三个 `wds-*.yaml` + `SC-<nn>` / `SC-<nn>.P<n>` / `TG-<n>` / `DF-<n>.<m>+|-` / `BG-<n>` |
| 3 | 前置门禁（零产出退出） | W2/W3（W1 = 入口） | 四种情形实跑零产出（上游缺失 / 非定稿 × 两技能） |
| 4 | ID 链接入 | 三 W | 唯一性 / 顺序性 / **不进 `help.py` CHAIN**（C·1 落地的 `registry.yaml` 把它们登记为**独立线**，外部机制实证） |
| 5 | 注册 | 主 agent | sync → **44 技能** |
| 6 | viewer 渲染 | 三 W 登记 + 主 agent 执行 | §八 |
| 7 | 冒烟 TC（≥5） | W1/W2/W3 | **35 / 38 / 44 = 117 用例** |
| 8 | 登记元数据（裁定 4） | 三 W | 六字段逐技能取**源实值**（V 逐字段比对零回退） |
| 9 | 读取成本纪律 | 三 W | 母本 §4 逐字（脚本比对，非目检） |
| 10 | 双源输入声明 | 三 W | 三技能**均非主线/WDS 交汇点**（交汇点在 C·3 的 `diy-design`）——逐技能明写 |
| 11 | 渲染静默 | 三 W | 规则段照母本 §5 逐字 |
| 12 | diyc 接线 a–e | 三 W | a 委托 `diyc.py resolve`；b 终门 = **自带引擎 `check`**；c 判 **no**（裁定 18）；d 母本 §3 逐字；e 写权边界 = 只写本技能产物 |
| 13 | 副作用纪律 | 三 W 自证 + V 抽验 | 唯一写面 = 自己的 `wds-*.yaml`（自动执行档）+ 静默渲染；**无外部服务、无确认档、无 defer 产生面** |

## 七、非阻断观察清单（欠账，C 阶段或后续批处置）

**V 发现 8 条**（1 高 3 中 4 低）：

| # | 级 | 归属 | 内容 | 处置 |
| --- | --- | --- | --- | --- |
| V-01 | **高** | W1 | 合同第 6 节 `availability` 被**无条件必填**，与步文件「**仅长期聘用**」互斥——固定价 + 10 节 → `check --final` rc=1，**且测试把 bug 固化了** | **已返工修复**：引擎改**条件性必填**（仅 `pricing_model: 长期聘用` 时计入）；测试补两条用例（固定价缺键 → rc=0 / 长期聘用缺键 → rc=1） |
| V-02 | 中 | 主 agent（§2.3.1） | W2 对 §2.3.1 冻结的四组键**实读仅 1/4**——**W2 的判断正确**（输出语言由 `diy-coder.yaml` 决定、视觉方向消费者在 C·3） | **已订正任务书**：§2.3.1 收窄「必读」面，其余降「可选读」——**不强推读无用键**（YAGNI） |
| V-03 | 中 | 主 agent（§2.3.1） | §2.3.1 **漏列 W3 的可选读行**（源侧 wds-3 确读简章的站点类型/页数/导航/SEO 关键词） | **已订正任务书**：补可选读行 |
| V-04 | 中 | 主 agent | `迁移计划.md` **§二十 / §二十一 施工期间被 C·4 / C·1 两窗写走**（开工前复核时 §二十 尚空） | **已处置**：本批改走 **§二十二**；教训写入 §9（**收口落笔前必须重查节号**） |
| V-05 | 低 | 主 agent | 驱动因素 ID 形态 `DF-<n>.<m>+|-` 是 W2 在裁定 8 之外的**补白**，首稿未登记 | **已在裁定 8 处追认并登记** |
| V-06 | 低 | W1 | 源侧缺陷四类台账里「断链**不可修**」的条目并入「断链**可修**」标签 | 留档（法据：裁定 5 已重排为四类且**判据 = 有没有落点**，W1 的归类实质正确、仅标签串味） |
| V-07 | 低 | W3 | Freya 第 4 条原则**零登记**（既没落本技能、也没写明归 B7b） | 留档：C·3/C 阶段归位时补登记 |
| V-08 | 低 | W3 | 驱动 ID 交叉核对**只核人物号、不核存在性** | 留档（现状不产生错判，后续批可加固） |

**另三条待办**：
1. **`visual_direction` 本批零消费者**——不是缺陷（下游在 C·3），但**保真度报告须明写「本批产出、C·3 消费」**（本报告 §0 已写）
2. **`line: wds` + WDS 线自有 `phase` 值首次引入** → **C1 面**：C·1 已落地 `registry.yaml`，须确认这两处的并表口径
3. **WDS 线机械写回命令面**（计划 §四 要求）——本批**只出契约不实现**，交 C·3（建议随 `design.py` 扩 `transition` 落地）

## 八、viewer 标签缺口清单（**C 阶段输入**）

三个新产物类型**均不在** `DOC_LABELS`（C·2 已扩至 32 条，普查面是「已建 41 技能」）：

| 产物 | 文档标签 | 键标签 | 值标签 | 备注 |
| --- | --- | --- | --- | --- |
| `wds-brief.yaml` | **缺** | `signoff` / `external_contract` / `service_agreement` / `internal` / `pricing_model` / `finalized` 等 | `signoff.type` / `alignment.status` / `intake.stage` 三个中文值域 | **另有一条着色硬需求**：这三处是**复合键名**，不在 `ENUM_KEYS` 内 → **既不报诊断也不着色**（要么扩 `ENUM_KEYS`、要么让 `VALUE_LABELS` 兜底） |
| `wds-trigger.yaml` | **缺** | 若干 | `personas[].priority` 的 `主\|其他` **+2 值标签** | **Effect Map 的 Mermaid 渲染器仍缺**——这不是「缺标签」而是**缺渲染器**，且**当前无责任人**（本批只登记不实现；产物侧已备好 `effect_map.diagram` 全文，渲染器上线即可直接消费） |
| `wds-scenarios.yaml` | **缺** | 若干（`design_intent` / `design_status` / `coverage.matrix` 等） | — | 渲染走通用降级 |

## 九、审阅指引（B7a 为**非强制人工审**）

**审阅面**：本报告 + `v-audit.md`（终审计证据）+ `v-capability-inventory.md`（能力清点）+ `dogfood-scan-2026-09-21.md`（开工前自检台账）。

**异常项才需看**：
1. **§三 的裁定 2/4 是被自检打回的**——`required` 填反、`phase` 自造，**根因是「凭前批先例类推源侧字段」**；B7b 编制时须先机械取数（`_req_check.txt` 那类）再填
2. **§七 的 V-04**：节号在施工期间被并行窗口写走（**第二次撞车**，B6 已遇一次）——**收口前重查节号**已成硬纪律
3. **§八 的 Effect Map 渲染器**：本批备好了数据，但**渲染器无人认领**——须在 §二十二 点名责任人
4. **§三 裁定 8 是对已定稿计划的改判**（废止 `P-*`）——**若你要维持 `P-*`，回退成本仅在 `diy-wds-scenarios` 一处**

**下一步**：**B7b**（`diy-wds-system` / `diy-wds-assets` / `diy-wds-evolution` / `diy-analyze` / `diy-reverse`，含用户拍板的两项：`diy-analyze` 建、`presentation-master` 完整建第 9 活动）或 C 阶段余项。
