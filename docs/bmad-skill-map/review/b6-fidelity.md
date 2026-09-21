# B6 批保真度报告 —— cis 创意套件（1 技能 · 4 方法分支）

- 批次：BMAD 迁移 阶段 B 第 6 批 ｜ 完成日期：2026-09-21 ｜ 编制：主 agent
- 任务书：`diy-coder/.analysis/2026-09-21-migration-b6/taskbook.md`（终态 md5 **`a3f0678875dc243d34642dffcc1390e6`** · **507 行** · 影子仓 `dcb825a` + 施工期 6 处订正未提交）
- 开工前自检：dogfood 扫描**两轮**（首轮 52 原始 → 36 去重全采纳；**开工前复扫又抓 3 处残留**，见 §七-0）
- 交付：`diy-cis-method` —— 套件从 40 → **41 技能**
- 本批三点特殊：① **首个「1 技能承载 4 条完整方法流」的批次**（4 合 1，四条流各有 7–10 步**逐份不同**的序列，合计 35 步）；② **源侧四份全产 md 文档**而 diy 侧取 YAML——「保真 vs 统一」的正面取舍，代价 = 新增 1 个 viewer 标签缺口；③ **源侧方法库接线性系统性缺陷**（四份库无一被完整引用，不可达率 0%/17%/50%/60%）——用户裁定「保真照搬 + `--all` 可查全库」

## 一、批次结果总览

| 项 | 源（`module=='cis'`） | diy |
|---|---|---|
| 方法流技能 | `bmad-cis-{innovation-strategy,problem-solving,design-thinking,storytelling}`（SKILL.md 1299 行 · 35 步） | `diy-cis-method`（`steps/` **5 文件** · 35 小节） |
| agent 人设 | 6 份（5 空壳 + `presentation-master` 非空壳） | **全裁**（风格并入 Rules 段；`presentation-master` 见 §九） |
| 模板 | 4 份（578 行 · 132 占位符） | `deliverable` 键表 **122 键** / 必填 **34 键** |
| 方法库 | 4 份 CSV（115 条） | 目录根 **`cis-methods.csv`**（表头 6 列 + **115 行**） |
| 引擎 | — | `cis_method.py` **976 行** · 5 子命令 |
| 测试 | — | `test_cis_method.py` **808 行** · **30 用例** |

**合计**：1 技能 · 4 源工作流 + 6 源 agent（普查基线 1299 行 SKILL.md + 578 行模板 + 115 条库）→ diy **5 个 `steps/` 文件 1135 行 · 1 引擎 976 行 · 30 用例 · 单表 116 行**。

**批级口径**：零阻断 · **能力丢失 0 条**（V 独立清点，唯一「有实值时被裁」的 `customize` 四键**四源实值全空**）· 真实损失 **0** · 欠账 **6 条**（见 §七）。

## 二、逐分支保真度

### 2.1 创新策略（源 `innovation-strategy` 347 行 · 9 步）

- **步骤小节 9/9**，标题逐条对译源 `goal`，每节带 `_源 step N：<英文 goal>_` 机械锚点
- **键**：源模板占位符 45 → `deliverable` **43 键**（−2 通用注入项 `date`/`user_name`）；必填 **9**
- **可达集 25 / 全库 30**：引 5 类（市场分析 / 商业模式 / 颠覆 / 战略 / 价值链）；**`技术` 类 5 条不可达 = 源侧缺陷，保真照搬**
- **能量检查点**：第 3 / 5 / 8 步

### 2.2 问题求解（源 `problem-solving` 325 行 · 9 步）

- **步骤小节 9/9**；**第 9 步为 `optional`**（源侧如此）——`已完成` 时 `current_step` ∈ {8, 9}，**四分支里唯一的同档例外**，引擎显式放行（测试⑥）
- **键**：35 → **33 键**（−2）；必填 **9**
- **可达集 30 / 全库 30**：6 类全引（源侧 0% 不可达）
- **能量检查点**：第 5 / 8 步

### 2.3 设计思维（源 `design-thinking` 274 行 · 7 步）

- **步骤小节 7/7**；`EMPATHIZE` / `DEFINE` / `IDEATE` / `PROTOTYPE` / `TEST` 五专名逐字保留英文大写
- **键**：23 → **21 键**（−2 通用注入项；模板首部的 `{{project_name}}` **保留为合法键、不入必填表**，见 §七-2）；必填 **7**
- **可达集 15 / 全库 30**：**只引 3 类**（共情 / 构思 / 原型）——`定义`/`测试`/`落地` 三阶段 15 条不可达 = **源侧缺陷，保真照搬**（**不是遗漏**，W2 三处显式声明）

### 2.4 叙事（源 `storytelling` 353 行 · 10 步）

- **步骤小节 10/10**；**无能量检查点**（源侧为零）
- **键**：29 → **25 键**（−4 = 通用注入项 2 + **agent 线残留 `agent_role`/`agent_name`**）；必填 **9**（**第 10 步唯一标签是四个注入项 → 该步无实键**）
- **多键合写**：源侧 10 步里 **9 步**是逗号分隔多键标签（另三份**零多键**）；W2 逐键切分列出、W3 引擎按逗号切分校验
- **两处源侧 bug 修复**（裁定 6，用户裁定 B）：
  1. **Step 2** 原硬编码 10 条框架 → 改**由引擎按类呈现全部 25 条**（默认集 = `--all`，**四分支唯一两值相等者**）
  2. **Step 3** 原引**不存在的列** `key_elements` → 改引真实列（源 `key_questions`，归并后列名 = `prompts`）
  - 源侧为 5 个框架写的专属提问**保留为增强段**；**净增 15 条可达（源 10 → 修后 25）**，登记为「**源侧缺陷修复**」而非保真偏离

## 三、批级裁定摘要

| 裁定 | 落点 |
|---|---|
| 1 四分支组织 = 主文件 + 路由步 + 4 分支文件 | **本批的「diy 版步数」= 分支文件内的小节数（9/9/7/10），不是 `steps/` 文件数**（B5 旧公式在此失效） |
| 2 6 个人设全裁 + 能力对账逐条落地 | 4 份风格 → Rules 段（一分支一句，取材回源 `communication_style` 原句）；Carson 一份归 `diy-brainstorm`（禁改面 → 登记 C 阶段补）；`presentation-master` → 见 §九 |
| 3 产物 = 单 YAML 集合 `cis-method.yaml` | 代价：新增 1 个 viewer 标签缺口（§八）；命名避让 = 限**文件名 / 顶层键 / 记录层键**，`deliverable` 内部键逐字保留 |
| 4 检查点四选项保留并接线 | `[a]`→`diy-elicit`、`[p]`→`diy-party-mode`（**本批新造句**）、`[y]` 首次定义 → **B6 是 C4 的先例** |
| 5 方法库 115 条合为目录根 CSV | 表头 6 列保英文、值中文化（**依据 = B4 先例**，非 glossary §9）；**23 个 `category` 中文名三工位逐字冻结** |
| 6 源侧引用的修与不修 | 可达性 20 条不修（照搬）；叙事 2 处 bug 修（见 §2.4） |
| 7 `customize` 面四键整裁 | 四源实值**全为默认空** → 裁撤**零行为变化** |
| 8 `{...}` 令牌白名单 | 保留 `{project-root}`；`{output_folder}`→`{output_dir}`；其余**一律 `TOKEN_UNRESOLVED`** |
| 9 子命令集与回执 | 形 A；`init` 是**唯一写盘**命令；**`--instance` 一律不做** |
| 10 `--previous` 判 **no** | `sessions[]` 只追加、无 ID 集合收缩面 |
| 11 `--final` 语义 | 骨架完备 + 枚举合法 + 34 键齐全 + 同档 + 零 `[假设]`；`exit 0` 唯一放行 |
| 12 登记面三处 | `NEW_SKILLS` / `CONVERTED_INSTANCE` / `CONVERTED_DISCIPLINE`；**禁入** `*_MEMBERS` 与全部 `PENDING_*` |
| **★ 用户裁定 A（2026-09-21）** | `presentation-master` = **(c′) 登记为 B7 批输入**（见 §九） |
| **★ 用户裁定 B（2026-09-21）** | 源侧可达性 = **保真照搬 + `--all` 可查全库**，仅修叙事引用 bug |

**违规码**：复用冻结集 8 个 + **唯一新增码 `TOKEN_UNRESOLVED`**（**不在** `batch3-contract.md` §3 冻结集内，V 实测 `grep -c` = 0 于该契约文件）——**不是「零新增」**。
**产物状态口径**：取 `diy-brainstorm` 先例**三值**（`草稿|进行中|已完成`），是对母本 §8 两值口径的**有据偏离**（已登记）。

## 四、V 独立验证结论（2026-09-21）

- **结论：审计通过，无阻断项。** 能力清点**真实损失 0 条**
- **八项重点验全过**：① 小节数 9/9/7/10（三处独立取数一致）② W1 指路 ↔ W2 键表一致 ③ **34 键 源 ⟷ W2 ⟷ W3 三向逐字相同**（注入项 ∩ 为空）④ **三方类别零漂移**（21 个去重类名逐字比对，零越界零漏点）⑤ 可达集 25/30/15/25 与 census §4.1 逐行对上 ⑥ 两处修复**落了且登记了**（`05-story.md:89`/`:120`，`key_elements` 全库命中**均在否定句内**）⑦ `presentation-master` 逐条在场 ⑧ 违规码恰 9 个 = 8 冻结 + 1 新增
- **三点另核**：(a) `{{project_name}}` 两侧真的按追认口径处置 ✓ (b) `--output-dir` 只读语义**亲手跑过，相容**（带→0、不带→`EMPTY_FIELD` 不静默）(c) 验收 13 项 **12 过 / 1 属主 agent 面**
- **抽验**：三测试独立复跑全 OK；母本逐字**脚本比对**（非目检）
- **V 发现 6 条**（1 中 5 低）→ **3 条就地处置、3 条留档**（§七）

## 五、主 agent 集成验证（2026-09-21）

| # | 收口链项 | 命令 / 口径 | 结果 |
|---|---|---|---|
| 1 | ① 登记 | `test_suite_texts.py` 三处 | **11 tests OK**（登记前 2 红）——连带证明 §1/§2/§3/§4/§5/§6 六节锚串**逐字携带、零回改** |
| 2 | ② sync | `bash diy-coder/sync.sh` | **41 个 skill** → `.claude/skills`（40 + 本批 1）；冒烟通过 |
| 3 | ③ 全量测试 | `python -m unittest discover -s diy-coder/tests` | **985 tests OK**（B5 基线 949 + 本批 30 + 其他 +6） |
| 4 | ④ 渲染自证 | `cis_method.py init`（tempdir）→ `viewer.py` | `init` rc 0（`CM-001`）；渲染 **rc 0 · rendered 1 doc**（`cis-method.html` + `index.html`）；标签缺口见 §八 |
| 5 | ⑤ 本报告 | `render_fidelity.py`（复用 B5 渲染器） | `b6-fidelity.{md,html}` |
| 6 | ⑥ 计划节 | `迁移计划.md` **§十九**（§十八 已被 C·2 线占用） | 见该节 |

## 六、验收 13 项对照（迁移计划 §二）

| # | 验收项 | 责任 | 证据 |
|---|---|---|---|
| 1 | 薄主文件 + steps/ 厚子文件 | W1/W2 | `SKILL.md` **81 行**（≤90 硬阈值，余量 9 行，**未触发裁撤序**）；`steps/` 5 文件 |
| 2 | 产物 schema / 稳定 ID | W3（`CM-###`） | schema 段 + `check` 用例（⑬ `DUPLICATE_ID`） |
| 3 | 前置门禁（零产出退出） | W1（`01-route.md` 门禁拍） | 源四份 `required: false` / 零上游依赖 → 门禁 = **议题非空**（**改写已登记**） |
| 4 | ID 链接入 | W3 | 四条实证：唯一性 `DUPLICATE_ID`（⑬）/ 顺序性 `init` 递增（③）/ **不进 `help.py` CHAIN、不被任何门禁引用**（anytime 咨询产物）/ `revisions[].change` 引用纪律句落规则段 |
| 5 | 注册 | 主 agent | sync 输出 **41 技能** |
| 6 | viewer 渲染 | W1 登记缺口 + 收口链④ 执行 | §八 |
| 7 | 冒烟 TC（≥5） | W3 | **30 用例**（十三类全覆盖） |
| 8 | 登记元数据 | W1 | frontmatter 六字段（`precededBy`/`followedBy` **四源逐源真为空**） |
| 9 | 读取成本纪律 | W1+W2 | 母本 §4 逐字（脚本比对） |
| 10 | 双源输入声明 | W1 | **判「非交汇点」**（不读 `prd.yaml` / `sprint.yaml` / WDS 产物） |
| 11 | 渲染静默 | W1 | 规则段照母本 §5 逐字（渲染是静默旁路） |
| 12 | diyc 接线 a–e | W1 | a 委托 `diyc.py resolve`；b 终门 = `check --final`；c 判 **no**；d 母本 §3 逐字；e 写权边界 = 只写 `cis-method.yaml` |
| 13 | 副作用纪律 | W1–W3 自证 + V 抽验 | 唯一写面 = `{output_dir}/cis-method.yaml`（自动执行档）+ 静默渲染；`[a]`/`[p]` 调零写面技能；**无确认档、无 defer 产生面** |

## 七、非阻断观察清单（欠账，C 阶段或后续批处置）

**0. 开工前复扫（机制项，重要）**：首轮自检的**机制教训**——「逐条处置 ≠ 逐处改透」，扫描台账记的是 finding 不是落点。首轮收尾复扫抓到 3 处漏改后，**开工前按旧值字符串再扫一遍又抓到 3 处**：
| 残留 | 位置 | 处置 |
|---|---|---|
| 子命令名 `new`（应 `init`） | 裁定 9 | **已改** |
| 「本批所需码全部在冻结集内，零新增」 | §1 必读输入 | **已改**（→ 冻结集复用 + 唯一新增 `TOKEN_UNRESOLVED`） |
| 「diy 侧 22 个 `outputs:`」 | §0 三点 | **已改**（→ 23 个 / 例外 3 处） |

→ **此道已写入任务书 §11 ⑤，此后强制。**

**V 发现 6 条**：

| # | 级 | 归属 | 内容 | 处置 |
|---|---|---|---|---|
| 1 | 中 | 主 agent | `迁移计划.md` §十八 **已被 C·2 线占用**（施工期间写入，开工前复核时为空） | **已处置**：本批改走 **§十九**，不覆盖 |
| 2 | 低 | 任务书 | §2.3「132（裁后基数）」自相矛盾 | **已订正**：`132` = 源占位符数，**`122`** = 裁后合法键数 |
| 3 | 低 | W2 | 创新/问题/设计三份**末步缺独立「落盘」行**（`落上述 N 键` 无先行词；键数经源侧核实**均正确**） | **已返工修复**（三处各补一行；叙事第 10 步无键可落，**正确未动**） |
| 4 | 低 | W1 | `diy-prfaq` 路由句不在 `interface-map.md` §3 的边界八对内 | **留档**：属路由建议句（非边界声明），C 阶段统一裁 |
| 5 | 低 | W3 | `--all` 与 `--random` 设为**互斥**（任务书未声明） | **留档**：V 判合理（`--random` 语义 = 从默认集抽） |
| 6 | 低 | W2/W3 | 只读子命令省 `--output-dir` 报 `EMPTY_FIELD`（措辞可两读） | **留档**：行为相容非缺陷；与 B5 欠账 #3「`--output-dir` 必填面三家不一致」**同源**，宜一次口径裁定 |

**另两条待办**：
- **任务书 §2.3 注入项枚举漏计 `project_name`**（W2 施工期发现，主 agent 实测确认：仅 `bmad-cis-design-thinking/template.md:1` 命中，其余三源零命中）→ **已订正为五个**，两侧按「保留在合法键表、不入 34 键必填表」处置
- **`machine-zh-glossary.md` §9 规则 5 的字面张力**（「技能自带数据表的值不改」vs 本批值中文化）→ 真依据是 **B4 先例**；**建议 C 阶段给规则 5 加一条例外注**，否则后续批次会反复遇到同一冲突

## 八、viewer 标签缺口清单（**C 阶段输入**）

`cis-method.yaml` 为**新产物类型**。V 与主 agent 两处实测：

- `grep -n "cis-method" viewer.py` → **零命中**；`DOC_LABELS` 经 C·2 线扩展后已有 **31 条**，但**其普查面是「已建 40 技能」，本技能为第 41 个** → 仍缺
- 渲染实况：`rc 0 · rendered 1 doc`，`cis-method.html` 页面**标题回落为裸类型名 `cis-method`**（走通用降级渲染，键值+列表卡片）
- **归属**：C2 面（缺口 2 通用降级渲染）已由 C·2 线落地通用路径，**本项只剩「补一条 `DOC_LABELS["cis-method"]` 中文标签 + `DOC_KEY_LABELS` 键标签」的收尾**，登记为 C 阶段输入

## 九、`presentation-master` 能力承接登记（**用户裁定 (c′) → B7 批输入**）

**定性**：6 个 agent 里唯一的**非空壳**——其 `SKILL.md` 与其余五份**逐字同构**（72 行空壳），真实内容全在 `customize.toml`（71 行，其余五份 36–58 行）。7 条菜单**全部指向 prompt、不绑任何技能**，故方案 B 的否决理由「人设无独有能力——菜单指向的技能本来就在迁移计划内」**在这一条上不成立**。

**裁定 (c′) 的落点（本批只「不丢」，不自造步骤序列、不改 B7 任何文件）**：
1. **本报告**（本节）载全文——**8 条原则 + 7 条配方**，未来可从本文件逐字取回
2. **`迁移计划.md` §十九** 记一条 **B7 前置项**：交 `diy-wds-assets`（源 `wds-6-asset-generation`）裁定归位

**为什么不是 `diy-design`**（2026-09-21 实测否决，非推断）：三条硬约束——① 输入契约硬门 `prd.yaml: 已定稿` + `design.py detect` 探 `has_frontend`；② 产物契约 `design.yaml` + `prototypes/<页 id>.html` + 框架实现落 `src`；③ 流水线位置在 `prd → design → dev` 中游。且 C·3 已排定它吸收 WDS 工作流 + bmad-ux + 场景桥。
**(c′) 的容器依据**：`wds-6-asset-generation` 同为「读规格 → 选风格 → 精炼 prompt → 生成 → 评审」范式，自带 `data/styles/` 库（design-styles 6 + content-styles 10），**确有 `workflow-videos.md`**（对得上 `EX` 配方）但**无 slides / pitch 活动**——故 B7 仍可能以「产物域不匹配」再裁；**那一裁由容器在场时作出**。

### 9.1 八条视觉传达原则（源 `principles`，逐字）

1. Know your audience — pitch decks, YouTube thumbnails, and conference talks are three different crafts.（懂受众：路演 / 缩略图 / 演讲是三种手艺）
2. Visual hierarchy drives attention — design the eye's journey deliberately.（视觉层级设计眼睛的旅程）
3. Clarity over cleverness, unless cleverness serves the message.（清晰优先于机巧，除非机巧服务于讯息）
4. Every frame needs a job — inform, persuade, transition, or cut it.（每帧都要有职责，否则剪掉）
5. Test the 3-second rule — can they grasp the core idea that fast?（3 秒规则）
6. White space builds focus — cramming kills comprehension.（留白构建焦点，堆砌扼杀理解）
7. Consistency signals professionalism — establish and maintain a visual language.（一致性即专业）
8. Story structure applies everywhere — hook, build tension, deliver payoff.（故事结构普适：钩子→张力→兑付）

### 9.2 七条 prompt 配方（源 `menu`，逐字）

| code | 描述 | prompt 全文 |
|---|---|---|
| `SD` | 多页幻灯片（专业版式 + 视觉层级） | Design a multi-slide presentation using Excalidraw frame-based layout. Apply audience-appropriate visual hierarchy, enforce the 3-second rule on every frame, and use consistent visual language throughout. |
| `EX` | 视频解说版式（视觉脚本 + 留人钩子） | Design a YouTube explainer layout. Produce a visual script with engagement hooks at 0s, 3s, and every 15-30s; specify on-screen visuals per beat; apply bold, casual typographic style appropriate to the platform. |
| `PD` | 投资人路演（数据可视化 + 叙事弧） | Craft an investor pitch presentation. Build a narrative arc (problem → solution → traction → ask), design data visualizations that make the numbers pop, and enforce a polished, professional visual language. |
| `CT` | 大会演讲 / 工作坊（演讲者备注） | Build a conference talk or workshop presentation. Include speaker notes per slide, design for a live audience (large type, minimal text), and structure a hook-build-payoff narrative. |
| `IN` | 信息可视化（视觉叙事） | Design a creative information visualization. Choose the chart/diagram type that lets the data tell the story, layer visual storytelling on top of the data, and cut every pixel that doesn't inform-persuade-or-transition. |
| `VM` | 概念插画（鲁布·戈德堡 / 旅程地图 / 创意流程） | Create a conceptual illustration — Rube Goldberg machine, journey map, or creative-process diagram. Use visual metaphor to explain the concept; prioritize memorability over comprehensiveness. |
| `CV` | 单张概念图 | Generate a single expressive image (concept visual) that explains the idea creatively and memorably. Apply visual metaphor, test the 3-second comprehension rule, and make the image the explanation — not a decoration on top of one. |

**人物设定参考**：Nancy Duarte（演示架构）+ Saul Bass（电影化平面）+ Excalidraw 帧即场景纪律。
**`communication_style` 原句**（供 B7 参考）："Energetic creative director in the editing room with you — sarcastic wit, dramatic reveals, visual metaphors, celebrates bold choices and roasts bad design with humor."

## 十、审阅指引（B6 为**非强制人工审**）

**审阅面**：本报告 + `v-audit.md`（终审计证据）+ `v-capability-inventory.md`（能力清点）。

**异常项才需看**：
1. §七-0 的**开工前复扫**机制——它证明「自检闭合」不等于「改透」，且已固化为 §11 ⑤
2. §八 的标签缺口收尾（只差两条标签的补录，C 阶段小活）
3. §九 的 **(c′) 承接**——B7 编制时须回看本节；7 条配方在 B7 是否真能落进 `diy-wds-assets`，届时信息更全
4. §七 的第 6 条与 B5 欠账 #3 **同源**（`--output-dir` 必填面），若要收敛需一次跨批口径裁定

**下一步**：**B7**（wds 8 技能，最大批，是 C·3 里 `diy-design`/`diy-dev` 升级的前置）或 C 阶段余项（§五 C 1–7 / 9 / 10）。
