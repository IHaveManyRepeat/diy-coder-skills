# Step 6 — 质检、交接与收尾（Finish）

Progress: `[1 质检四维] → [2 五维校验并入] → [3 交接与设计意图拍定] → [4 定稿、终门与 32 闸清单]`

**Read (input):** `./05-overview.md` 的放行（覆盖 100%、四项核对全过）；`{output_dir}/wds-scenarios.yaml` 全部记录；`{output_dir}/wds-trigger.yaml`（人物优先级——质检要跟它对表）；`{output_dir}/wds-brief.yaml` 的 `brief.content.content_language.seo_keywords`（选读）；`check` 回执。
**Write (output):** 质检结论与修复；`scenarios[].design_intent`（逐场景拍定）+ `design_status: not-started`；`project.status: 已定稿`；`project.updated` 刷今天；`revisions`（未决项与用户改动）；给用户的交付摘要与路由。

你是**收尾的主持人**（源 step-07 / step-08 / step-09 + `steps-v` 五步）。前两步是本技能的**质量门槛**，第三步把交接契约拍定，第四步才是定稿与终门。

**本段纪律**：① **不许橡皮图章**（源 `Rubber-stamping without thorough checking` 列为失败面）——逐条过、不合格回对应步骤文件修；② **本技能只设 `design_status` 初值**，设计期的推进归 C·3 的 `diy-design`；③ **终门唯一放行 = `check --final` 的 `exit 0`**。

## 第 1 步 —— 质检四维（源 step-07 四张评分表）

**先说清为什么**：讲清「为什么要自己给自己打分」——源侧这一步的价值是**在交接前把已知的软处找出来**，别等下游卡住才发现。用你自己的话讲。

**逐场景打分**（四张表与源 step-07 同构；**阈值取源侧最小值**，不合格回去修，修完重跑本节）：

**一、完整性（7 项；最低 6/7）**
- [ ] `transaction` 以用户目的陈述，不是功能名
- [ ] 入口三件齐（`device` + `situation` + `entry`）
- [ ] 心理状态齐（`driving_forces.hope` 与 `.worry` 各一句、具体可感）
- [ ] 双方成功都具体可量（`success.user` / `success.business`）
- [ ] `pages[]` 是线性的（页号连续、零分支）
- [ ] `name` 含人物名且 `id` 已铸
- [ ] `trigger_map_context` 三键齐（人物 / 驱动 / 目标）

**二、质量（7 项；最低 5/7）**
- [ ] 人物具体（不是泛化的「用户」）
- [ ] 心理状态可感（不是「感兴趣」「好奇」）
- [ ] 两个成功都可量（不是「拿到更多客户」）
- [ ] 路径零「如果」语句
- [ ] 步数最省（每页都说得清为什么删不掉）
- [ ] 入口现实（不是「用户打开应用」）
- [ ] 业务目标连接显式（不是默认的）

**三、避坑（7 项；**7/7 全避**——本维度零容忍；裁定 6 取 checklist 权威版）**
- [ ] 阳光路径里没有边界情形
- [ ] 命名对人（目标优先），不是对功能
- [ ] 心理状态在场（不只是动作）
- [ ] 每页写了目的（不只是页名）
- [ ] 用的是触发图里的真人物（不是编的用户）
- [ ] 业务价值显式定义
- [ ] 单条描述不超两句（入口 / 心理 / 成功三处尤其）

**四、最佳实践（4 项；最低 2/4）**
- [ ] 场景名带人物名
- [ ] 从最高价值人物起（`SC-01` = P1）
- [ ] 一条场景一件事（不塞第二个 job）
- [ ] 驱动因素显式挂上（盼与怕都点名）

〔**源侧缺陷修复**〕源 step-07 正文的「避坑」只列 6 条、`6/6`，与 `data/quality-checklist.md` 的 7 条、`7/7` 互斥（census-2 B2）。本批取 **checklist 的权威版 7 项**，阈值 `7/7`（裁定 6）。

**落盘**：不合格项**回对应文件修**（页的问题回 04-outline，链的问题回 02-strategy），改完重跑本步与 `check`。

**检查点（六拍）**：① 生成 → ② 落盘（修复结果）→ ③ 分隔 → ④ 呈出四维评分表 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 五维校验并入`。

## 第 2 步 —— 五维校验并入（源 `steps-v` 五步；**裁定 15**）

〔**裁定 15 的落地**〕源侧带一条独立的校验子流程（`workflow-validate.md` + `steps-v/` 五步 / 751 行）并产一份 `validation-report.md`。**diy 侧裁掉独立子流程与报告产物**（终门 = `check --final`，复检 = 重跑 `check`；另立 md 报告 = 双实现）——**五个校验维度与阈值全部保留下表**，逐条在会话里过。

**组 A 场景覆盖（源 v-01，3 项）**
- [ ] 上游每条业务目标至少被一条场景承接
- [ ] P1 链有**专属**场景（不是顺带覆盖）
- [ ] 覆盖矩阵无空洞（`unassigned` 空、覆盖率 100%）

**组 B 导航模式（源 v-02，8 项）**
- [ ] 页面命名跨场景一致（同名必同义）
- [ ] 页名是用户语言（不是技术标识）
- [ ] 无同名异义页
- [ ] 首步是入口页（不是内部页）
- [ ] 末步收在成功态
- [ ] 每步到下一步自然（无跳变）
- [ ] 无死端（每页都有明确的下一步）
- [ ] `slug` 的 `NN.<p>` 与 `id` 同源（父子引用一致）

**组 D 跨场景一致（源 v-04，16 项）**
- [ ] 同一页在多条场景里用途一致
- [ ] 共享页的描述互不矛盾
- [ ] 共享页能照顾到它伺候的每个人物
- [ ] P1 人物拿到的场景最多
- [ ] 没有人物被过度代表（相对其优先级）
- [ ] 每个首要人物至少有一条专属场景
- [ ] 每条业务目标至少被一条场景承接（跨场景复核）
- [ ] 高优目标的场景覆盖更多
- [ ] 没有目标被孤立（提到了却没场景）
- [ ] 没有两条场景是同一个（同路径不同名）
- [ ] 重叠场景的用户意图能分开
- [ ] 共享是刻意的、不是撞上的
- [ ] 索引表所列场景数 = 记录数
- [ ] 优先级与触发图的人物优先级一致
- [ ] 覆盖矩阵与实际 `pages[]` 一致（页数对得上）
- [ ] 每条摘要的用户价值 / 生意价值两栏都非空且非套话

**组 E SEO 关键词对齐（源 v-05，9 项；`wds-brief.yaml` 无 SEO 图时整组标〔跳过〕并记 gap）**
- [ ] 每页至少挂一个主关键词（来自简报的关键词图）
- [ ] 关键词与页面意图相配（不是硬塞）
- [ ] 没有两页抢同一个主关键词
- [ ] 高优关键词至少落到一页
- [ ] 服务类词落到服务页
- [ ] 地域类词落到对应地域页
- [ ] 问题类词落到解答页
- [ ] 页名与规划里的 URL slug 相容
- [ ] 场景名与 SEO slug 无命名冲突

**组 C 大纲完整（源 v-03）已去重**：该组的 7 个组件（名称与 ID / 核心交易 / 入口 / 心理 / 成功 / 路径 / 触发图连接）与第 1 步「一、完整性」的 7 项**同一组**——按去重口径**只保留一份**，见上表。

**落盘**：五组结论与修复（同第 1 步：回对应文件修，改完重跑 `check`）。

**检查点（六拍）**：① 生成 → ② 落盘（修复结果）→ ③ 分隔 → ④ 呈出五组逐条结论 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 交接与设计意图拍定`。

## 第 3 步 —— 交接与设计意图拍定（源 step-08 + step-09）

### 3.1 设计意图逐场景拍定（源 step-09 第 2 指令；**裁定 17 的交接契约**）

逐条问用户「这条场景怎么进设计」，五选一写进 `scenarios[].design_intent`：

| 值 | 含义（源侧原话） |
| --- | --- |
| `K` | Sketch——用户自己画，智能体后面解读 |
| `C` | Discuss——逐页做创意对话 |
| `S` | Suggest——智能体逐步提议，用户逐条确认 |
| `D` | Dream Up——智能体整条做出来，用户看结果 |
| `L` | Later——到设计阶段再定 |

同时把 `design_status` 落成初值 `not-started`（方向已定、还没开工）。**这两个键 + `trigger_map_context` 就是交给 C·3 `diy-design` 的全部锚点**（本技能只设初值，推进归设计线）。

### 3.2 设计日志的 diy 口径（源 step-08；**单一源纪律**）

〔**源侧缺陷修复**〕源 step-08 要把进度与决策**追加**进 `_progress/00-design-log.md`（源 `FORBIDDEN to overwrite` / 逐条列举、禁 `etc.`）。diy 侧**不建这份散 md**：**进度 = 记录级 `status` + `project.updated`；决策与用户改动 = `revisions`**——写 `revisions` 时**只追加、不动既有条目**，`change` 点名 `SC-<nn>` 而不复制内容，`reason` 写为什么。源侧「逐条列举、不许 `etc.`」的纪律由**记录集本身**承接（每条场景各占一条记录，不可能被摘要吞掉）。

### 3.3 交接摘要（源 step-09 第 1、3 指令）

呈出**一页交接包**（会话内，不落盘）：① 完成摘要（项目名 / 场景数 / 逐条摘要表 / 覆盖率 / 质检结论）；② 各场景的 `design_intent` 与本线止点说明：

> **WDS 线止于本步。** 下游设计（源侧 Phase 4）在 diy 侧是 **C·3 的 `diy-design`**——它接手时要吃的是主线 `prd.yaml` 与页面规格**两路输入**，在 C·3 之前**不接本线**。本技能的交付物 `wds-scenarios.yaml` 与该链的两个上游产物一起，等 C·3 接线后由它消费。

③ 未决项（写进 `revisions`，一条一句；无则写「无」）。

**落盘**：`scenarios[].design_intent` + `design_status` + `revisions`。

**检查点（六拍）**：① 生成 → ② 落盘 `design_intent` / `design_status` / `revisions` → ③ 分隔 → ④ 呈出交接包 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 定稿、终门与 32 闸清单`。

## 第 4 步 —— 定稿、终门与 32 闸清单

### 4.1 定稿落盘

`project.status: 已定稿` + `project.updated` 刷今天（记录级 `status` 在第 4 步之外已全为 `已大纲`）。

### 4.2 终门（机械；`exit 0` 是唯一放行）

```
python "{project-root}/.claude/skills/diy-wds-scenarios/scripts/wds_scenarios.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`--final` 核：`project.status: 已定稿` + 全部记录 `status: 已大纲` + 各记录键表齐备（含裁定 17 的三键）+ 覆盖 100% + 零 `[假设]` + `design_status` 为初值。**按回执 `where` 就地修、重跑，不得跳过**；渲染与收尾都等 `exit 0`。

### 4.3 渲染（静默旁路）

`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

### 4.4 源 `workflow.xml` 的 32 闸抽取清单（**裁定 14 K7**：先抽清单，再裁文件）

源 `workflow.xml`（450 行）与 9 个 md 步骤**双写**且口径已分叉（census-2 C6/B2/B6）→ **文件裁**，但 32 个 `<gate>` 是质量门槛素材，逐条抽取并落到下表位置（**本清单即其唯一落点**）：

| # | 源闸（`type`） | 落点 |
| --- | --- | --- |
| 1 | `config-resolved`（初始化） | SKILL.md 激活段第 1 步（配置解析 + 缺省链） |
| 2 | `file-exists`（简报） | 本技能**上游读契约**：`wds-brief.yaml` 可选读（简报侧硬门归 `diy-wds-trigger`） |
| 3 | `file-exists`（触发图） | 激活段门禁 + `init` 机械门（`wds-trigger.yaml` 已定稿） |
| 4 | `data-extracted`（站点类型 / 目标 / 人物） | `01-context.md` 第 1 步的读取表（三样必须读出来） |
| 5 | `user-confirms`（上下文摘要） | 六拍检查点（每步呈出 + 等响应） |
| 6 | `user-confirms`（规模分析） | **用户关卡 1**（`01-context.md` 2.4 呈批） |
| 7 | `coverage-check`（all-pages-assigned） | 引擎覆盖矩阵 `unassigned`（`check` 的 `coverage` 键） |
| 8 | `decision-matrix-complete`（7 问） | `02-strategy.md` 第 1 步的 7 问表（全答） |
| 9 | `user-confirms`（链清单） | 六拍检查点 |
| 10 | `naming-check`（场景名含人物名） | 命名铁律（03-plan 2.1 / 04-outline 2.1）+ 引擎骨律软核 |
| 11 | `coverage-check`（all-pages-assigned-no-repetition） | 引擎覆盖矩阵 `repeated` + 05-overview 四项核对 |
| 12 | `user-confirms`（场景计划） | **用户关卡 2**（`03-plan.md` 第 1 步呈批） |
| 13 | `quality-gates-pass`（all-7） | `04-outline.md` 第 2 步的 7 道闸 |
| 14 | `file-created`（场景文件） | **裁**（裁定 12）→ 改为「`scenarios[]` 记录落盘」（04-outline 第 3 步） |
| 15 | `page-folder-created` | **裁**（裁定 12）→ 改为「`pages[]` 记录落盘」（04-outline 第 3 步 3.2） |
| 16 | `all-scenarios-complete` | 引擎 `--final`：全部记录 `status: 已大纲` |
| 17 | `file-created`（00-ux-scenarios.md） | **裁**（裁定 12/15）→ 改为会话内索引呈出（05-overview 第 1 步） |
| 18 | `links-verified` | **裁**（无文件链接）→ 改为**父子引用完整性**（引擎核 `SC-<nn>` ↔ `SC-<nn>.P<n>`） |
| 19 | `coverage-matrix-complete` | 引擎覆盖矩阵（`check` / `show` 的 `coverage.matrix`） |
| 20 | `user-confirms`（总览） | 六拍检查点 |
| 21 | `quality-threshold`（完整性 6/7） | 本文件第 1 步「一、完整性」 |
| 22 | `quality-threshold`（质量 5/7） | 本文件第 1 步「二、质量」 |
| 23 | `quality-threshold`（避坑 7/7） | 本文件第 1 步「三、避坑」（裁定 6 权威版） |
| 24 | `quality-threshold`（实践 2/4） | 本文件第 1 步「四、最佳实践」 |
| 25 | `user-confirms`（质检摘要） | 六拍检查点 |
| 26 | `file-read-before-write`（设计日志） | **裁**（散 md 已裁）→ 改为「写 `revisions` 前先回读记录」 |
| 27 | `append-only`（设计日志） | `revisions` 只追加、不动既有条目（06-finish 3.2 + 规则段） |
| 28 | `artifacts-listed`（逐条列举） | 改为「交接摘要逐条列举记录，禁 `etc.`」（06-finish 3.3） |
| 29 | `user-confirms`（日志已更新） | 六拍检查点 |
| 30 | `design-intent-saved` | 引擎必填键 `scenarios[].design_intent`（`--final` 机械核） |
| 31 | `design-status-set` | 引擎必填键 `scenarios[].design_status`（初值 `not-started`） |
| 32 | `user-confirms`（完成摘要） | 六拍检查点（06-finish 3.3 交接包） |

**收尾与路由**：`check --final` 回 `exit 0` 后，一句话给「本场景集已定稿，WDS 前置三段（简报 → 触发图 → 场景）到此跑通；设计线 `diy-design` 的接线排在 C·3」。**本文件到此结束**——不再读任何 `steps/` 文件。
