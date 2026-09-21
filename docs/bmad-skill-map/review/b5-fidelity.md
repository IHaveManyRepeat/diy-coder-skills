# B5 批保真度报告 —— bmb 元能力（3 技能）

- 批次：BMAD 迁移 阶段 B 第 5 批 ｜ 完成日期：2026-09-21 ｜ 编制：主 agent
- 任务书：`diy-coder/.analysis/2026-09-20-migration-b5/taskbook.md`（终态 md5 `c9fc38421b1e307f43ce74090b58db6b` · 305 行 · 影子仓 `877eca4`）
- 开工前自检：dogfood 扫描两轮（首轮 50 + 增量补扫 13，全部处置）→ 机器产物 `SS-029`（终门 `check --final` PASS）
- 交付：`diy-bmb-builder` / `diy-bmb-module` / `diy-eval-runner` —— 套件从 37 → **40 技能**
- 本批三点特殊：① **「造物者」批**（产物是 diy 体系自身的构件：技能树 / 批次计划 / 评测档案）；② 源侧**五源全零 YAML 产物**（B1–B4 之后首例，验收 #2/#6 按 `diy-test-author` 判例给等价形态）；③ 源侧 **module / eval 两个概念在 diy 整体不存在**——本批的接口工作不是「接上去」而是「先定落点」

## 一、批次结果总览

| 技能 | 源（`module=='bmb'`） | 源步数 → diy | 引擎 | 测试 | 状态 |
|---|---|---:|---|---|---|
| `diy-bmb-builder` | `bmad-agent-builder` 8 + `bmad-workflow-builder` 10（**2合1**） | 8→5 · 10→5 | `bmb_builder.py` 1467 行（7 子命令） | 25 用例 | ✅ |
| `diy-bmb-module` | `bmad-module-builder` 12 + `bmad-bmb-setup` 6（**2合1**，setup 整体裁） | 12→4 · 6→0 | `bmb_module.py` 774 行 | 28 用例 | ✅ |
| `diy-eval-runner` | `bmad-eval-runner` 7 | 7→3 | `eval_runner.py` 1528 行 | 22 用例 | ✅ |

**合计**：3 技能 · 5 源技能（普查基线 18809 行）→ diy **12 个 `steps/` 文件 · 3 引擎 3769 行 · 75 用例**。

**批级口径**：零阻断 · **能力丢失 0 条**（V 独立清点）· 冻结项偏离 **1 条**（登记项）· 欠账 **6 条**（非阻断观察，见 §七）。

## 二、逐技能保真度

### 2.1 diy-bmb-builder（技能工厂：Build / Edit / Analyze 三意图）

- **交付**：`SKILL.md` 65 行（四段）· `steps/` 5 文件（`01-intent` / `02-build` / `03-analyze` / `04-gate` / `05-finish`）· `scripts/bmb_builder.py` 1467 行 · `test_bmb_builder.py` 25 用例
- **保真**：单循环构建流（懂来意 → 扎真专家知识 → 硬化 → 隐含项 → memlog → 最小版本 → 真输入上跑 → 两版对比才加脚手架 → 脚本机会 → lint gate → handoff）全程保留；5 个共有 lens 的契约形状与 `schema_version: 2` 与既有 12 份实物同形
- **Analyze 复用既有报告格式**（裁定 6）：12 件全落（`findings.json` + `lens-*` × 5 + `prepass-*` × 2 + `scan-*` × 2 + `report.{md,html}`），V 实跑验证与 2026-09-13 的 12 份实物逐文件名相同
- **裁剪**：agent 全线（sanctum / Three Laws / PULSE / 三型梯度 / 2 个 lens / 3 个模板脚本）· customize 面（`customize.toml` 三层合并 / `{agent.*}` 占位符 / 引导文档）· CW（源侧有档无实体）· `report-shell.html`（改用自包含精简模板）
- **能力对账**（V 核）：身份 → 技能 Rules 段；记忆 → diy 产物 YAML；自主 → `runner.py` 调度

### 2.2 diy-bmb-module（批次规划器：只规划不造）

- **交付**：`SKILL.md` 81 行 · `steps/` 4 文件 · `scripts/bmb_module.py` 774 行 · `test_bmb_module.py` 28 用例
- **产物**：`{output_dir}/module-plan.yaml`（`MP-###` + `slug` + `skills[]` 逐技能自足 brief），**本批唯一带 schema 的新产物类型**
- **保真**：IM 七相 **7/7 在**（含「灌骨架 + 未定」手法改造为「YAML 空值 + 显式禁令」）；`validate-module.py` 11 项 → diy **10 项有等价落点 + 1 项换对象**（CSV 相关的 ④⑤⑨ 与 ① 随 help CSV 与 setup 形态裁）
- **`--previous` 判 yes**（清单收缩 = 计划变更）：按 `slug` 配对（号段重铸不失配），`dropped: true` 留痕放行
- **零写面**：校验不写任何被校验技能的文件（frontmatter 亦然），有「前后逐字节快照相等 + 无 `.tmp` 残骸」用例断言
- **裁剪**：`bmad-bmb-setup` 整体 6 步（`merge-config`/`merge-help-csv`/`cleanup-legacy` 三件套 + `_bmad` 三写面）· CM 的「打包」出口换成「按 `build_order` 指路 builder」· 往他人 SKILL.md 注入注册检查那一手（本批不授权）

### 2.3 diy-eval-runner（四模式评测器）

- **交付**：`SKILL.md` 67 行 · `steps/` 3 文件 · `scripts/eval_runner.py` 1528 行 · `references/` 5 文件 · `test_eval_runner.py` 22 用例
- **产物**：`{output_dir}/eval-runs/<YYYYMMDD-HHMMSS>-<label>/`（**零 YAML 主产物**），四模式目录形状逐行列清即 `check --run-dir` 的判据表；「永不删除、覆盖、轮转」写进规则
- **保真**：`state_prefix`（单发模拟多轮的关键发明）逐字保留；清场环境契约（从零构建、绝不继承）**经 V 反向探针验证**——假运行时落盘的 env 键**恰为** `['CLAUDE_CONFIG_DIR','HOME','PATH']`，宿主密钥零泄漏，空串 auth 不传
- **两条反自欺硬规则经反向探针**：① trigger 禁子串——V 用「init 事件列全部技能名 + 纯文本点名」构造，**触发率实测 0.0**，证明子串面真关闭；② grader 三纪律（不给部分分 / 举证责任在通过方 / 反向批评 rubric）落进引擎终门 + 文档
- **同构件**：`mlog` 与 W1 两份实现——V 用 4 场景族 14 步对跑，**rc / ack 键集 / 违规码 / 文件 md5 全同**
- **裁剪**：platform-adapter 抽象层 + 硬编码 CLI 配置 · `BMAD_EVAL_ADAPTER` 发现位 · `_bmad` 配置回落 · `~/bmad-evals/` 落点 · `--workers` 并发 · `evals_required` 整键

## 三、批级裁定摘要

| 裁定 | 落点 |
|---|---|
| 1 产物形态（混合） | W2 产 YAML；W1/W3 零 YAML 主产物（按 `diy-test-author` 判例给等价形态条款） |
| 2 `diy-bmb-module` = 批次规划 + 注册校验（**只规划不造**） | 用户 2026-09-20 拍板；`bmad-bmb-setup` 整体裁撤 |
| 3 eval run 目录落 `{output_dir}/eval-runs/` | 否则无头下写盘被 defer、自改进闭环不可用 |
| 4 adapter 裁为薄配置 | 保留「不硬编码模型名」纪律 + `--invocation` 覆盖位 + 可选 `adapter.json` |
| 5 `diy-bmb-builder` 只造 diy 技能 | agent 全线裁；保留构建流程本体 + prompt-quality-canon + 5 lens |
| 6 Analyze 复用既有五透镜报告格式 | 本批是能力**收编**、不是新建 |
| 横切纪律 1–4 | 源侧概念不存在则裁 / `{project-root}` 二象性 / 副作用纪律三档 / 产物一步到位 + 自足可分发 |

## 四、V 独立验证结论（2026-09-21）

- **结论：可进入收口链，无阻断项。** 能力清点**丢失项零条**（8 组裁剪全部有裁定依据）；步数逐源与 raw JSON 相等
- **四条重点逐条**：① W1 的 Analyze 模式对 W2/W3 实跑**通过**（12 件全落，且**真抓出 3 条非空转问题**）② W1↔W2 交棒接口**功能一致 6/7**（仅名字前缀约定单侧写明，实跑确认现状不出错）③ W3 隔离契约与两条反自欺规则**在场、可测、经反向探针** ④ memlog 双实现**逐字节相同**
- **抽验**：三测试独立复跑 23/28/22 全 OK；母本逐字**脚本比对**（非目检）三技能全 PASS；结构面（≤90 行 / 四段同序 / 六字段取值）逐格相符
- **8 条需定夺项**→ 2 条已修、6 条登记欠账（§七）

## 五、主 agent 集成验证（2026-09-21）

| # | 项 | 命令 / 口径 | 结果 |
|---|---|---|---|
| 1 | 收口链① 登记 | `test_suite_texts.py` 三处（`NEW_SKILLS` / `CONVERTED_INSTANCE` / `CONVERTED_DISCIPLINE`） | 11 tests **OK**（登记前 2 红）——连带证明三技能 §1/§2/§3/§4/§6 锚串逐字携带 |
| 2 | 收口链② sync | `bash sync.sh` | **40 个 skill** → `.claude/skills`；源↔副本 **427 文件 0 差异**（仅副本多出 1795 为 bmad-* 既有技能） |
| 3 | 收口链③ 全量测试 | `python -m pytest tests/ -q` | **949 passed**（874 基线 + 75 本批 − 0），86 subtests |
| 4 | 收口链④ 渲染自证 | `bmb_module.py new --slug demo-batch`（tempdir）→ `viewer.py` | `new` rc 0（`MP-001`）；渲染 **rc 0 · rendered 1 doc**（`module-plan.html` + `index.html`） |
| 5 | 修复验证（V 发现①） | 越界 `mlog --file ../../escaped.md` | **rc 1 + `NAME_ILLEGAL` + 零写入**（修前 rc 0 且文件落到 `--dir` 外两层） |
| 6 | 修复验证（V 发现②） | `test_bmb_builder.py` | 25 用例 OK（含 2 条新增守卫用例） |

## 六、验收 13 项对照（迁移计划 §二）

| # | 验收项 | 责任 | 证据 |
|---|---|---|---|
| 1 | 薄主文件 + steps/ 厚子文件 | 各 W | 65/81/67 行 · 5/4/3 个 steps |
| 2 | 产物 schema / 稳定 ID | W2（`MP-###`）；W1/W3 **豁免**（零 YAML 主产物，回报已写理由与替代形态） | schema 段 + `check` 用例 |
| 3 | 前置门禁（零产出退出） | 各 W | 门禁用例（W1 四门 / W2 三门 / W3 四门） |
| 4 | ID 链接入 | W2（`skills[].name` 引用闭包 + `MP-###` 稳定）；W1/W3 **N/A**（无全局 ID 体系） | `--previous` / 对称性用例 |
| 5 | 注册 | 主 agent（37 + 3 经 sync）+ W1 产物直落安装面 | sync 输出 + W1 落点断言用例 |
| 6 | viewer 渲染 | W2 登记标签缺口（§八）；渲染执行归收口链④；W1/W3 **N/A**（无 YAML 产物，规则段写明理由） | §五 第 4 行回执 |
| 7 | 冒烟 TC（≥5） | 各 W | 25 / 28 / 22 用例 |
| 8 | 登记元数据 | 各 W | frontmatter 六字段（V 逐格核对） |
| 9 | 读取成本纪律 | 各 W | 母本 §4 逐字（脚本比对） |
| 10 | 双源输入声明 | 各 W | 三技能均非主线/WDS 交汇点（逐条确认） |
| 11 | 渲染静默 | W2（viewer 调用照母本 §5）；W1 适用（脚本渲染不打开、不报路径）；W3 无 viewer 调用（写明理由） | 规则段 + V 抽验 |
| 12 | diyc 接线 a–e | 各 W | a 三技能均委托 `diyc.py resolve`；b W1/W2 = `check --final`、W3 = `check --run-dir`；c W2 yes / W1、W3 no；d 母本 §3 逐字；e W1 三写面 / W2 零写面 |
| 13 | 副作用纪律 | 各 W 自证 + V 抽验 | W1 的 Edit 覆盖无头入队（`defer-add` 唯一产生面）；W3 白名单未覆盖 → warning + skip **不入队** |

## 七、非阻断观察清单（欠账，C 阶段或后续批处置）

V 发现 8 条，**2 条已修**（`mlog --file` 写面越界 / `INTERNAL_ERROR` 码登记），余 **6 条**留档：

| # | 归属 | 内容 | 建议 |
|---|---|---|---|
| 1 | W1 | 围栏容差 `.strip()` 与源 + W3 不一致（宽容侧） | 与 #3 同批统一 |
| 2 | W2 | 文档写 `missing_slug`、实现报 `EMPTY_FIELD`（违 §10 第 6 条「文档与实现必须一致」） | 改文档措辞 |
| 3 | W1/W2/W3 | 只读子命令 `--output-dir` 必填面三家不一致（W1/W2 必填且与既有 37 技能先例同侧，W3 可选且缺省落空串） | 一次口径裁定后统一 |
| 4 | W2 | 「frontmatter 是 `diy-help` 的读面」——全仓搜索证实**当前零消费者**（任务书自述为「备供 C 阶段登记表驱动」） | C·1 落地时回填 |
| 5 | W3 | `--runs 0` 静默按 1（同库 `--random 0` 是先例拒） | 统一为拒 |
| 6 | W3 | docstring 声明 `UNPARSABLE_JSON` 而实文另有 `UNPARSABLE_YAML` | 补登记 |

**另两条待办**（来自 V 未决问题）：① 七对边界句的「对方侧随 C 阶段补」——W1 已写明该句、**W3 的规则 7 没写**，建议 C 阶段统一；② W2 的 `--previous` tombstone 边缘（旧稿标 `dropped: true` 的条目若在新稿被整条删掉，现口径仍判 `ID_UNSTABLE`）——**主 agent 裁定：维持严格口径**（清单收缩必留痕），无用例覆盖该分支，留待后续批按需补。

## 八、viewer 标签缺口清单（**C 阶段输入**）

`module-plan.yaml` 为**新产物类型**，V 用 W2 的 tempdir 产物实跑 `viewer.py`（渲染成功 rc 0，`module-plan.html`），发现缺口**比任务书描述更重**——分两条登记：

**(a) 缺文档级标签覆盖**：`slug` / `kind` / `dropped` / `new` / `brief` 等键无中文标签（回落原名；`待决问题` / `项目定位` 命中全局键表故正常）。建议补 `DOC_LABELS["module-plan"]` 与 `DOC_KEY_LABELS["module-plan"]`。

**(b) 引用语义错配导致假「引用不存在」徽章（更有害）**：`depends_on` / `dependencies` / `build_order` 里的**技能名**被通用跨文档引用解析器当作**记录 ID**——`diy-alpha`（合法计划内引用）与 `diy-nope`（真悬空）**同样**挂 `<span class="dangling">` + 徽章「引用不存在」。**它会把一份健康的计划显示成有病**，比 (a) 更需优先处置。

`viewer.py` 在禁改面内，故只登记不改；两条均归 C 阶段「缺口 2：viewer 通用降级渲染」。

## 九、审阅指引（B5 为**非强制人工审**）

**审阅面**：本报告 + `v-audit.md`（终审计证据）+ `v-capability-inventory.md`（能力清点）。

**异常项才需看**：
1. §七 的 6 条欠账（其中 #3「`--output-dir` 必填面三家不一致」是唯一的跨技能一致性面，若要收敛需一次口径裁定）
2. §八 的标签缺口 (b)（假「引用不存在」徽章会误导使用者）
3. 「造物者」批的自我兑现：W1 的 Analyze 模式审自家产品**真抓出 3 条问题**（`diy-` 前缀无机械校验 / 全问句触发率 0 无诊断 / step 3 重复读取）——这些是**能力的正面证据**，但其中前两条是否要修，留作后续批判断

**下一步**：C 阶段余项（`迁移计划.md` §五 C 1–7 / 9 / 10）或 B6 / B7 批。
