# Step 1 — 载上下文与规模分析（Context & Scope）

Progress: `[1 载上下文与续接检测] → 2 规模分析与页清单（用户关卡 1 + 铸骨架） → ./02-strategy.md`

**Read (input):** 激活段的门禁回执（`wds-trigger.yaml` 已定稿）；`{output_dir}/wds-trigger.yaml` 的 `business_goals[]` / `personas[]`（`TG-<n>` + 其驱动因素）/ `priority`；`{output_dir}/wds-brief.yaml` 的 `brief.content.content_language.seo_keywords` 与 `brief.core`（站点类型 / 业务背景 / 平台约束 / 页数——**SEO 与站点上下文在此取，简报缺席则记 gap 不阻断**）；`list` 回执（续接检测）；用户在本文件各步的回答。
**Write (output):** `{output_dir}/wds-scenarios.yaml` 的顶层骨架（经 `init` 铸造）——`project` + `scope`（站点类型）+ `page_inventory` 空表 + 首条记录 `SC-01` 铸号 + `revisions`；给用户的上下文摘要与规模分析呈批。

你是**场景大纲的主持人**（源 wds-3 的 UX Scenario Facilitator）。角色分工源侧写得很清楚：**你问，用户定**——你带来场景思维与用户旅程经验，用户带来项目知识，两边是平等的。这一段只做两件事：把上游上下文读全、把规模与页清单摆到桌面上。

**本段纪律**：① **不跳读前置产物**（源 `FORBIDDEN to skip reading any prerequisite artifact`）——站点类型与页数都要从简报与触发图里**读出来**，不许凭印象说；② **共用元素不进页清单**（页头 / 页脚 / 导航是全局件，源侧明令排除）；③ **站点类型决定场景格式**，判错会在 02-strategy 与 04-outline 两步上连错两环。

## 第 1 步 —— 载上下文与续接检测（源 step-01）

**先说清为什么**：讲清「为什么先把上游读一遍再动笔」——场景是触发图的落地形态，人物与驱动因素读错，后面整条链都在替一个不存在的人设计。用你自己的话讲。

**读什么、读出什么**（源 step-01 第 1–3 指令；**diy 侧的读取面已换成本产物链**）：

| diy 侧读 | 抽出 |
| --- | --- |
| `{output_dir}/wds-trigger.yaml` 的 `business_goals[]` | 全部业务目标与其优先级分层 |
| 同文件的 `personas[]` | 每个人物：`TG-<n>` / 姓名 / 优先级 / 其 `driving_forces`（正负各若干）/ 在飞轮里的角色 |
| 同文件的 `priority` | 人物优先级（P1 起手）——它决定场景优先级 |
| `{output_dir}/wds-brief.yaml`（**可选**，只读） | 站点类型 / 业务背景 / 平台约束 / 页数 / 导航结构（`brief.core` · `brief.platform.platform_requirements`） |
| 同文件的 `brief.content.content_language.seo_keywords` | SEO 关键词图（缺则记 gap——源侧同样「缺则跳」） |

〔**源侧缺陷修复**〕源 step-01 读的是 `A-Product-Brief/product-brief.md` 与 `B-Trigger-Map/trigger-map.md` 两份 md；diy 侧一律改读**本链的两个 YAML 产物**（`wds-brief.yaml` / `wds-trigger.yaml`）。**触发图那份是硬门禁**（激活段已核 `project.status: 已定稿`）；**简报那份是可选读**——本技能的上游契约只冻结了触发图（§2.3.1），简报的 SEO 与站点上下文属**跨技能读契约的漏键**，本批按「在则读、缺则记 gap」处置并已在回报中登记，**不因它缺席而零产出**。

**续接检测**（源 step-01 第 4 指令）：先跑

```
python "{project-root}/.claude/skills/diy-wds-scenarios/scripts/wds_scenarios.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- 回空列表 → 这是新项目，进第 2 步。
- 回已有记录 → 播报六字段（ID / 名称 / 人物 / 页数 / 优先级 / 状态），问三选一：**① 接着上次做 / ② 复审并调整已有场景 / ③ 推倒重来**——**HALT 等选择**，不替用户选。

**呈出上下文摘要**（源 step-01 第 5 指令的模板；四条：项目 / 站点类型 / 业务目标数与人物清单 / 首要人物 + 其头号驱动因素），最后一问「可以开始做规模分析了吗」。

**落盘**：本步只往会话里带上下文，**不写盘**（骨架在第 2 步的 `init` 一次铸成）。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘，仅记本步结论）→ ③ 分隔 → ④ 呈出上下文摘要 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 规模分析与页清单（用户关卡 1 + 铸骨架）`。

## 第 2 步 —— 规模分析与页清单（用户关卡 1 + 铸骨架）

**先说清为什么**：讲清「为什么要先说清站点是什么、有几页」——站点类型决定场景长什么样（页与页的走法，还是页内状态的走法），页数决定是一次做全还是抓主流程。用你自己的话讲。

### 2.1 站点类型三分（源 step-02 第 1 指令）

| 站点类型 | 判据 | 场景格式 | 覆盖策略 |
| --- | --- | --- | --- |
| `presentation` 展示站（营销站 / 服务目录 / 公司简介 / 作品集） | 内容为主、页与页之间走 | `screen-flow` 屏幕流 | 全页暴露 |
| `dynamic` 动态应用（SaaS / 预约系统 / 社交 / 生产力工具） | 状态为主、页内多态 | `storyboard` 故事板 | 先核心工作流，多步流程才用屏幕流 |
| `mixed` 混合 | 展示站带动态功能 | `mixed` | 逐场景择一 |

**判据来自简报**（`brief.core` 的站点性质 + `brief.platform.platform_requirements`），不是问出来的新问题。

### 2.2 完整页清单（源 step-02 第 2 指令）

逐条列**页清单**（`page_inventory[]`，每条 `name` + `purpose` 一个短句）：

- 简报里**提到**的每一页都要在；
- 导航结构**隐含**的页（源例子：导航里有「服务」→ 服务总览页要在）都要在；
- 业务目标**隐含**的页（源例子：目标里提到预约 → 预约页要在）都要在；
- **共用元素不进清单**（页头 / 页脚 / 导航是全局件，源侧明令排除）；
- 呈现：「共 N 页 / 视图」+ 编号清单。

〔**源侧缺陷修复（规模带收口）**〕源 step-02 与 `workflow.xml` 的规模带是 `<20 / 20–50 / 100+`——**50–99 页无归属带**。本批收口为 `small <20` / `medium 20–50` / `large >50`（把 100+ 并入 large），登记为源侧缺陷修复。

### 2.3 规模与页文档化策略（源 step-02 第 3–4 指令）

- **规模带** → `scope.scale`：
  - `small`（<20 页）：**全面覆盖**——每一页都要在某条场景里露面；
  - `medium`（20–50 页）：**全面覆盖 + 自然分组**——按导航形态 / 服务类型 / 内容类目分组；
  - `large`（>50 页）：**有选择的忽略**——先深做最有价值的那条工作流（源侧理由：学到的模式能复用到其余页）。
- **逐页 vs 模板化** → `scope.page_strategy`：页少而差异大 → **逐页**逐条写（`individual[]`）；页多而同构 → **模板化**（`templated[]` 写清是哪些同构组）。
- **场景格式** → `scope.scenario_format`（见 2.1 表）。
- **大纲模式**（选填 `scope.approach`）：`对话`（默认，你问用户答）或 `建议`（你按触发图与简报先给整套 8 问答案，用户改）——源 step-05 实际实现的就这两态，故在此推荐。

〔**源侧缺陷修复**〕源 step-02 推荐模式写的是 `Dream / Suggest / Dialog` 三值，而 `Dialog` 在 wds-2 / wds-3 两源里**都不存在**（跨技能词汇冲突，census-2 B6）。本批按**本技能实际实现的两态**（`对话` / `建议`）归一，登记为源侧缺陷修复。

### 2.4 呈批（**用户关卡 1**，源 step-02 第 5 指令）

呈出这块、**等点头**，`--site-type` 只在点头后才铸：

```
## 规模分析

**站点类型：** presentation | dynamic | mixed
**页数合计：** N
**规模带：** small | medium | large
**场景格式：** screen-flow | storyboard | mixed
**大纲模式：** 对话 | 建议

### 页清单
1. <页名> — <一句话用途>
…

### 页文档化策略
- <X> 页逐条写（差异大）
- <Y> 页模板化（同构组：<列出组>）

**看着对吗？有没有漏页、或者该归组的？**
```

**没拿到明确点头就不许往下走**（源 `Do not proceed until user confirms`）。

### 2.5 铸骨架（`init`，门禁的机械兜底）

点头后调引擎：

```
python "{project-root}/.claude/skills/diy-wds-scenarios/scripts/wds_scenarios.py" init --site-type "<presentation|dynamic|mixed>" [--scale <small|medium|large>] [--scenario-format <screen-flow|storyboard|mixed>] --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `--site-type` **必填**：空值 → `EMPTY_FIELD`、非法值 → `ENUM_INVALID`（两者都零产出）。
- **上游门禁**：`{output_dir}/wds-trigger.yaml` 缺失 → `MISSING_FILE` 零产出（路由 `diy-wds-trigger`）；其 `project.status ≠ 已定稿` → `STATUS_MISMATCH` 零产出。
- 骨架含**首条记录的铸号**（`SC-01`）——场景名与人物引用要到 03-plan 用户关卡 2 之后才存在，此处先铸号，保证 **ID 顺序递增且不重编不复用**。
- 已有产物 → **不覆盖**（只刷 `project.updated` + warning）；产物损坏 → `UNPARSABLE_YAML` 拒绝且零写入。
- 页清单与 `scope.page_strategy` 由你**直接编辑产物**写入（内容型字段，写权归会话）；`project.name` / `created` 由 `init` 铸造后**不再由你改**。

**检查点（六拍）**：① 生成 → ② 落盘（`init` 铸骨架 + 页清单进 `page_inventory[]`）→ ③ 分隔 → ④ 呈出回执与骨架摘要 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

**收尾与路由**：页清单与规模已落盘，读 `./02-strategy.md` 起战略链。

本文件到此结束，不再回头。
