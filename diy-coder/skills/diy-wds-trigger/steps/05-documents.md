# Step 5 — 成品成稿与 Effect Map（Documents & Effect Map）

Progress: `[1 成品成稿与交叉核对] → 2 Effect Map 构图 → ./06-finish.md`

**Read (input):** `./04-features.md` 的放行（六个主体段齐）；`templates/trigger-map.template.md`（**唯一完整 Mermaid 骨架**——第 2 步逐条照它填）；用户对成品视图与图的确认。
**Write (output):** `effect_map` 全段（`derived_from` / `format` / `direction` / `config` / `nodes` / `connections` / `class_defs` / `diagram`）；对六个主体段的补齐与交叉核对修正；`stage` 推进到 `成品`。

你是**成稿与构图的主持人**（源 Saga 线）。本文件承载源侧的**两个主步**：文档生成（`07a`–`07f`）与 Mermaid 效果图（`08a`–`08h`）。

## 第 1 步 —— 成品成稿与交叉核对（源 step-07a–07f）

**先说清为什么**：讲清「为什么还要再走一遍」——前面各步是分头落的段，这一步把**段与段之间**对一次表，并把成品视图摆给用户看。用你自己的话讲。

**源侧产物 → diy 落点**（源侧生成 7 份 md 文档；diy 的成品是**一个 YAML + viewer 渲染**，逐条对照如下）：

| 源侧 md | 承载内容 | diy 落点 |
| --- | --- | --- |
| `00-trigger-map.md`（hub） | 图 + 各节页内摘要 + 导航 + Flywheel + How to Read | **`wds-trigger.yaml` 本身 + viewer 渲染**（单记录就是 hub：六个主体段即六节）；「页内摘要」= `summary` / `rationale` 等既有键，**不另建一节** |
| `01-Business-Goals.md` | 愿景 + 三档目标 + Flywheel + 成功指标对齐 | `business_goals[]`（顺序 = 优先级 = Flywheel 的因果序） |
| `02/03/04-<Name>-the-<Role>.md` | 人物画像 13 节 | `personas[]`（13 节 → 已定的 10 键 + `transformation`；映射见 `02-goals.md` 第 2 步） |
| `05-Key-Insights.md` | 战略含义 9 节 | **去重收口**（见下） |
| `06-Feature-Impact.md` | 特征影响 | `feature_impact[]`（`04-features.md`） |

**`05-Key-Insights.md` 的 9 节去处（源侧缺陷修订，逐条给落点）**：Header → 不落；Flywheel → `business_goals[]` 顺序；Primary Development Focus → `priority.focus_statement.must`；Critical Success Factors → 会话内呈出（不落盘）；Design Implications → **每条驱动因素的 `promise` / `answer`**（源侧「按页面分区的 must do」在 diy 由驱动因素承诺承载，不另立散文节）；Emotional Transformation Goals → `personas[].transformation`；Design Focus Statement → `priority.focus_statement`；Development Phases → 会话内呈出；Related Documents Footer → 不落（单文件无互链）。源侧该 md 与 hub 的「页内摘要」**大面积重复**（源侧 07a:106-117 与 07f 双写），diy 按单一源收口，**内容不丢、载体合并**。

**★ 交叉一致性核对（源 `07a:126-134` 的 Cross-Validation Check，逐条做，不符就改）**：

1. `business_goals[0].statement` 的愿景与 `wds-brief.yaml` 的 `brief.core.vision` **逐字符相同**——**找不到原文就问用户，不得转述**（源 `07a:80` 硬规则）。
2. 人物名在 `personas[]` / `priority.ranked_personas` / `driver_patterns` 三处**拼写一致**。
3. 驱动因素条数与 `driver_patterns` 的引用一致；引用 ID 全部可解析。
4. 优先级顺序在 `personas[]`（`priority` 分档）/ `priority.ranked_personas`（排序）/ `business_goals[]`（顺序）三处**不矛盾**。
5. 特征影响的 `rationale` 点名的驱动因素 ID 全部在场。

**成品视图呈出**：把六段缩成一页给用户看（愿景一句 / 目标 3–5 条 / 人物与主群 / 主群 Wants-Avoids / 焦点声明 / 特征三档）。**用户关卡**：问「**这一页就是你的战略北极星，认吗？**」

**检查点（六拍）**：① 生成 → ② 落盘（补齐与修正）→ ③ 分隔 → ④ 呈出成品视图 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— Effect Map 构图`。

## 第 2 步 —— Effect Map 构图（源 step-08a–08h，**收编的唯一定义**）

**载体口径（裁定 7，先读）**：**`wds-trigger.yaml` 是单一源，Mermaid 是派生视图**。图**不单独落盘 md**——它落 `effect_map.diagram`（人读用）与 `effect_map` 的结构键（机器核对用）。源侧 `08a`–`08h` 的构图纪律（配置 / 节点模板 / emoji 规则 / 连接数校验 / 4 类样式）**全部收编在本节**，是本技能对构图的**唯一定义**；源侧 `data/mermaid-formatting-guide.md`（无消费方、与步骤正文重复且数字互斥）**已裁**，`templates/trigger-map.template.md`（唯一完整骨架）**已收编为本技能 `templates/` 下的同名文件**。

### 一、配置与结构（源 08a）

图**永远**以这三行起头（主题 / 字体 / 字号 / 方向逐字不改）：

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'fontFamily':'Inter, system-ui, sans-serif', 'fontSize':'14px'}}}%%
flowchart LR
```

节注释按左→右六段排：`%% Business Goals (Left)` / `%% Central Platform` / `%% Target Groups (Right)` / `%% Driving Forces (Far Right)` / `%% Connections` / `%% Styling`。

**节点 ID**（**保源侧 0 基口径**，与产物 ID 的对照见 SKILL.md「结构」段末）：

- 业务目标 `BG0`、`BG1`…（顺序对应 `business_goals[]` 的数组序，**`BG0` 在顶**）
- 平台 `PLATFORM`（**恒单个**）
- 目标群 `TG0`、`TG1`…（对应 `personas[]` 数组序）
- 驱动因素 `DF0`、`DF1`…（**与 TG 一一对应**：`TG0` ↔ `DF0`）

**落盘**：`effect_map.derived_from` / `format` / `direction` / `config` / `nodes`。

### 二、节点模板（源 08b / 08c / 08d / 08e 四条，逐字保留结构）

```
BGX["<br/>EMOJI 标题全大写<br/><br/>要点1<br/>要点2<br/>要点3<br/><br/>"]
```

- **业务目标 `BGX`**（源 08b）：`<br/>` 起 → emoji + 标题全大写 → 空行 `<br/><br/>` → **3–5 条要点**（各以 `<br/>` 收）→ `<br/><br/>` 收尾。**优先级只靠纵向顺序**（`BG0` 在顶），**不得用特殊样式**。emoji 按主题取（钱袋 / 笑脸 / 闪电 / 火箭 / 星 / 图表 / 握手 / 靶心）；**禁项**：节点内不得出现 HTML 标签（粗体 / 斜体）。
- **平台 `PLATFORM`**（源 08c）：`<br/>` 起 → emoji + **产品名全大写** → 空行 → 品类 / 一句话定位 → 空行 → **转型陈述（跨 3–5 行，讲清 before → after）** → `<br/><br/>` 收尾。
- **目标群 `TGX`**（源 08d）：`<br/>` 起 → emoji + **人名全大写** → **优先级全大写**（PRIMARY TARGET / SECONDARY TARGET；2 群时只有前两个）→ 空行 → **3–4 条特征** → `<br/><br/>` 收尾。**记下每群的 emoji —— DF 节点必须用同一个。**
- **驱动因素 `DFX`**（源 08e）：`<br/>` 起 → **与对应 TG 相同的 emoji** + `PERSONA'S DRIVERS` 全大写 → 空行 → `WANTS`（**标题不带 emoji**）→ 每条正向一行、行首 ✅ → 空行 → `FEARS`（**标题不带 emoji**）→ 每条负向一行、行首 ❌ → `<br/><br/>` 收尾。
  **条数口径**：源侧「exactly 3」与采集端 3–5 冲突（裁定 6）——**本节按 `driving_forces` 的实际条数渲染**（3–5 条都合法），**不再截断到 3**；这是「展示端自适应」的落地处。驱动因素文本**尽量 40 字符内**。

**落盘**：`effect_map.nodes`（四组节点 ID 序列，与记录数一一对应）。

### 三、连接与连接数校验（源 08f）

只用简单箭头 `-->`（**不得**加花式样式）：

```
BG0 --> PLATFORM
PLATFORM --> TG0
TG0 --> DF0          %% 配对严格：TG0→DF0、TG1→DF1…
```

**连接数校验**：`BG 连接数 = 业务目标数` + `平台→TG 连接数 = 人物数` + `TG→DF 连接数 = 人物数`，即 **连接数 = 目标数 + 2×人物数**（3 个人物示例：3+3+3=9；本产物含愿景节点时目标数 = `business_goals[]` 的长度）。**配对错（TG0→DF1）或数量不符 = 图坏**——`check` 与 `metrics` 都会报。

**落盘**：`effect_map.connections`（字符串列表，逐条一行）。

### 四、四类样式（源 08g，**色值逐字不改**）

```css
classDef businessGoal fill:#f3f4f6,color:#1f2937,stroke:#d1d5db,stroke-width:2px
classDef platform fill:#e5e7eb,color:#111827,stroke:#9ca3af,stroke-width:3px
classDef targetGroup fill:#f9fafb,color:#1f2937,stroke:#d1d5db,stroke-width:2px
classDef drivingForces fill:#f3f4f6,color:#1f2937,stroke:#d1d5db,stroke-width:2px
```

应用：`class BG0,BG1 businessGoal` / `class PLATFORM platform` / `class TG0,TG1 targetGroup` / `class DF0,DF1 drivingForces`（节点数按实际改）。**平台边框 3px、其余 2px**；全部节点用浅灰底 + 深灰字，**不得自创配色**。源侧 `quality-checklist` 要求的 `primaryGoal` 金色高亮类**不存在**（源侧缺陷：与 `08b:84`「优先级不得用特殊样式」互斥）——**本批不实现该类**。

**落盘**：`effect_map.class_defs`（恰四条，逐字）。

### 五、构图质检（源 08h，逐条过）

- 配置：字体 / 字号 / `flowchart LR` / 节注释四样齐。
- 节点：全部 `<br/>` 起、`<br/><br/>` 收；标题全大写；**无 HTML 标签**；引号与方括号闭合。
- emoji：每群在 TG 与 DF 两处**同一个**；`WANTS`/`FEARS` 标题**无 emoji**；正 ✅ 负 ❌。
- 驱动因素：条数与产物一致；两栏间有空行。
- 连接：BG 全连 PLATFORM、PLATFORM 全连 TG、TG 与 DF 配对；简单箭头；连接数 = 目标数 + 2×人物数。
- 样式：四条 `classDef` 逐字在场；平台 3px、其余 2px；节点数与实际一致。

**落盘**：`effect_map.diagram`（把上面的节点 / 连接 / 样式拼成完整 Mermaid 块，**代码块以 ```mermaid 起**）。

**用户关卡**：出图给用户看（渲染或直接读代码块），问「**这张图讲清了你和用户之间的关系吗？**」

**检查点（六拍）**：① 生成 → ② 落盘 `effect_map` 全段 + `stage: 成品` → ③ 分隔 → ④ 呈出图 + 构图质检结果 → ⑤ 出四选项 → ⑥ 等响应。

**收尾与路由**：`effect_map` 全段齐、`stage: 成品`，读 `./06-finish.md`。本文件到此结束，不再回头。
