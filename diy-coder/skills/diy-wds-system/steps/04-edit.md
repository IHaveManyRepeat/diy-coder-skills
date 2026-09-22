# Step 4 — 组件就地编辑（Edit；**已去 Figma 通道**）

Progress: `[1 选择组件] → [2 就地编辑组件定义] → [3 变更审批与写回] → [4 同步校验] → ./05-finish.md`

**Read (input):** `{output_dir}/wds-design-system.yaml` 被选记录的全文；`{output_dir}/design.yaml` 的 `tokens`（**可选读**——在场则编辑时以它的值为准，本技能不写它）；`data/component-prefixes.yaml` · `data/component-categories.yaml`（改分类 / 改前缀时的合法值域）；`check` 回执。
**Write (output):** `components[]` 被改记录的对应键 + `version.updated` / `version.changes` + `revisions`。

你是**组件定义的编辑者**（源 `workflow-edit.md` 的作业面）。**本步与源的差别只有一处，但那一处是整块的**——先把账算清（裁定 6 连带的必需登记）：

> ### ★ 裁了什么、留了什么、留的部分为什么不需要外部服务
>
> **裁掉（裁定 6，用户 2026-09-21 拍板「不接任何外部服务」）**：
> 1. **源 `workflow-edit.md` 的整条 Figma 通道**——源 `:8` 的目标句是「Open selected components in **Figma** for visual editing」，`:33–42` 是「生成 Figma 兼容表示 → **经 MCP 集成推送**（或给导出文件）」，`:46–50` 是「在 Figma 里改完再告诉我」，`:57–62` 是从 Figma 拉回改动。**这四段全部依赖外部服务**（Figma MCP / 导出文件回灌），与用户裁决直接冲突。
> 2. **`figma_mappings` 段**（源专属存储 Mode B，`figma-mappings.md`）——同上，**从产物 schema 里整段拿掉**（§2.3 已把它标为「裁」）。
> 3. **源 `[E]` 活动在菜单里的存在理由**（`workflow.md:56`「Open selected components in Figma」）——已改写为「本地编辑组件定义」。
>
> **留下（能力本体，一条不少）**：
> | 源能力 | 源出处 | 留法 |
> | --- | --- | --- |
> | 选中要改的组件 | `:22–31` | 原样（`list` 回执呈出，用户勾选） |
> | 读当前定义与关联令牌 | `:37–39` | 原样（本地读 YAML） |
> | **改动差异（diff）** | `:59` | 原样，且**加强**——见第 3 步的逐键 diff 表 |
> | **按审批写回** | `:60–62`（`Present changes for approval`） | 原样——**写回前必须过审批**，这是本活动的核心纪律 |
> | **改后校验同步**（改了令牌不破坏别的组件 / 变体齐备 / 命名一致） | `:64–72` | 原样，且**机械化**（交引擎 `check`，见第 4 步） |
> | 改完回目录刷新 | `:79` | 原样（路由 `./03-view.md` 重生成 catalog） |
>
> **为什么留下来的部分不需要外部服务**：留下的是「**选中 → 读定义 → 改 → diff → 审批 → 写回 → 校验**」这条链，它操作的**全部对象都是本地文本**——
> ① 编辑对象 = `components[]` 记录的键值（YAML 字段），改键值就是编辑；
> ② diff = **同一记录两次读的对比**（本技能自己就能算，见第 3 步）；
> ③ 校验 = 引擎 `check` 的机械判据（`token_refs` 解析、前缀/分类合法、编号连续、变体齐备）。
> **没有任何一步需要网络、第三方账号或图像服务**——源的「视觉编辑器」只是把同一批键值搬到了 Figma 里改，**搬去的目的是可视化**，而可视化的职能在本技能由 `./03-view.md` 的本地 HTML 应用承接（不依赖任何外部服务）。
> **登记**：Figma 通道的裁撤属**用户裁决的能力裁撤**（非平台耦合），承 B7b 任务书 §0.2 裁定 6。

**本段纪律**：① **改前先 diff、diff 完先审批**——不许静默改记录；② **不动 `design.yaml`**——token 的单一源在那边（裁定 5），本技能对它是**只读**，要改 token 得回 `diy-design`；③ **改完必须重跑 `check`**（第 4 步是硬收尾，不是选做）。

## 第 1 步 —— 选择组件（源 `workflow-edit.md:22–31`）

**先说清为什么**：源这一步的措辞是「Select components to edit」——**先圈定范围再动手**，一次只改用户点名的组件（避免"顺手"改到别处）。

呈出组件目录（`list` 回执六字段），让用户勾选（逗号分隔，**不支持 `all`**——编辑是逐条审批的，全量编辑等于没有审批）。

```
python "{project-root}/.claude/skills/diy-wds-system/scripts/wds_system.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json
```

**落盘**：不写盘。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 呈出目录与选件确认 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 就地编辑组件定义`。

## 第 2 步 —— 就地编辑组件定义（源 `workflow-edit.md:37–39` 的本地读 + 源 `:46–50` 的编辑动作本地化）

**先说清为什么**：源把「读当前规格 + 读关联令牌」（本地）和「在 Figma 里改」（远端）分成两段，**本地那段原样可用，远端那段换成就地编辑**。

**逐条读全**（源 `:37–39`）：读被选记录的**全文**（不是只读要改的那一格——源明令 `Read the complete step file before taking any action` 同款纪律），并读它 `token_refs[]` 指向的令牌（值回 `design.yaml.tokens` 取；缺席则用本产物 `独立` 模式下的本地值）。

**改什么**（六类，逐类给合法值域）：

| 类 | 落点键 | 值域 / 判据 |
| --- | --- | --- |
| A 加状态 | `states[]` | 每条 `{name, signals[]}`；必含 `默认`；`signals` 非空 |
| B 改样式 | `styling.visual_properties` / `styling.layout` | 改样式**只许引 `token_refs` 里的令牌名**，不许写一次性色值/字号（源侧 D18 与 `design.py audit` 的 `one-off-*` 纪律同源） |
| C 改行为 | `behavior.interactions[]` / `.animations[]` / `.rules[]` | — |
| D 无障碍 | `accessibility.{aria, keyboard[], screen_reader}` | — |
| E 文档 | `usage.*` / `notes` | — |
| F 重构（改名 / 改分类 / 改前缀） | `name` / `category` / `prefix`（+ `id`） | `category` 必在 6 分类内且与前缀表一致；**改 `prefix` 等于换 ID**——按铸号纪律重铸（**旧号不复用**），并在 `revisions` 记明新旧号对照 |

〔**源侧缺陷修复**〕源 `step-08c:434` 的「更新 `components/README.md` 统计段」在 diy 侧**整块消失**（无 README 文件，统计由 `list` / `show` 回执与 catalog 的 `{{COMPONENT_COUNT}}` 机械产生）——登记为「按裁定 2 的 YAML 化消解」，并顺带消掉源 D13（总数靠人肉改写）。

**落盘**：就地改 `components[]` 被选记录的对应键；**此时不写 `version` / `revisions`**（那是审批通过后第 3 步的事）。

**检查点（六拍）**：① 生成 → ② 落盘（改记录键）→ ③ 分隔 → ④ 呈出改动前后的片段 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 变更审批与写回`。

## 第 3 步 —— 变更审批与写回（源 `workflow-edit.md:57–62` 的审批内核）

**先说清为什么**：源这条工作流的**核心机制不是可视化，是审批**——「Present changes for approval: Token values changed / New variants added / Properties modified」然后「Update files with approved changes」。**机制原样搬过来，可视化那半由第 2 步的就地编辑替代。**

**逐键 diff**（改前一份、改后一份，逐键列，只列**真变了**的）：

| 源侧 diff 三类 | diy 键 | 呈现 |
| --- | --- | --- |
| Token values changed | `token_refs[]` 的增删 | 逐条列旧名 → 新名 |
| New variants added | `variants[]` 的增删 | 逐条列 |
| Properties modified | `states` / `styling` / `behavior` / `accessibility` / `usage` / `name` / `category` | 逐键列旧值 → 新值 |

**审批**：整块呈出 diff 表，**逐条问「采纳 / 改回 / 搁置」**——源侧的 `FORBIDDEN to auto-fix inconsistencies without user approval`（`steps-m/step-03:46`）在编辑面上同样成立。

**写回**（源 `:62` `Update WDS design system files with approved changes`）：
- 采纳项落键；
- `version.updated` 刷今天、`version.changes` +1；
- `revisions` 追加一条 `{date, change, reason}`——`change` 点名 `[prefix]-[NNN]` 与改动键名，**不复制内容**；`reason` 写为什么（用户的意图，不是「按用户要求」这类空话）；
- **搁置项**写进 `revisions` 的 gap 记录（不许静默丢）。

**检查点（六拍）**：① 生成 → ② 落盘（采纳项 + `version` + `revisions`）→ ③ 分隔 → ④ 呈出审批结果与写回摘要 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 同步校验`。

## 第 4 步 —— 同步校验（源 `workflow-edit.md:64–72`；机械化）

**先说清为什么**：源这一步的三项校验（改了令牌不破坏别的组件 / 变体齐备 / 命名约定维持）是**改完必跑的收尾**——源侧把它写成散文让模型自己核；diy 侧它有引擎，**必须交给引擎**。

```
python "{project-root}/.claude/skills/diy-wds-system/scripts/wds_system.py" check --project-root "{project-root}" --output-dir "{output_dir}" --json
```

逐条对齐源的三项：

| 源校验项（`:66–71`） | 引擎判据 | 违规码 |
| --- | --- | --- |
| 改动的令牌不破坏其他组件 | `used_in[]` / `token_refs[]` 逐条解析；被改记录的引用是否仍在 `tokens.namespaces` 内 | `TOKEN_UNRESOLVED` / `UNKNOWN_ID` |
| 变体齐备 | `variants[]` 至少 1 条（`--final`） | `EMPTY_FIELD` |
| 命名约定维持 | `id` 形态 `[prefix]-[NNN]`、`prefix` ∈ 26 表、同前缀编号连续 | `SET_MISMATCH` / `ENUM_INVALID` |

**跨记录影响面**（源 `step-08c` 的影响分析内核，`scope / breaking changes / compatibility`）：改一条记录时，**列出引用它的页面**（`used_in[]`）并把影响面写进 `revisions` 的 `reason`；页面侧引用的改写**不归本技能**（页面规格在 C·3 的 `diy-design`，本技能只读不写）。

**收尾与路由**：按回执 `where` 就地修、重跑到 `exit 0`；然后读 `./05-finish.md`（定稿）或 `./03-view.md`（重生成 catalog 看效果）。

**检查点（六拍）**：① 生成 → ② 落盘（修复结果）→ ③ 分隔 → ④ 呈出 `check` 结论 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

本文件到此结束，不再回头。
