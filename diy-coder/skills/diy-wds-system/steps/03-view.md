# Step 3 — 预览与浏览（View + Browse 合一；含 catalog 生成链）

Progress: `[1 载入系统数据与选件] → [2 生成浏览应用] → [3 交互复核与反馈收集] → [4 生成 catalog] → ./04-edit.md`

**Read (input):** `{output_dir}/wds-design-system.yaml` 全量（`tokens` / `categories` / `prefixes` / `components[]`）；`{output_dir}/design.yaml` 的 `tokens`（**在场则渲染出真实色板与字号**——裁定 5 的值只在那边）；`templates/catalog.template.html`（18 个占位符）；`list` 回执（选件用）。
**Write (output):** `{output_dir}/wds-design-system-catalog.html`（一次运行一份，可反复重生成）；反馈项进 `revisions` 或路由到 `./04-edit.md` / `./01-create.md`。

你是**浏览器的搭建者**（源 `workflow-view.md` 的精选预览 + `workflow-browse.md` 的四视图浏览器）。**本步把源的 V 与 B 合成一件事做**（裁定 4）：源侧两条工作流都产一个 localhost 应用、功能高度重叠（一个是「看我选的」，一个是「随便逛」）——**合一省一份重复实现**，差别的部分（选件 vs 全量）落成同一个应用的**一个过滤入口**，而不是两个应用。

**本段纪律**：① **不开服务、不阻塞**——源的 localhost 服务与端口（`workflow-view.md:36`「Build a minimal localhost application」/ `workflow-browse.md:57,60`「Start the localhost server」+ `http://localhost:XXXX`，四路由 `/tokens` `/components` `/graph` `/search` 见 `:63–66`）在 diy 侧换成**静态 HTML 文件**（本项目无 localhost 服务依赖，且 diy 的渲染纪律是静默旁路）；② **产物可重生成**——源 `workflow-browse.md:86` 明写「退出时丢弃生成物」，diy 侧它落在 `{output_dir}/` 且**是 B7 必交的 viewer 相关项**，故**留存**（每次生成即全量覆盖，永远反映最新状态）；③ **只读系统**——浏览过程发现问题**不改库**，路由到 `./04-edit.md` 或 `./01-create.md`。

## 第 1 步 —— 载入系统数据与选件（源 `[V] step-01` + `[B] step-01`）

**先说清为什么**：源 V 的第 1 步是「让用户挑要看哪些组件」，B 的第 1 步是「把全部数据读进来」——**同一件事的两半**（读全量是前提，挑是范围）。合一后：读全量是机械动作，挑是用户选择。

**读全量**（源 `[B] step-01:20–28`）：把 `tokens`（三个命名空间）/ `components[]`（含变体、状态、令牌依赖）/ `categories` / `prefixes` 全部读进来，并**构出关系图**（组件 → 它引用的令牌；令牌 ← 引用它的组件）——这是源侧 `Relationship Viewer` 的数据底座。
**值从哪来**：本产物的 `token_refs` 只有**名字**（裁定 5 的引用不复述）；要渲染色板与字号，**回 `design.yaml.tokens` 取值**。`design.yaml` 缺席（`tokens.source.mode: 独立`）→ 色板渲成名字 + 标注「独立定义，值见源文件」。

**选件**（源 `[V] step-01:24–32`）：呈出组件目录（`list` 回执：ID / 名称 / 分类 / 前缀 / 复杂度 / 状态），问用户「要看哪些」——逗号分隔，或 `all`（全量 = 源 B 的形态）。**默认 `all`**。

**落盘**：不写盘（选件结果是第 2 步的入参）。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 呈出目录与选件确认 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 生成浏览应用`。

## 第 2 步 —— 生成浏览应用（源 `[V] step-02` + `[B] step-02` + `[B] step-03`）

**先说清为什么**：源 B 的四视图是这条工作流真正的独有能力（Token Explorer / Component Catalog / Relationship Viewer / Intent Search），V 的「全变体并排 + 全状态 + 断点 + 深浅色」是它真正的独有能力——**清单里一条都不能少**，合的是外壳不是能力。

装填 `templates/catalog.template.html`，按 18 个占位符逐个填（见第 4 步的表），生成 `{output_dir}/wds-design-system-catalog.html`。**四视图与精选预览各自的能力落点**：

| 源能力 | 出处 | 在应用里的落点 |
| --- | --- | --- |
| **Token Explorer**（可筛选 / 可排序 / 带实时预览的令牌表） | `[B] step-02:34–37` | 令牌区：三命名空间分表；色值渲色块、间距渲长度条、字号渲真实字样 |
| **Component Catalog**（缩略网格 → 展开全变体 / 全状态 / 令牌依赖） | `[B] step-02:39–43` | 组件区：每卡片展开变体并排 + 状态并排 + `token_refs` 清单 |
| **Relationship Viewer**（点组件高亮它用的令牌，点令牌高亮用它的组件） | `[B] step-02:45–48` | 关系区：数据在卡片上以 `data-tokens` 落属性，点选即高亮双向链 |
| **Intent Search**（自然语言输入 → 匹配名字/描述/分类/用法） | `[B] step-02:50–53` | 搜索框：对名称 / 分类 / 用法 / 令牌名做包含匹配，结果带令牌名可复制 |
| **精选预览**（V：全变体并排 / 全状态 / 断点 / 深浅色） | `[V] step-02:36–45` | **就是 Component Catalog 的被选子集**：第 1 步选件结果只装填被选中的组件；断点与深浅色由样式表里的媒体查询与 `prefers-color-scheme` 承载 |

〔**源侧缺陷修复（D22）**〕源侧是 localhost 服务 + 四路由 + 端口占位 `XXXX`；diy 侧**不开服务**——单文件静态 HTML，四视图落成同页四个区，`/tokens` 类的路由**不保留**（无服务的路由是死物）。登记为「平台耦合 → 裁」。

**落盘**：写 `{output_dir}/wds-design-system-catalog.html`（**本技能唯一的非 YAML 写面**；`/03-view` 每次运行整份覆盖）。

**检查点（六拍）**：① 生成 → ② 落盘（写 HTML）→ ③ 分隔 → ④ 呈出生成结论（路径 + 组件数 + 令牌数）→ ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 交互复核与反馈收集`。

## 第 3 步 —— 交互复核与反馈收集（源 `[V] step-03/04` + `[B] step-04`）

**先说清为什么**：源两条工作流都收了反馈，而且**都规定了反馈的去处**（V 路由 [E] Edit 或 [C] Create、B 路由 [C]/[E]/[V]）——收反馈不是终点，**路由才是**。

用户对着生成的应用看，你逐条记下发现（源 `[V] step-04:57–61` 的三字段：**组件名 / 问题描述 / 严重度**），然后**每条给一个去处**：

| 发现类型 | 去处 |
| --- | --- |
| 令牌名不对 / 缺令牌 | `./04-edit.md`（本地改组件定义）或回 `design.yaml` 侧（**token 单一源在那边，本技能不写它**） |
| 组件定义要改（属性 / 状态 / 变体） | `./04-edit.md` |
| 要新增组件 | `./01-create.md` |
| 用法不一致（同组件在不同页表现不同） | 本技能 `05-finish`（用法一致性校验的入口） |
| 纯观察项（不改，先记下） | `revisions` 追加一条 |

**落盘**：`revisions` 追加（`change` 点名 `[prefix]-[NNN]`，`reason` 写为什么）；其余发现作为下一步的入参。

**检查点（六拍）**：① 生成 → ② 落盘（`revisions`）→ ③ 分隔 → ④ 呈出反馈清单与路由 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 生成 catalog`。

## 第 4 步 —— 生成 catalog（源 `step-08e`；**catalog.html 生成链保留**）

**先说清为什么**：源 `step-08e`（755 行）是「把当前状态装进一份 HTML」的独立链路，计划把它定为 **B7 必交的 viewer 相关项**（裁定 4 连带）——**本步是它的唯一落点**。源侧每次改完组件都要重跑它（`workflow-create.md` 的 AFTER COMPLETION 明写「Run catalog generation」）。

**19 个占位符 → 18 个的逐条对译**（源 `step-08e:103–123` 的变量表 vs `templates/catalog.template.html`，机械核对一致）：

| # | 源占位符 | diy 取值 | 处置 |
| --- | --- | --- | --- |
| 1 | `{{PROJECT_NAME}}` | 本产物 `project.name` | 保留 |
| 2 | `{{PROJECT_ICON}}` | 用户给或留空 | 保留 |
| 3 | `{{PROJECT_DESCRIPTION}}` | 用户一句描述 | 保留 |
| 4 | `{{PROJECT_OVERVIEW}}` | 组件数 / 分类分布 / 令牌数 | 保留 |
| 5 | `{{VERSION}}` | 本产物最近一条 `revisions.date` | 保留 |
| 6 | `{{COMPONENT_COUNT}}` | `len(components[])` | 保留 |
| 7 | `{{DESIGN_SYSTEM_MODE}}` | `design_system_mode`（`on` / `off`） | 保留（裁定 17 归一后的唯一开关键） |
| 8 | `{{CREATED_DATE}}` | `project.created` | 保留 |
| 9 | `{{LAST_UPDATED}}` | `project.updated` | 保留 |
| 10 | `{{INSTALLATION_INSTRUCTIONS}}` | 用户给（可留空） | 保留 |
| 11 | `{{USAGE_EXAMPLE}}` | 引一条记录的片段 | 保留 |
| 12 | `{{COMPONENT_NAVIGATION}}` | 按 6 分类分组的侧栏 | 保留（**取 6 分类，不取源 README 骨架的 4 分类**——源 D12 缺陷） |
| 13 | `{{DESIGN_TOKENS_CONTENT}}` | 三命名空间总表 | 保留 |
| 14 | `{{COLOR_TOKENS}}` | 色板（值取 `design.yaml.tokens.color`） | 保留 |
| 15 | `{{TYPOGRAPHY_TOKENS}}` | 字号样张（同上） | 保留 |
| 16 | `{{SPACING_TOKENS}}` | 间距条（归一后的 10 个名字） | 保留 |
| 17 | `{{COMPONENTS_CONTENT}}` | 组件卡片（含变体 / 状态 / 令牌依赖） | 保留 |
| 18 | `{{CHANGELOG_CONTENT}}` | `revisions` 列表 | 保留 |
| 19 | `{{FIGMA_LINKS}}` | — | **裁**（裁定 6：不接外部服务，Figma 通道整块裁） |

**保留的是唯一链路**：源 `step-08e` 里还有「生成后直接 `git add` + `git commit`」（`:585–596`，census-3 D18）——**整块裁**（与 diy 的副作用纪律直接冲突：本技能零 git 写操作，提交由用户决定）。

**落盘**：`{output_dir}/wds-design-system-catalog.html` 整份覆盖。

**收尾与路由**：本文件到此结束，读 `./04-edit.md`（要改组件）或 `./05-finish.md`（要定稿）。

**检查点（六拍）**：① 生成 → ② 落盘（覆盖 HTML）→ ③ 分隔 → ④ 呈出 18 个占位符的装填结论 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

本文件到此结束，不再回头。
