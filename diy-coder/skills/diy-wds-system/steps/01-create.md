# Step 1 — 盘点与建库、重复检测、组件落库（Create）

Progress: `[1 盘点现状与建库（用户关卡 1 + init）] → [2 候选扫描与四维比对] → [3 相似度聚合与推荐] → [4 机会与风险打分] → [5 决策呈批与执行（用户关卡 2）] → [6 组件落库与复杂度路由] → ./02-import.md`

**Read (input):** 激活段的门禁回执（`wds-scenarios.yaml` 已定稿）；`{output_dir}/wds-scenarios.yaml` 的 `scenarios[].pages[].id`（页面清单——组件的 `used_in[]` 要引它们）；`{output_dir}/design.yaml` 的 `tokens`（**可选读**：在场则 token 走派生、缺席则独立，裁定 5）；`data/component-prefixes.yaml` · `data/component-categories.yaml` · `data/complexity-router.md`；`list` 回执（续接检测）；用户在本文件各步的回答。
**Write (output):** `{output_dir}/wds-design-system.yaml` 顶层骨架（经 `init` 铸造）+ `components[]` 记录（新建 / 加变体 / 更新三条路径的产物）+ `revisions`。

你是**设计系统架构师**（源 wds-7 的角色名），本次做的是它的 **[C] Create 活动**：从页面规格里长出组件、把重复的拦下来、把复杂的拆开。源侧一句话讲清了本活动的存在理由：**「重复检测是创建之内的一个步，不是一个独立工作流」**（`workflow.md:79`）——本文件按这条把建库、评估、落库串成一条。

**本段纪律**：① **先扫后建**——不许跳过候选扫描直接新建（源各 step 的 ❌ SYSTEM FAILURE 首两条就是「`Skipping any instruction in the sequence`」与「`Generating content without user input`」，见 `step-01` / `step-07` 的失败面清单）；② **不许橡皮图章**——四维等级由你判，但**百分比与等级由引擎算**（聚合段可机械、输入段不可，见第 3 步的边界说明）；③ **决策权在用户**——第 5 步是用户关卡，没点头不许落库。

## 第 1 步 —— 盘点现状与建库（源 `[M] step-01` + `wds-7 step-08a`）（**用户关卡 1**）

**先说清为什么**：源 `step-08a` 的开场句是「这是你的第一个设计系统组件」——建库动作**由首个组件触发**，不是先建一个空壳等组件来。所以这一步只做两件事：把系统现状摊开（源 `[M] step-01` 的清册 + 缺口分析），然后一次把骨架铸成。

**清册与缺口分析**（源 `steps-m/step-01:57–75`）：

```
python "{project-root}/.claude/skills/diy-wds-system/scripts/wds_system.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json
```

回空列表 → 新库，直接进呈批；回已有记录 → 播报六字段（ID / 名称 / 分类 / 前缀 / 复杂度 / 状态），并同步做源侧的三项缺口分析（**只报不做**，处置在第 6 步与本技能 `05-finish`）：

| 缺口 | 判据 | 出处 |
| --- | --- | --- |
| 规格有、系统无 | 页面规格里出现的组件没有对应记录 | 源 `step-01:71` |
| 系统有、无人用 | 记录 `used_in: []` | 源 `step-01:72` |
| 用法不一致 | 同组件在不同页属性/状态不同 | 源 `step-01:73`（细核归 `05-finish`） |

**提取时机规则**（裁定 17，**唯一阈值**）：**第二次使用才提取**——同一模式（同状态、同行为）第一次出现时留在页面规格里当一次性件，**第二次出现**才提取进设计系统。
〔**源侧口径归一**〕源另有对照规则「**间距首次使用即提取**」（`workflow-design-system.md:27–28`）——**本批不保留**（裁定 17 明定：只留「二次使用」一条阈值，KISS）。**它在本技能里已无对象**：间距名不再由本活动产生，而是**派生自 `design.yaml.tokens.spacing`**（裁定 5），故「何时提取间距」这个问题已不存在。

**呈批（用户关卡 1）**：呈出「库现状（或：尚无库）+ 打算落的首个组件（类型 / 前缀 / 分类 / 复杂度）+ 提取时机口径」，**等点头**。没拿到明确点头不许 `init`。

**铸骨架**（`init` 是本技能**唯一写盘**子命令）：

```
python "{project-root}/.claude/skills/diy-wds-system/scripts/wds_system.py" init --mode <on|off> --prefix <p> [--name "<组件名>"] [--complexity <simple|moderate|complex>] --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `--mode` 缺省 **`on`**（裁定 17：设计系统默认纳入设计流水线；**显式关闭 = 一行写 `off`**）。
- `--prefix` **必填**：空值 → `EMPTY_FIELD`、非法值 → `ENUM_INVALID`（两者都零产出）；**26 条前缀**见 `data/component-prefixes.yaml`（机械取数：源 `step-08b:68–95` 的箭头表 26 行）。
- **上游门禁**：`wds-scenarios.yaml` 缺失 → `MISSING_FILE` 零产出（路由 `diy-wds-scenarios`）；`project.status ≠ 已定稿` → `STATUS_MISMATCH` 零产出。
- **token 段**（裁定 5）：`design.yaml` 在场 → `tokens.source.mode: 派生`，`tokens.namespaces` 逐字取它的键集；**缺席 → `独立` 降级 + warning**（不阻断），此时 token 名按设计系统自己的表定。
- 已有产物 → **不覆盖**（只刷 `project.updated` + warning）；产物损坏 → `UNPARSABLE_YAML` 拒绝且零写入。
- `project.name` / `created` 与首条记录的 `id` 由 `init` 铸造后**不再由你改**。

**检查点（六拍）**：① 生成 → ② 落盘（`init` 铸骨架）→ ③ 分隔 → ④ 呈出回执与骨架摘要 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 候选扫描与四维比对`。

## 第 2 步 —— 候选扫描与四维比对（源 `step-01` + `step-02`）

**先说清为什么**：源 `step-01` 的原话是「先扫再判」——扫得窄，后面的分数再准也是错的。这一步因此分成**半机械的检索**与**不可机械的比对**两半，边界写清楚，不许混。

### 2.1 候选检索（源 `step-01:56–62`；**半机械**）

规则是「读组件全量 → 按类型过滤」：先 `list --prefix <同前缀>` 取同类型候选（机械），**再把跨前缀的功能近邻显式列全**（例：加 `drp` 前要看 `lnk` / `tab`——源侧类型判定本身是判的，不是查的）。候选清单每条带：`id` / 名称 / 变体数 / 状态集 / 关键样式 / 使用次数。

### 2.2 四维比对（源 `step-02:56–199`；**不可机械，人工判定**）

> **★ 边界声明（本批的诚实口径）**：源 `step-02:94–199` 的四维比对**只有散文示例、没有任何字段级比对规则**（如 `✓ Size: medium (both)` / `✗ Current: Has icon on left`）——**这是给模型看的示范，不是可机械实现的判据**。故本批：**四维等级由会话逐维判定 + 用户逐维确认**，引擎**不重算**；只有它下游的聚合段（第 3 步）可机械。**不得假装全自动。**

逐维按源的四类属性表比对，每维给一个等级（`high` / `medium` / `low`）：

| 维 | 源属性清单（`step-02:60–92`） |
| --- | --- |
| **Visual** | 尺寸 / 形状 / 配色 / 字体排版 / 内外边距 / 边框 |
| **Functional** | 目的意图 / 用户动作 / 输入输出类型 / 校验规则 / 必填可选 |
| **Behavioral** | 状态集 / 交互 / 动画过渡 / 键盘支持 / 无障碍 |
| **Contextual** | 使用场景 / 频次 / 与其他组件的关系 / 用户旅程阶段 |

**落盘**：本步结论只在会话里带（候选清单 + 四个等级 + 逐维的相同点 / 差异点），**不写盘**；写盘在第 6 步。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘，仅记结论）→ ③ 分隔 → ④ 呈出候选清单与四维比对 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 相似度聚合与推荐`。

## 第 3 步 —— 相似度聚合与推荐（源 `step-03:56–167`；**可机械段，交引擎算**）

**先说清为什么**：四维等级一旦给全，剩下的全是算术——**算术不该由模型做**（源侧三处标定不一致正说明人算会漂）。这条命令是聚合段的唯一实现：

```
python "{project-root}/.claude/skills/diy-wds-system/scripts/wds_system.py" similarity --visual <high|medium|low> --functional <high|medium|low> --behavioral <high|medium|low> --contextual <high|medium|low> --json
```

把第 2 步的四个等级原样传进去，取回执的 `similarity.{percentage, level, level_number, recommendation, key_factors}`。

**引擎实现的公式与阈值**（逐字取源 `step-03:149–167` 的 action 块）：

```
Overall = Visual×0.30 + Functional×0.30 + Behavioral×0.25 + Contextual×0.15
数值映射：high=1.0 / medium=0.6 / low=0.2
百分比 = Overall × 100
```

| 级 | 区间 | 源等级名 | 推荐 |
| --- | --- | --- | --- |
| L1 | 95–100 | Identical | 复用既有组件引用 |
| L2 | 80–94 | Very High Similarity | 考虑给既有组件加变体 |
| L3 | 65–79 | High Similarity | 设计师定：加变体还是新建 |
| L4 | 45–64 | Medium Similarity | 倾向新建，请设计师确认 |
| L5 | 20–44 | Low Similarity | 新建组件 |
| L6 | 0–19 | No Similarity | 必新建组件 |

**三处源侧标定不一致的处置**（census-3 §5.3 实测；本批逐条裁定，**登记而非默改**）：

1. **维度口径取计算段**：源 `step-02:213–217` 把 dim 等级定义成 `High=80%+ / Medium=50–79% / Low=<50%`，而 `step-03:158–160` 把 Low 映射成 `0.2`（=20%）——**Low 的区间被压成单点、非单调**。本批**取 `step-03` 的计算段**（数值映射与公式同段，是聚合段的权威）；`step-02` 那张是给模型判维度用的**口语带**，不作数值来源。
2. **示例取 72%**：源 `step-02:254` 给「Overall: Medium-High (71%)」，而按同一公式代入同一组维度分（1.0 / 0.6 / 0.6 / 0.6）得 **0.72**；源 `step-03:169–184` 自己的示例也是 **72%**。本批取 **72%**（两处对一处）。
3. **「High」一词两义 → 呈现层改用等级号**：源 `step-06:351` 的「High Similarity (80%+)」指 **L1+L2**，而 `step-03:88` 的「Level 3: High Similarity」是 **65–79**。本批在呈出与落盘时**一律用 `L1…L6` + 区间**，不用裸词「High」。

**一条连带缺陷（登记不改）**：在 high=1.0 / medium=0.6 / low=0.2 三值映射下，**L6（<20）取不到任何组合**——16 种输入的百分比最小值是 20（全 low）。范围收缩是源公式的固有结果；本批**不改映射**（改了就不再是源算法），只在呈出时保留该级。

**落盘**：不写盘（只读命令）；把回执的 `percentage` / `level_number` / `recommendation` 带进第 4 步。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 呈出百分比与等级 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 机会与风险打分`。

## 第 4 步 —— 机会与风险打分（源 `step-04` + `step-05`）

**先说清为什么**：源把这一步拆成两张表是有道理的——**同一件事的好处分与坏处分必须分开列**，否则推荐会变成「只说好处」。本批把两张表并进一个小节，因为它们读同一份输入（第 3 步的分类）且同刻呈出。

**三条候选路径**（源 `step-04:56–72`，逐字保留）：

| 路径 | 含义 |
| --- | --- |
| **A 复用** | 直接用既有组件 |
| **B 加变体** | 给既有组件加一个变体 |
| **C 新建** | 造一个新组件 |

**逐路径打分**（源 `step-04:76–177` 的机会框架 / `step-05:58–159` 的风险框架——两张框架各 3 项，逐条给分）：

- **机会侧**（源 Option 1/2/3 各列 3 项收益）：复用省下的实现与维护、变体带来的表达力、新建换来的边界清晰。
- **风险侧**（源同构的 3 项风险）：复用带来的语义污染、变体的组合爆炸、新建的重复度。
- **`deal_breaker`**（源 `step-05:257–286`）：逐路径判有没有**一票否决**项，有则**必须给 `mitigation`**，否则该路径出局。

**落盘**：只在会话里带；写盘在第 6 步（结论落 `components[].notes` 与本技能 `revisions`）。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 呈出机会表与风险表 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 5 步 —— 决策呈批与执行`。

## 第 5 步 —— 决策呈批与执行（源 `step-06` + `step-07`）（**用户关卡 2**）

**先说清为什么**：源 `step-06` 的末尾是一句 `WAIT`，`step-07` 只执行三条已定路径之一——**决策归用户，执行归你**。这一点不许省。

### 5.1 呈批（源 `step-06:56–296` 的六段式）

依次呈出：① **上下文摘要**（要落的组件是什么、它要接哪一页）；② **三个选项**；③ **取舍表**（机会 × 风险，逐路径一行）；④ **详细分析**（高分路径的两侧证据）；⑤ **你的推荐**（含推荐理由，并**明写哪个等级驱动了它**——L1/L2 倾向 A/B、L4–L6 倾向 C、L3 是分水岭）；⑥ **请用户拍板**。

**没拿到明确点头不许落库。**

### 5.2 执行（源 `step-07:72–405` 的三条路径）

| 路径 | 源步骤 | diy 落点 |
| --- | --- | --- |
| **A 复用**（源 Path A） | 确认 → 抽取页相关内容 → 建引用 → 更新使用计数 | 既有记录的 `used_in[]` 追加该页 `SC-<nn>.P<n>`（**不新建记录、不铸号**） |
| **B 加变体**（源 Path B） | 确认 → 抽组件级信息 → 改组件定义 → 建引用 → 更新使用计数 | 既有记录的 `variants[]` 追加一条 + `version.changes` +1 + `used_in[]` 追加该页 |
| **C 新建**（源 Path C） | 确认 → 铸 ID → 抽组件级信息 → 建组件记录 → 建引用 → 更新索引 | 进第 6 步铸号落库 |

**落盘**：按上表就地编辑 `wds-design-system.yaml`（`components[]` 的对应记录 + `revisions` 追加一条 `{date, change, reason}`，`change` 点名 `[prefix]-[NNN]` 而不复制内容）。

**检查点（六拍）**：① 生成 → ② 落盘（记录编辑 + `revisions`）→ ③ 分隔 → ④ 呈出执行结果 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 6 步 —— 组件落库与复杂度路由`。

## 第 6 步 —— 组件落库与复杂度路由（源 `step-08b` + `step-08c` + `step-08d` + `[M] step-02` + `COMPLEXITY-ROUTER`）

**先说清为什么**：源 `workflow-create.md:54–63` 自己就把 Create new / Update / Add variant 归成**同一组「Step 3: Component Operations」**——本批照它的分组并成一个小节；`[M] step-02` 的「定义组件」与 `step-08b` 的「新建组件」是同一件事的一轻一重两个入口（census-3 §7.1），一并归此。

### 6.1 铸号（源 `step-08b:56–64`）

新组件一律 **`[prefix]-[NNN]`**：扫同前缀现有 ID → 计数器 +1 → 三位补零。**逐前缀独立计数、顺序递增、不重编不复用**（引擎 `check` 机械核：跳号 → `SET_MISMATCH`、重号 → `DUPLICATE_ID`）。

### 6.2 十一条必填（源 `templates/component.template.md` 的 11 段 → `components[]` 的键）

| 源段 | diy 键 | 备注 |
| --- | --- | --- |
| Type / Category / Purpose（Overview） | `name` · `category` · `complexity` | `category` 必在 6 分类内，且与前缀表同前缀那一行一致 |
| Variants | `variants[]` | 源 `step-08d` 的变体命名与专属样式 |
| States | `states[]`（每条 `{name, signals[]}`） | 必含 `默认`；源要求状态带描述 |
| Styling | `styling{visual_properties, layout, library_component}` | `library_component` = 源 `component-library-config` 的映射（**Mode C 的落点**） |
| Behavior | `behavior{interactions[], animations[], rules[]}` | 源 `Interactions` + `Animations` + 业务规则 |
| Accessibility | `accessibility{aria, keyboard[], screen_reader}` | 源 `ARIA / Keyboard / Screen Reader` |
| Usage | `usage{when_to_use, when_not_to_use[], best_practices[]}` | — |
| Used In | `used_in[]` | 引 `SC-<nn>.P<n>`；**引擎核它必须解析到 `wds-scenarios.yaml`** |
| Related Components | `related[]` | 分解后的父子关系写这里（见 6.3） |
| Version History | `version{created, updated, changes}` | `changes` 计数 |
| Notes | `notes` | — |
| （新增）Design Tokens | **`token_refs[]`** | **裁定 5 的机械兑现面**：每条 `命名空间.名`（`color.*` / `spacing.*` / `typography.*`），值一律回 `design.yaml.tokens` 取——**本产物不复述值**；解析不到 → `TOKEN_UNRESOLVED` |

**更新与加变体**（源 `step-08c` / `step-08d`）：改既有记录时**先回读记录**，改后 `version.updated` 刷今天、`version.changes` +1；源 `step-08c` 的**影响分析**（scope / breaking changes / compatibility）与**回写受影响页面**在 diy 侧落成两件事——① 在 `revisions` 写清影响面；② `used_in[]` 对账（页面侧引用归 C·3 的 `diy-design`，本技能**只读不写**）。

### 6.3 复杂度路由（源 `[M] step-02:75–81` → `data/complexity-router.md`）

逐组件判三级（Simple / Moderate / Complex，判据见 `data/complexity-router.md` §1），写进 `complexity`：

- **Simple** → 单条记录，`states` 至少 1 条；
- **Moderate** → 单条记录 + `notes` 一句写清「哪一部分将来会独立」；
- **Complex** → **先问用户要不要拆**（源 `<ask>` 二选一，**绝不替用户拆**）；拆则**拆成多条记录、各铸各的号**，父件在 `related[]` 列子件 ID；用户不拆也放行，但把源侧警示原样带出——「这可能产生一份过大的规格，维护成本会上升」。
  **`WHERE / HOW / WHAT` 三问的 diy 承载位**：`usage`+`used_in`（WHERE）· `styling`+`states`+`variants`（HOW）· `behavior`（WHAT）。

**落盘**：`components[]` 记录 + `revisions`。**完成本文件后**读 `./02-import.md`（若用户还要导入既有设计系统）或直接跳 `./03-view.md`。

**检查点（六拍）**：① 生成 → ② 落盘（组件记录）→ ③ 分隔 → ④ 呈出记录摘要与铸号 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

本文件到此结束，不再回头。
