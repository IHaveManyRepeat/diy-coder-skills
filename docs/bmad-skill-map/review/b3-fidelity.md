# B3 批保真度报告 —— TEA 测试架构（5 技能）

- 日期：2026-09-19 ｜ 批次：BMAD 迁移 阶段 B 第 3 批 ｜ 状态：**待用户知悉**（B2–B7 按计划 §五为**非强制人工审**，异常项才需看；本报告为知悉面）
- 任务书与裁定记录：`diy-coder/.analysis/2026-09-15-migration-b3/taskbook.md`；九项未决问题与裁定全过程：同目录 `work/pending-decisions.md`
- 范式蓝本：P1 样板 + B1/B2 批 11 技能（均已拍板）；写作蓝本：套件级句式母本 `diy-coder/.analysis/2026-09-16-skill-remediation/suite-texts.md`
- 驱动：agent team `migration-b3`（W1-W5 分技能交付 + V 独立验证）→ 能力清点判 FAIL（丢失 32 条）→ 5 并行 agent 返工 → V 复验通过
- 验证档案：`diy-coder/.analysis/2026-09-15-migration-b3/v-capability-inventory.md`（能力清点 + 终审计 + 返工落地）

## 一、批次结果总览

| 技能 | 源技能 | 产物 | 领域引擎 | steps | 测试数 |
| --- | --- | --- | --- | --- | --- |
| diy-test-author | atdd + automate（**仅取规则集**） | **无 YAML**——红相脚手架代码落项目测试目录 | `author.py`（detect / audit）961 行 | 6 文件 | 30 |
| diy-test-gate | trace + nfr | `test-gate.yaml`（TG-###） | `gate.py` + `gate_check.py` + `gate_lib.py`（collect / check）1818 行 | 6 文件 | 43 |
| diy-test-framework | framework + ci | `test-framework.yaml`（TF-###）**+ 项目文件**（脚手架 / CI 配置） | `test_framework.py`（detect / scaffold / check）1269 行 | 6 文件 | 33 |
| diy-test-review | test-review | `test-review.yaml`（RV-###） | `test_review.py`（scan / score / walkthrough / check）1778 行 | 5 文件 | 33 |
| diy-teach-me-testing | teach-me-testing | `learning-progress.yaml` + `notes/session-<NN>.md` + `completion-summary.md` | `progress.py`（init / status / update / check）1194 行 | 5 文件 | 29 |

静态资产：`diy-test-gate/adr-checklist.yaml`（29 行）· `diy-test-review/criteria.yaml`（35 行留档 / 32 有效）· `diy-test-framework/templates/`（**45 模板**：framework 33 + ci 12）· `diy-teach-me-testing/{curriculum,quiz-questions}.yaml` + 2 md 模板。

**批级要点**

1. **三处形态首次出现**：`diy-test-author` 是 diy 体系第一个**零 YAML 写面**技能（产物 = 项目测试代码）；`diy-test-framework` 是第一个**以产出项目文件为重**的技能（台账 YAML 仅记「选了什么、生成了什么」）；`diy-teach-me-testing` 是第一个 **Hub-and-spoke 多会话状态**技能（定义态静态资产 / 运行态进度分离）。
2. **确定性下沉五处**：author 的红相纪律审计（源 checklist 手工核对 10 条 → 引擎规则码）、gate 的矩阵 join + 覆盖判定表 + 软指标六项、framework 的栈/平台探测 + 模板渲染 + CI 对齐重扫、review 的评分账本（severity 复算 / 去重 / 分档 / recommendation 推导）+ 三向走查、teach 的派生三式 + 进度完整性校验。
3. **引用式纪律**：全批跨文档一律 ID 引用（`S-x` / `AC-x.y` / `TC-x.y.z` / `FR-x.y` / `DA-0xx` / `path:<relative>`）——author 的 TC 锚注释、review 的 `coverage_gaps.route`、framework 的 `static_check_alignment[].order`（**禁抄录命令内容**）。
4. **能力零丢失口径落地**：V 按「源里有、规格未明裁、diy 里没有 ⇒ 丢失」判定，**丢失 32 条全部返工**（甲 2 = 执行漏项 / 乙 2 = 功能性缺陷 / 丙 28 = 补齐），新增 **15 个违规码**，测试 120 → 168。返工中另修 3 条既存缺口（N-1/N-2/N-3），追认 5 项（P-1–P-5）。
5. **副作用纪律三档**（计划 §二 #13）：framework 的依赖安装 / 跑测试 / `chmod +x` 走**自动化档**（结果记台账 `checks`）；hook 合并（改用户级配置）走**保留确认档**——`diyc.py defer-add` 入队 `deferred-actions.yaml`（`reason: user-config`），台账 `deferred:` 记 `DA-0xx` 引用。
6. 母本句式 5 技能已登记 `test_suite_texts.py` 三面（`NEW_SKILLS` / `CONVERTED_INSTANCE` / `CONVERTED_DISCIPLINE`），此前对它们**静默跳过**的 §1–§5 面即时生效（5 用例绿）。

## 二、逐技能保真度

### 2.1 diy-test-author

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | atdd 5 步（steps-c 9 文件）+ automate 4 步（10 文件，**仅取禁则规则集**）→ 6 文件（01 detect + 门禁 → 02 范围选择 → 03 生成 → 04 纪律审计 → 05 静态确认 → 06 终门 + 摘要 + 路由） |
| 源 menu → diy 分支 | 源子代理分派架构（04a/b/c）与 C/R/V/E 菜单裁剪；diy 无独立分支——范围选择四入口（story / type / priority / 显式 TC 列表） |
| 门禁 | test-plan.yaml 须 `final` + 范围内 TC 在场且 `status: pending` + `technique` / `kill_target` 非空；无框架 → HALT + 路由 `diy-test-framework`；范围内全 pass/空 → 一行报告 + 零产出（不静默空跑） |
| ID 链 | TC 锚注释 `TC: TC-x.y.z`（C 族 `// TC:`）是幂等消重的**唯一凭据**；零 YAML 写面——不碰 `{output_dir}` 任何文件 |
| viewer | **无 YAML 产物 → 无渲染步骤**（Rules 写明理由）→ 无新增标签缺口 |

**核心改造**：源双模式（`[A]` pre-code / `[B]` post-code）**收敛为单模式**——红线脚手架，`[B]` 随 A1 裁定删除（连带：`--mode` 参数、`SKIP_RESIDUAL`/`UNANCHORED_TEST` 两码、`02-mode-scope`/`05-execute` 改名、`followedBy` 收敛为 `[diy-dev]`）。自动化规则集（禁硬编码依赖 `waitForTimeout` / 禁 `isVisible()` 条件流 / 禁 page object / 单断言原子 / **确定性隔离** / 文件行数上限）逐条落为引擎违规码；补齐 10 条（`PRIORITY_TAG_MISSING`/`MISMATCH`、`NAME_UNDESCRIPTIVE`、`GWT_MISSING`、`ORDER_DEPENDENCY`、`SHARED_STATE`、`NONDETERMINISTIC_SOURCE`、`TRY_CATCH_TEST_LOGIC`、`DEBUG_STATEMENT`、`FIXTURE_NO_TEARDOWN`）。**与 diy-dev 的 TDD 契约**：脚手架 `skip` = 「待实现」标记，diy-dev 开始实现前先去掉 skip 跑红。裁剪：`expected_to_fail` 字段、子代理编排 + `/tmp` JSON 契约、生成模式（AI vs 浏览器录制）、执行与自愈。**B4 后回接：无**。

### 2.2 diy-test-gate

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | trace 5 步（steps-c 6 文件）+ nfr 5 步（12 文件）→ 6 文件（01 产物在场 + collect → 02 oracle → 03 矩阵/缺口/盲区 → 04 NFR 四域 + ADR → 05 门决策 → 06 终门 + 渲染 + 摘要） |
| 源 menu → diy 分支 | tri-modal C/R/V/E 菜单与人设裁剪；diy 无分支菜单（scope 只有 `story` 一值） |
| 门禁 | stories + test-plan（final）+ prd 三件套；oracle 解析不出 → HALT + 路由 `diy-epics-stories`；prd 缺席 → HALT + 路由 `diy-prd`（priority 是 P0/P1 分数线的前提）；sprint 缺席 → 证据面降级（说明写进 `gate.basis` 末句） |
| ID 链 | TG-###；AC/TC/S/FR 引用解析（产物自校自实现 + 跨文档委派 diyc）；waivers 8 键完整契约（security 域 FAIL 不可豁免） |
| viewer | 通用降级 rc=0；test-gate 枚举缺口见 §八 |

**核心改造**：**源数据源替换**——oracle 改 `stories.yaml` 的 AC（四级降级链保留，external pointer 裁剪）；live 证据改 `sprint.yaml` 的 `test_refs` + evidence 台账 + test-plan `status`（**替代**源 `live-verification-results.json` 与 `source_sha` HEAD 匹配，不做 sha 比对）。**NFR 不另立门**（并入同一门决策：域 FAIL → 门 FAIL 且 security 不可豁免；UNKNOWN 阈值 → 域 CONCERNS → 门至少 CONCERNS）。**覆盖率口径拉满**（2026-09-15 用户裁定）：P0 / overall / P1 **三线全 100%**，无中间档（源 overall≥80% / P1≥90%）。**两组判据拆分**：`hard_criteria`（一票否决：三线 100% + `mutation_score` ≥90% + NFR critical=0 + P0 零用例=0）与 `soft_criteria`（业务规则/边界/负面场景覆盖、覆盖深度、有效用例占比、ID 链可解析率——任一 fail → CONCERNS）。**A1 连带消解**：源 live-only overlay 不落地（diy 台账即真源），压档会误伤的假 FAIL 随删 `[B]` 一并消失。裁剪：去重测试库存、门合格机制、机器可读双 JSON、人读报告模板、上游回写 story 段、四域子代理编排。**B4 后回接：无**。

### 2.3 diy-test-framework

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | framework 5 步（steps-c 6 文件 + 1098 行 hook 脚本）+ ci 4 步（5 文件 + 五平台模板）→ 6 文件（01 detect + 冲突/附加门 → 02 选型 → 03 脚手架 → 04 流水线 → 05 冒烟自检 → 06 台账 + 终门 + 路由） |
| 源 menu → diy 分支 | C/R/V/E 菜单 → Create/Update + 重入；`mode: framework / ci / both` 三段路由 |
| 门禁 | 项目清单探测（**五清单为示例、非封闭枚举**，任一命中即过门；不可解析 → warning 不拒）；冲突框架未确认替换 → 拒绝（引擎不删不覆盖既有文件）；ci 模式附加门（就绪凭据两条：本技能脚手架在场 / detect 报出既有框架） |
| ID 链 | TF-###；`static_check_alignment[].order` 引用 test-plan 的 `static_checks`（**以 order 引用、禁抄录命令**）；`files[].path` 形态对齐 correct-course `path:` 口径（相对、正斜杠、无 `.` `..`） |
| viewer | 通用降级 rc=0；test-framework 枚举缺口见 §八 |

**核心改造**：**产物双面**——台账 `test-framework.yaml`（可审、可被下游引用）+ 项目文件（脚手架与 CI 配置）。**模板渲染协议**：唯一模板来源（技能内 `templates/` 45 份，覆盖 detect 清单可识别的栈；无模板覆盖 → HALT + 登记，**禁 LLM 手写冒充**）；逐字节复制 + 封闭占位符替换；渲染确定性（不注入时间戳/随机/环境值，同模板同 plan → 同字节）；**幂等重入靠内容等价**（同 plan 二次运行全 skip），目标冲突 → 删除本次已写文件回滚 + 整条拒绝（`FILE_CONFLICT`）。**CI 三方对齐**：路径形态 / `static_checks` blocking 层命令出现在 CI（匹配键 = `tool` 整串 + 边界判定，挡 `npm run lint` 误配 `lint:fix`）/ 阈值注入一致性（`ci.gates` 字面量须现于 CI 文本）——`check` 现场重算，台账记录仅为留痕（`CI_MISALIGNED`）。**注入防护**：`${{ inputs.* }}` 严禁直接进 `run:`（DATA-not-COMMAND），新码 `UNSAFE_INJECTION` 补扫生成物。裁剪：59 knowledge fragment + `tea-index.csv`、写时 hook（`tea-enforce.cjs`）、进度 md、私有库脚手架、子代理编排、mobile 面（A5 裁定）、circle-ci（走 conflict 转用户确认）。**B4 后回接：无**。

### 2.4 diy-test-review

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 4 逻辑步（steps-c 11 文件）→ 5 文件（01 scope + scan → 02 规则集 + baseline 解读 → 03 逐文件评估 + 三向走查 → 04 账本计算 → 05 报告 + 终门） |
| 源 menu → diy 分支 | 人设 / tri-modal / steps-e / steps-v 裁剪；diy 单线（scope 三形态：路径集 / 目录 / 全库） |
| 门禁 | 测试文件在场（scope 内 ≥1 个，否则 HALT——源「无测试文件 → Halt」保留）；文件格式无对应规则 → `excluded`（不评分）；walkthrough 三源不满足 → 降级不阻塞主体 |
| ID 链 | RV-###；finding 的 `row` ∈ 有效 32 行（`disabled` 行 C 组 M9/M10/L9 不得出现）；`coverage_gaps.route` 建议路由（非自动调用） |
| viewer | 通用降级 rc=0；test-review 枚举缺口见 §八 |

**核心改造**：**评分账本全部沉到引擎**（源文自述有 CLI 双向校验）：LLM 只产 findings（规则命中 + 位置 + 说明，**severity 不由 LLM 填**），引擎复算 severity（convention 行按 `class` 降档）、按 `file:location:row` 去重（文件级行 H5/H6/H7/H8/L4 以 `file` 取代行号）、算分（`deductions = CRITICAL*10 + HIGH*5 + MEDIUM*2 + LOW*1`，bonus 六类 0/5 上限 30，clamp 0–100，分档 A–F）并推导 recommendation（带 bonus 矛盾复核）。**convention baseline 7 key**（源 8 减 `playwrightUtils`）：5 机械键由 `scan` 直出 `{adopted, status}`，`bdd_naming` / `assertion_style` 无机械信号 → LLM 判读（回执标 `judged_by: llm`）。**三向走查层（2026-09-15 用户拍板）**：`walkthrough` 做 AC ↔ 代码 ↔ 测试对账，四类缺口（`no_impl` / `no_test` / `orphan_tc` / `never_run`）落 `coverage_gaps`，**不进 35 规则评分**、逐条给路由；源码面**子进程委派 `diyc.py trace`**（不重写扫描），`orphan_tc` 转记 diyc 的 `UNKNOWN_ID`。**与 diy-review 的边界**写进 Rules：diy-review 审实现代码（L1-L4 + 四类路由），本技能审测试代码（32 规则 → 账本），互不调用。返工补齐：recommendations 排序 + Top 10（R-1）、**convention 引用与实际语料交叉复核**（R-2，堵「谎报 class 多扣分」）、空/极简测试文件扣分（R-3，堵「空 spec 得 100 分」）、pact 上报（R-4）。**B4 后回接：无**。

### 2.5 diy-teach-me-testing

| 维度 | 数据 |
| --- | --- |
| 源 steps → diy | 5 逻辑步（steps-c 12 文件）→ 5 文件（01 init → 02 assess → 03 hub → 04 session → 05 completion） |
| 源 menu → diy 分支 | C/E/V 三模式 + 人设 + Advanced Elicitation / Party Mode 裁剪；diy 入口按**判定映射表**分流（进度不存在 → init；画像未采集 → assess；未满 7 节 → hub；7/7 未出摘要 → completion；已出摘要 → hub 完成态） |
| 门禁 | 进度文件已存在 → 强制 resume（不得跳检查）；quiz <70% → 停下让用户选（复习 / 带分继续）；`--final` 三条件（7/7 + `summary.generated` + summary 文件在场） |
| ID 链 | **无独立 ID**——session 整数 1-7 即键（与 `curriculum.yaml` 对齐）；notes 路径相对 `{output_dir}` 且须归属 `notes/` |
| viewer | 通用降级 rc=0；learning-progress 枚举缺口见 §八 |

**核心改造**：**定义态 / 运行态分离**——课程结构落技能内静态资产（`curriculum.yaml` 7 节 + learning_paths + roles 适配 + completion 门槛；`quiz-questions.yaml` 题面/答案/解析静态固化，禁运行时生成），学员进度落 `{output_dir}/learning-progress.yaml`；两者以 session id 对齐、**禁混为一文件**。**派生三式引擎写**（`sessions_completed` = status 计数；`completion_percentage = floor(completed*100/7+0.5)`；`next_recommended` = 最小未完成 id），LLM 不得手写（不符 → `SET_MISMATCH`）。**单一写通道**：`update` 三形态互斥（`--session` / `--learner` / `--summary`），落盘即重算三式。**教学内容落 md 例外**（`notes/session-<NN>.md`，五件事写死：目录创建归 `init`、路径相对 output_dir、固定命名、重做覆盖、**notes 不进渲染面**）；完成摘要 `completion-summary.md` 为第二个 md 落点。**加性偏离两处**（均追认并补录规格）：`init --recover`（T-6：进度文件损坏 → 先备份 `*.corrupt-<时间戳>.bak` 再重建；文件可用时带它也拒）与 `update --session [--topics N]`（A8：否则 session 7 完成判据与 `--final` **永不可达**）。**覆盖目标口径**（P-2 裁定）：**全 100% 不区分**（不按优先级递减）。裁剪：`tea-resources-index.yaml`（483 行）、S7 硬编码 `score: 100`、`stepsCompleted` 类第二套断点位、平均分 ÷7、Web-Browsing 兜底。**B4 后回接：无**。

## 三、批级裁定摘要（A1–A9 + 返工 + 追认）

**A1–A9 九项全部闭合**（2026-09-18，明细见 `work/pending-decisions.md`）：

| # | 问题 | 裁定与落地 |
| --- | --- | --- |
| A1 | `diyc green` 强制 red/green 非空 → `[B]` 直出即 pass 无红相来源、下游假 FAIL | **删 `[B]` post-code 模式**（根治：无 `[B]` 即无红相缺口）；连带见 §2.1 |
| A2 | 源「仅 live 证据」压档 CONCERNS | **不压档**；warning 改「摊事实」（带 `technique`、去伪判定措辞）——引擎分不出那条 pass 是谁写的，替读者摊事实不替读者下结论 |
| A3 | 引擎形态不一致（仅 gate 拆 3 模块，其余单文件超 800 行） | **接受现状不改**（`<800` 是全局标准，本轮明确不管到技能引擎） |
| A4 | `p1_coverage` / `p0_coverage` 空档取值无 n/a 枚举 | **只修枚举、不改行为**：判据 `actual` 补 `n/a`（两取值各有出处，都不动） |
| A5 | mobile 面无模板 → HALT | **永久裁剪**：保留探测、走 HALT（零产出）；SKILL.md 不动 |
| A6 | `check --final` 自加「须 `status: final`」 | **保留 + 补录进 §6**（终门语义的必要条件） |
| A7 | `dimensions` 自洽校验纳入 check | **保留**（= §6 check 首项「报告 schema / 枚举」本身） |
| A8 | schema 要 `topics_explored` 但命令面无写通道 | **追认 `--topics N`**（**全批唯一加性偏离**）+ 补录进 §7 |
| A9 | check 面自加 7 条超集自洽规则 | **保留 + 补录进 §6**（1–6 = schema 自检本身；第 7 条 = 终门前提） |

**判别法（防越权闸，A6/A7/A9 共用）**：一条自加规则若**能从规格已写的内容推出**，是对规格的**执行**；推不出才是**加码**。

**返工中另行闭合**：N-1 **A1 漂移**——`curriculum.yaml` + `quiz-questions.yaml` 4 处仍在教已删除的 `[A]/[B]` 双模式（已修 + 加守卫测试；主 agent 松模式全扫技能/测试/docs 三面 → 零残留）；N-2 **cypress `supportFile` 悬空**——config 引用 `support/e2e.ts` 而技能内无该模板（已补模板 + 落点条文 + 守卫测试「config 引用 ↔ 模板在场」绑死）；N-3 **`convention_baseline` 整块省略可过 `--final`**（已修：缺失即违例，与「未采样」不可区分）。

**追认 5 项**：P-1 teach `--recover`（见 §2.5）· P-2 teach 覆盖目标「全 100% 不区分」· P-3 framework 三处纯加性引擎变更（`UNSAFE_INJECTION` 码 / `FILE_KINDS` 增 `doc` / `detect` 回执增 `git` + `context`）· P-4 gate 4 新码 + 回执子键（`check --final` 义务变严：五标准合规行必填，`draft` 不受影响）· P-5 author 10 新码（`audit` 行为变严）。

**三条「未完成」有理由（非偷工）**：F-1 在 **Jenkins**（无声明式缓存原语，源本身也只 GHA/GitLab 有 → 模板注释 + `docs/ci.md` + steps 三处写明由 agent 工作区保留承担）· F-7/F-11 在 **Harness**（无 `upload/download-artifact` 同级原语 → 聚合面在平台执行页，`docs/ci.md` 记明）· F-12 不扫 Jenkins Groovy `sh "${params.X}"`（文本层无法区分注入与安全 → 按源 steps-v 口径只扫 YAML 表达式 + Harness `<+input>` 族）。

## 四、V 独立验证结论

**能力清点（§11 前半）判定：FAIL —— 丢失 32 / 裁剪 63 / 已迁 92**（口径 = 用户裁定的「能力零丢失」：源里有、规格未明裁、diy 里没有 ⇒ 丢失）。

| 技能 | 源 | 丢失 | 裁剪 | 已迁 |
| --- | --- | --- | --- | --- |
| diy-test-author | atdd + automate | 6 | 18 | 7 |
| diy-test-gate | trace + nfr | 4 | 15 类 | 24 |
| diy-test-framework | framework + ci | 12 | 9 | 19 |
| diy-test-review | test-review | **4（含 1 功能性缺陷）** | 9 | 22 |
| diy-teach-me-testing | teach-me-testing | **6（含 1 死锁缺陷）** | 12 | 20 |

**根因留档（两条线从未被区分）**：§二 13 项验收谈的是**形态迁移**（「不是复制文件」）→ 全达标 = PASS；§11 能力清点谈的是**能力迁移** → 判据空缺 → 32 条 = FAIL。本次「32 条全补」即把这条线**画死**。

**用户裁定（2026-09-18）**：32 条全部处置——**甲 2 修**（A-1 P0-P3 标签、A-2 确定性隔离是规格明写却未落地 = 执行漏项）· **乙 2 修**（R-2 反捏造只说一半、T-6 进度损坏死锁）· **丙 28 收**（规格没说、源有 diy 无 → 逐条补入实物）。

**返工落地**：32/32 全部找到落点（文件:行），新增 15 个违规码、**零 schema 扩、零 CLI 改**（回执只加子键），测试 **120 → 168**。

**V 终审计（§11 后半）**：母本片段逐字比对 ✅（5 用例绿，**且先完成 5 技能登记**，反面验证确认真被检查）· 门禁路径实测 ✅ 646 用例全绿（当时值）· 三技能边界声明互不矛盾 ✅（并发现 `diy-augment` 自身无边界声明，已记）· CI 三方对齐 ✅（`check_ci_alignment` 实现齐 + 用例 10/11/12 覆盖三条判据）· 评分账本数值口径与源文一致 ✅（severity 权重 / convention 降档 / bonus 三处零漂移）。

**复验**：一轮，**通过**（2026-09-18）——各技能测试绿、全库 694 用例绿、母本零漂移、A1 漂移零残留。

## 五、主 agent 集成验证（2026-09-19）

| 项 | 命令/方式 | 结果 |
| --- | --- | --- |
| 注册（验收 #5） | `bash diy-coder/sync.sh` | 已安装 **32 个 skill**（27 存量 + 5 本批）；5 新技能**源树/副本逐文件聚合 md5 一致**（`9b736597…`/`8a8073c1…`/`4d4b3224…`/`750494c2…`/`41e9a3c4…`） |
| 全量回归 | `cd diy-coder && python -m unittest discover -s tests` | **Ran 694 tests OK**（本批 5 技能 168：30/43/33/33/29；54 subtests） |
| 渲染（#6） | viewer.py 探针（4 类型样例 → temp 项目真跑） | rc=0，`rendered 4 doc(s)` + index，未识别类型不崩；缺口清单见 §八 |
| 母本一致性 | `tests/test_suite_texts.py` | 5 用例绿（5 技能已登记三面） |

> 边界声明：本节为主 agent 自测数据；§四 由 V 本人事实核对（其脚本/实测面）。

## 六、验收 13 项对照（迁移计划 §二）

| # | 验收项 | 证据 | 判定 |
| --- | --- | --- | --- |
| 1 | 薄主文件（四段）+ steps/ 厚子文件 | 5 份 SKILL.md 56–90 行；steps 5–6 文件 | 通过 |
| 2 | 产物 YAML schema + 稳定 ID 前缀 | TG / TF / RV；author 无 YAML（TC 由 test-plan 承载）；teach 以 session 编号为键 | 通过 |
| 3 | 前置门禁（零产出 + 路由） | 各技能门禁用例 + 拒绝路径零产出 | 通过 |
| 4 | ID 链接入 | 上游 S/AC/TC/FR 全解析（gate/review/framework 委派 diyc；本产物 ID 稳定） | 通过 |
| 5 | 注册 | `sync.sh` → 32 技能，5 新技能源/副本 md5 全一致 | 通过 |
| 6 | viewer 渲染 | 4 类型通用降级 rc=0；标签缺口清单入 §八（C 阶段输入） | 通过（降级） |
| 7 | 冒烟 TC | 168 条新用例，全量 694 绿 | 通过 |
| 8 | 登记元数据 | frontmatter 5/5 与任务书 §2.1 表一致（V 复验） | 通过 |
| 9 | 读取成本纪律 | On Activation + Workflow 双处「一次一 step 文件」 | 通过 |
| 10 | 双源输入声明 | **N/A**——本批 5 技能均非主线/WDS 交汇点 | 不适用 |
| 11 | 渲染静默 | 各 Workflow 仅命令一行；**W1 无渲染步骤**（Rules 写明理由） | 通过 |
| 12 | diyc 接线（a-e） | a 实例委托（5/5 母本句）；b 终门（各引擎 `check`/`audit --final`）；c `--previous`（5/5 记账不实现——追加式台账无 ID 收缩面）；d 语言绑定（母本 §3）；e Rules 写权边界 | 通过 |
| 13 | 副作用纪律 | framework 自动化档（依赖安装/测试/`chmod` 直接执行 → 台账 `checks`）+ 保留确认档（hook 合并 → `defer-add` 入队，`reason: user-config`） | 通过 |

## 七、非阻断观察清单

| # | 技能 | 观察 | 严重度 | 处置 |
| --- | --- | --- | --- | --- |
| O1 | diy-test-gate | 引擎拆 3 模块、其余 4 技能单文件 961–1778 行（超全局 `<800` 线） | 低 | **用户已裁：接受现状不改**（A3） |
| O2 | diy-test-framework | mobile 面无模板 → HALT（零产出） | 低 | **用户已裁：永久裁剪**（A5），保留探测 |
| O3 | diy-test-framework | F-1 / F-7 / F-11 三条在 Jenkins / Harness 无同级原语（见 §三 末） | 低 | 模板注释 + `docs/ci.md` 记明，不修 |
| O4 | diy-test-framework | `install.py` `copytree` 不过滤 `__pycache__`（B2 既有缺陷）——本批 3 技能含 `scripts/__pycache__` | 极低 | 沿用 B2 裁定：排 C 阶段一并处理 |
| O5 | diy-augment | 自身无边界声明（三技能边界对账时发现） | 低 | 记录不修（B4 存量改造面） |
| O6 | diy-test-gate | `mutation_score` 的「关键路径 100%」承载字段待 C 阶段 report schema 定义（B3 期记 warning） | 低 | 已排 C，记录不修 |
| O7 | diy-teach-me-testing | quiz 通过线按算式为准（3 题须全对，2/3=67 未达线）——源文例句与算式自相矛盾，diy 取算式 | 极低 | 已裁并记（SS-001-69） |

## 八、viewer 标签缺口清单（**C 阶段输入**，SS-001-86）

4 个新产物类型全部走**通用降级**（rc=0、逐页渲染、不崩）；缺口实测 = temp 项目样例渲染 + 映射表核对（`viewer.py` 的 `DOC_LABELS` / `KEY_LABELS` / `VALUE_LABELS` / `ENUM_KEYS` / `BADGE_CLASSES`）：

| 类型 | 文档名标签 | 枚举值缺口（有 stderr 告警） | **静默枚举字段**（key 不在 `ENUM_KEYS` → 不映射也不告警） | key 标签缺口（英文直出，示例） |
| --- | --- | --- | --- | --- |
| test-gate | 缺（页标题 / 导航出英文名） | `PASS`/`CONCERNS`/`FAIL`（status 与 decision）、`P0`–`P2`（badge 无配色）、`stories`/`synthetic`（source） | `confidence` / `coverage`（FULL 等 5 值）/ `overall_risk` / `result` / `kind` / `scope` | `actual` / `basis` / `covered` / `rows` / `pct` / `target` / `tests` |
| test-framework | 缺 | `frontend`/`backend`/`fullstack`/`mobile`（type） | `mode` / `kind` / `action` / `result` / `platform`（含 6 值）/ `in_ci` | `command` / `stages` / `runner` / `language` / `package_manager` / `p0` / `p1` |
| test-review | 缺 | `established`/`emerging`/`absent`/`unknown`（status 与 class，**badge 无配色**）、`CRITICAL`–`LOW`（severity）、`diy-*`/`user`（route）、`full`/`partial`/`skipped`（walkthrough.status） | `basis` / `grade` / `recommendation` / `kind` / `reason` | `adopted` / `corpus_size` / `sampled` / `files_reviewed` / `row` / `line` / `paths` / `score` |
| learning-progress | 缺 | `not-started` / `completed`（badge 无配色）、`in-progress` 已有 | `role`（QA/Dev/Lead/VP）/ `generated` | `assessed` / `experience` / `sessions_completed` / `completion_percentage` / `next_recommended` / `duration_min` / `topics_explored` |

**实测 stderr 原始诊断**（8 条 `[diy-viewer] unmapped enum:`）：`completed` / `frontend` / `stories` / `established` / `emerging` / `CRITICAL` / `diy-test-author` / `full`。

**处置口径**：共享文件（`viewer.py`）改动统一排 **C 阶段**（与 B1/B2 标签缺口同批处理，避免逐批 churn）；本清单即 C 阶段的启动输入。

## 九、审阅指引（B3 为**非强制人工审**）

B2–B7 批按计划 §五只出报告。若你要抽查，建议顺序：

1. **§三 裁定摘要** —— A1–A9 九项 + 32 条能力返工怎么裁的，3 分钟扫完。
2. **§四 V 结论** —— 能力清点 32 丢失 → 全补；V 复验通过。
3. **§八 标签缺口** —— C 阶段输入，确认口径。
4. 抽 1 个技能的 SKILL.md（56–90 行）确认四段结构与写权边界；`diy-test-author` 的**零写面**与 `diy-test-framework` 的**写盘声明**最值得看。
5. 抽一个引擎冒烟：`python diy-coder/skills/<技能>/scripts/<引擎>.py check --final --project-root . --output-dir diy-output --json`（产物不存在时应回 `MISSING_FILE` rc=1）。
