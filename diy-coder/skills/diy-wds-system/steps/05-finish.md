# Step 5 — 用法一致性校验、定稿与交接（Finish）

Progress: `[1 用法一致性校验] → [2 缺口处置与回写] → [3 定稿与终门] → [4 渲染、交接与收尾]`

**Read (input):** `{output_dir}/wds-design-system.yaml` 全量；`{output_dir}/wds-scenarios.yaml` 的 `scenarios[].pages[].id`（用法对账的另一半）；`{output_dir}/design.yaml` 的 `tokens`（可选读——核 `token_refs` 是否漂移）；`data/complexity-router.md`（复核 `complexity`）；`check` 回执。
**Write (output):** 用法报告结论 · 三份缺口清单的处置 · `components[]` 的修复与 `complexity` 复核 · `project.status: 已定稿` · `project.updated` · `revisions` · 给用户的交付摘要与路由。

你是**收尾的主持人**（源 `steps-m/step-03` + 六个活动工作流的 `AFTER COMPLETION` 段）。第 1–2 步是本技能**独有的**质量门槛（`wds-7` 本体没有），第 3 步是定稿与终门，第 4 步是交付。

**本段纪律**：① **不许橡皮图章**——用法报告逐条过，不合格回 `./01-create.md` / `./04-edit.md` 修；② **终门唯一放行 = `check --final` 的 `exit 0`**；③ **只写本产物**——页面规格的写权归 C·3 的 `diy-design`，本技能对 `wds-scenarios.yaml` 只读。

> ### ★ 本活动的来路与归口（归口裁定，须登记）
>
> 源的「**跨页用法一致性审计**」有**两个入口**：
> - `wds-4/steps-m/step-03-validate-usage.md`（127 行；属 `[M]`，即本技能）；
> - `wds-4/steps-v/step-09-design-system-consistency.md`（属 `[V]` 活动，归 **C·3** 的 `diy-design`）。
>
> 两者做的是同一件事（census-3 §7.1 实测：跨页组件一致性审计）。本批**取 `[M]` 版**，依据两条：
> ① **`wds-7` 本体完全没有这个能力**（它只管创建/编辑，无「跨页用法审计」步骤）——不落本技能则整条链缺闭环；
> ② 计划要求「**页面规格引用其 token**」，而「引用有没有真的用对、用一致」正是本审计回答的问题。
> `diy-design` 的 `[V]` 段在 C·3，**本批不涉**（对方侧随 C·3 补）。

## 第 1 步 —— 用法一致性校验（源 `steps-m/step-03:57–80`）

**先说清为什么**：源这一步的原话是「**扫描 → 交叉引用 → 报告 → 再与用户决议**」——注意顺序：**报告在决议之前**，不许边扫边改。

### 1.1 Component Usage Report（源 `:70–80` 的表，逐列对齐）

逐组件一行，五列：

| 列 | 判据 | 可机械？ |
| --- | --- | --- |
| **Component** | 记录 `id` + `name` | 机械 |
| **Defined** | 该组件在设计系统里是否在册 | 机械（记录在场即 yes） |
| **Pages Used** | `len(used_in[])`；且**每条必须解析到 `wds-scenarios.yaml` 的页面 ID** | 机械（引擎 `check` 核 `used_in[]` → `UNKNOWN_ID`） |
| **Consistent** | 同组件在不同页的属性 / 状态是否一致（源 `:65` 的 `same props/states`） | **★ 不可机械**（见 1.2） |
| **Issues** | 该行的问题摘要 | 人工 |

> **★ 边界声明（本批的诚实口径）**：**`Consistent` 一列不可机械。** 源 `step-03:59–66` 给的是「扫描页面规格 → 抽出组件引用 → 逐条判 yes/warning」的散文，**没有字段级比对规则**；而 diy 侧的页面规格载体（`wds-scenarios.yaml` 的 `pages[]`）只有页面元数据，**不含组件级属性**（属性住在 C·3 的 `diy-design` 侧）——所以本列的判定**只能由人工在会话里逐条问、逐条答**，不得假装自动。**机械的那三列（Component / Defined / Pages Used）交引擎**，人工的那两列（Consistent / Issues）在会话里过。

### 1.2 三份缺口清单（源 `:77–80`，逐字保留三个桶）

| 源桶 | diy 判据 | 处置去向 |
| --- | --- | --- |
| **Missing from system**（页面用到、系统里没有） | `wds-scenarios.yaml` 的页面上有某组件，而本产物无对应记录 | 回 `./01-create.md` 建（走完重复检测全流程） |
| **Inconsistent usage**（用法不一致） | 第 1.1 步 `Consistent: warning` 的行 | 回 `./04-edit.md` 改组件定义，或在页面侧改用法（**页面侧改写归 C·3**，本批记 gap） |
| **Unused components**（系统里有、无人用） | `used_in: []` | 逐条与用户决议：留（备用）→ `notes` 注明；弃 → `status: 已废弃`（**不删记录**——ID 不复用） |

**落盘**：报告与三桶清单进会话；处置在第 2 步。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘，仅记报告）→ ③ 分隔 → ④ 呈出报告表与三桶清单 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 缺口处置与回写`。

## 第 2 步 —— 缺口处置与回写（源 `steps-m/step-03:82–87`）

**先说清为什么**：源这一步的四条指令里有两条是**双向回写**（「改组件定义去匹配用法」/「改页面规格去匹配设计系统」），还有一条是**删孤儿**。diy 侧写权收窄了（页面规格不归本技能），所以回写方向要**逐条点名**。

逐条决议、逐条落：

| 源指令（`:84–87`） | diy 落法 |
| --- | --- |
| 改组件定义去匹配用法 | 落本产物 `components[]`（回 `./04-edit.md` 走审批） |
| 改页面规格去匹配设计系统 | **不落本技能**——页面规格在 C·3 的 `diy-design`；本批写进 `revisions` 的 gap 记录并**路由 `diy-design`（C·3）** |
| 移除孤儿组件 | **改为标 `status: 已废弃`**（源侧是「删」，diy 侧删记录会破坏 ID 不复用的纪律）——登记为本批的**口径改判** |
| （补）component_references_present / design_system_tokens_used 两类引用存在性 | 机械核：`used_in[]` 解析（`UNKNOWN_ID`）+ `token_refs[]` 解析（`TOKEN_UNRESOLVED`）——这两条正是源 `steps-v/step-07:69–70,101–102` 的判据，**并入本步的机械面**（同族去重，见 `01-create.md` 的缺口表） |

**落盘**：`components[]` 修复 + `status: 已废弃` 的标记 + `revisions`（逐条决议各一条，`change` 点名 ID）。

**检查点（六拍）**：① 生成 → ② 落盘（修复 + 标记 + `revisions`）→ ③ 分隔 → ④ 呈出逐条决议结果 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 定稿与终门`。

## 第 3 步 —— 定稿与终门（**用户关卡：定稿需明确点头**）

**先说清为什么**：这是**唯一一次状态不可逆的写入**（`草稿 → 已定稿`），也是下游（C·3 的 `diy-design`、`diy-wds-assets`）唯一的门禁依据——所以它必须由用户点头、由引擎放行。

### 3.1 定稿前的四项复核

1. **复杂度复核**（`data/complexity-router.md` §1）：逐条核 `complexity` 是否仍成立——改过范围/状态的记录要重判（源 `[M] step-02` 的复杂度评估在这里做**终局确认**）。
2. **令牌对账**：`token_refs[]` 逐条解析；`design.yaml` 在场时再核一次命名空间无漂移。
3. **零 `[假设]`**：扫全部散文值（`name` / `usage.*` / `notes` / `revisions.*`），有 `[假设]` 前缀的**逐条与用户确认后才删前缀**；确认不了的写进 `revisions`。
4. **用法报告闭环**：第 1 步的三桶缺口全部有处置记录（无遗留）。

### 3.2 定稿落盘

`project.status: 已定稿` + `project.updated` 刷今天（记录级 `status` 本批只有两值 `在用|已废弃`，无推进态）。

### 3.3 终门（机械；`exit 0` 是唯一放行）

```
python "{project-root}/.claude/skills/diy-wds-system/scripts/wds_system.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`--final` 核：`project.status: 已定稿` + 顶层七键齐备 + `design_system_mode` 合法 + `prefixes` / `categories` 与冻结表逐条一致 + 全部组件记录十五键齐备 + `used_in[]` / `token_refs[]` 全部解析 + 同前缀编号连续 + 零 `[假设]` + 零组件不允许。**按回执 `where` 就地修、重跑，不得跳过**；渲染与收尾都等 `exit 0`。

**WDS 型产物一律走本引擎终门**，不得改用 `diyc.py check --type`（那是主线 8 型封闭集，且**不教 `--previous` 轮**——本产物只增不减，无 ID 集合收缩面，裁定 19）。

**检查点（六拍）**：① 生成 → ② 落盘（定稿状态）→ ③ 分隔 → ④ 呈出四项复核结论与 `check --final` 回执 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 渲染、交接与收尾`。

## 第 4 步 —— 渲染、交接与收尾

### 4.1 渲染（静默旁路）

`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

〔**C2 面缺口（登记，不在本批修）**〕本产物名 `wds-design-system` **不在 `viewer.py` 的 `DOC_LABELS` 里**——表现为标题回落英文 stem、键名英文直出（**不报错、不红测**，`test_viewer_labels.py` 只遍历已登记的键）。另：`03-view.md` 产出的 `catalog.html` 与 `wds-design-system-catalog.html` **不是 YAML**，`viewer.py` 只扫顶层 `*.yaml`（`viewer.py:1419`）——**渲染不到**。两条都归 **C2 面**，由主 agent 收口期登记。

### 4.2 交接摘要（会话内，不落盘）

① **完成摘要**：组件数 / 逐分类分布 / 令牌名数量（三命名空间）/ `token_refs` 覆盖的组件数 / `used_in` 覆盖的页面数 / 用法报告结论；② **本产物的下游与止点**：

> **本产物是设计系统段，WDS 线与主线在此交汇。** 下游两类消费者：
> - **C·3 的 `diy-design`**（主线侧）：按 `used_in[]` 的页面 ID 与 `token_refs[]` 的令牌名消费——**页面规格引用本系统的 token** 这条计划要求落在它那侧；
> - **`diy-wds-assets`**（本批同批技能）：读本产物的 `tokens` 段做资产侧的令牌一致性校验（**可选读**，缺则降级）。
> **token 的单一源始终是 `design.yaml.tokens`**（本产物只引用不复述）——要改 token 值回 `diy-design`，不要改本产物。

③ **未决项**（`revisions` 里各一条一句；无则写「无」）；④ **明确不做的**：不提交 git（源 `step-08e:585–596` 的自动提交已裁）、不写页面规格、不写 `design.yaml`。

**收尾与路由**：本文件到此结束——不再读任何 `steps/` 文件。
