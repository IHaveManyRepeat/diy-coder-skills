# B4 批保真度报告 —— core 通用工具（5 技能 + 存量回接）

- 日期：2026-09-20 ｜ 批次：BMAD 迁移 阶段 B 第 4 批 ｜ 状态：**待用户知悉**（B2–B7 按计划 §五为**非强制人工审**，异常项才需看；本报告为知悉面）
- 任务书与裁定记录：`diy-coder/.analysis/2026-09-19-migration-b4/taskbook.md`（终态 md5 `77667d6b84ad8644694f34f91857af9f` · 444 行）；开工前 dogfood 扫描回合：同目录 `dogfood-scan-2026-09-20.md`（首轮 68 条 + 增量补扫 15 条，**阻断 7/7 处置完毕**）
- 范式蓝本：P1 样板 + B1/B2/B3 批 16 技能（均已拍板）；写作蓝本：套件级句式母本 `diy-coder/.analysis/2026-09-16-skill-remediation/suite-texts.md`
- 驱动：主 agent 编排（W1–W5 分技能并行交付 → V 独立验证**分两路**：能力清点 + 终审计）
- 验证档案：同目录 `v-capability-inventory.md`（能力清点 296 行）· `v-audit.md`（终审计 248 行）· `v-viewer-gaps.md`（标签缺口 89 行）

## 一、批次结果总览

| 技能 | 源技能 | 产物 | 领域引擎 | steps | 测试数 |
| --- | --- | --- | --- | --- | --- |
| diy-brainstorm | bmad-brainstorming | `brainstorm.yaml`（BS-### + 会话内 `no` 序号） | `brainstorm.py` 870 行（list / techniques / init / check） | 5 文件 | 11 |
| diy-elicit | bmad-advanced-elicitation | **零产物**（增强交还调用方） | `elicit.py` 192 行（**只读**：`methods`；形 B） | **单文件** | 9 |
| diy-party-mode | bmad-party-mode | **零产物**（对话即交付） | **无引擎**（形 C——无确定性面） | **单文件** | 9 |
| diy-spec | bmad-spec | `spec-kernel.yaml`（SK-### + CAP-N） | `spec_kernel.py` 683 行（new / check；**本批唯一 `--previous` yes**） | 4 文件 | 11 |
| diy-editorial-review | prose + structure（2 合 1） | `editorial-review.yaml`（ER-###） | `editorial_review.py` 714 行（stats / check） | 3 文件 | 9 |

静态资产：`diy-brainstorm/brain-methods.csv`（**61 技术 / 10 类**）· `diy-elicit/methods.csv`（**69 方法 / 12 类**；`output_pattern` 箭头结构逐字保留）——两侧均**全译不裁**、条数与类别数零损失（CSV 解析器计数）。

**批级要点**

1. **全批 anytime 横切工具**——5 技能均不产主线产物链节点；验收 #10 逐条确认「非主线/WDS 交汇点」。
2. **两处零产物**：`diy-elicit`（增强在会话内完成，落盘归产物持有者）与 `diy-party-mode`（对话即交付）——判例承自 B3 `diy-test-author`；**真零写盘**（不写自有产物、亦不写任何其他文件）。
3. **第一个通用契约工具**：`diy-spec` 与 `diy-quick-dev` 的 `spec.yaml` 划清边界（「被多方消费的独立契约」vs「小变更执行通道」），**双向声明**——diy-spec 侧写在自己的 SKILL.md，quick-dev 侧属本批存量回接 ⑤。
4. **形 B / 形 C 两档引擎新形态首次出现**：`diy-elicit` 是只读工具引擎（无 `check`、无写回命令、旗标只收 `[--json]`、回执键豁免 `project_root`/`output_dir`/`violations` 三键）；`diy-party-mode` **无引擎**（名册解析已裁、零产物 → 无确定性面可下沉，**不得为凑测试造无意义引擎**）。
5. **存量回接五处**（本批收口链执行）：① brief 强制调用档（C 方案，连带 4 文件）· ② quick-dev `02-plan.md` · ③ project-context `03-rules.md` · ④ prfaq `01-ignition.md` · ⑤ quick-dev 结构段**新增** spec 边界句（无既有实文）。
6. **YAML 1.1 裸键 `no` 陷阱**：PyYAML 把裸键 `no:` 解析为布尔 `False`——W1（`brainstorm.py` 载入归一）与 W5（`editorial_review.py` 读点双形）各自处置，V2 真跑裁决**结果等价**；viewer 层同类问题（表头直出 `False`）登记 C 阶段（§八）。

## 二、逐技能保真度

### 2.1 diy-brainstorm

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 8 文件 → **5 文件**（01 session + 续接 → 02 techniques 四模式 → 03 facilitate → 04 organize → 05 finish）；`step-01b-continue` 的续接能力落 **`current_step: 1-5`** 路由表；`02a-d` 四个同构模板收敛为单文件内 A–D 模式分支 |
| 源 menu → diy 分支 | 4 → 4 一一对应（用户自选 / AI 推荐 / 随机 / 渐进流）；源内嵌菜单续接 3 项 + 教练 K/T/A/B/C 5 项全保留（源 `menu` 字段未登记它们，属**源登记面残缺**，非 diy 超范围） |
| 门禁 | 无上游依赖；薄输入（无议题也无素材）→ 拒绝 + 零产出（**不代拟议题**）；`已完成` 记录只读回看不再写入 |
| ID 链 | `BS-###` 由引擎 `init` 铸造（取最大值 +1，空号不复用）；想法用会话内序号 `no`（1..N 连续，跳号/重号报 `SET_MISMATCH`）；`themes[].ideas` / `priorities` / `actions[].idea` 引用可解析（越界 `UNKNOWN_ID`） |
| viewer | 有 YAML 产物 → 有渲染步骤；`technique` 值（61 技术名）是**必然告警路径**，缺口见 §八 |

**核心改造**：**教练对话过程不入产物**（源 `Facilitation Narrative` / `Session Highlights` / 能量观察整段裁——对话即过程记录，产物只收结论，契合母本 §6）；源 frontmatter 状态机（`stepsCompleted[]` / `session_active` 等）转为记录级 `status: 草稿|进行中|已完成` + `current_step: 1-5`（三态不足以定位续接点，源靠专门的 01b 读 `stepsCompleted` 续接）；会话续接 diy 化（`list` 只回五字段 `id/topic/date/status/current_step`，「只列不读」纪律保留）；菜单 A（深挖）接线 `diy-elicit`（同批建成互引）。**61 技术库中文化**：逐条保留「适用时机 + 核心动作」，`--category` 合法值随库中文类名。**裁剪**：会话 md 文档 + `template.md`（YAML 单一源）· `context_file`/`inputDocuments` 参数面（customize 不迁；替代 = 可选**只读** `project-context.yaml`/`prfaq.yaml`/`brief.yaml`）· 人设剧本。**B4 后回接：无**（本技能是回接的受益方——④ prfaq 改道路由到它）。

### 2.2 diy-elicit

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 单文件（`steps: null`）→ **0**（无 `steps/`；源即单文件短流程，决策阶段 ≤3，不硬拆） |
| 源 menu → diy 分支 | 4 → 4 + 2（`1-5` / `r` 洗牌 / `a` 全列 / `x` 交还；另 2 个源侧响应分支 `Direct Feedback` / `Multiple Numbers` 逐个保留） |
| 门禁 | 增强对象在场（当前 section 或 `--target` 文档段）；空对象 / <1 句 → 拒绝 + 零产出；独立使用时无对象 → 问一次 |
| ID 链 | **N/A**（零产物、零写面） |
| viewer | **无渲染**（零 YAML 产物；Rules 写明理由） |

**核心改造**：**零 YAML 写面**（本技能不改任何文件）——源 Case 1-5 的「apply to the doc」语义在 diy 单源体系下等价于「调用方接受后自行落盘」（`revisions` 由产物持有者记）；**形 B 只读引擎**（`methods`：加载 / 随机抽 / 按类筛选 / 全列，无 check 无写回）；**69 方法全译**（`category` 12 中文类名即 `--category` 合法值；`method_name` 中文名 + 原英文括注；`output_pattern` 整列英文**逐字保留**——箭头与顺序是弹性流程引导，部分为不可译符号串）。**与 W5 的边界**（V2 逐句核）：elicit **增强当前内容**（增强版交还、落盘归持有者），editorial-review **只评审出建议**（`revised` 是建议稿、从不产出目标文档新文本）；两者都不**代改** target。**B4 后回接：无**（C 阶段横切入口接线属另一项，见 §七）。

### 2.3 diy-party-mode

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 单文件 → **0**（无 `steps/`） |
| 源 menu → diy 分支 | 2 → 2 零裁剪（`--model <model>` / `--solo` 逐字保留） |
| 门禁 | 无议题 → 开场问一次（源 welcome 路径）；子代理不可用且用户拒绝 `--solo` → 一行说明 + 停止 |
| ID 链 | **N/A**（零产物） |
| viewer | **无渲染**（零 YAML 产物；Rules 写明理由） |

**核心改造**：**视角动态派生取代 agent 名册**（本批最大改造）——源 `resolve_config.py --key agents` 四层合并 + 7 字段名册 + `{icon} **{name}:**` 人设 prompt **一体裁撤**（diy 无 agent 人设体系）；**三要素回落**：身份（code/name/title/icon）→「视角名」（用户可点名/增补/替换）、专长（description/module）→「关注点」、立场 → **显性写出 + 反面义务**（必须找出该视角下的风险或反例）——源靠人设隐含立场，diy 显性化并加产出义务，**对源是加强**。方法本体逐条保留：真子代理独立 spawn + 并行派发（**禁自己生成视角发言**，`--solo` 例外且须明示）、逐字呈现不合成、讨论摘要 ≤400 词、2-4 选角 + 轮换 + 点名必含、异常处置四条、自然语言退出、交叉应答。**零引擎**（形 C）：源唯一机械面（名册解析）已裁，其余全是 LLM 对话判断。**与 `diy-review` 的边界**：diy-review 是**结构化缺陷检出**（findings 台账，供门禁与路由），本技能是**讨论形态**（产出对话本身）——两侧不互替（V2 机械化为断言：对侧不得自称「圆桌」「多视角」）。**B4 后回接：无**（②③ 两处是回接方向相反——quick-dev / project-context 点名它）。

### 2.4 diy-spec

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 单文件（129 行）→ **4 文件**（01 input 判定 + slug 解析 → 02 distill 五字段 + artifacts 开条判据 → 03 validate 两遍自校验 → 04 finish 终门） |
| 源 menu → diy 分支 | 2 → 2 零裁剪（`express` / `guided`；稀疏输入二选一，无头默认 express 并记录） |
| 门禁 | 无输入 → 交互问；输入过薄 → 拒绝 + 路由 `diy-prd`；slug 无头缺失 → 拒绝 + `missing_slug` 语义说明（headless JSON error_code 改人读诊断，已登记偏离） |
| ID 链 | `SK-###` 由引擎 `new` 铸造；`CAP-N` 由 LLM 铸造、引擎校验（格式 / 唯一 / **稳定不重用**，退役标 `retired: true` 留痕）；**`--previous` 按 slug 配对**比 CAP 集合，旧有新无且未标 retired → `ID_UNSTABLE` |
| viewer | 有 YAML 产物 → 有渲染步骤；缺口见 §八 |

**核心改造**：**md 文件夹形态折叠**——`.decision-log.md` → `revisions` + 记录级 `verdict`（判决段）；spec-authored companions → `artifacts[]`（内容内联，图表用多行块字符串；「kernel 一行装不下」保留为开条判据）；adopted companions → `companions[]` 路径引用（只引用不改）；「不许静默丢弃」落 `verdict.preservation.dropped`。**CAP 退役机制**：源有「never reuse retired IDs」但无承载字段（落 md 靠人记），diy 用 `retired: true` 痕迹位（退役 = 保留条目 + 标真，绝不删——删除会同时毁掉审计价值与 `--previous` 可判性）。**`--previous` 判 yes**（本批唯一）：CAP 稳定不重用是 Spec Law 6 招牌纪律，**只有机械保障才拦得住**（记录可被 LLM 直编改写）。**命名避让**：产物 `spec-kernel.yaml` / 引擎 `spec_kernel.py`（V 实核全库无第二处使用）。**边界双向**：与 `diy-quick-dev` 的 `spec.yaml` 互不读写；`diy-spec ≠ diy-prd`（轻内核契约 vs 完整产品需求文档）。**裁剪**：`customize.toml` 全配置面 · headless JSON 契约（改人读诊断 + 引擎回执）。**B4 后回接：无**（⑤ 是 quick-dev 侧加句）。

### 2.5 diy-editorial-review

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 单文件 + 单文件 → **3 文件**（01 scope + stats 结构地图 → 02 analyze 结构透镜→文风透镜 → 03 report findings 落盘 + 终门） |
| 源 menu → diy 分支 | 0 + 0 → 2（`--lens 结构` / `--lens 文风`，缺省两支全跑；源无菜单项可裁；源 `args: [path]` → `--target <path>`） |
| 门禁 | target 不存在 / 空 / <3 词 → 拒绝 + 零产出；非法 `--lens` / `--reader-type` → `ENUM_INVALID`；「无问题」是合法完成（源 HALT 语义保留） |
| ID 链 | `ER-###` 随首次评审由 LLM 铸造、`check` 校验格式与唯一性（无骨架命令）；findings `no` 记录内序号自 1 连续；`target` 基准 = project-root 相对 + 正斜杠 + 无 `path:` 前缀（写入侧与校验侧同基准） |
| viewer | 有 YAML 产物 → 有渲染步骤；缺口见 §八 |

**核心改造**：**两透镜一次评审**（prose + structure **A 级组 2 合并**）——findings 分槽承载（`structure.findings` / `prose.findings`），结构先行（源文自述 "run this BEFORE copy editing"）；`reader_type` 枚举中文化 `人类|LLM`。**建议制保留**：只出 Original/Revised/Changes 与 CUT/MERGE/MOVE/CONDENSE/QUESTION/PRESERVE 六分类建议（含影响词数估计），**不代改 target**。**被调用形态**（与 brief 的强制调用档接口，§12.1 ①）：被 `diy-product-brief` 调用时默认两透镜全跑、不中途问、直接 `check --final` 置 `已定稿`（交互点跳过是本形态的**明示例外**，Rules 写明）；`--lens` 单透镜自由度只属独立调用形态。**`stats` 词数口径**：中文字符按 1 词计 + 西文按词分词（与 LLM 的 `impact_words` 估计同口径；`--final` 只核内部自洽，不判估计合理性）。**裁剪**：两源独立入口收敛（单透镜仍可只跑）· 人设段（`Your Role`）· 源 markdown 报告形态（YAML 单源 + viewer 投影）· `length_target` 不落字段（判断结果落 `meets_length_target`）。**B4 后回接：无**（① 是它被 brief 调用）。

## 三、批级裁定摘要

**六项前置裁定**（主 agent 编制期，用户过审时未推翻）：

| # | 裁定 | 落地 |
| --- | --- | --- |
| 1 | `diy-brainstorm` 产物 = `brainstorm.yaml`；教练过程不入产物；`status` 三态 + **`current_step: 1-5`**（源 `stepsCompleted[]` 的 diy 单值承载） | §2.1 |
| 2 | `diy-elicit` **零 YAML 写面**（落盘归产物持有者，「记入 revisions」按**由持有者记**执行） | §2.2 |
| 3 | `diy-party-mode` **视角动态派生**取代 agent 名册（保留真子代理 + 逐字不合成） | §2.3 |
| 4 | `diy-spec` 产物 = `spec-kernel.yaml`（避让 quick-dev 的 `spec.yaml`；引擎名 `spec_kernel.py` 同避让） | §2.4 |
| 5 | `diy-editorial-review` 两透镜一次评审 + **建议制不代改**；两源独立入口收敛为「一次评审两透镜」 | §2.5 |
| 6 | 两方法库**全译不裁**（61 + 69 条；条数与类别数不得减少） | §一 |

**V 终审计衍生裁定（4 条，主 agent 拍板）**：

| # | 事项 | 裁定 |
| --- | --- | --- |
| R1 | W2 边界句「两者都不落盘」与 W5 有自有产物字面冲突 | **采纳改写**：「两者都不把改动落盘」（消歧，不改分工语义）；已由 W2 落地复跑绿 |
| R2 | W4 `verdict.coherence` 兼载 express/guided（冻结 schema 无 `verdict.note` 键——§6 裁定 4 措辞与 schema 不一致） | **追认**（有据落点）；§6 裁定 4 措辞待更正，登记本报告 |
| R3 | W4 `constraints` 允许空列表（与「五字段非空」字面张力） | **追认**（Spec Law 3 是品质判据——凑一条不淘汰设计的约束 = decoration，比空列表更坏） |
| R4 | 裸键 `no` 两处处置形态差异（W1 写回后 `'no':` / W5 原样 `no:`） | **合规放行 + 登记**（读面等价、写面不同键类型；viewer 层归一入 C 阶段 §八） |

**改进采纳 3 条**（V1 能力清点的观察项）：W5 prose 原则 2「保留结构」补显式句（B 段第 3 条）· W4 补 `project-context.yaml` 只读取材面（落 `steps/01-input.md`，理由：母本 §4 禁主文件列举封闭清单）· 两处均已落地复跑绿。

## 四、V 独立验证结论

**能力清点（V1，296 行）**：**零丢失**——5 技能逐条对照 BMAD 原文，所有裁剪项均有据（§0 裁定 / 迁移计划改判）；两方法库条数与 `output_pattern` 箭头计数逐位相等（168 = 168）；W1 的 8→5 并步对账成立（含 01b 在 `current_step` 上的落点）；W4 `--previous` 是真机械保障（义务链完整：留 `.prev` → 必附 `--previous` → 过门才删）。**观察 2 条**（已处置，见 §三 改进采纳）· 另发现两处普查文档毛刺（`source-census.md` 的「60 + 69」与「SKILL 130」笔误，不影响产物）。

**终审计（V2，248 行）**：**总判通过，无阻断项**。

| 审计项 | 判 | 证据摘要 |
| --- | --- | --- |
| A 母本逐字（§1–§6） | ✅ | 手工逐字比对全过（判据比测试更严：§3 比四行全文）；5 技能**尚未登记时该方法静默跳过**——V 手工结果先于测试接管（登记后由 `test_suite_texts.py` 强制） |
| B 门禁路径实测 | ✅ | 20 条真跑（全 tempfile）：W1 `UNKNOWN_ID`/`ENUM_INVALID` · W2 `ENUM_INVALID` + 形 B 回执键 · W3 **6 组变异测试全数转红**（含对侧 `diy-review` 改写触发双向断言）· W4 `ID_UNSTABLE` 真造旧稿丢 CAP + 退役放行 · W5 三拒绝路径 |
| C 跨技能一致性（4 项） | ✅ | ① W2↔W5 增强/建议边界 · ② W3↔diy-review 双向（反向 grep 零命中 + 断言） · ③ W4↔quick-dev（quick-dev 反向句属回接 ⑤） · ④ 61 + 69 对账 |
| D W 自报裁定复核 | ✅ | **裸键 `no` 真跑裁决**：两引擎对裸键产物均 rc=0、注入重号/跳号均转红——机制不同（载入归一 vs 读点双形）而**结果等价**；W5 报告点名 `brainstorm.py:495` 的疑虑**已过时**（该处依赖载入期归一，`brainstorm.py:98-127` 已处理） |
| E 结构面 | ✅ | 5 份 SKILL.md 88/73/65/84/87 行（≤90）；四段中文标题无额外二级标题；frontmatter 六字段逐格同值；12 个 steps 文件 H1 + `Read (input)`/`Write (output)` + 尾节点名齐全 |

**分歧点裁决留档**：W5 施工期观察「`brainstorm.py:495` 可能未处理 `no` 键」与 W1 自报「已加 normalize_keys」冲突——V2 真跑裁决**以实测为准：两处等价**（W5 的观察基于其施工时点的未完成态）。

## 五、主 agent 集成验证（2026-09-20）

| 项 | 命令/方式 | 结果 |
| --- | --- | --- |
| 回接锚句复核（收口链①） | 逐个打开五处挂点**按文本**重扫实文 | ① 确认失效（中文化轮改写，C 方案替换）· ②③④ 前向标记完好（仅点名）· ⑤ 无既有实文（新增句）——与任务书 §12.1 的 2026-09-20 实核一致 |
| 存量回接（收口链②） | ① 连带面 4 文件（03-finalize / SKILL.md / brief.py / test_brief.py）+ ②③④⑤ | ① 六条校验全落（**零新码**：EVIDENCE_MISSING / MISSING_FILE / UNKNOWN_ID / STATUS_MISMATCH + 降级档 TOOL_MISSING）；test_brief **20 → 28 用例**；②③④⑤ 各一处最小改动 |
| 母本登记（收口链③） | `test_suite_texts.py` 三处（`NEW_SKILLS` / `CONVERTED_INSTANCE` / `CONVERTED_DISCIPLINE`） | **10 passed**（登记前 2 红为预期中间态）；5 技能进 §1/§2 强制断言面 |
| 注册（验收 #5） | `bash diy-coder/sync.sh` | 已安装 **37 个 skill**（32 存量 + 5 本批）；冒烟四检全 OK |
| 全量回归 | `cd diy-coder && python -m pytest -q` | **854 passed / 54 subtests passed**（146s；795 → 854 = 5 技能 49 条 + test_brief 新增 8 条 + 其他） |
| 渲染（#6） | viewer.py 探针（3 新类型 temp 项目真跑） | rc=0，`rendered 3 doc(s)`，stderr 0 字节；**但该值样本相关**——V 的映射表核对（§八）另查出 brainstorm `technique` 的必然告警路径 |
| 并发窗口声明 | `git status` 全程核对 | 本批写面（5 新目录 + 5 新测试 + 回接 4 文件 + test_suite_texts + docs）与另一窗口的「枚举中文化」改动（21 个存量文件）**零重叠**；854 全绿同时覆盖两侧 |

> 边界声明：本节为主 agent 自测数据；§四 由 V 独立取证（其脚本/实测面）。

## 六、验收 13 项对照（迁移计划 §二）

| # | 验收项 | 证据 | 判定 |
| --- | --- | --- | --- |
| 1 | 薄主文件（四段）+ steps/ 厚子文件 | 5 份 SKILL.md 65–88 行；W1/W4/W5 有 steps（5/4/3 文件），W2/W3 **单文件形态**（理由已在体写：无多会话状态、决策阶段 ≤3） | 通过 |
| 2 | 产物 YAML schema + 稳定 ID 前缀 | `BS-###` / `SK-###`+`CAP-N` / `ER-###`；W2/W3 零产物（N/A） | 通过 |
| 3 | 前置门禁（零产出 + 路由） | 各技能门禁用例 + 拒绝路径零产出（V2 实测 20 条） | 通过 |
| 4 | ID 链接入 | W1 序号引用可解析 · W4 `CAP-N` 稳定不重用 + 退役痕迹 · W5 `no` 连续 + `target` 基准；W2/W3 N/A | 通过 |
| 5 | 注册 | `sync.sh` → **37 技能** | 通过 |
| 6 | viewer 渲染 | ⓐ 母本 §5 逐字（V2 核）· ⓑ 3 新类型降级 rc=0；标签缺口清单入 §八 | 通过（降级） |
| 7 | 冒烟 TC | 5 技能 49 条新用例；全量 **854 绿** | 通过 |
| 8 | 登记元数据 | frontmatter 5/5 与 §2.1 表逐格同值（V2 核） | 通过 |
| 9 | 读取成本纪律 | W1/W4/W5 母本 §4 逐字；**W2/W3 无 steps → 永久不适用**（理由句在场） | 通过 |
| 10 | 双源输入声明 | **N/A**——5 技能均非主线/WDS 交汇点（逐条确认） | 不适用 |
| 11 | 渲染静默 | W1/W4/W5 母本 §5 逐字；**W2/W3 无渲染**（理由句在场） | 通过 |
| 12 | diyc 接线（a–e） | a 实例委托（5/5 母本句 + `diyc.py resolve`）· b 终门（W1/W4/W5 各引擎 `check --final`；W2 无 check、W3 无引擎——N/A 说明在场）· c `--previous`（**W4 唯一 yes**，其余记账不实现）· d 语言绑定（母本 §3）· e 写权边界（W1/W4/W5 写 `{output_dir}`；**W2/W3 真零写盘声明**） | 通过 |
| 13 | 副作用纪律 | ① 自动执行档 = 渲染（回执见 §五）· ② 环境自适应档 = 无 · ③ 保留确认档 = W3 的 spawn >4 / `--model` 覆盖（**对话内确认，不入 defer 队列**）；`defer-add` 取证由主 agent 在 tempfile 完成 | 通过 |

## 七、非阻断观察清单

| # | 对象 | 观察 | 严重度 | 处置 |
| --- | --- | --- | --- | --- |
| O1 | W5 | prose 7 原则中「保留结构」仅隐式承接 | 低-中 | **已补**（`steps/02-analyze.md` B 段第 3 条显式句） |
| O2 | W4 | 缺 `project-context.yaml` 只读取材面（同批不对称） | 低 | **已补**（`steps/01-input.md` 的 `Read (input)` + 可选素材段） |
| O3 | W5 | 双原则集（human/LLM 各 9 条）压缩为 4 轴 + 义务句，未逐条枚举 | 低 | 接受（母本 §6 + §7 回报必答未要求逐条），登记不修 |
| O4 | W4 | TDD 顺序：`steps/01` 的 `.prev` 快照时机与 `04` 的删除时机跨步（非同一文件内闭环） | 极低 | 契约 §8.3 先例同构，接受 |
| O5 | LINK1 | brief 的「下次 04-update 时补跑」未写进 `04-update.md` 自身文本（连带面 4 文件不含它） | 低 | **裁定：不改**——任务书 ⓖⓑ 的实质约束（报错 + 指引 + 不静默放行）已满足于 `03-finalize.md` + 引擎诊断 |
| O6 | LINK1 | `TOOL_MISSING` 只覆盖「环境缺兄弟引擎」档（「无头 runner 无法派发子技能」产物侧不可区分） | 低 | 接受（引擎无判据；ⓖⓒ 已明确不给开关） |
| O7 | 全批 | C 阶段横切入口接线（prd / architecture / epics-stories / design 接 elicit / party-mode） | — | **不在本批**（任务书 §12.2 递延），主 agent 已在任务书登记，C 阶段执行 |
| O8 | 全批 | `diy-help` CHAIN 不登记（5 技能均不产主链产物） | — | 确认（§12.4）；C 阶段「登记表驱动」改造按 frontmatter 六字段自动纳入 |
| O9 | 普查文档 | `source-census.md` 两处笔误（「60 + 69」应为 61；「SKILL 130」应为 129） | 极低 | 记录不修（研究档，产物已按正数） |

## 八、viewer 标签缺口清单（**C 阶段输入**，任务书 §12.8）

3 个新产物类型 + `brief.yaml` 新字段 `review_refs` 全部走**通用降级**（不崩、逐页渲染）；缺口实测 = 收口链⑥ temp 项目渲染 + V 的**映射表核对**（`viewer.py` 的 `DOC_LABELS` / `KEY_LABELS` / `VALUE_LABELS` / `ENUM_KEYS` / `BADGE_CLASSES`）：

| 对象 | 文档名标签 | 枚举值缺口（有 stderr 告警） | 静默枚举字段（key 不在 `ENUM_KEYS`） | key 标签缺口 |
| --- | --- | --- | --- | --- |
| brainstorm | 缺（页标题 / 导航出英文名） | **`technique`**——61 个技术名 0 命中词表，凡有非空 `ideas[].technique` **必然告警** | `approach` / `category` / `current_step` | 22 键（含 `no` 布尔化——表头直出 `False`） |
| spec-kernel | 缺 | **无**（`verdict` 虽 ∈ `ENUM_KEYS` 但值是映射，不触发 badge） | — | 19 键；`retired` 布尔直出 `True` |
| editorial-review | 缺 | **无** | `category`（CUT/MERGE/… 英文原样直出）/ `meets_length_target` / `lenses` / `reader_type` / `model` | 20 键（`purpose` 语义漂移——与文档 purpose 混淆） |
| brief · `review_refs` | 存量缺口（`brief` 文档名本就缺） | 另发现 `decisions[].decision` 自由文本撞 `ENUM_KEYS` → 每文档 2 行告警（需补 `FREE_TEXT_FIELDS`） | `review_refs` **不在 `REF_KEYS`** → 无悬空检测（目标不在场时静默断裂，既不标红也不告警） | 英文直出 `<h2 id="review-refs">` |

**实测 stderr 原始诊断**（V 以 4 份 W 测试夹具做等价渲染复测；收口链⑥ 的「stderr 0 字节」**成立但样本相关**——骨架样本无 `technique` 值）：

```
单文档 brainstorm: 41 字节 / 1 行  →  unmapped enum: 连续五问
单文档 spec-kernel: 0 字节
单文档 editorial-review: 0 字节
单文档 brief: 100 字节 / 2 行  →  产物落 YAML 单一源、外部交接裁剪
四文档合批: 141 字节 / 3 行
```

**附带发现**：`no` 键布尔化在 viewer 层同样存在（表头直出 `False`，实测 4 处）——**加 `KEY_LABELS["no"]` 修不掉**，需键归一（两引擎均有先例：`normalize_keys()` / `seq_no()`，viewer 无）。

**处置口径**：共享文件（`viewer.py`）改动统一排 **C 阶段**（与 B1/B2/B3 标签缺口同批处理，避免逐批 churn）；本清单即 C 阶段的启动输入。**待 C 阶段拍板**：`no` 键归一形态 · 61 个 `technique` 值逐个入表还是 doc 级豁免 · `brief` 存量文档名标签是否同批补 · `verdict`/`purpose` 语义漂移是否走文档级覆盖。

## 九、审阅指引（B4 为**非强制人工审**）

B2–B7 批按计划 §五只出报告。若你要抽查，建议顺序：

1. **§三 裁定摘要** —— 六项前置裁定 + V 衍生的 4 条 + 3 条改进采纳，3 分钟扫完。
2. **§四 V 结论** —— 能力清点零丢失 + 终审计五面全过；**分歧点裁决**（`no` 键）是最有信息量的一处。
3. **§八 标签缺口** —— C 阶段输入，含一个反直觉发现（收口链的「零告警」是样本相关）。
4. 抽 2 个技能的 SKILL.md 确认四段结构与写权边界：`diy-elicit`（**零写面** + 形 B 只读引擎）与 `diy-party-mode`（**零产物零引擎** + 视角动态派生）最值得看。
5. 抽一个引擎冒烟：`python diy-coder/skills/diy-spec/scripts/spec_kernel.py check --final --project-root . --output-dir diy-output --json`（产物不存在时应回 `MISSING_FILE` rc=1）；`--previous` 的 `ID_UNSTABLE` 是唯一机械保障路径，值得单独试。
