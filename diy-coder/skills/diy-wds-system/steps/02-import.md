# Step 2 — 导入既有设计系统（Import）

Progress: `[1 识别来源] → [2 提取令牌] → [3 提取组件] → [4 写入本产物] → [5 校验导入] → ./03-view.md`

**Read (input):** `./01-create.md` 的放行（骨架已铸）；用户提供的来源（**URL / 文件导出 / 代码库**三源——**Figma 源已裁**，见下）；`{output_dir}/design.yaml` 的 `tokens`（可选读，在场则导入的令牌要回落到它）；`{output_dir}/wds-design-system.yaml` 现有记录；`data/component-prefixes.yaml` · `data/component-categories.yaml` · `data/token-vocabulary.yaml`。
**Write (output):** `components[]` 追加记录 · `tokens.namespaces` 的对账结论 · `revisions`（导入批次一条）。

你是**导入的接引者**（源 `workflow-import.md` 的四源接入）。源侧这一步的全部价值是：**把别人已经做好的东西变成这套库能认的形状**——不是重做，是翻译。

**本段纪律**：① **来源三源，不是四源**——源侧 `workflow-import.md:21–28` 列 URL / File / **Figma** / Code 四源，其中 **Figma 源随裁定 6 裁**（用户 2026-09-21 拍板不接外部服务），本批保留 **URL / File / Code** 三源；② **令牌不新造名字**——导入的令牌必须归到本产物的三个命名空间（`color` / `spacing` / `typography`），归不进去的**逐条记 gap**，不塞第四个桶；③ **模糊映射必须标出来**（源 step 2 明令 `Mark any ambiguous mappings`）。

## 第 1 步 —— 识别来源（源 `workflow-import.md` step 1）

**先说清为什么**：三种来源的抽取手法完全不同（文档要读语义、文件要读结构、代码库要读实现），先说清来源，后面三步才有明确的做法。

问用户来源属于哪一类，并各取一件**可核的凭据**：

| 来源 | 说明 | 取什么作凭据 |
| --- | --- | --- |
| **URL** | 公开的设计系统文档（如 Material UI / Chakra / 自建） | 具体页面路径 |
| **File** | 导出的令牌文件（JSON / CSS 自定义属性 / SCSS 变量） | 文件路径 |
| **Code** | 既有代码库里的组件库 | 目录路径 |

〔**源侧缺陷修复（D11）**〕源 `workflow-import.md:60` 写输出 `component-library-config.md`（**无目录前缀**），而同技能 `workflow.md:109` 与 `step-08a:205` 都带 `D-Design-System/` 前缀——同一技能内不自洽。diy 侧无此文件（`component-library-config` 的职能折进 `components[].styling.library_component`），**缺陷自然消失**，登记为「按裁定 2 的 YAML 化消解」。

**收尾动作**：把来源类型与凭据写进会话上下文，并声明「**Figma 源不支持**」（若要 Figma 请先自行导出为文件再走 File 源）。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 呈出来源判定 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 提取令牌`。

## 第 2 步 —— 提取令牌（源 `workflow-import.md` step 2）

**先说清为什么**：源把令牌列成 7 类（Colors / Typography / Spacing / Shadows / Borders / Breakpoints / Motion）——这是**来源侧的分类**，不是本产物的分类。本步做的是**一次映射**：把来源的 7 类压进本产物的 3 个命名空间。

**逐类映射**（源 `:33–41` 的 7 类 → 本产物的 3 命名空间）：

| 源类（7） | 本产物命名空间 | 处置 |
| --- | --- | --- |
| Colors | `color` | 归到 `design.yaml.tokens.color` 的键集；**键对不上就标模糊** |
| Typography | `typography` | 归到 `family_base` / `family_heading` / `scale` |
| Spacing | `spacing` | **必须落到 `data/token-vocabulary.yaml` 的 10 个归一名字**上；来源的第 4 套写法（数值阶）按「`n × unit`」折算，**不新增名字** |
| Shadows / Borders / Motion | `typography` 之外 → **记 gap** | 本产物的命名空间装不下（`design.yaml.tokens` 只有三个桶）→ **逐条记 gap 并说明去处**（归 C·3：`design.yaml` 若要扩桶，本侧随批跟进） |
| Breakpoints | **记 gap** | 同上；且源侧断点用 `sm` / `md` 裸名，**与间距的旧裸名撞名**（正是归一表依据②要消掉的） |

〔**源侧缺陷修复（D15/D16）**〕源侧四套并存的间距词汇表（`space-3xs…3xl` / `zero…3xl` / 含 `flex` 的 8 元 / Tailwind 数值阶）在本步**一律按 `data/token-vocabulary.yaml` 归一表折算**——该表是四套 → 一套的唯一定义，依据逐条在该表内。

**令牌呈批**：逐条呈出「来源令牌 → 归一后名字 → 值来源（`design.yaml.tokens`）」，**模糊映射逐条标出**；`design.yaml` 缺席时令牌走 `独立` 模式（值就地定，并在 `revisions` 记一条）。

**落盘**：`tokens.namespaces` 若需调整就**就地改名**（值一律不写进本产物——裁定 5）。

**检查点（六拍）**：① 生成 → ② 落盘（`tokens.namespaces` 对账结果 + gap 清单）→ ③ 分隔 → ④ 呈出映射表 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 提取组件`。

## 第 3 步 —— 提取组件（源 `workflow-import.md` step 3）

**先说清为什么**：源 step 3 的四条指令里，**第 4 条才是关键**——「把不能干净映射的标出来」。导入的最大风险不是漏，是**硬塞**。

逐条做（源 `:47–52`）：

1. 列出来源里**全部**能识别的组件；
2. 每个给：名称 / 属性与变体 / 它依赖的令牌；
3. 映射到本产物的组件形状（第 6 步的 11 段 —— 见 `./01-create.md` 6.2）；
4. **标出映射不干净的**（名称对不上类型前缀表、变体语义不明、令牌依赖悬空）。

**分类与前缀归属**：按 `data/component-prefixes.yaml` 的 26 条前缀逐条归；**归不进去的类型**（比如来源有 breadcrumb，而本表没有）**逐条记 gap 并请用户裁决**——归到最近的现有前缀（在 `notes` 注明借用）或按同款命名规则新增前缀并回写前缀表。**不许静默丢弃。**

**呈批**：组件清单逐条呈出（名称 / 归属类型前缀 / 变体数 / 令牌依赖数 / 是否干净映射），**等用户点头**。

**落盘**：本步结论进会话，写盘在第 4 步。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 呈出组件清单 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 写入本产物`。

## 第 4 步 —— 写入本产物（源 `workflow-import.md` step 4）

**先说清为什么**：源 step 4 要生成三件（`design-tokens.md` / `components/*.md` / `component-library-config.md`）——那是源侧的三文件形态。diy 侧**只写一个 YAML**（裁定 2），所以这一步的实质是「**逐条落到 `components[]`**」。

逐组件落库，规则与 `./01-create.md` 第 6 步**逐条相同**（同一套键、同一套铸号纪律），差别只在**来源不是页面规格而是外部系统**：

- **铸号**：`[prefix]-[NNN]` 逐前缀独立计数（导入也要走铸号，**不许借用来源的 ID**）；
- **`used_in[]` 留空**——导入的组件尚未被本项目任何页引用（源侧同样不建页引用）；后续由 `used_in` 对账补齐；
- **`complexity`**：按 `data/complexity-router.md` §1 判；**Complex 件同样要问用户拆不拆**；
- **`token_refs[]`**：逐条落第 2 步归一后的名字（`命名空间.名`），**解析不到 → `TOKEN_UNRESOLVED`**；
- **`styling.library_component`**：来源若来自某个组件库（Source=Code 常见），映射写这里（源 `component-library-config` 的 `WDS Component → Library Component` 表 → 本字段）。

**批量落库的落盘纪律**：一次 `revisions` 追加**一条**导入批次记录（`change` 写「导入 <来源类型>，N 条组件」，`reason` 写清来源与范围），**不为每条组件各写一条**——否则 `revisions` 会被导入刷屏。

**检查点（六拍）**：① 生成 → ② 落盘（`components[]` 逐条 + `revisions` 一条批次记录）→ ③ 分隔 → ④ 呈出落库结果与铸号表 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 5 步 —— 校验导入`。

## 第 5 步 —— 校验导入（源 `workflow-import.md` step 5）

**先说清为什么**：源 step 5 的四项校验是导入的**唯一质量门**——导入最容易出的错是「名字在第 2 步归一了、组件在第 4 步还写着旧名」。这一步把它挡在能力范围内。

跑引擎核（**机械，不靠目检**）：

```
python "{project-root}/.claude/skills/diy-wds-system/scripts/wds_system.py" check --project-root "{project-root}" --output-dir "{output_dir}" --json
```

逐条对齐源的四项校验（源 `:64–71`）与引擎的违规码：

| 源校验项 | 引擎判据 | 违规码 |
| --- | --- | --- |
| 组件引用的令牌全部存在 | `components[].token_refs[]` 逐条解析到 `tokens.namespaces` | `TOKEN_UNRESOLVED` |
| 无孤儿令牌（定义了没人用） | 反向扫：`tokens.namespaces` 里零引用的名字 → **warning**（不阻断：源侧允许备用令牌） | — |
| 命名一致 | 记录 `prefix` / `category` 对 `data/component-prefixes.yaml` · `data/component-categories.yaml` | `ENUM_INVALID` / `SET_MISMATCH` |
| 变体齐备 | 每条 `variants[]` 至少 1 条（源侧「变体齐备」的 diy 判据） | `EMPTY_FIELD`（`--final` 时） |

〔**源侧缺陷修复**〕源 step 5 只给「呈现校验报告，交互式修问题」一句，**没给判据**——本批把四项判据全部机械化为上面的表，并落进引擎 `check`（**导入的校验不另立报告产物**，复检 = 重跑 `check`；承 B7a 裁定 15 同款口径）。

**落盘**：按回执 `where` 就地修、重跑，直到 `exit 0`；修不掉的（如命名空间装不下的类）写进 `revisions` 的 gap 记录。

**收尾与路由**：导入完成即可读 `./03-view.md` 看结果。

**检查点（六拍）**：① 生成 → ② 落盘（修复结果 + gap 记录）→ ③ 分隔 → ④ 呈出校验结论 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

本文件到此结束，不再回头。
