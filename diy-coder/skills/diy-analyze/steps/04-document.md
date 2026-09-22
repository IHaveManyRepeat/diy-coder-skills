# Step 4 — 成文、定稿与收尾（Document）

Progress: `[1 架构总览与 Mermaid 图] → [2 风险与技术债 + 建议] → [3 定稿、终门与渲染]`

**Read (input):** `{output_dir}/analysis.yaml` 的第 2、3 步全部素材（`architecture.tech_stack[]` / `components[]` / `data_flow[]` / `dependencies[]` / `architecture.layers[]` / `architecture.patterns[]`）；`question` 四项（成文要**回答它**）；`check` 回执。
**Write (output):** `architecture.summary` / `architecture.overview` / `architecture.mermaid`（**字符串**）；`risks[]`；`recommendations[]`；`project.status: 已定稿` + `project.updated` 刷今天；`revisions`（未决项与 gap）；给用户的交付摘要与路由。

你是**报告的成文者**（源 step-04 Document Findings）。前两步是取证与绘图，这一段把它们合成一份**回答原问题**的产物，再走终门。源侧提醒：**不重做分析**（`FORBIDDEN to redo analysis — use findings from Steps 2 and 3`）。

**本段纪律**：① **不跳读**：本步只读它点名的那一份产物，绝不批量预载 `steps/`；前一步的产物没落盘，本步不许开工。② **不编造**：读不出来的值留空并记 gap；绝不用印象补。③ **不代决**：检查点呈出后 HALT 等响应，绝不替用户拍板。④ **只记事实**：本技能**不做技术决策**——建议写着「可做什么」，不写「就这么定了」（拍板归主线 `diy-architecture` / `diy-correct-course`）。

## 第 1 步 —— 架构总览与 Mermaid 图（源 step-04 第 1–2 指令）

**先说清为什么**：讲清「为什么总览要放在最前面」——读的人先要的是结论，不是过程。用你自己的话讲。

### 1.1 成文（源 step-04 第 1 指令）

- `architecture.summary`：**2–3 句**关键发现（源 `2-3 sentence overview`）。
- `architecture.overview`：系统是怎么组织的（高层面描述）——把第 2 步的目录 / 入口 / 状态三段串成连贯叙述，**不复述清单**（清单已在 `components[]` / `tech_stack[]` 里，引用它们）。

### 1.2 Mermaid 图（源 step-04 第 2 指令）

图**住在 `architecture.mermaid` 的字符串字段里**（多行字符串，不落散文件）。源侧三类图**全保**，至少出一张（定稿门机械核其在场）：

| 图 | 源形态 | 用来回答 |
| --- | --- | --- |
| 架构图 | `graph TD` | 谁连着谁 |
| 依赖图 | `graph LR` | 谁依赖谁、哪里是核心 |
| 数据流 | `sequenceDiagram` | 一次请求怎么走完 |

**首词必须是合法图纸类型**（`graph` / `flowchart` / `sequenceDiagram` / `classDiagram` / `stateDiagram` / `erDiagram` / `journey` / `gantt` / `pie`），否则引擎判 `ENUM_INVALID`。图里的节点名用 `components[].name`，**别另起一套叫法**。

〔**源侧缺陷修复**〕源 step-04 把成文结构写成一份 **11 段 Markdown 文档**，落盘位置却未定义（`docs/architecture/` 与「agent experiences folder」两个兜底都无根，census-5 §4.2）。diy 侧：**段落全部落进 `analysis.yaml` 的对应键**（段 → 键的对译见下表），**不落 markdown、不落 `docs/`**。

| 源文档段 | diy 产物键 |
| --- | --- |
| Summary | `architecture.summary` |
| Tech Stack | `architecture.tech_stack[]` |
| Architecture Overview + Diagram | `architecture.overview` + `architecture.mermaid` |
| Component Map | `components[]` |
| Data Flow | `data_flow[]` |
| Dependencies | `dependencies[]` |
| Patterns and Conventions | `architecture.patterns[]` |
| Risks and Tech Debt | `risks[]` |
| Recommendations | `recommendations[]` |
| Date / Scope / Questions（页头） | `project.created` / `question.scope` / `question.text` |

**落盘**：`architecture.summary` / `architecture.overview` / `architecture.mermaid`。

**检查点（六拍）**：① 生成 → ② 落盘 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。本步：② 落盘（`architecture` 三键）；④ 呈出总览与图。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 风险与技术债 + 建议（源 step-04 第 3–4 指令）`。

## 第 2 步 —— 风险与技术债 + 建议（源 step-04 第 3–4 指令）

**先说清为什么**：讲清「为什么风险和事实要分开写」——事实不会过期，风险会；混在一起，后人分不清哪条是读到的、哪条是当时担心的。用你自己的话讲。

### 2.1 风险与技术债（源 step-04 第 3 指令）

逐条落 `risks[]`，四键**全保**：`risk`（一句话说清是什么）/ `severity`（`高|中|低`）/ `location`（project-root 相对 `path:line`）/ `impact`（会怎样）。源侧示例的三类都收：裸奔的端点、循环依赖、静默失败。

### 2.2 建议（源 step-04 第 4 指令）

逐条落 `recommendations[]`，每条三性**全保**——**具体**（点名模块 / 文件 / 模式）/ **可执行**（说做什么，不只说哪不对）/ **排过序**（按影响与工作量）。键：`action` / `priority`（`高|中|低`）/ `effort`（工时估）/ `target`。

**优先级降序排列**（引擎核：`高` 不许排到 `中` 后面，乱序判 `SET_MISMATCH`）。**建议不是决策**：写成「可以这样办 + 为什么」，拍板留给用户与主线。

**落盘**：`risks[]` + `recommendations[]`。

**检查点（六拍）**：① 生成 → ② 落盘 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。本步：② 落盘（两个清单）；④ 呈出风险表与建议表。 四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 定稿、终门与渲染`。

## 第 3 步 —— 定稿、终门与渲染

### 3.1 定稿落盘

`project.status: 已定稿` + `project.updated` 刷今天；`revisions` 补上本轮未决项与 gap（一条一句，`change` 点名 `AN-<nn>` 或字段名，`reason` 写为什么）。

### 3.2 终门（机械；`exit 0` 是唯一放行）

```
python "{project-root}/.claude/skills/diy-analyze/scripts/analyze.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`--final` 核：`project.status: 已定稿` + `question` 四项非空 + `architecture.summary` / `overview` 非空 + `tech_stack[]` 非空 + Mermaid 首词合法 + `AN-<nn>` 唯一且顺序 + `components[]` / `data_flow[]` / `risks[]` / `recommendations[]` 四段非空 + 建议按优先级降序 + **零 `[假设]`**。**按回执 `where` 就地修、重跑，不得跳过**；渲染与收尾都等 `exit 0`。

### 3.3 渲染（静默旁路）

`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

### 3.4 交付摘要与路由

呈出一页摘要（会话内，不落盘）：**问题 → 答到了什么**（总览一句）/ 组件与数据流计数 / 风险条数与最高档 / 建议条数与最高档 / 未决项。随后一句话给路由：**本产物不进主链 CHAIN、不被任何门禁引用**——它是现状事实源；要把某条风险变成决策，走 `diy-architecture`（决策式）；要立项执行，走 `diy-correct-course` / `diy-epics-stories`。

**收尾与路由**：`check --final` 回 `exit 0` 后，本文件到此结束——不再读任何 `steps/` 文件，也不再回头改前序产物（要改就往 `revisions` 追加）。

本文件到此结束，不再回头。
