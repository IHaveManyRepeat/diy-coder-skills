# B2 批保真度报告 —— bmm 故事循环收尾（6 技能）

- 日期：2026-09-14 ｜ 批次：BMAD 迁移 阶段 B 第 2 批 ｜ 状态：**待用户知悉**（B2–B7 按计划 §五为**非强制人工审**，异常项才需看；本报告为知悉面）
- 任务书与裁定记录：`diy-coder/.analysis/2026-09-14-migration-b2/taskbook.md`
- 范式蓝本：P1 样板 + B1 批（均已拍板）；写作蓝本：`batch4/frozen-texts.md`
- 驱动：agent team `migration-b2`（W1-W6 分技能交付 + V 独立验证）
- 验证档案：`diy-coder/.analysis/2026-09-14-migration-b2/{v-audit.md, v-capability-inventory.md}`

## 一、批次结果总览

| 技能 | 源技能 | 产物 | 领域引擎 | steps | 测试数 |
| --- | --- | --- | --- | --- | --- |
| diy-create-story | create-story | `story-context.yaml`（SC-###） | `story_context.py`（collect/check） | 5 文件 | 18 |
| diy-retrospective | retrospective | `retrospective.yaml`（RT-###） | `retrospective.py`（collect/check） | 7 文件 | 17 |
| diy-correct-course | correct-course | `change-proposal.yaml`（CP-###） | `change_proposal.py`（collect/check） | 6 文件 | 17 |
| diy-quick-dev | quick-dev | `spec.yaml`（SP-###） | `spec.py`（check） | 6 文件 | 13 |
| diy-investigate | investigate | `investigation.yaml`（IV-###） | `investigation.py`（collect/check） | 6 文件 | 15 |
| diy-e2e-tests | qa-generate-e2e-tests | 追加 TC 至 `test-plan.yaml`（**不新增产物类型**） | `e2e.py`（detect/record） | 5 文件 | 13 |

**批级要点**

1. **5 个新产物类型走技能自带领域引擎**（P1 R1 裁定延续）；`diy-e2e-tests` 对齐 `diy-augment` 窄写权先例——**只追加 TC 进既有 `test-plan.yaml`**，不新增文档类型（少一组 viewer 标签缺口）。
2. **确定性下沉六处**：create-story 的上游情报采集（AC/TC/前序 note/git）、retrospective 的指标与缺陷归属、correct-course 的六产物影响面 + `--target` 引用链扫描（委派 diyc 交叉核对）、investigate 的 VCS/结构情报、e2e 的框架探测、quick-dev 的 verification 底线校验。
3. **引用式纪律**全面落地：6 技能跨文档一律 ID 引用（`S-x`/`AC-x.y`/`TC-x.y.z`/`D-x`/`FR-x.y`/`BUG-0xx`），源技能"把内容抄进 md"的形态被系统性替换——这是 diy 哲学对 BMAD 的核心改造。
4. 冻结文本 6/6 逐字命中；登记元数据 6/6 与任务书 §2.1 表一致。

## 二、逐技能保真度

### 2.1 diy-create-story

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 6 → 5 文件（源 2+3 取材面合入 02；源 3 的「读要改的文件」独立为 03；源 6 拆为 04 落盘 + 05 定稿路由） |
| 源 menu → diy 分支 | 3 处菜单（4/3/5 选项）→ 4 分支（显式 ID / sprint 首个非 done / 人工选择 / 拒绝路由） |
| 门禁 | stories.yaml 须 `final` + story 存在；不满足零产出 + 路由 diy-epics-stories（3 用例实测） |
| ID 链 | story→AC→TC→D 全解析校验（含 tc 归属、epic 一致 → `SET_MISMATCH`）；SC-### 稳定唯一 |
| viewer | 通用降级 rc=0；story-context 标签缺口入 C 阶段清单 |

**核心改造**：源把上下文抄进 story md 文件（违反"引用而非复制"）→ diy 版 = **引用式上下文包**。源「READ FILES BEING MODIFIED」硬纪律保留（`current_state` + `preserve` 字段 + `--final` 强制）。裁剪：template.md（Tasks/Dev Agent Record → diy-dev 现场派生 + sprint.yaml）、discover-inputs.md（whole/sharded 双形态在固定文件名体系下消失）、联网研究（无源不联网，diy 栈信息为 project-context + architecture）。**B4 后回接：无**。

### 2.2 diy-retrospective

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 13 → 7 文件（源 1→01；0.5→collect+01/02；2→02；3→03§1；4→03§2；5→01 尾指标块；6→04；7→05+03§2；8→05；9→06；10/11/12→07） |
| 源 menu → diy 分支 | 无菜单；入口触发语 + 三级 epic 发现分支（源优先级逻辑保留） |
| 门禁 | stories+epics 须 final、epic 可解析、≥1 done story；未收尾 → `PENDING_DECISION` warning + partial 三选项分流（4 用例实测） |
| ID 链 | epic/evidence/prev_followup/next_epic.id 全解析，悬空 `UNKNOWN_ID`；RT-### 稳定 |
| viewer | 仅渲染命令、零交互点；retrospective 标签缺口入 C 阶段清单 |

**核心改造**：输入面从 story md 的 dev notes → **结构化产物**（sprint note/evidence/loop/review.findings + bug-log + test-plan + stories）；指标由 `collect` 机械采集（与 `check --final` 共用 `collect_metrics()` 单一函数互证，不符即 `SET_MISMATCH`）。源 party-mode 五角色剧本整段裁剪，**保留** facilitations 纪律（no blame / 系统非个人 / 具体例证）与四视角清单（开发者/产品/QA/架构）。写权：不碰 sprint.yaml/stories.yaml（源 sprint-status 更新在 diy 无对应物）；significant_changes 只出条目 + 路由 diy-correct-course。**B4 后回接**：若 diy-party-mode 建成，回顾对话形态可回接。

### 2.3 diy-correct-course

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 6 → 6 文件（1:1 镜像） |
| 源 menu → diy 分支 | 1（CC 入口）→ 2（mode: incremental/batch）+ 3（scope 路由 minor/moderate/major） |
| 门禁 | prd+epics+stories 三件套 final；缺失零产出 + 路由（2 用例实测） |
| ID 链 | CP-### + impacts/edits target 格式校验；`--target` 链扫描实测回 4 条上下游边（prd F / stories AC / epics E / stories S） |
| viewer | 渲染静默；change-proposal 标签缺口入 C 阶段清单 |

**核心改造**：**只出提案、不改真源**（明写三处：Boundary 段 / Rule 1 / step 5 末段）——源直接给 old→new 编辑提案并路由；diy 版提案结构化（`edits[]`），真源修改由各产物所属技能执行。`collect` 委派 diyc 五型交叉核对（对齐 readiness 先例）+ 影响面链扫描（含 test-plan TC.ac 与 sprint test_refs 引用字段）。裁剪：md 文档发现与加载（whole/sharded/模糊匹配——diy 单一源下此线消失）、源 checklist §6.4 sprint-status 更新（归 diy-sprint）。**B4 后回接：无**。

### 2.4 diy-quick-dev

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 6（5 步 + one-shot）→ 6 文件 |
| 源 menu → diy 分支 | 1（QQ）→ 2（one-shot / plan-code-review） |
| 门禁 | anytime 无上游依赖；resume 按 status 路由；`verification` 空 + 状态前进 → `EMPTY_FIELD` 拒绝（轻量 TDD 硬底线） |
| ID 链 | SP-### 稳定唯一；跨文档零复制 |
| viewer | 静默旁路；spec 标签缺口入 C 阶段清单 |

**核心改造**：**审查层对齐 diy-review**（源三审查者 blind/edge/acceptance ≡ L1 正确性/L2 边界/L3 验收覆盖 + 四类路由，不另造体系）；**不自动 git / 不开编辑器**（源 commit/`code -r`/push 提示 → 一句话建议）；**TDD 轻量处置**：不做红绿台账，改为 `verification.commands[{cmd,expect,result}]` 实测留证（明文标注与 diy-dev 的差异）；`bad_spec`/`intent_gap`/`defer` 语义按 quick-dev 无上游产物面本地化（change_log 留痕 / 回人重议 frozen intent / 记录内 deferred）。裁剪：`compile-epic-context`（由 diy-create-story 承担）、`sync-sprint-status`（diy 无 sprint-status.yaml；走 `diyc check --type sprint`）。**B4 后回接**：step-02 的 elicitation / party-mode 提示语。

### 2.5 diy-investigate

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 14（激活 6 + 业务 7 + 结案判定）→ 6 文件（01 输入确认/路由 → 02 据点/立案 → 03 边界测绘 → 04 推理/假设 → 05 源码追踪 → 06 结案/交接） |
| 源 menu → diy 分支 | 4 路由（quick-dev / correct-course / create-story / review）+ 2 内部（resume / evidence-light） |
| 门禁 | anytime 入口；evidence-light 无 `missing_evidence` → `EVIDENCE_MISSING`；MISSING_FILE 结构化拒绝 |
| ID 链 | IV/EV/H 三位零填充 + 记录内唯一 + 生命周期完整性机械校验 |
| viewer | 通用降级；investigation 枚举（grade/hypothesis status/confidence/mode）标签缺口入 C 阶段清单 |

**源纪律逐条保留**：证据分级三态（confirmed `path:line` / deduced 推理链 / hypothesized 待验证）、据点先行、假设永不删除（只更新 status + resolution）、缺失证据也是发现、反驳轮、前提验证、>10K tokens 委派子代理返 JSON、并行独立操作。`collect` 采 VCS/结构情报（`NO_VCS` 降级不崩；`SCAN_TRUNCATED` 上限降级——两 warning 码均 docstring 声明）。裁剪：激活 6 步（customize 一体）、case-file-template.md（YAML Schema 承接）。**B4 后回接：无**。

### 2.6 diy-e2e-tests

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 6 → 5 文件（源 4 运行并入 04；源 5 摘要重定义进 05 record） |
| 源 menu → diy 分支 | 1（QA 入口）→ 0 独立分支（本体即流程）；源内 2 条件分支（API "if applicable" / E2E "if UI exists"）→ 02 目标层分流 |
| 门禁 | test-plan/stories 缺席 → 零产出 + 路由 diy-test-design；无框架 → `suggested` 决策点不自动安装 |
| ID 链 | `TC-{ac}.{seq}` 续号不重号（`DUPLICATE_ID`）+ ac 解析（`UNKNOWN_ID`）+ technique 枚举（`ENUM_INVALID`） |
| viewer | 静默旁路（无新增文档类型 → 无新增标签缺口） |

**窄写权三面**（对齐 diy-augment 先例）：① test-plan.yaml 追加 TC；② 项目测试目录代码；③ 收尾会话摘要。引擎强制零写入拒绝路径（重号/非法 technique 实测字节不变）。`record` 后委派 `diyc check --type test-plan` 交叉验证（违规并入回执作 warning）。**边界声明**（SKILL.md Rules 4）：编码前设计归 diy-test-design（九技法）、编码后补测归 diy-augment（三技法）、ATDD+自动化归 diy-test-author（B3 未建，明标）。裁剪：TEA 推广段（外部链接非能力）、联网搜框架（改 `detect` 的 `suggested` 本地清单）、test-summary.md（改会话摘要）。**B4 后回接：无**。

## 三、批级裁定摘要（主 agent）

- **备案采纳 3 条（W3）**：① `approach: {path: direct-adjustment|rollback|mvp-review, why}` 字段——源 checklist 的三方案评估是核心分析产物，任务书 schema 漏项，补上正确（`--final` 经 `PENDING_DECISION` 强制）；② 终门 status 口径 `{final|approved}`（分析定稿 / 路由放行）；③ 违规码零新增。
- **适配项（W 自决，主 agent 认可）**：W1 `preserve` 字段 draft 期不强制/`--final` 强制 + `suggestions` 回执键；W2 指标单函数互证 + sprint.yaml 零写入；W3 collect 链扫描含 TC.ac/test_refs 引用字段；W4 `--final` scope = project 定稿且 scope 内全 done（单条收口走 `--id`）；W5 evidence-light 复用 `EVIDENCE_MISSING`（不新增码）；W6 `record` 的 `ac` 单值收窄（一条绑一 AC）。
- **新增违规/警告码 3 个**（均 docstring 声明并经 V 核对）：`EVIDENCE_MISSING`（W5 违规码）、`NO_VCS` + `SCAN_TRUNCATED`（W5 warning 码）、`MANIFEST_UNPARSABLE`（W6 warning 码）。
- **`--previous` 全批判断**：6/6 不实现（追加/原位更新语义，无 ID 集合收缩风险）——各技能 SKILL Rule 显式记账（O1 由 W6 补修后 6/6 齐）。
- **V 唯一丢失项已修复**：W5 源 `case-file-template.md:111-115`「Side Findings」→ schema 增可选 `side_findings: [{note, ref?}]` + 06-report 承接句 + 引擎校验（复用 `EMPTY_FIELD`）+ 1 用例（15/15 绿）。

## 四、V 独立验证结论

**终版判定：可发布 yes，阻断项 0。**

| 审计项 | 结果 |
| --- | --- |
| 冻结文本 md5 | **6/6** 两值全中 |
| 薄主文件 + 四段 | 61–86 行（≤90）6/6；四段齐全有序 |
| 登记元数据 | 6/6 逐字段与 §2.1 表一致；description 逐字保留源触发语 |
| 测试 | 6/6 全绿、92 用例（含契约冒烟 + 门禁路径） |
| 门禁实测 | **32 场景全过**（W1 4 / W2 6 / W3 8 / W4 5 / W5 4 / W6 5，拒绝路径均零产出） |
| 跨技能一致性 | **15 维全过**（引擎契约 / 回执共同键 / `--output-dir` 必填 / where 口径 / 违规码 / 渲染串逐字 / steps 链 35/35 / 读取纪律 / 零 `bmad-` 悬空 / diy-* 引用全可解析 / 角色剧本零残留 等） |
| 红线 | 本批文件与所有权表一一对应，禁改面零触碰 |

**能力清点：保留 148 / 裁剪 38（全部有据）/ 丢失 1（已修复，见 §三）**。重点面全通过：W1「READ FILES BEING MODIFIED」硬纪律、W2 四视角与重大变更检测、W3 checklist 四段走查、W4 spec 八段全映射 + 五类→四类路由、W5 五纪律 + 六结局、W6 生成测试 ONLY 边界。

## 五、主 agent 集成验证（2026-09-14）

| 项 | 命令/方式 | 结果 |
| --- | --- | --- |
| 注册（验收 #5） | `bash diy-coder/sync.sh` | 已安装 **26 个 skill**（20 现有 + 6 本批）；6 新技能 SKILL.md 源码/副本 md5 全一致 |
| 全量回归 | `cd diy-coder && python -m unittest discover -s tests` | **Ran 488 tests OK**（395 基线 + 93 新增：18/17/17/13/15/13） |
| 渲染（#6） | `viewer.py --project-root .` | rc=0，rendered 8 docs，stderr 零字节，静默无交互点（新类型走通用降级，各 W temp 项目已实测） |
| 冻结文本 | 6 份双段 md5 | 6/6 命中 `5445f98b…` / `f1b3b6fb…`（V 独立复算同值） |

> 边界声明：本节为主 agent 自测数据，V 未独立复跑（V 已核对并确认来源标注清楚）；§四 的 V 结论段由 V 本人事实核对。

## 六、验收 12 项对照（迁移计划 §二）

| # | 验收项 | 证据 | 判定 |
| --- | --- | --- | --- |
| 1 | 薄主文件（四段）+ steps/ 厚子文件 | 6 份 SKILL.md 61–86 行；steps 5–7 文件 | 通过 |
| 2 | 产物 YAML schema + 稳定 ID 前缀 | SC / RT / CP / SP / IV（W6 走 test-plan 追加，无独立前缀） | 通过 |
| 3 | 前置门禁（零产出 + 路由） | 各技能门禁用例 + V 32 场景实测 | 通过 |
| 4 | ID 链接入 | 上游引用全解析（W3/W6 委派 diyc）；本产物 ID 稳定 | 通过 |
| 5 | 注册 | `sync.sh` → 26 技能，副本 md5 全一致 | 通过 |
| 6 | viewer 渲染 | 通用降级 rc=0；标签缺口 5 组入 C 阶段清单 | 通过（降级） |
| 7 | 冒烟 TC | 93 条新用例，全量 488 绿 | 通过 |
| 8 | 登记元数据 | frontmatter 6/6 与 §2.1 表逐字一致 | 通过 |
| 9 | 读取成本纪律 | On Activation + Workflow 双处「一次一 step 文件」 | 通过 |
| 10 | 双源输入声明 | **N/A**——本批 6 技能均非主线/WDS 交汇点 | 不适用 |
| 11 | 渲染静默 | 各 Workflow 仅命令一行；无交互点 | 通过 |
| 12 | diyc 接线（a-e） | a 实例委托（6/6 frozen 句）；b 终门（各引擎 check/record）；c `--previous`（6/6 记账不实现，判据正确）；d 语言绑定模板；e Rules 写权边界 | 通过 |

## 七、非阻断观察清单（V 清点，O1 已修 / O2–O9 记录不修）

| # | 技能 | 观察 | 严重度 | 处置 |
| --- | --- | --- | --- | --- |
| O1 | diy-e2e-tests | 唯一未显式记账 `--previous` | 低 | **已修**（SKILL.md Rules 6；62 行，md5 不变，13/13 绿） |
| O2 | diy-quick-dev | frozen 范围收窄（源冻结三节 → diy 冻结 intent 两键；boundaries 可改须留痕） | 低 | 记录不修 |
| O3 | diy-retrospective | 末步未声明结束语义（其他 5 技能有） | 极低 | 记录不修 |
| O4 | diy-retrospective | 「Team Collaboration Highlights」裁剪未显式说明（单人+AI 语境，方向合理） | 极低 | 记录不修（本报告 §2.2 已补记） |
| O5 | diy-create-story | `suggestions` 在无候选时为空列表，措辞可补「转人工指定」 | 极低 | 记录不修 |
| O6 | diy-retrospective | 「epic 无 done story」复用 `EMPTY_FIELD`，route 文案略偏 | 极低 | 记录不修 |
| O7 | 主 agent | `b1-fidelity.{md,html}` 有未提交改动（B1 拍板落盘，非本批触碰） | — | 提交时一并纳入 |
| O8 | 仓库 | 技能目录 `__pycache__` 残留（gitignore 已覆盖；install.py `copytree` 不过滤——**既有缺陷，本批未扩大处置**） | 极低 | 记录不修（见 §八 提请） |
| O9 | diy-investigate | 源「每个 outcome 后 pause」在 05/06 未显式保留（01–04 均有） | 极低 | 记录不修 |

## 八、既有缺陷登记（用户已裁定，2026-09-14）

**`install.py:33` / `sync.sh` 的 `shutil.copytree` 不过滤 `__pycache__`** —— 分发时会把运行残留复制进用户项目（`.gitignore` 已覆盖 git 层，仅影响物理复制；源码侧 7 处、副本侧 4 处；非 B2 引入）。

**用户裁定：排 C 阶段一并处理** —— C 阶段本就重做 install.py 分发清单（验收 #5，「48 技能同步测试，含子目录递归 copytree 验证」），届时一次改到位，避免同一文件两次 churn。（落地方式：`ignore=shutil.ignore_patterns("__pycache__")` 于 install.py 与 sync.sh 两处 + 现有残留清理。）

## 九、审阅指引（B2 为**非强制人工审**）

B2–B7 批按计划 §五只出报告。若你要抽查，建议顺序：

1. **§一 批级要点** —— 6 个技能各做了什么改造，2 分钟扫完。
2. **§四 V 结论** —— 阻断 0；能力清点 148/38/1（唯一丢失已修）。
3. **§八 提请决断** —— install.py pycache 一项。
4. 抽 1 个技能的 SKILL.md（各 61–86 行）确认四段结构与写权边界。
5. 抽一个引擎冒烟：`python diy-coder/skills/<技能>/scripts/<引擎>.py check --final --project-root . --output-dir diy-output --json`（新产物不存在时应回 `MISSING_FILE` rc=1）。
