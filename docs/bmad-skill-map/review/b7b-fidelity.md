# B7b 批保真度报告 —— wds 设计段与后段（5 技能）

- 批次：BMAD 迁移 阶段 B 第 7 批**后半**（B7 已按用户 2026-09-21 裁定拆为 **B7a / B7b**）｜ 完成日期：2026-09-22 ｜ 编制：主 agent
- 任务书：`diy-coder/.analysis/2026-09-21-migration-b7/taskbook-b7b.md`（自检后定稿；**收口期订正 1 处**，见 §三）
- 开工前自检：dogfood 扫描 **72 条**（阻断 4 / 高 20 / 中 35 / 低 12 → 采纳 **58** / 驳回 10）；片 3 核引 **83 条 / 9 条不实**；收尾按旧值字符串全库复扫**真残留 0**
- 交付：`diy-wds-system` / `diy-wds-assets` / `diy-wds-evolution` / `diy-analyze` / `diy-reverse` —— 套件从 44 → **49 技能**
- 本批四点特殊：① **WDS 线设计段落地**（B7a 的三段短链自此接上设计段与后段，成为一条可跑到底的六节点线）；② **两个独立入口技能**（`diy-analyze` / `diy-reverse`，`line: any`，不进任何链）；③ **本批零外部服务**（裁定 6 —— 无 Figma 通道、无生成式 API，唯一出口是提示词导出）；④ **`diy-wds-evolution` 是三线唯一有「目标项目代码写面」的技能**（`[I]` 相），与其余四技能的「只写自己产物」不同型（见 §七-1）

## 一、批次结果总览

| 技能 | 源 | 源规模 | 源步 | diy 交付 | 用例 |
| --- | --- | ---: | --- | --- | ---: |
| `diy-wds-system` | `wds-7-design-system` + `wds-4` 的 `[M]` 活动 | 24 文件 / 7,855 行（排 html 7,492）+ [M] 4 / 434 | 3 + 3 | `SKILL.md` **89 行** · `steps/` **5 文件 23 小节** · 引擎 680 行 | 61 |
| `diy-wds-assets` | `wds-6-asset-generation` | 91 / 13,217 | 8 活动 W/P/U/I/M/V/C/E | **89 行** · `steps/` **9 文件 48 小节** · 引擎 630 行 | 42 |
| `diy-wds-evolution` | `wds-8-product-evolution` | 22 / 5,099 | 6 活动 A/S/D/I/T/P | **88 行** · `steps/` **6 文件 27 小节** · 引擎 619 行 | 44 |
| `diy-analyze` | `wds-5` 的 `[A]` 活动 | 5 / 813 | 4 | **78 行** · `steps/` **4 文件 11 小节** · 引擎 453 行 | 26 |
| `diy-reverse` | `wds-5` 的 `[R]` 活动 | 5 / 685 | 4 | **83 行** · `steps/` **4 文件 11 小节** · 引擎 460 行 | 33 |

**合计**：5 技能 · 源 **151 文件 / 28,103 行** → diy **28 个 `steps/` 文件 · 120 小节 · 5 引擎 2,842 行 · 206 用例**（全量套件 **1322 用例全绿**）。

**批级口径**：V 独立验证核出 **25 条**（1 阻断 / 2 高 / 9 中 / 13 低）→ **阻断与高项全部返工修复**（§四），中低项登记留档（§七）· **能力损失 3 处**（全部显式登记，见 §二）· **源侧处置四类口径**（裁定 5）· **零外部服务**（裁定 6）。

## 二、逐技能保真度

### 2.1 `diy-wds-system`（设计系统段：组件库 + 令牌命名空间）

- **5 个步骤文件 / 23 小节**：`01-create`(C,含重复检测) · `02-import`(I) · `03-view`(V+B 合一) · `04-edit`(E,已去 Figma) · `05-finish`(收尾 + [M] 用法一致性校验)
- **产物** `wds-design-system.yaml`：`components[]`（ID `[prefix]-[NNN]`，**26 前缀 / 6 分类**）· `tokens`（**派生自 `design.yaml.tokens`**，引用不复述）· `categories` · `prefixes`；另产 `wds-design-system-catalog.html`
- **裁定 4（V+B 合一）**：源 `workflow-view.md`(68) + `workflow-browse.md`(87) 都产 localhost 应用，功能高度重叠 → 合一
- **裁定 5（token 单一源）**：`tokens` 段从 `design.yaml.tokens` **派生**；`design.yaml` 不存在时降级为「独立定义 token」并标注
- **裁定 6 射程延及本技能**：源 `wds-7/workflow-edit.md` 是**纯 Figma 活动** → 裁 Figma 通道，`04-edit` 降级为**本地组件文件编辑**
- **`COMPLEXITY-ROUTER`(842 行) 归本技能**（自检裁定）：`data/complexity-router.md` 64 行五节
- **验收 #4 的证据面**：本技能 `line` 收口期从 `any` 裁决回 `wds`（见 §三）

### 2.2 `diy-wds-assets`（资产工厂：8 活动 + 第 9 活动）

- **9 个步骤文件 / 48 小节**：`01-wireframes` · `02-page-designs` · `03-ui-elements` · `04-icons` · `05-images` · `06-motion` · `07-content` · `08-presentation`（**第 9 活动**）· `09-finish`
- **产物** `wds-assets.yaml`：`activities[]`（每活动一组 `items[]`，ID `AS-<nn>.<m>`）· `prompts[]`（提示词导出）· `presentation[]`（第 9 活动）；HTML 优先，落 `{output_dir}/assets/<活动>/`
- **★ 第 9 活动（裁定 7，**本批对 B6 §九的正式交付**）**：B6 移交 → B7a 登记 → **本批落地**。**8 原则 + 7 配方逐条在场**，7 段 prompt 与 `b6-fidelity.md` §九**逐字符相同**（V2 独立核对）；新建第三轴 `data/presentation-formats/`（7 配方 + index）
- **裁定 6（零外部服务）**：源 8 活动的生成调用全部裁 → **唯一通道 = 导出提示词**（用户在外生成后回填）；V2 独立复测：`requests/urllib/socket/subprocess` **零命中**
- **源侧真能力 11 项**（census-4 §8.1）：**承接 10 / 裁 1**（A10 的 `OBJECT ID` 五项校验随 `[E]` 整块裁，符合普查自带的「条件不成立」判据）
- **V 高项 V2-01 已返工**：`pages[].id` 必读键**零机械核**（实测非法 ID 与删上游均 `rc=0`）→ 补 `PAGE_ID_RE` + `page_ids()` 抽取 + `check` 沿用 `gate_upstream`，**复用冻结违规码**（`SET_MISMATCH` / `UNKNOWN_ID` / `MISSING_FILE` / `STATUS_MISMATCH`），补 2 用例

### 2.3 `diy-wds-evolution`（棕地增量：Kaizen 迭代流水线）

- **6 个步骤文件 / 27 小节**：`01-analyze` · `02-scope` · `03-design` · `04-implement` · `05-test` · `06-finish`
- **产物** `wds-evolution.yaml`：`rounds[]`（每轮 A/S/D/I/T/P 六相）· `kaizen_priority`（Impact×Effort×Learning），ID `EV-<nn>`
- **裁定 9（入口技能）**：门禁 = 既有产物**任一**在场（`design.yaml` / `sprint.yaml` / `wds-*.yaml`），**不硬性要求 `已定稿`**
- **Kaizen 差异化内涵全保**：`data/kaizen-principles.md` 118 行六节（Kaizen vs Kaikaku / 四条原则 / 何时暂停三情形）+ `data/priority-framework.md` 69 行
- **★ 写面特殊性**：`[I]` 相**写目标项目代码**（源侧语义），另有确认档与可选 `gh pr create` —— 三线唯一，与验收 #13 的字面措辞不符，**判「书错物对」**（见 §六 #13 与 §七-1）
- **V 高项 V3-01 已返工**：`--output-dir` 缺省是 **CWD 相对**、不认 `--project-root`（实测**静默读到另一个项目的产物且 rc=0**）→ 修为 `os.path.join(args.project_root, "diy-output")`，与其余四技能逐字一致，补 1 用例

### 2.4 `diy-analyze`（独立入口：代码库分析）

- **4 个步骤文件 / 11 小节**：`01-define` · `02-scan` · `03-map` · `04-document`
- **产物** `analysis.yaml`：`question` · `architecture`（含 Mermaid 字符串）· `components[]` · `data_flow[]` · `dependencies[]` · `risks[]` · `recommendations[]`，ID `AN-<nn>`
- **门禁 = 代码库可读**（入口技能，无上游 diy 产物）；**只记既有事实、不做技术决策**
- **与用户级 `arch-analyze` 的分工**（用户 2026-09-21 拍板）：本技能管「就一个问题分析既有代码库」、产 `diy-output/analysis.yaml`；`arch-analyze` 管「任意项目代码库体检」、产 `docs/arch/` —— **本批只落本侧边界句**，对方不改（属用户私有技能）
- **源能力（census-5 §7.1）**：七类问题分类表 / 四档范围 / 时间盒 / 三类产出**全部承接**并 YAML 化

### 2.5 `diy-reverse`（独立入口：外部目标逆向）

- **4 个步骤文件 / 11 小节**：`01-define` · `02-explore` · `03-specs` · `04-extract-tokens`
- **产物**：**逆向填充既有 `design.yaml`**（`tokens` 标提取来源 + 页规格 `P-<n>`）+ 逐页结构稿
- **★ 裁定 13（写权边界）**：**只在 `design.yaml` 不存在时初始生成**；已存在 → **拒绝覆盖**（`OVERWRITE_REFUSED`）走 `revisions` 建议 + 路由 `diy-design`。**必须满足既有 `design.yaml` schema 与 `design.py validate` 三道**（自检阻断项：首稿自造 `SC-<nn>.P<n>` 形态被纠正）
- **三条纪律承接**（census-5 E8）：先观察后提取 / 尊重知识产权 / **抓规则不抄像素**
- **与 `diy-analyze` 同族**：共享骨架 11 条逐字串在八份文件全覆盖（V2 实测逐字行重合 **144/329 = 44%**，与裁定 1「省 40–50% 重复」同量级）

## 三、批级裁定摘要（20 条 + 收口期裁决 1 条）

任务书 §0.2 载 **20 条前置裁定**，其中 **6 项经用户 2026-09-21 拍板**（拆 B7a/B7b · 签核分支全留 · `diy-analyze` 建且产物进 `diy-output/` · `presentation-master` 完整建第 9 活动 · 不接外部服务 · 二进制资产落位）。要点：

| 组 | 裁定 | 内容 |
| --- | --- | --- |
| 结构 | 1 · 4 · 11 | 步骤文件构成 §2.4 为准（自检订正 3 处）· V+B 合一 · 跨技能读契约 16 行 |
| 内容 | 5 · 7 · 8 · 12 · 13 | token 派生自 `design.yaml` · 第 9 活动完整建 · 门禁取链上邻居 · 二进制资产落位 · `diy-reverse` 写权边界 |
| 纪律 | 6 · 16 · 17 · 19 | **零外部服务** · 不可机械的部分必须写明 · 设计系统默认开启 · `--previous` 判 no |
| 元数据 | 3 | frontmatter 六字段逐格取数（自检订正 4 处） |
| 批务 | 2 · 9 · 10 · 14 · 15 · 18 · 20 | 合并口径 · 入口技能 · 文件所有权 · … |

**★ 收口期裁决 1 条（推翻任务书自检的「订正 4」）**：

**`diy-wds-system` 的 `line` = `wds`（非 `any`）**。任务书自检的「订正 4」依据计划 §四 `:232`「设计系统…**主线与 WDS 线通用**」把 `line` 改判为 `any` —— **经查该句主语是「设计系统能力」（默认开启的射程，说的是这一步两条线都会走到），不是技能线归属**。四条同向证据：

1. 计划 §四 `:230` 把本技能列在「**其余 WDS 技能**」标题下；
2. **本任务书 §9 #10** 明写「`diy-wds-system` / `diy-wds-assets` / `diy-wds-evolution` **属 WDS 线**」（同一份任务书内部，订正 4 与 #10 自相矛盾）；
3. §10 ⑦ 要求把三节点接入 `wds.chain`；
4. C·1 守卫 `tests/test_help_registry.py:93-101` 断言**链节点 `frontmatter.line` == 线名**。

**四条同向、唯「订正 4」反向**。V1 以**真守卫方法**独立复现了冲突（追加三节点 → `AssertionError: 'any' != 'wds'`；现登记表因未被 ⑦ 触碰而暂绿）。**处置**：`SKILL.md` 回改 `line: wds` + 正文 `:15` 的依据句一并改写（去掉「（`line: any`）」，保留「本产物是两线共用的设计系统单一源」的事实表述）+ 任务书订正 4 留痕推翻。**性质：收口期修复，非偏离**。

## 四、V 独立验证结论（2026-09-22）

**编制**：3 个互不可见的独立验证 agent 并行作业（结构面 / 内容面 / 合规面），口径统一为「**不采信施工方自述**」——每条结论自带亲手取数（`grep -c` / 引擎实跑 / 真守卫复现 / 常量转储），夹具一律 `tempfile`，探针落系统临时目录，未读写仓库真实 `diy-output/`。

| 面 | 报告 | 总判定 | 阻断 | 高 | 中 | 低 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| V1 结构面 | `v-b7b-struct.md` | 有条件通过 | **1** | 0 | 1 | 2 |
| V2 内容面 | `v-b7b-content.md` | 有条件通过 | 0 | **1** | 4 | 4 |
| V3 合规面 | `v-b7b-compliance.md` | 有条件通过 | 0 | **1** | 4 | 7 |
| **合计** | — | — | **1** | **2** | **9** | **13** |

**验证覆盖面（V 亲手实跑）**：小节数逐文件校准 120 / 28 文件 · 步骤名双向闭合零 MISS · frontmatter **30 格**全可溯源（零「待取数」）· 跨技能 schema 逐键对账 · 第 9 活动 8 原则 + 7 配方**逐字符相同** · 裁撤台账 **24 行**逐条回源（零无依据、零「声明裁了还在」）· 能力清点 **25 条**（承接 21 / 部分 1 / 裁 3，**未复现 0**）· 引擎契约 **119 条断言**零失败 · 门禁 **18 种情形**实跑 · 全库红线扫描 · ID 跳号/重复夹具 · md5 写面核 · 既有测试 **203 → 206** 全绿。

**三处返工（阻断 + 高，全部修复）**：

| # | 项 | 根因 | 修复 |
| --- | --- | --- | --- |
| **V1-01**（阻断） | `line: any` ↔ WDS 链登记互斥 | 任务书自检「订正 4」误读 `:232` | `SKILL.md` 回改 `wds` + 正文改写 + 任务书订正（§三） |
| **V2-01**（高） | `diy-wds-assets` 的 `pages[].id` 零机械核（非法 ID / 删上游均 `rc=0`） | `check` 全程不读上游 | 补 `PAGE_ID_RE` + `page_ids()` + `check` 沿用 `gate_upstream`；**复用冻结码零新增**；补 2 用例 |
| **V3-01**（高） | `diy-wds-evolution` 的 `--output-dir` 缺省为 CWD 相对 → **静默读到另一项目的产物且 rc=0** | 缺省未拼 `project_root` | 修为 `os.path.join(args.project_root, "diy-output")`，与其余四技能逐字一致；补 1 用例 |

**中低项**：22 条全部登记留档（§七），**不返工**（承 B7a 先例：只对高及以上返工）。其中 **3 条判「书错物对」**（V3-05/06/07）—— 指向任务书与 research 的陈旧数字与措辞，**交付以实物为准**。

## 五、主 agent 集成验证（收口链 ①~⑦）

| 步 | 内容 | 结果 |
| --- | --- | --- |
| ① | `test_suite_texts.py` 三处登记（**+5 名**） | ✅ 清掉本批开工以来的 2 条预期红灯（`PENDING_PRECISE` / `PENDING_READ_DISCIPLINE` 台账未同步） |
| ② | `sync.sh`（`install.py` 兼容壳） | ✅ **49 个 skill** 已安装 + 四项冒烟通过 |
| ③ | 全量测试 | ✅ **1322 passed / 0 failed**（170 subtests，258.91s）—— 含 V 返工新增的 3 条用例 |
| ④ | 五产物渲染自证 + 标签缺口 | ✅ `init rc` 全 0 · `viewer rc` 全 0 · `rendered` **2/2/2/1/1**（前三个含夹具上游）；渲染静默成立（`_is_interactive()=False`，浏览器未开、零阻塞）；**门禁独立复现 6 条**（上游缺失 → 连 `diy-output` 目录都不建）；缺口 **18 条** → §八 |
| ⑤ | 本报告 | ✅ |
| ⑥ | `迁移计划.md` **§二十三** | ✅ |
| ⑦ | `diy-help/registry.yaml` WDS 链补登记 | ✅ `wds.chain` 3 → **6 节点**（brief → trigger → scenarios → **system → assets → evolution**）；`exec_note` 改写为链尾说明并**订正原先把两个独立入口列为「WDS 线下游」的错**；`notes` 补三条可选节点文案；`test_help_registry.py` **11 项 / 60 subtests 全绿** |

**收口期修复留痕（2 处，值得单记）**：

1. **`diy-wds-system` 的 `line`**（§三）：V1 以真守卫复现冲突 → 主 agent 裁决 + 任务书订正。**机制意义**：这是**第二次**由 C·1 守卫体系提前暴露「取数误判」（首次是 B7a 的 `precededBy` 悬空名）——守卫正在把「值错」从人工审转为机械拦截。
2. **`test_wds_system.py:670` 的连带红灯**：改 `line` 后该用例（硬编码断言 `line: any`）转红，由返工 agent 如实上报（它守住了「不碰面外文件」的纪律）→ 主 agent 改断言为 `line: wds`。**教训**：**改 frontmatter 值必须同步全库扫该值的断言**——这是「按旧值字符串全库复扫」纪律的**新命中场景**（前三批的复扫针对文档，本次针对**测试断言**）。

## 六、验收 13 项对照（迁移计划 §二）

| # | 验收项 | 结果 | 证据 |
| --- | --- | --- | --- |
| 1 | 薄主文件 + `steps/` 厚子文件 | ✅ | SKILL.md **89/89/88/78/83** 全 ≤90 硬阈值；steps **5/9/6/4/4** 文件；小节 **23/48/27/11/11** 合计 120（V1 逐文件校准） |
| 2 | 产物 schema（`{output_dir}/`、稳定 ID 前缀） | ✅ | 五种 ID 形态（`[prefix]-[NNN]` 26 前缀 / `AS-<nn>.<m>` / `EV-<nn>` / `AN-<nn>` / `P-<n>`）；各 `check` 用例在场 |
| 3 | 前置门禁（零产出退出 + 路由） | ✅ | **18 种情形**实跑；上游缺失四种情形**全部零产出**（连输出目录都不建） |
| 4 | ID 链接入 | ✅ | 唯一性 + 顺序性实跑；`analyze`/`reverse` **不进任何线**（`line: any`）；三个 `diy-wds-*` **进 WDS 链**（收口链 ⑦） |
| 5 | 注册 | ✅ | `sync.sh` → **49 技能**；`registry.yaml` 六节点登记 |
| 6 | viewer 渲染 | ✅（缺口登记） | 五产物渲染 rc 全 0；缺口 18 条落 §八（C 阶段输入） |
| 7 | 冒烟 TC（≥5） | ✅ | 各技能 **61 / 42 / 44 / 26 / 33**，远超下限；全量 1322 绿 |
| 8 | 登记元数据（裁定 3） | ✅ | frontmatter **30 格**逐格取数证据，零「待取数」；`_req_check.txt` 无本批行 → 取数改指 `module-wds.json`（V1 独立核实属实） |
| 9 | 读取成本纪律（母本 §4 逐字） | ✅ | V1 逐技能核锚串在场 |
| 10 | 双源输入声明 | ✅ | 三个 `diy-wds-*` 属 WDS 线、两个入口技能**逐技能明写**（`diy-reverse` 的否定式归属句 V1 判缺 → V1-02，**中项，登记留档**） |
| 11 | 渲染静默（母本 §5 逐字） | ✅ | 规则段在场 + 渲染自证实测静默 |
| 12 | diyc 接线（a~e） | ✅ | a 委托 `diyc.py resolve` · b 终门走自带引擎 · c `--previous` 判 no · d 语言绑定逐字 · e 写权边界（`diy-reverse` 的 `design.yaml` 唯一跨产物写面，且只初始生成） |
| 13 | 副作用纪律 | ⚠️ **书错物对** | **本批零外部服务**成立（V2 独立扫 `requests/urllib/socket/subprocess` 零命中）；**唯一写面**在 evolution 上为假 —— 其 `[I]` 相写目标项目代码、有确认档、可选 `gh pr create`，三处均有源侧依据且被 §5 W3 卡默许 → **措辞须改，交付合理**（§七-1） |

**13 项中 12 项 ✅、1 项 ⚠️（书错物对，交付无缺）**。

## 七、非阻断观察清单（欠账，C 阶段或后续批处置）

**0. 写面模型（★ 建议单列一句）**：`diy-wds-evolution` 的 `[I]` 相**写目标项目代码**，超出「跨技能共享面不共写」的表述范围。**C 阶段建立写面模型时勿按「本批只写产物」假设**（V3 §未决 5）。

**1. 待返工/待登记（中项 9 条）**

- **V1-02**（中）：`diy-reverse` 缺 #10 要求的**否定式归属句**（`diy-analyze` 有三处、它零处）；机器字段 `line: any` 正确。修法：规则 10 边界段补一句（一行）。
- **V2-02**（中）：`diy-wds-assets/steps/09-finish.md:23` 称引擎回执给 `coverage`，实测无此键。
- **V2-03**（中）：§2.3.1 的可选读 `brief.visual.visual_direction` 在 `diy-wds-system` **零落点**。
- **V2-04**（中）：裁定 17 的三套枚举归一表无落点（`design_system_enabled` 7 引用 / 0 生产者）。
- **V2-05**（中）：验收 #13 的「唯一写面」与 evolution 实测不符（同 §六 #13）。
- **V3-02**（中）：`diy-wds-assets` 回执面四处偏离套件契约（键名 `message` 应为 `msg`；`where` 绝对 + 反斜杠应为相对 + 正斜杠；`project_root` 被 `resolve()` 应为 as-given；`--json` 22 行多行应为单行）。**回执是机器读面**，与四技能不同源会漏判。
- **V3-03**（中）：`diy-wds-assets` 四个**只读**子命令强制 `--output-dir`（rc=2），§2.2 只要求写盘子命令必填；根因是缺 `{project_root}/diy-output` 兜底。
- **V3-04**（中）：`diy-wds-assets` 的 `AS-<nn>.<m>` 无**活动内递增**机械核（跳号实跑 rc=0），与 `SKILL.md:78` 规则 5 与验收 #4 的「顺序性」不符。
- **V3-05**（中）：验收 #13 措辞面（同 §六 #13）。

**2. 留档（低项 13 条）**：V1-03（任务书「25 前缀」实为 26，交付对、**已在任务书与本报告 §三 侧以实物为准**）· V1-04（两技能声明 `outputs: design.yaml`，判非缺陷但**提示：收口期若新增反查须按「一产物多写者」设计**）· V3-06/07（同型「书错物对」：前缀计数与 `diy-reverse` 的 ID 形态表）· V3-08（evolution 门禁收窄未在 §2.3.1 登记）· V3-09（两个入口技能缺红线否定句，实际风险≈0）· V3-10（红线守卫只抓 `--previous` 形态，**守卫声明应限定**）· V3-11（registry 未接入，**已由 ⑦ 闭环**）· V3-12（第 5 子命令未登记为对 §2.2 的偏离，三处均只读零写盘）· V2-06…V2-09（回执形态 / 任务书 §2.3 与裁定 13 自相矛盾 / 令牌一致性无在场核 / §2.3.1 表漏 assets 对 brief·trigger 的读面）。

**3. 本批已闭环的前批欠账**：B7a 移交的 `presentation-master` 归位（8 原则 + 7 配方**逐字符相同**落地）· B7a 的「WDS 链 5 节点登记 + `lines.wds.exec`」（**⑦ 闭环，实际落 6 节点**）。

**4. 移交 C 阶段**：`line: wds` + WDS 线自有 `phase` 值的 C1 并表 · 五个新产物标签 + `presentation-formats` 渲染路径 + `assets/<活动>/` 子目录（**⑧ 见 §八**）· token 派生关系对 `design.py audit` 的影响 · WDS 线**机械写回命令面**（本批只出契约不实现）· `diy-design`/`diy-dev` 的 WDS 模式（C·3）。

## 八、viewer 标签缺口清单（**C 阶段输入**）

收口链 ④ 实测（`b7b-render-check.md`，**18 条**）：

| 类 | 条数 | 内容 |
| --- | ---: | --- |
| `DOC_LABELS` 缺 | **4** | 5 个新产物中 `design` **已存在**（`viewer.py:331`），实缺 4 类 |
| `ENUM_KEYS` 缺 | **12 键** + 一批值级 | `design_system_mode` / `complexity` / `category` 等键整体缺；值级缺 `在用` / `已评审` / `已交付`、`analysis` 五值**全缺** |
| **渲染器级** | **2** | ① `data/presentation-formats/` **无渲染路径**；② `assets/<活动>/` **子目录静默丢弃**（`viewer.py` 只扫顶层 `*.yaml`） |
| **本批新增** | **2** | ① `KEY_LABELS` 缺 **59 键**；② `code` 同键异义被误标「违规码」 |

**渲染自证结果**：五产物 `init rc` 全 0、`viewer rc` 全 0、`rendered` **2/2/2/1/1** —— **渲染本身无缺陷**，缺口全在**标签映射**与**目录扫描面**。

## 九、审阅指引（B7b 为**非强制人工审**）

按迁移计划 §五 人工审核点设计：**B2–B7 只需出报告**（剩余风险降为单技能内容质量，抽样 + 自动校验比全审划算）。**本批非强制人工审**，建议抽查三处：

1. **§三 的收口期裁决**（`line: wds`）—— 该裁决推翻任务书自检的一条订正，请确认论证链（四条同向证据）成立；
2. **§二 2.2 的第 9 活动**（B6 §九的正式交付）—— 8 原则 + 7 配方是否确为「完整落地」；
3. **§七-0 的写面提醒** —— evolution 的代码写面是否需要在 C·3 建 WDS 机械写回时一并建模。

**报告族**：本报告 · `review/b7a-fidelity.md`（前半批）· `diy-coder/.analysis/2026-09-21-migration-b7/` 下 `v-b7b-{struct,content,compliance}.md`（三份 V 原始报告）与 `b7b-render-check.md`（渲染自证）。
