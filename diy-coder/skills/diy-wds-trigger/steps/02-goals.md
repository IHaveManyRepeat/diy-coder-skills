# Step 2 — 业务目标与目标群（Business Goals & Target Groups）

Progress: `[1 业务目标（愿景 + 3–5 目标）] → 2 目标群与人物画像（2–4） → ./03-drivers.md`

**Read (input):** `./01-mode.md` 的放行（`mode` / `entry` / `stage: 模式`）；`{output_dir}/wds-brief.yaml` 的 `brief.core`（愿景 / 定位 / 目标用户 / 产品概念——本文件的两步都要跟它对齐）；`entry: 既有产物` 时另读 `./01-mode.md` 第 2 步覆盖图里点名的产物键；用户对每个引导问的回答。
**Write (output):** `business_goals[]`（`BG-1` 愿景 + 3–5 条 `BG-<n>` 目标，各带 `metric` / `target` / `timeline`）；`personas[]`（2–4 条，`TG-<n>`，各带 `name` / `role` / `priority` / `summary` / `context` / `goals` / `frustrations` / `current_behavior`）；`stage`：第 1 步落 `目标`、第 2 步收尾落 `驱动`。

你是**战略分析的主持人**（源 Saga 线）。本文件承载**两个工作坊**，各是源侧一个主步。`mode: S` / `D` 时把每一步的「问」改成「我出稿 + 自审（对照 `06-finish.md` 的键表与质检查表）→ 你复核」。

## 第 1 步 —— 业务目标（源 step-02）

**先说清为什么**：讲清「为什么要分两层」——**愿景**是激励性的方向（不好量化），**目标**是可量的进度指标（SMART）；先做梦，再把它变可量。用你自己的话讲。

**引导问句（源 `step-02:72-110`，逐条问、不代答）**：

1. **愿景**：「**你想走到哪儿？**往大了想——如果一切顺利，你想占住什么位置？」（源侧示例：成为瑞典狗主人最信任的平台 / 独立设计师的首选工具 / 让项目管理真的好玩）。听激励性的语言，**帮它变清楚**，不替用户写。
2. **目标**：「**怎么衡量你正在接近这个愿景？**」给三类提示——用户指标（采用 / 互动 / 留存）、业务指标（收入 / 增长 / 市场份额）、质量指标（满意度 / 推荐 / 评价）。
3. **SMART 打磨**（逐条过一遍五问）：**S** 具体是什么？**M** 数字是多少？**A** 现实吗？**R** 跟愿景相关吗？**T** 什么时候完成？源侧给的反例 → 正例：「拿到有影响力的用户」→「2026 Q4 前签下 10 位 1000+ 粉的认证训犬师」。
4. **收窄到 3–5 条**（源侧硬规则：少于 3 或多于 5 都要显式讨论）。

**产出键**（源 `templates/trigger-map.template.md` 的 Business Objectives 段落到本产物）：

- `business_goals[0]`：`{id: BG-1, kind: 愿景, statement: <逐字符的愿景原文>}`——`init` 已铸好位，本步填 `statement`。
- `business_goals[1..]`：`{id: BG-<n>, kind: 目标, statement, metric, target, timeline}`——`id` 顺着 `BG-2`、`BG-3`… 铸（**不改 `BG-1`**）；四键缺一不可（`check --final` 逐键核对）。
- 优先级**靠数组顺序承载**（首条目标 = THE ENGINE / 主目标），**不外设 `prioritized_objectives`**——源侧的 `prioritized_visions` / `prioritized_objectives` 是采集侧有、消费侧无人读的死能力（census E9），本批**单一源收口到数组顺序**。

**用户关卡**：三条以上目标逐条念一遍，问「这条的目标数与时点你认吗？」——**没点头不落盘**。

**检查点（六拍）**：① 生成 → ② 落盘 `business_goals` + `stage: 目标` → ③ 分隔 → ④ 呈出「愿景 + 目标表」→ ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 目标群与人物画像`。

## 第 2 步 —— 目标群与人物画像（源 step-03）

**先说清为什么**：讲清「为什么先问人、再问产品」——业务目标要靠**真实的人用起来**才成立；这一步找的是「谁用了产品，目标就会发生」。用你自己的话讲。

**引导问句（源 `step-03:74-117`，逐条问、不代答）**：

1. **列出人群**：「**谁用了你的产品，你这些目标才成立？**」三类提示——**主要使用者**（直接且高频地用）、**影响者**（影响别人采不采用）、**决策者**（拍板买不买）。把提到的**全部**先记成 `target_groups_raw`（会话内，不落产物）。
2. **收窄到 2–4 群**：「**哪 2–4 群对你最关键？**」判据：谁对目标影响最大？谁被伺候好了会带动其他人？机会最大的是哪儿？
3. **逐群建画像**（源侧五问，一群人一次问完再问下一群）：① **他们是谁**（角色 / 处境）② **他们的一天什么样**（上下文与职责）③ **他们想达成什么**（目标）④ **什么让他们受挫**（痛点）⑤ **他们今天怎么解决这个问题**（当前行为）。
4. **给名字、让他像真人**——源侧硬规则：**叙述型画像，不是一串要点**（`FORBIDDEN to create personas without user input or skip persona depth`）。**人物取头韵名**（源 saga principle：如 Harriet the Hairdresser）；**行为特征而非人口统计**。

**产出键**（源 `templates/persona-document.template.md` 的 1–5 节落到本产物）：

- `personas[]` 每条：`{id: TG-<n>, name, role, priority: 主|其他, summary, context, goals[], frustrations[], current_behavior}`——**`id` 按序号铸（`TG-1`、`TG-2`…），此后不随优先级重排**（裁定 8）。
- `priority` **恰一条 `主`**（源侧的 Primary；Feature Impact 的加权基准，裁定 10）；**不设「三级」假设**——2 群时没有二级、三级槽位（裁定 6）。
- `transformation: {before, after}` **仅主人物必填**（源侧 `PRIMARY PERSONA ESPECIALLY`）——BEFORE/AFTER 是情绪旅程，不是功能清单。
- 源侧画像模板的 2a 视觉提示词 / 7 转型旅程 / 8 战略三角 / 9–12 各节：**2a 裁**（diy 无图像生成面）、**7 落 `transformation`**、**8 的三角关系落 `driver_patterns.tensions`**、**9–12 是叙事展开**——落 `summary` / `context` 与驱动因素的 `why`（不另立键）。

**用户关卡**：每群画像念一遍，问「**这像你要设计的那个人吗？**」——不像就当场改，**不像真人不往下走**（源侧 SYSTEM FAILURE 判据）。

**检查点（六拍）**：① 生成 → ② 落盘 `personas[]` + `priority` 分档 → ③ 分隔 → ④ 呈出「人群表 + 逐群画像」→ ⑤ 出四选项 → ⑥ 等响应。

**收尾与路由**：`personas[]` 全部经用户点头、恰一条 `主` → `stage: 驱动`，读 `./03-drivers.md`。本文件到此结束，不再回头。
