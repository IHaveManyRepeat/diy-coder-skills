# C·3a 批保真度报告 —— WDS 全链可用 ＋ 架构技能升级（6 技能改造 + runner 分线编排）

- 批次：C 阶段第 3 项（**C·3b 已并入本批**：两透镜 → W4 · `diy-architecture` → W9）｜ 完成日期：2026-09-28 ｜ 编制：主 agent
- 任务书：`diy-coder/.analysis/2026-09-22-migration-c3/taskbook-c3a.md`（**22 裁定 / 6 技能 / W1–W9 / 验收 20 项 / 三段串行**；第六轮修正版，含 §0.2d 用户全修授权）
- 基线：HEAD `a1c0469`（C·11 收口，**1397 passed / 173 subtests**）→ 段1 **1442 / 192** → 段2 **1522 / 192** → 段3 **1568 / 231** → 跨轮补丁 **1573 / 235**（V-H）→ **收口态 1575**
  - 取数：段1 `v-reports-seg1-rework.md:22` · 段2 `v-reports-seg2-rework.md:279` · 段3 `v-reports-seg3-rework.md:252` · 补丁后 `v-reports-seg3-final.md:24/:158` · 收口态本报告实测 `pytest tests/ --collect-only -q` = **1575 tests collected**（差额 +2 = 收口链④ 的 viewer 标签用例：`tests/test_viewer_labels.py` **+89 行 / 2 用例**，mtime 09-28 04:46，`git diff -U0 | grep -c "^+    def test_"` = 2）
- 本批改动：**55 tracked 文件 +3171 / −559 ＋ 10 未跟踪**（3 新目录 + 7 新测试文件；`git status --short` = 65 项 = 55 `M` + 10 `??`）——工作树**未提交**
- 改造对象：`diy-design` · `diy-dev` · `diy-review` · `diy-wds-evolution` · `diy-wds-assets` · `diy-architecture` ＋ **`runner.py`（非技能）** ＋ 收口面 `viewer.py` / `registry.yaml` / `help.py` / `diyc_lib.py`
- 三处特殊：① **三段串行 · 十工位**（段1 W1/W2 → 段2 W3/W4/W5/W8/W9 → 段3 W6/W7，段间硬依赖）——与 B 阶段「新建技能」批形态不同，本批重心是**「增补什么 + 保住什么」**（任务书开篇）；② **「不得静默降级」是贯穿全批红线**（裁定 21 / §5b #3b），而独立 V 在**同一族失效**上三次命中（§八）；③ **多工位并行写同一工作树** → 收口链③ 全量测试必须等全部停笔后串行跑（机制见 §七.2①）

## 一、批次结果总览

| 段 | 工位 | 面 | 交付（**现测取数**） | 自测 |
| --- | --- | --- | --- | ---: |
| 1 | W1 | `diy-design` 主文件 / 步骤层 / 数据层 | `SKILL.md` 93→**104** · `steps/` **10 件 619 行** · `data/object-types/` **5 件 532 行**（源 1,689 行改写）· `test_design_skill.py` **296 行 / 26 用例** | 面内 72 passed / 19 subtests |
| 1 | W2 | `diy-design/scripts/design.py` 引擎 | **473 → 1162** 行 · `test_design.py` 347→**523**（18 用例）· `test_design_transition.py` **474**（20 用例） | 面内 31 passed |
| 2 | W3 | `diy-dev` WDS 模式 | `SKILL.md` 73→**88**（贴线）· 新增 `steps/wds-*.md` × **5 件 221 行 / 19 小节** · `test_diy_dev_wds.py` **426 行 / 22 用例** | 22 passed |
| 2 | W4 | `diy-review` WDS 审查 + 两透镜 | `SKILL.md` 83→**91**（硬锁 93）· `test_diy_review_wds.py` **415 行 / 24 用例** | 24 passed |
| 2 | W5 | `diy-wds-evolution` 边界改写 | **+5 / −5 行（3 文件）**，`SKILL.md` 88 · 引擎 625 行 · 46 用例**改前=改后** | 46 passed |
| 2 | W8 | `diy-wds-assets` 产出直出 | 16 文件 · `SKILL.md` 89（未变）· 引擎 **836 行**（+3/−2，仅 docstring）· 测试 **+197/−0**（61 既有零删改 + 7 新增 = 68 用例） | 68 passed |
| 2 | W9 | `diy-architecture` 升级 + 引擎 SC/P 域 | `SKILL.md` 87→**93** · `diyc_check_docs.py` 705→**751** · `test_diyc_check.py` **+81/−0**（42→47 用例）· `test_diy_architecture.py` **265 行 / 20 用例** | 67 passed |
| 3 | W6 | `runner.py` 分线编排 | **428 → 848** 行（+462/−42）· `test_runner.py` **1563 行 / 57 用例**（既有 27 条零删改 + 新增 30 = 21 + 返工 4 + 跨轮补丁 5） | 48 passed / 36 subtests |
| 3 | W7 | 跨工位测试 | `test_design_wds.py` **675 行 / 14 用例** · `test_design_open_questions.py` **382 行 / 6 用例** | 20 passed / 33 subtests |
| 3 | 补漏 | `design_intent: L` 落点 + 守卫 | `SKILL.md:34` 同行补 `L` 处置（`SKILL.md` 仍 104）· `test_design_skill.py:142` 新守卫 | 变异 → RED |
| 收口 | 主 agent | ④ viewer / ⑦ registry / ⑨ diy-help / `diyc_lib.py` | `viewer.py` 1631→**1648**（+17 行）· `registry.yaml` `exec: diy-dev` + `exec_note: ""` · `help.py` +2/−1 · `diyc_lib.py` 并入 `wds-scenarios`（+5 行） | 见 §五 |

**全批既有断言改动面**：`test_restore.py` **3 行**（越界，已裁定接受，§七.5）· `test_design.py` 断言改名 14 行（§2.4 授权）· `test_runner.py` 1 处用例 **3 处**改写（V-H 反演核验，§四）· `test_suite_texts.py` +10/−1（登记面）——其余全部为本批新增用例。

**红线**：`0wds-` 本批文件面 **0 命中**（V-G 实测 6 物理行 / 5 逻辑位置全在源侧与 B7a 面）· `compare` 未复活 · 无技能教 `check --type design --previous` · 平台耦合词 `runner.py` / `test_runner.py` **0 命中**。

## 二、逐段销账

### 2.1 段1 · W1（`diy-design` 主文件 + 步骤层 + 数据层）

**核心交付**：双源输入判定（`SKILL.md:24-25`，缺源零产出）· 九活动吸收（`steps/` 10 件）· 原型循环 `steps/prototype-loop.md` · 场景桥 `steps/scenario-bridge.md` · `bmad-ux` 并入 · `pages[].status` + `open_questions` + `token_scope` · 源侧缺陷台账 47 条逐条落定（`w1-defect-ledger.md`：断链 13 / 幽灵 8 / 冗余 12 / 孤儿 14）。
**关键实测**：§4 锚串（`ANCHOR_READ_DISCIPLINE`）为本批**唯一新增锚串**，段1/段2 前置登记进 `LANDED_READ_DISCIPLINE`（`test_suite_texts.py:184-193`，含 `design`/`dev`/`review` 三名预登记注释）；主文件点名的 `steps/*.md` 集合 == 磁盘实况（10/10，机械断言 `test_design_skill.py`）。
**台账定性纪律**：裁定 12 的 8 条幽灵判定中 **3 条经跨技能复核改判为误判（3/8）**——误判只影响定性、不影响落点（`w1-defect-ledger.md:50`）。

### 2.2 段1 · W2（`design.py` 引擎）

**销账**：四命令回执归一为 `{ok,command,violations[{code,where,msg}],warnings,counts,file}`（单行 JSON，exit 0/1/2）· `transition` 9 合法边 + 4 非法边 + 6 复用码 + 新建 `GATE_FAILED` · `--previous` 双挂 `validate`/`check` · `.prev` 快照 + `ID_UNSTABLE` 对账 · `token_scope` · `open_questions` · `check` 维度 3 → **8**。
**保真实测**：既有三维（`contrast` / `color-only-signal` / `semantic-html`）**code 与 msg 逐字不变**（V2 对拍 9/9 SAME + V4 复验重跑）· 命令专有键全保（`checked.contrast_pairs` 5 对 / `has_frontend` / `skipped` / `audited`）。
**有意偏离 5 条**（`malformed`→`UNPARSABLE_YAML` · `--previous` 双挂 · 越界改 `test_restore.py` · `--instance` 非法值 1→2 · `--to` 表外值走 argparse exit 2）+ **1 条未申报偏离**（破坏性边实为 4 条 vs §2.5 冻结表 2 条，V3 M2）。M2 **未返工**（V4 复核：实现判据 `design.py:1093` = `dst == "已移除" or (src,dst)==("已批准","结构稿中")` = 4 条，与 `SKILL.md:86` 自洽）——**由本报告按裁定 14 口径登记为 4 条，并注明 §2.5 表注不全**（V4 建议，见 §三.1）。

### 2.3 段2 · W3（`diy-dev` WDS 模式）

双模式分支（门禁 `design.yaml` 的 `project.status: 已定稿` 单一判据，无「或」）· 目标页 = `结构稿中` 首条 · 回填**一律经 `transition`** · **浏览器强制门 good↔bad 两轮实跑**（9/9 判据命中；删两变体 → 3 条未过 → 回修 → 3/3 通过）· 裁定 21 三情形（安装后重跑 / 用户同意跳过 / 未问即跳过=违规）。
**偏离 5 条**（新增第 5 个 step 文件 `wds-fix.md` · `# trace:` 的 WDS 形态 · `[T]` 判据分类取 `HP/REG/EC/A11Y` · 门禁路由细化 · 浏览器门改用本地 HTTP（`file://` 被 Playwright 策略拦截））——最后一条 V-A 判为**文档未提示**的 steer 缺失（中-4），**R2 返工已补进两处门文档**（`diy-dev/steps/wds-self-verify.md:12` + `diy-design/steps/prototype-loop.md:50`，均写明「须起本地静态服务；该拦截不算环境不可用」），V-D 复核「双向点名且同向」。

### 2.4 段2 · W4（`diy-review` WDS 审查 + 两透镜）

**不拆 `steps/`**（91 ≤ 93 硬锁，见 §七.7）· 两透镜三项接口事逐条落（映射表 / 格式归一 / HALT 对齐）· **判决不代用户批准三重机制**（文本禁令 + 全文不教 `--to 已批准` 的 `assertNotIn` 机械锁 + 说明引擎不辨触发者）· `ds-token-*` 三维纳入 L4 (d)（实跑三码真报）· #4b WDS 路由落点表四类齐。
**保真**：主线入口 `MISSING_FILE` 拒绝 / WDS 入口 rc=0 对照实跑；同一 `design.yaml` 双入口行为分离。

### 2.5 段2 · W5（`diy-wds-evolution` 边界改写）

**行为零变化**：引擎 625 行 / 46 用例 / 小节数 4-5-5-5-5-3 全未变（`git diff` 为空）· 失效条件句一律**替换为现状陈述**，不新增承诺 · 对端句清单 5 行（sha1 快照）。
**★ 诊断（本批最有价值的机制发现之一）**：并发假红的成因 = `diyc_mutate.py:56-66` 的 `_git_dirty` 在 fixture 目录里跑 `git status --porcelain`，**拿到全仓脏度**（实测 32 行 = 全仓）→「未提交 + 多工位并行写」必随机红（§七.2①）。

### 2.6 段2 · W8（`diy-wds-assets` 产出直出）

**8 处「提示词导出 = 唯一生成通道」假陈述连根拔**（§5.8 列 7 处 + 自查扩面第 8 处 = 引擎 `:15` docstring），全树断言固化（该类措辞技能树内 0 命中）· **零行为改动**（`exported` 翻转机制与终门判定原样，模板位清单 94 条与 HEAD 集合相等）· 8 活动直出实跑（`counts={activities:8, items:9, prompts:1, exported:1, presentation:1}`，`check --final` rc=0）· **M 图片两路**实测（插画 → SVG 直出；照片 → `prompts/AS-05.2.md`，`assets[]` 留空 = 合法）。
**C 文案定为直出成稿 `.md`**（超出 §5.8 表「维持现状」字面，属**加项/收敛**，登记）

### 2.7 段2 · W9（`diy-architecture` 升级 + 引擎 SC/P 域）

**裁定 22**：`affects` 值域扩 `SC-<nn>` / `SC-<nn>.P<n>`（**扩展非替换**，`FR-x.y | NFR-x` 保留）；**接入前后对照**：接入前该域**要么误拒（prd 可解析）要么漏检（prd 缺席时伪造 `SC-99` 可过终门 = 假过）**，接入后两方向都正确 · 双源**四情形**实跑（含两源俱缺 → 无产物 + `MISSING_FILE`）· 可测性 / 运维两维落规则 7（**零新增产物键**，结构段顶层键集合改前改后 diff 为空）。
**偏离**：`DOC_FILES` 就地 `setdefault("wds-scenarios")` → **收口期正式并入 `diyc_lib.py:50` 并删本地注册**（本报告实测已落地：`diyc_lib.py` +5 行，注释含「两处真相 → 归位」）。

### 2.8 段3 · W6（`runner.py` 分线编排 + 无头集成）

**主线保真五面逐字节**（对同构夹具 12 场景 × rc/stdout/stderr/桩调用序列/写回文件 md5 全同；两条主线提示词 10 组参数逐字节相同）· **WDS 线**：`--line {mainline,wds}`（缺省 mainline，**不做自动探测**）· 链 = `diy-dev` WDS 模式 → `diy-review` WDS 路径（两次 spawn 真点名，不沿用 `diy-build-loop`）· 审查通过后页**仍 `待验收`**、只报「待用户批准」· runner 对 `design.yaml`/`sprint.yaml` **零写** · 三个「不做」显式拒绝（`--skip-augment` / `--augment-only` / `--reopen-failed` = rc=1 + 零 spawn + 教学句）· 并发锁 `O_EXCL`（24 进程竞争恰 1 胜者）。
**返工 2 轮**（F-1 阻断级 + F-2 + 三条低项 + 跨轮盲区高-1/中-1）——见 §四.2。

### 2.9 段3 · W7（跨工位测试）

§6 八条「需两工位以上合力」断言面全覆盖 · **去重是机械做的**（`ast`/`tokenize` 提取断言内字符串字面量，对 **15 个既有测试文件**子串比对）→ 删 1 条真重复、改写 2 条撞字面、点名 3 条「同字面异对象」保留理由 · 面 7 直接 `import test_suite_texts` 取锚串常量与台账（不复制第二份母本文本）· 6 条变异全部转红并逐字节还原。
**定位越界 8/20 条**（单工位可自测）→ **保留 + 登记**（主 agent 裁定：断言有效、经机械去重确认不重复，删则覆盖真空、移位要动 8 个已定稿测试文件）。

### 2.10 段3 · 补漏与段间订正

- **`design_intent: L` 落点**（收尾补漏）：`SKILL.md:34` 同行补处置（问用户一次，未指定缺省 `[C]`）+ 新守卫 `test_design_skill.py:142`（变异：整行回退 → RED）
- **段2 期间三处跨段订正**（主 agent 裁定后派单，属段1 面）：`design.py:999` `next_hint` 的「待验收 → 进入实现」与 §5.1/§5b 链互斥 → 改「用户批准（人裁，无自动后续步）」· `steps/prototype-loop.md:71` 设计侧抢 `待验收` 写权 → 改会话门 + 点名写者 · `steps/c-discuss.md:47` 笼统句收严点名写者
- **段1 微修轮**：值域守卫**补成双向**（从 `SKILL.md` 规则 1 机械提取反引号值 → 断言 ⊆ 上游枚举；变异注入 `in-progress` → FAILED）——**闭合 H1 的原始失效模式**

## 三、批级裁定与有意收严

### 3.1 裁定与拍板执行摘要

**§0.3 的 22 条裁定 + §0.2/§0.2b/§0.2c/§0.2d 的 13 项用户拍板全部执行，无静默降级**（取数：V-C 段2 逐条判 `v-reports-seg2-global.md:520-548` + V-F 全批 20 项汇总 `v-reports-seg3-global.md:278-309`）。点名五条影响面最大者：

- **裁定 4（2026-09-27 用户改判）**：`object-types` 由「全裁」改「部分保留」——五件模板 1,689 行改写后落 `data/object-types/`（其余 5 件裁），是本批 W1 体量由 700–1,000 扩至 1,300–2,000 行的原因
- **裁定 9**：P0 全并；P1 #8/#9 已升 P0；#11 判「并」；**#7（形态/默认主题）不并 → 进能力损失台账**（§七.1①）；#10 不并本技能（承载方 `diy-wds-system` 实证在场，再持一份即双源）
- **裁定 14/15**：`revisions[]` 只在**两条破坏性边**追加——**实现实测 4 条**（`结构稿中→已移除` / `待验收→已移除` / `已批准→结构稿中` / `已批准→已移除`），V3 M2 判「超集、方向安全、属未申报偏离」、V4 建议收口报告按 4 条登记并注明 §2.5 表注不全（**本报告已登记**，§2.2）+ `.prev` 快照 + `ID_UNSTABLE` 对账
- **裁定 21/16**：浏览器强制门的环境不可用分支 = **停下如实上报 → 用户决定「安装」或「跳过」**（既不静默降级，也不无条件硬停）
- **裁定 22**：`affects` SC/P 域接入 + 引擎 `known` 域扩展（原「回报主 agent」作废，因承接步不存在 = 阻断）

### 3.2 ★ 有意收严 + 迁移口径（**存量 `design.yaml` 可能由绿转红**）

`check` 新增 5 维（`a11y-touch-target` / `a11y-keyboard` / `ds-token-color` / `ds-token-font-size` / `ds-token-spacing`，源 `steps-h/step-03:96-108` 的 3+4 项）——**这是本批对存量产物影响最大的一处**（V2 M-4 判「可能一夜变红」）：

- **实测（HEAD 版既有夹具对跑）**：原型里字面色值 `#1a1a1a` 不在 `tokens.color` 归一集内 → HEAD `check` exit 0，NEW `exit 1` + `ds-token-color`；W2 为让既有用例通过**改写了既有夹具**，该收严**未在回报偏离清单点名**（V4 复验确认「真收严」）
- **达标路径（本报告实测三态复现，取数 `design.py` 现测）**：① 原型走 `var(--*)` → 三码零报（`collect_ds_violations` 对 `var(` 显式放行）；② 字面值**已在 `tokens.*` 登记** → 零报（`collect_token_hexes:735` / `collect_font_sizes:746` / `collect_spacing_values:484` 归一集命中）；③ 未登记字面值 → `ds-token-color` + `ds-token-font-size` + `ds-token-spacing` 三码齐报
- **★ 豁免面边界**：`token_scope` **只豁免 `audit`、不豁免 `check` 新维度**——`token_scope` 仅在 `cmd_audit` 消费（`design.py:867` 定义 / `:882` `resolve_token_scope` / `:893/:902/:907` 跳过判定），`cmd_check`（`:542`）无 scopes 分支。**「继承外部 UI 系统」的出口对 `check` 不生效**——原型从外部系统照抄字面值时，出口是「把值登记进 `tokens.*`」或「改走 `var(--*)`」，不是 `token_scope`
- **落地提醒**：段2 `diy-review` L4 已纳入 `ds-token-*` 三维（`SKILL.md:40`，实跑三码真报）——否则会出现「实现稿照抄字面色值被 `check` 拦、`review` 却判过」的错配（V2 M-4 建议已落实）

### 3.3 改裁定留痕：2026-09-19「12 个单文件技能不拆 steps」

**本批对 `design` / `dev` 作废**（为吸收 WDS 九活动与原型循环，二者拆出 `steps/` 并补 §4 锚串，已登记进 `LANDED_READ_DISCIPLINE`）；**对 `review` 仍有效**（受 `test_review_contract.py:103/108` 两条硬锁，见 §七.7）。留痕落点 = `tests/test_suite_texts.py:211` `_steppers()` docstring 的「★ 2026-09-28 C·3a 留痕」段（`:220-223`）——**不留痕则后人读 docstring 会误判**。

## 四、独立验证结论（口径「不采信施工方自述」）

### 4.1 V 报告清单与分级

**十二份独立报告**（同目录 `diy-coder/.analysis/2026-09-22-migration-c3/`），**分段命名**：段1 = V1–V4 · 段2 = V-A–V-D · 段3 = V-E–V-H。

| 段 | 报告（轴） | 阻断 / 高 / 中 / 低 | 关键证据 |
| --- | --- | --- | --- |
| 1 | `v-reports-seg1-doc.md`（V1 文档面） | 0 / 0 / **5** / 9 | 锚串逐字 · 路由 10/10 · 保真面七条实证 · 裁定 4 四条逐件落地 |
| 1 | `v-reports-seg1-engine.md`（V2 引擎面） | 0 / 0 / **4** / 6 | 冻结契约逐条实跑成立；既有三维 code+msg 逐字；M-4 = 有意收严 |
| 1 | `v-reports-seg1-cross.md`（V3 交叉账目） | 0 / **1** / 2 / 5 | 全量复跑 1435/192 逐字一致；**H1 = `design_status` 值域无值可写** |
| 1 | `v-reports-seg1-rework.md`（V4 返工复验） | 0 / 0 / 0 / 7 | 五次变异全转红/绿并还原；HEAD vs 现引擎对跑「既有行为 SAME」 |
| 2 | `v-reports-seg2-chain.md`（V-A 交互链） | 0 / **1** / 4 / 6 | 主线保真成立；高-1 = `已移除` 双写者 |
| 2 | `v-reports-seg2-assets.md`（V-B 资产+演进） | 0 / 0 / 4 / 5 | 零行为改动 + 8 处假陈述连根拔**独立复现**；**V-B-03 = W8 报告引文失真** |
| 2 | `v-reports-seg2-global.md`（V-C 全局账目） | 0 / **3** / 7 / 5 | 全量 1521/192 亲跑复现（唯一全量路）；**高-3 = 上游终门与推进权互斥** |
| 2 | `v-reports-seg2-rework.md`（V-D 返工复验） | 0 / 0 / 0 / 4 | 8 项返工逐条真落地；全量 1522/192；两处独立变异证明有牙 |
| 3 | `v-reports-seg3-runner.md`（V-E runner 面） | 0 / **1** / 2 / 4 | 12 场景 × 5 面逐字节全同；**F-1 = 审查环静默降级** |
| 3 | `v-reports-seg3-global.md`（V-F W7+全局） | 0 / **2** / 4 / 5 | 全量 R1 撞偶发红（9 failed）/ R2·R3 连续全绿 1564/228；W7 越界 8/20 |
| 3 | `v-reports-seg3-rework.md`（V-G 返工复验） | 0 / **1** / **1** / 3 | F-1/F-2 真落地 + 8 变异全还原；**高-1 / 中-1 = 跨轮盲区** |
| 3 | `v-reports-seg3-final.md`（V-H 极聚焦复验） | **0 / 0 / 0 / 0** | 四点全过且每条判据有「对上一轮版本转红」的鉴别力自检；全量一次跑绿 1573/235 |

### 4.2 返工四轮 ＋ 微修轮（每一轮均带「改坏 → 转红 → 逐字节还原」自证）

| 轮 | 范围 | 触发 | 复验 |
| --- | --- | --- | --- |
| R1 段1 返工（W1-R / W2-R） | 全部中项 + 三条真缺口（`design_status` 值域 / `--previous` 文档面零出现 / 路径基址二制并立） | V1/V2/V3 | V4：0/0/0/7，判「段1 可收口」 |
| R1′ 段1 微修轮 | 值域守卫补双向 + `k-sketch.md` 补 `design_status` 写句 + 反向相对引用归一 | V4 低项 | 面内 72 passed / 19 subtests |
| R2 段2 返工 | 8 项（`已移除` 写权 / findings 落点 / 跳过留名 / `file://` steer / dev 零目标页 / 软线固化 …） | V-A/V-B/V-C | V-D：0/0/0/4，全量 1522/192 |
| R3 段3 返工 | F-1（按阻断级）+ F-2 + 三条低项 | V-E | V-G：F-1/F-2 真落地、8 次变异全还原、全量 1568/231 |
| R4 段3 跨轮补丁 | **高-1**（未复验页分列 + rc≠0）+ **中-1**（dev 落点对称收紧） | V-G §9 | V-H：四点全过、0/0/0/0、**全量 1573/235 一次跑绿** |

**R4 的相关性**：V-G 明确指出「跨轮区分需不需要加键」是**两件事**——「持久的审查判决」确需加键（撞 §2.3 冻结），但「**不得把审查结论未知的页与真通过页同列呈为可批准**」**零新键、约 5 行可解**；同理 dev 侧越界停手「不是能力边界，本轮可廉价解决」（`v-reports-seg3-rework.md:319-335`）→ 主 agent 由此派单，两条均落地。

### 4.3 收口后状态

V-H 复核三点：① 未复验页**只在待批准行剔除 + 单列警示 + rc=1 + 零 spawn**（对上一轮 runner 同夹具转红，鉴别力成立）；② dev 越界**恰 1 次 dev / 0 次 review** + stderr 点名实际落点；③ `test_runner.py` 3 行改写经**反演申报编辑 → md5 与 V-G 快照逐字节一致**证明「无未申报改动」，且原用途断言逐字仍在。**信息级 1 条**：施工方临时副本（仓库外）差 1 字节/1 行，非施工文件差异。

## 五、主 agent 集成验证（收口链 ①~⑨，**本报告落笔时实测**）

| 步 | 项 | 本报告实测状态 |
| --- | --- | --- |
| ① | `test_suite_texts.py` 台账 | ✓ **本报告亲跑 `tests/test_suite_texts.py + tests/test_viewer_labels.py` = 33 passed**（2026-09-28 05:0x）；49 名全在册（本批无新增技能），`design`/`dev`/`review` 三名前置登记在 `:184-193` |
| ② | `sync.sh` | 收口期执行（本报告不跑——`install.py`/`sync.sh` 属禁改面，且会写安装镜像）；`.claude/skills` 镜像待同步 |
| ③ | 全量测试 | ⚠ **时序前提**：必须等全部工位停笔后**串行**跑（V-F R1 撞 9 failed 假红）；本报告只做 `--collect-only` = **1575**；末次全量亲跑 = V-H **1573 passed / 235 subtests** |
| ④ | `viewer.py` 标签登记 | ✓ **已执行**（`viewer.py:89` 五状态值徽章 · `:148/:150` `token_scope`/`removed_reason` 中文标签 · `:433-434` 值标签；`tests/test_viewer_labels.py` +89 行 / 2 用例）；文件 1631→**1648** 行（+17） |
| ⑤ | 保真度报告 | ✓ 本文件 |
| ⑥ | `迁移计划.md` §二十八 | 由另一路执行（**本报告不越界**；§二十七 为末节，实测 :1032 行） |
| ⑦ | `registry.yaml` | ✓ **已执行**：`exec: diy-dev` + `exec_note: ""`（原「随 C·3 落地，此前链走完即止」已清，注释留痕）；`line: mainline` **未动**（`test_help_registry.py:93-101` 的逐字约束保持） |
| ⑧ | 过期边界句统一订正 | 收口期**执行中**：`diy-wds-brief/SKILL.md:78` 已改写为现状陈述；`diy-wds-scenarios/SKILL.md:4/:42/:61/:70` 与 `diy-wds-system/SKILL.md:71` 仍带「C·3 的 `diy-design`」阶段标记（C·3a 落地后所指技能已存在，非假陈述，但仍是旧标记） |
| ⑨ | `diy-help` WDS 读面 | ✓ **已执行**：`help.py` +2/−1（`wds` 链补 `wds-system(可选) → wds-assets(可选) → wds-evolution(可选) → <exec>`），与 ⑦ 同批 |

## 六、验收对照（任务书 §9，**20 项**）

| 判 | 项 | 证据 |
| --- | --- | --- |
| **过 16** | #1–#4 · #7 · #9–#16 · #18–#20 | V-F 全批汇总（`v-reports-seg3-global.md:282-303`，逐行判）+ V-C 段2 逐条判（`v-reports-seg2-global.md:520-548`）逐项实测；#18 的「双向外加面无技能侧机械门」见 §七.1④ |
| **留后续 4** | #5 注册 · #6 viewer · #8 registry · #17 `diy-help` | 全属主 agent 收口面；**#6/#8/#17 已于收口期执行**（§五 ④⑦⑨），#5 待 `sync.sh`（V-F 实测：`.claude/skills` 的 `diy-*` = 49，但**镜像 STALE**——`diy-design/SKILL.md` src `2b3f9e78` vs mirror `5d86ce34`） |
| **无不过** | — | 无一项判「不过」 |

**★ 口径订正（本报告核对发现）**：V-F 的**合计行写「过 15」**（`v-reports-seg3-global.md:305`，`:366` 与 `w-reports-seg3.md:56` 沿用），但其**自查表逐行判为 16 个「过」**（15 个「**过**」+ #14 一个「**过（本路亲验）**」）+ 4 个「留后续」= 20。**逐行口径正确，合计行低算 1**——后续引用一律按 **过 16 / 留后续 4 / 无不过**。

**V 阶段未实跑面（如实登记）**：裁定 21 两情形（安装后重跑 / 用户同意跳过）与 WDS 线端到端**无真实实例**（全仓零 `wds-scenarios.yaml`，W7 用合成夹具覆盖）——W3 偏离 ⑤ 已登记；`diy-wds-assets` 的「浏览器实开 3 份 HTML」**无留痕可核物**（V-B-02，V 已独立复现该纪律链路，缺的是留档）。

## 七、能力损失与欠账台账（★ 本批必须点名的条目）

### 7.1 能力损失台账（6 条，逐条 + 现处置）

| # | 条目 | 性质 | 现处置 |
| --- | --- | --- | --- |
| ① | **裁定 9 P1 #7「形态 / 默认主题模式」** | 源侧 census P1 #7 的能力在 diy **无承载位**（`direction` 是自由串，落它无机械抓手）；理由句已订正（非「无键可载」） | **维持「不并」+ 进台账**；**备选（落 `direction` 一句）留用户裁定**（`w-reports-seg1.md:68` / `w1-defect-ledger.md:122`） |
| ② | **WDS 线审查 findings 无持久化载体** | 主线落 `sprint.yaml` 任务条目的 `review.findings[]`；WDS 线**无 `sprint.yaml`** + 裁定 14 禁新增键 → 审查结论**只落会话报告**（技术债读面在 WDS 线缺失） | **已裁定维持、登记能力边界**（`w-reports-seg2.md:34`）；文本面已补显式不对称句（`diy-review/SKILL.md:51`：「主线/WDS 不对称……WDS 线只落审查报告与本轮会话（无 YAML 载体）」）——V 中-2 的「假落点」印象已关闭 |
| ③ | **照片类提示词已导出未回填时 `assets[]` 为空** | 照片是「提示词通道」：产物在外部生成后回填，中间态磁盘无实体 | **维持合法**（`w-reports-seg2.md:48`；V-B 实测 `assets/images/prompts/` + `assets[]` 留空 = 合法，`v-reports-seg2-assets.md:123`） |
| ④ | **§5.8 判据②「双向核」无机械门** | 引擎只核路径**形态**、不核文件存在（`assets[]` 指向不存在文件 → `check --final` rc=0）；判据的「牙」只在 `test_wds_assets.py` 的 helper 内 → 对**交付物**的回归保护 ≈ 0 | **接受为「散文纪律 + 能力边界」并登记**（V-B-04 建议 (a)，主 agent 未选改引擎）；`SKILL.md:79` 规则 6 **已诚实声明**「注意（引擎不核的）……由会话双向对表自证」 |
| ⑤ | **runner 的「未复验」区分只在本轮内有效** | R4 的修复把「本轮走完整审查环且通过」与「本轮未复验」**分列**（`wds_summary` 与 `wds_unverified_pages` 的 `unreviewed`/`verified` 双集合，`runner.py:497-542`；V-H 实测 stdout 两行），但**跨轮不可持久区分**：上一轮真通过的页与上一轮崩掉的页同被标「未复验」 | **接受（保守高报，非误报）**：提示语写「未复验」而非「未通过」；持久化需加键、撞 §2.3 冻结 → 登记 |
| ⑥ | **失败页无持久标记（与主线 `已阻塞` 不对称）** | WDS 页状态机（裁定 5 的 5 值 9 边）**无「已阻塞」态** → 重试用尽只 exit 1，`skipped` 仅本进程有效；重跑 = 再烧 1+max_retries 轮（V-E 实测累计 6 次 dev） | **登记**（V-E F-3；`v-reports-seg3-runner.md:276-283`）。**不建议**为 runner 造「已阻塞」（会动冻结词表）；备选出口 = 页级选择器，留后续批 |

> **§11-1 的裁定 7 条目（源侧 Object Registry 对象级双向核对 = 净损失）**另计：本批处置见任务书裁定 13/裁定 4（五件模板改写为参考层 + 全树断言），**非本表六条**；`w1-defect-ledger.md §4` 逐件给落点与证据命令。

### 7.2 跨批欠账（不在本批修）

| # | 条目 | 机制 | 取数 |
| --- | --- | --- | --- |
| ① | **`diyc_mutate.py:56-66` `_git_dirty` 量错对象** | `subprocess.run(["git","status","--porcelain"], cwd=fixture 目录)`——git 自动**上溯到仓库根**，故**拿到全仓脏度**（实测 32 行 = 全仓）→「未提交 + 多工位并行写」**必随机红**。**收口链③ 因此要求停笔后串行跑**（与「`test_diyc_mutate` 的 `WORKSPACE_TOUCHED`」并列的两条「并发/脏树假红」） | V-F 高-2（`v-reports-seg3-global.md:197`）· W5 诊断（`w-reports-seg2.md:40`） |
| ② | **上游 `wds_scenarios.py check --final` 与 `diy-design` 推进权互斥** | `:770` 要求 `design_status` **恰为初值** `not-started`（`:132`），而 C·3a 把推进写权交给 `diy-design`；一旦推进任一档，重跑上游终门必 `STATUS_MISMATCH`（`:772`），且 `:22/:55/:773` 三处文案仍写「归 C·3 的 `diy-design`」 | **一次性门、非活不变式** → **无流程阻断**（V-C 高-3，`:390-404`）；`wds_scenarios.py` 属 B7a 交付面（本批禁改）→ 跨批欠账 |
| ③ | **`wds_assets.py` 在 `activities` 非列表时崩栈** | `activities: "nope"` → `init`/`list`/`show`/`prompts`/`check` 全抛 `AttributeError`，rc=1 且 **stdout 空**（违反自订回执契约） | **预存在缺陷**（HEAD 与工作树逐字同款）→ 跨批欠账（V-B-09） |
| ④ | **`diy-wds-trigger/steps/01-mode.md:32` 的「5 条不存在的文档」措辞** | 其中 2 条在**安装布局** `_bmad/wds/data/agent-guides/saga/` 真实存在（Layer 1 方法本体） | 已由用户 2026-09-27 裁定**单独立项**（`迁移计划.md` §二十七），归 C·7 同批订正 |
| ⑤ | **B7b 遗留中低项**（22 条） | 承 B7a 先例留档、不返工 | 本批**不碰**，收口报告重申即可（§11-5） |

### 7.3 viewer 欠账（2 条；**均只入欠账，不登记为设计边界**）

1. **`assets/<活动>/` 产物渲染不到**：viewer 只渲染 `output_dir` **顶层 YAML**（V-B 实测 `.view/` 仅 3 件，9 份产物零渲染；stderr 已有 C·11 W3 加的一行诊断，`viewer.py` 的 `note` 档）。**口径**：按 C·11 用户裁定（`taskbook-c11.md:60/:154`——viewer 的渲染扩展面转「**需求 ②，另排批**」，**不得**写成「设计边界」销账）→ 本条**只入欠账**，收口④ 的动作面限于标签登记（已执行，§五④）
2. **`pages[].prototype` / `implementation` 渲染成纯文本且被 ID 链接截断 → 不可点**（**既存缺陷，本批新发现**）：二者不在 `ASSET_PATH_FIELDS`（该集合只有 `("wds-assets","path")`，`viewer.py:646`）→ 走 `cell()` → `linkify()` 的 `ID_RE`（`:639` `\b[A-Z]{1,4}-\d+(?:\.\d+)*\b`）在路径串**中间**命中页 ID 并插入链接。**本报告实证**（临时夹具渲染后 HTML 原文）：`prototypes/P-1.html` → `prototypes/<a class="idl" href="design.html#P-1">P-1</a>.html`——路径被 ID 链接截断、指向页锚而非文件，**不可点开产物**；`implementation: src/pages/home.tsx` 无 ID 匹配 → 纯文本。**处置**：登记（不属本批文件面；修法 = 扩 `ASSET_PATH_FIELDS` 或对路径型值跳过 `linkify`）

### 7.4 报告失真点名（纪律案例，**不得被后续文档转引**）

**W8 报告「★ 开工取数」引「任务书 §5.8 口径 = 引擎 820 / 测试 969」——任务书全 5 个版本均无此数**（`grep` + `git log -S` 双证零命中；任务书真实记载引擎 **662** = C·11 前的值）。**结论对**（实测 HEAD 确为 835 / 998，须重测的纪律成立），**引文虚构**——V-B-03 判「中」，处置：**该句不得被后续文档转引；本批行数一律以 `wc -l` 现测为准**。
（同族纪律见 §八：这是「以『没有变化』反推『成功』」的**报告面变体**——「结论对了」不等于「引文为真」。）

### 7.5 越界与登记（3 项）

| # | 事项 | 裁定 |
| --- | --- | --- |
| ① | **W2 越界改 `tests/test_restore.py` 3 行**（自报 4 行，W2-R 实测 `git diff --stat` = 3+/3− 订正） | **接受 + 登记**（该文件无工位认领且不在禁改清单；不改则段1 验收必红）。V-F 复核「仍是同 3 行、无扩大」（`v-reports-seg3-global.md:215`） |
| ② | **W7 定位越界 8/20 条**（单工位可自测） | **保留 + 登记**（断言有效、经机械去重确认不重复；删则覆盖真空、移位要动 8 个已定稿测试文件） |
| ③ | **W2-R 改过 `v-reports-seg1-doc.md:251` 一处订正句**（「4 行 → 3 行」） | **不构成越界**：该文件在 `diy-coder/.analysis/**`，被外层 `.gitignore:19` 排除 → **属报告面、非施工面**；核对证实订正内容为真（`v-reports-seg1-rework.md:236`） |

### 7.6 口径差登记

1. **任务书 §2.5 的 `结构稿中 → 待验收` 描述**：「结构稿完成、呈测前」（`:427`）**与 §5.1/§5b 把 `待验收` 放在实现之后不同**（§5.1 的 dev 回填目标 = `pages[].status`；§5b #3b 的链 = dev 实现 → review 审查，审查通过后页仍 `待验收`）。**任务书不回改，本报告即为点名处**（段2 主 agent 裁定 1；`w-reports-seg2.md:61`）
2. **`diy-dev/SKILL.md` 88 行 = 控制线 88，零余量**，且 `test_diy_dev_wds.py:184` 把**软线固化成硬断言**（今后任何一行新增都会红，修测试即等于改验收口径）——登记（V-F 中-1 同族 / V-A 低-4）
3. **`diyc_check_docs.py` 行数口径**：W9 回报写「705→**753**」，现测 = **751**（`wc -l`；`git diff --numstat` = +55/−9，705+55−9 = 751）→ **回报值高 2 行**，本报告按 751
4. **`diy-design/steps/` 行数口径**：段1 终值 605 行（`w-reports-seg1.md:94`）→ **现测 619**（段2/段3 跨段订正与补漏触及 `prototype-loop.md` / `h-delivery.md` / `k-sketch.md`）——引用一律取现测
5. **`0wds-` 计数口径**：5 = **逻辑位置数**（diy 文件与其 `.claude` 镜像合并计一行）、**6 = 物理行数**（V4 L-2 判定「口径差异，非虚报」）
6. **W7 回报的书面载体缺失（V-F 高-1）**：`w-reports-seg3.md` 系**事后补写**（V-F 发现 W7 无落盘回报 → 主 agent 依两工位回报原文补录，口径 = 原样转述声称、不作背书）

### 7.7 关键闸门事实（**后续批的前置**，本批物理不可行面）

- **`tests/test_review_contract.py:103`** 硬锁 `assertLessEqual(len(raw.splitlines()), 93)`（`diy-review` 薄主文件 ≤93 行）· **`:108`** 硬锁 `assertNotIn("Read (input)", raw)`（无 `steps/` 的技能不得出现 §4 步骤锚串）。两条合起来使 **`diy-review` 拆 `steps/` 在本批物理不可行**——该文件是 W4 的禁改面（`SKILL.md` 现 91 行 = **2 行余量**）。
  → **后续批若要把 WDS / 两透镜细节下沉 `steps/`，前置 = 先放宽这两条**（连带 `test_suite_texts.py` 的 `_steppers()` 适用面与 §4 锚串登记，见 §3.3）。登记，不返工。
- 关联事实：`diy-dev` **88 = 控制线 88（零余量）** 且软线已被固化成硬断言（§7.6②）——两条共同构成「**主文件扩容面已封顶**」的现状。

## 八、本批提炼的方法论判据 —— 「产物没变」不等于「一切正常」

### 8.1 四处同源失效（独立 V 三次发现、施工自测三次遗漏）

| 处 | 失效 | 为什么「无变化」被当成了「成功」 | 取数 |
| --- | --- | --- | --- |
| **H1** | `design_status` **值域无值可写** | 文档只写「推到**进行中值**」（占位符），从无值可写；既有测试只断言字符串 `"design_status"` **在场**，不校验值域 → **不写值也不报错** | `v-reports-seg1-cross.md:225-233`；段1 面内 47 passed 未发现 |
| **F-1** | 审查环**静默降级** | 「审查通过」在产物上的表现**就是不写** → `drive_page` 丢弃 `spawn_wds_review` 的退出码后，「审查崩了/没跑成」与「审查通过」**不可区分**（实测 review `exit(7)` 零写回 → runner 报「→ 待用户批准（审查通过…）」且 **rc=0**） | `v-reports-seg3-runner.md:260`；W6 自测 48 passed、**21 条新用例零覆盖** |
| **高-1** | 未复验页**混进待批准** | 上一轮崩掉留在 `待验收` 的页，与「本轮真通过」的页**产物状态完全相同**（都不变）→ 直接进「待用户批准」名单、rc=0，四词探测（上一轮/未经审查/遗留/审查结论未知）全 False | `v-reports-seg3-rework.md:342-351`；W6-R 返工自测 1568/231 绿未发现 |
| **中-1** | dev 越界**仍重试** | `drive_page` 只对**审查后**的回读做落点收紧，**dev 后没有** → 任何落点都 `continue` 重试（页已 `已移除` 仍在上面重复 spawn dev）；「没推进 = 正常」的结果被反推为「继续」 | `v-reports-seg3-rework.md:352-364`；同上 |

**根因（一句话）**：这四处都是**以「没有变化」反推「成功」**——判据读的是「产物的当前状态」，而当「成功」与「没成功」在产物上**同为无变化**时，判据就退化成恒真。

### 8.2 可复用判据（建议写入后续各批的验收面）

> **凡是「成功」在产物上的表现是「无变化」的环节，必须另有显式的成功信号（退出码 / 回执 / 计数 / 显式名单），否则不得判成功。**

三条推论（本批的落地形态）：
1. **判据不许只读产物状态**——必须读**动作方的显式回执**（F-1 的修法 = 接住子进程 rc）
2. **测试只断言「键名/字面量在场」不构成值域守卫**——须有**双向断言**（写入值 ⊆ 上游枚举 + 枚举值 ⊆ 文档在场；H1 的微修轮形态）
3. **状态集合的作用域必须显式分列**——「本轮通过」与「本轮未复验」不得同列呈为可批准（高-1 的修法）；只在会话内有效的集合必须在输出里点名其作用域（§七.1⑤⑥ 的残余）

## 九、审阅指引

- **必读**：§三.2（有意收严 + 迁移口径，**直接关系存量产物**）· §七（能力损失与欠账 6+5+2 条）· §八（方法论判据）
- **可跳过**：§二（逐段销账，与任务书 §3–§9 对应，已在 `w-reports-seg{1,2,3}.md` 完整报备）
- **须与另一路对齐**：§五 的 ⑥ `迁移计划.md` §二十八（本报告不越界；⑧ 的收尾状态以该节为准）
- 十二份 V 报告原文在 `diy-coder/.analysis/2026-09-22-migration-c3/`，含逐条实跑证据（命令 + 输出摘要）；源侧缺陷台账 `w1-defect-ledger.md` 含逐条可复现 `grep` 命令
