# Step 1 — 分析产品与选定目标（Analyze Product）

Progress: `[1 载上下文与入口门禁] → 2 双轨上下文与改进目标清单 → 3 优先级排序与选定目标（用户关卡 1 + 铸骨架） → 4 分析落盘与根因合成 → ./02-scope.md`

**Read (input):** `{output_dir}/` 下**任一**既有产物（`design.yaml` / `sprint.yaml` / `wds-*.yaml`——本轮要演进的对象）；`list` 回执（续接检测）；`data/kaizen-principles.md` 与 `data/priority-framework.md`（`data/` 路径从本技能安装目录解析）；用户在本文件各步的回答与它带来的产品数据（分析后台数字 / 反馈原话 / 团队观察）。
**Write (output):** `{output_dir}/wds-evolution.yaml` 的顶层骨架（经 `init` 铸造）——`project` + `kaizen_priority`（公式 / 三档量表 / 候选清单）+ 首轮记录 `EV-01`（铸号、`analysis` 段）+ `revisions`；给用户的 Product Snapshot 与候选清单呈批。

你是**Kaizen 迭代的主持人**（源 wds-8 的 Freya 线）。动作只有一件：**把「下一步该改什么」问出来并排出先后**——你带来 Kaizen 方法论与优先级框架，用户带来产品知识、真实数字与团队观察。这一段【不做】方案设计、【不做】范围估算，那些是 02-scope 之后的事。

**本段纪律（源 `steps-a/step-01` 的 Step-Specific Rules）**：① 问题必须**具体、可量、范围小**——「让它更好用」这类表述一律打回；② **先定义问题再谈方案**（源 `FORBIDDEN to jump to solutions before the problem is clearly defined`）；③ 每条目标都要挂到**一个人物或一个业务目标**上，挂不上的不进清单。

## 第 1 步 —— 载上下文与入口门禁（源 [A] step-01）

**先说清为什么**：为什么先把产品的现状读一遍再动手——Kaizen 是在**既有系统与既有约束**里做小改，不是重画；现状读错，后面整轮都在替一个不存在的产品改东西。用你自己的话讲。

**你是入口技能**（`precededBy: []`，任务书裁定 9）：源侧 `precededBy` 指向的实体不在本迁移范围，且源定位就是「**面向已存在产品的持续改进**」——输入是**已存在的产品**，不是某个指定上游产物。故门禁 = **既有产物任一在场**，不绑任何单一上游。

**读什么、读出什么**：

| diy 侧读 | 抽出 |
| --- | --- |
| `{output_dir}/design.yaml`（若有） | 页面清单与 `tokens`（改的是哪几页、视觉基线是什么） |
| `{output_dir}/wds-*.yaml`（若有） | 本 WDS 短链的简报 / 触发图 / 场景页树（人物与业务目标从此取锚） |
| `{output_dir}/sprint.yaml`（若有） | 已排期任务（避免与在飞任务撞车） |
| 用户带来的产品数据 | 分析后台数字 / 反馈原话 / 团队观察（源 [A] 的 live URL 与 codebase 两条在这两栏里） |

**Product Snapshot（呈出，不落盘）**：现有页 / 导航 / 关键用户流三条 + 技术栈与设计令牌的**观察所得**（不是清单复述）。**读不出来就写「未读取」，不许凭印象补**。

**续接检测**：先跑

```
python "{project-root}/.claude/skills/diy-wds-evolution/scripts/wds_evolution.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- 回空 → 新的一轮，进第 2 步。
- 回已有轮次 → 播报四字段（ID / 目标 / 状态 / 入口），问三选一：**① 接着上一轮做 / ② 开新的一轮（追加 `EV-<nn>`） / ③ 复审并调整既往轮次**——**HALT 等选择**，不替用户选。

**门禁（零产出退出）**：`{output_dir}` 下**无任何**既有产物 → 一行说明并**零产出停止**（本技能不产零起点项目；新建项目走 `diy-wds-brief` / `diy-prd`）。`init` 会把它机械兜住（`MISSING_FILE`）。

**产出键**：Product Snapshot（现状三观察：页 / 导航 / 关键流 + 技术栈与设计令牌的观察所得）——只呈出，第 4 步的 `analysis.snapshot` 溯它。

**落盘**：本步只往会话里带上下文，**不写盘**（骨架在第 3 步的 `init` 一次铸成）。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘，仅记本步结论）→ ③ 分隔 → ④ 呈出 Product Snapshot → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 双轨上下文与改进目标清单`。

## 第 2 步 —— 双轨上下文与改进目标清单（源 [A] step-02 + 源死分支 `steps-a/`）

**先说清为什么**：目标从哪来——不是拍脑袋，是**从产品自己吐出来的东西里捞**。用你自己的话讲。

**双轨入口**（源 `steps-a/step-01` 第 1 指令；`init --entry` 的取值就是它）：**两轨的产物形态相同，采集面不同**。

| 轨 | 判据 | 采集面 |
| --- | --- | --- |
| `存量接入` | 你**第一次**接手这个产品 | 源 `steps-a/step-02` 的 Context A：业务材料 / 用户材料 / 产品材料三栏 + **亲自把产品走一遍**（源 `First Impressions` 模板的四段：Onboarding / Core Features / Overall Impression） |
| `上线后持续` | 产品是你（或团队）做出来的，正在线上迭代 | 源 `steps-a/step-02` 的 Context B：分析深潜（用量 / 分层 / 流失点）· 反馈归类（主题 / 频次 / 原话）· **回看原始设计意图**（当初为什么这么设计、哪些假设已变）· 竞品对照 |

**本步的两条纪律**：① **存量接入轨必须亲身体验产品**（源侧把它列为 SYSTEM FAILURE 项）——只读文档不算；② 反馈归类**保留原话**，不要在这一步就改写成结论。

〔**源侧缺陷处置（死分支复活，任务书 W3 卡）**〕源侧 `workflow.md:64` 的路由表声称 [A] 用 `steps-a/`，但 `workflow-analyze.md:19-64` 的 4 个内联步**从不加载任何步骤件**（全库 `grep "steps-a"` 仅 2 处命中、**零加载点**）——**361 行不可达**。且两套分解内容互不覆盖：内联版是「清单式」、`steps-a` 版是「Kaizen 双轨 + 优先级公式」。**diy 处置 = 合并而不是二选一**：活动文件的内联步序为**骨架**（它才是实际可达的那一套），`steps-a/` 的双轨采集、`Priority = Impact × Effort × Learning` 与 Context Synthesis 四键**逐条并入**本文件第 2/3/4 步——死分支的**内容全部落地、只是不再作为一份独立文件存在**。

**改进目标清单（五源，源 [A] step-02 第 1 指令）**：逐源过一遍，**每条目标写「现象 + 数字或原话 + 影响的页/流」**：

| 源 | 问句 |
| --- | --- |
| 用户反馈 | 用户在哪一步卡住？（带原话与出现次数） |
| 业务指标 | 哪个数字没达标？（带动当前值与目标值） |
| 技术债 | 哪里脆、哪里旧？（带位置） |
| 视觉缺口 | 哪里不一致、哪里过时？（带页名） |
| 竞品差距 | 竞品哪里做得更好？（带对照点） |

**产出键**：候选逐条进会话清单（此时**尚未落盘**）；每条附三因子的初判（第 3 步定稿）。

**落盘**：本步不写盘。

**检查点（六拍）**：① 生成 → ② 落盘（本步无写盘）→ ③ 分隔 → ④ 呈出候选清单（逐条：现象 / 证据 / 影响的页）→ ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 优先级排序与选定目标（用户关卡 1 + 铸骨架）`。

## 第 3 步 —— 优先级排序与选定目标（用户关卡 1 + 铸骨架，源 [A] step-03）

**先说清为什么**：为什么一次只做一条——Kaizen 的成本优势来自**小批量、快反馈**，并行三条会把「哪条起了作用」这个信息本身弄丢。用你自己的话讲。

**Kaizen 优先级框架（源 `data/kaizen-principles.md`，全文落 `data/priority-framework.md`）**：

```
Priority = Impact × Effort × Learning
```

三因子各取 `high|medium|low`（权重 5 / 3 / 1），`score` = 三档权重之积。**三因子一律「越大越好」**——`Effort` 的 `high` 指**省力度高**（源表逐字：「High = 1-2 days」），**不是**「活儿大」。故 `score` 高 = 该先做。

〔**口径归一（源侧两处表述互斥）**〕`kaizen-principles.md` 把 Effort 的 High 记作「1-2 days」、`steps-a/step-01` 的表把 High 记作「1-2 days」而列头写 High/Medium/Low——两处的 High 都指向**最省力**，但字面「Effort 高」会被读成「工作量大」，与乘法公式自相矛盾。**diy 归一 = 三因子统一为「收益向」**：`effort` 的取值语义是「省力度」，`score` 高即优先。**框架名与公式逐字保留**（它是本技能相对 `diy-dev` 的不可替代内容）。

**逐条排序与呈批（用户关卡 1）**：排出候选清单，呈出后**等点头**：

```
## 改进目标（按 Priority = Impact × Effort × Learning 排序）

| # | 目标 | Impact | Effort(省力度) | Learning | Score |
|---|------|--------|----------------|----------|-------|
| 1 | <目标> | high|medium|low | high|medium|low | high|medium|low | <积> |
…

**本轮先做哪一条？**（源侧口径：一次一条；其余进留存，下一轮再看）
```

**不得替用户选**（源 [A] step-3 原话 `Which target should we tackle first?`）。

**铸骨架（`init`，门禁的机械兜底）**：点头后调引擎：

```
python "{project-root}/.claude/skills/diy-wds-evolution/scripts/wds_evolution.py" init --entry "<存量接入|上线后持续>" --target "<选定目标>" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `--entry` 与 `--target` **皆必填**：空值 → `EMPTY_FIELD`、非法值 → `ENUM_INVALID`（两者都零产出）。
- **入口门禁**：`{output_dir}` 下无任何既有产物 → `MISSING_FILE` 零产出。
- 骨架含**首条记录的铸号**（`EV-01`）+ `kaizen_priority` 的公式与三档量表；候选清单与 Score 由你**直接编辑产物**写入（内容型字段，写权归会话）。
- 已有产物 → **不覆盖**（只刷 `project.updated` + warning）；产物损坏 → `UNPARSABLE_YAML` 拒绝且零写入。
- 追加新一轮：会话直接追加 `EV-<nn>`（序号 = 最大序号 + 1、两位补零、`status: 草稿`）；`check` 机械核对连续性与唯一性。

**产出键**：`kaizen_priority.candidates[]`（逐条 `target` + 三因子 + `score` + `rationale`）+ `rounds[0]` 的 `id` / `target` / `entry`。

**落盘**：`project` + `kaizen_priority` + `rounds[0]`（`EV-01` / 选定目标 / `entry` / `status: 草稿`）+ `revisions: []`。

**检查点（六拍）**：① 生成 → ② 落盘（候选清单进 `kaizen_priority.candidates[]` + `init` 铸骨架）→ ③ 分隔 → ④ 呈出回执与骨架摘要 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 分析落盘与根因合成`。

## 第 4 步 —— 分析落盘与根因合成（源 [A] step-04 + 源 `steps-a/step-02` 第 4 指令）

**先说清为什么**：为什么「现象」还不够、非要一层根因——不找到根因的改进会在同一个地方反复打转，那正是 Muda（無駄）里的「返工」。用你自己的话讲。

**Context Synthesis 四键（源 `steps-a/step-02` 的 Synthesis，两轨共用）**，写进 `rounds[0].analysis`：

```yaml
analysis:
  snapshot: <Product Snapshot 三条 + 技术栈/令牌的观察所得>
  sources: [<五源里真拿到的那几源，各带数字或原话>]
  root_cause: <为什么会这样——一句话，带位置>
  hypothesis: <改什么会解决它>
  validation_plan: <怎么知道起作用了——数字 / 时点 / 判据>
  current_state: <源 [A] 的「现在用户看到什么、哪里不对」>
  targets_considered: [<全部候选，含未选中的>]
  selected_rationale: <为什么是这一条——引用 score 与用户的话，不复述排序表>
```

- **根因必须先立住再往下走**（源侧原文 `Root cause must be identified before moving forward`）。
- `targets_considered` **全留**：未选中的目标是下一轮的原料（源 [P] step-5 的「回看剩余目标」靠它）。

**产出键**：`rounds[EV-<nn>].analysis` 的四键（`root_cause` / `hypothesis` / `validation_plan` / `selected_rationale`）+ `snapshot` / `sources[]` / `current_state` / `targets_considered[]`。

**落盘**：`rounds[0].analysis` + `rounds[0].status: 分析` + `project.updated`。

**检查点（六拍）**：① 生成 → ② 落盘（`analysis` 段 + 状态推进）→ ③ 分隔 → ④ 呈出四键摘要（Snapshot 一带而过，重点念 root_cause 与 hypothesis）→ ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

**收尾与路由**：分析已落盘，读 `./02-scope.md` 把选定目标变成有边界的一次变更。

本文件到此结束，不再回头。
