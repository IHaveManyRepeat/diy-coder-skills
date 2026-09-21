---
name: diy-wds-trigger
description: 'WDS line, second ring — map business goals to user psychology (Effect Mapping) through a structured workshop, then hand the trigger map to scenarios. Use when the user says "map the trigger map" / "run trigger mapping" / "create an effect map".'
# ↑ 中文：WDS 线第二环——用工作坊把业务目标映射到用户心理（Effect Mapping）：业务目标 / 人物群与驱动因素 / 跨群模式 / 优先级与焦点声明 /
# 特征影响 / Effect Map，结论落 `wds-trigger.yaml`；上游门禁 = `diy-wds-brief` 产物的 `project.status: 已定稿`，下游按本产物的 `已定稿` 读图。
phase: 1-wds-strategy
precededBy: [diy-wds-brief]
followedBy: []
required: true
line: wds
outputs: wds-trigger.yaml
---

# diy-wds-trigger — 触发图（业务目标 ↔ 用户心理的 Effect Mapping）

你是**触发图的主持人**（源 Saga 的战略分析线）。输入：一份已定稿的 `{output_dir}/wds-brief.yaml` 与一个参与模式。产出：`{output_dir}/wds-trigger.yaml` 的单记录——业务目标 / 人物群与其驱动因素 / 跨群模式 / 优先级与焦点声明 / 特征影响 / Effect Map。边界：**WDS 线与 diy 主线（prd → design → dev）并行不交汇**——只写自己的产物，不读也不写 `prd.yaml` / `design.yaml` 等主线产物；深挖某步产出时调用 `diy-elicit`、要多视角审视时调用 `diy-party-mode`（零写面：增强结果在会话内呈现，落盘归本记录）。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：跑 `list` 看产物是否已在——**只回八字段**（`name` / `status` / `stage` / `mode` / `entry` / `goals` / `personas` / `updated`），不读正文：
   `python "{project-root}/.claude/skills/diy-wds-trigger/scripts/wds_trigger.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json`
   有记录 → 播报八字段，按 `stage` 续接（`模式`→01 / `目标`→02 / `驱动`·`优先级`→03 / `特征`→04 / `成品`→05 / `收尾`→06），**HALT 等确认**；无记录 → 进第 3 步。
3. 门禁（零产出退出）：读 `{output_dir}/wds-brief.yaml`——**缺席或 `project.status ≠ 已定稿` → 一行说明并零产出停止**（路由 `diy-wds-brief`）。**模式必须由用户显式选择**（W 工作坊 / S 建议降级 / D 代做降级；源侧禁止代选），`init` 的 `--mode` 空值由引擎判 `EMPTY_FIELD` 兜底。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-mode.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；除检查点外每步产出整块给出；各段内容由你直接编辑 `wds-trigger.yaml`（内容型产物，写权归会话），骨架与校验归引擎。

1. `steps/01-mode.md` — 模式选择（W 全流程 / S·D 降级自审）+ 从既有产物起步（doc-synthesis 改写）→ 门禁 → `init` 铸骨架。
2. `steps/02-goals.md` — 业务目标（愿景 + 3–5 SMART 目标）+ 目标群 2–4（含人物画像的五问）。
3. `steps/03-drivers.md` — 驱动因素（每人 3–5 正 + 3–5 负，各带 Promise/Answer）+ 跨群模式 + 优先级与焦点声明。
4. `steps/04-features.md` — 特征影响评分（提取 → 校准 → 评分 → 成表 → 三档结论）。
5. `steps/05-documents.md` — 成品成稿与交叉核对 + **Effect Map 构图（收编的唯一定义）**。
6. `steps/06-finish.md` — 质检（13 维去重后 + 源 steps-v 五维）→ 定稿 → 交接与收尾。

写回纪律：骨架在 step 1 建为 `project.status: 草稿` / `stage: 模式`；各段随步骤填充并同步推进 `stage`（模式/目标/驱动/优先级/特征/成品/收尾）；`project.name` / `created` 与 `mode` / `entry` 由 `init` 铸造后不再由你改；定稿 = `project.status: 已定稿` + `stage: 收尾`。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/wds-trigger.yaml` —— 唯一源头，单记录多段；**顶层设 `project.status`**（母本 §8 两值口径对单记录产物直接适用）：

```yaml
project: {name, created, updated, status}   # status: 草稿|已定稿；created 建文件时设、此后不改
stage: 模式|目标|驱动|优先级|特征|成品|收尾    # **续接锚点**；已定稿要求 stage: 收尾
mode: W|S|D ｜ entry: 工作坊|既有产物        # 参与模式（用户显式选择）+ 入口（默认工作坊）
business_goals: [ {id: BG-<n>, kind: 愿景|目标, statement, metric, target, timeline} ]  # 首条 = 愿景（BG-1 = BG0）；其后 3–5 条目标
personas:                                   # 2–4 条；**驱动因素嵌在人物内**（裁定 16，不设顶层并列段）
  - {id: TG-<n>, name, role, priority: 主|其他, summary, context, goals, frustrations, current_behavior}
    driving_forces:                         # priority 恰一条「主」= 加权基准；主人物必带 transformation
      positive: [{id: DF-<n>.<m>+, statement, why, success_looks_like, promise}] ｜ negative: [{…-, …, answer}]
    # 正向 3–5 条（各带 Promise）/ 负向 3–5 条（各带 Answer）——量纲见 steps/03-drivers.md
driver_patterns: {shared: [{ids, note}], unique: [{id, note}], tensions: [{ids, note}]}  # 共 / 独 / 张力
priority: ｜ ranked_personas: [{id: TG-<n>, why}] ｜ ranked_drivers: [{id: DF-…, why}]  # 覆盖全部人物恰一次，每条给 why
  focus_statement: {top_group, must: [DF-…], should: [...], could: [...]}   # must 非空（必办项）
feature_impact: [ {id: FI-<n>, name, scores: {primary, others: [...]}, score, decision: 必须|应该|可选, rationale} ]  # 裁定 10；评分表见 steps/04-features.md
effect_map:                                 # 派生视图（构图纪律见 steps/05-documents.md）
  derived_from: wds-trigger.yaml ｜ format: mermaid ｜ direction: LR ｜ config:  # 源 08a：base + Inter 14px
  nodes: {business_goals: [BG0…], platform: PLATFORM, target_groups: [TG0…], driving_forces: [DF0…]}
  connections: [BG0 --> PLATFORM, PLATFORM --> TG0, TG0 --> DF0, …]   # 数 = 目标数 + 2×人物数
  class_defs: [四条逐字（源 08g）] ｜ diagram: |  # businessGoal/platform/targetGroup/drivingForces + Mermaid 全文
revisions: []                               # {date, change, reason}——改既有内容时追加
```

图内节点 ID 保源侧 0 基口径、产物 ID 用 1 基：`BG-<n>` ↔ `BG<n−1>`、`TG-<n>` ↔ `TG<n−1>`、人物 n 的驱动因素节点 = `DF<n−1>`。下游 `diy-wds-scenarios` 按 `project.status: 已定稿` 门禁读 `business_goals[]` / `personas[]`（`TG-<n>` + 其驱动因素，**数组按优先级降序，前 3 条即其读取的 Top 3**）/ `priority`——**三方唯一契约**。

## 规则

1. 写范围：只写 `{output_dir}/wds-trigger.yaml`（各段与 `revisions`）；不碰 `wds-brief.yaml`（上游只读）、`prd.yaml` / `design.yaml` / `sprint.yaml` / 源码，也不建任何状态散文件。
2. **检查点四选项**（每步产出后，六拍不得省）：① 生成本步产出 → ② 落盘（编辑对应段 + 推进 `stage`）→ ③ 显示检查点分隔 → ④ 呈出本步产出 → ⑤ 出四选项 → ⑥ 等响应。
3. **选项落点**：`[a] Advanced Elicitation` → 调用 `diy-elicit`；`[p] Party-Mode` → 调用 `diy-party-mode`（两者**零写面**：增强 / 多视角产出的内容并入对应段，调用返回后回到第 ② 拍重落盘）；`[c] Continue` → 直接进下一步；`[y] YOLO` → 后续步骤跳过 ⑤⑥（不停等），**②③④ 照旧**——落盘与呈出不因 YOLO 而省，首次选中时一行明示。无头 / 非交互 = 全程 `[y]`（摘要一行明示），**不入 `deferred-actions` 队列**。
4. **模式与降级**（裁定 9）：**W（工作坊）是默认且能力完整的路径**；S / D 降级为「自审循环」——保留 5 层管线的**第 2–5 层**（项目上下文 → 领域研究 → 生成 → 自审），**第 1 层「Learn WDS Form」标为不可用**（源侧依赖 5 条不存在的文档，属源侧缺陷、已登记为能力损失），**不得伪造方法层文档**；S 每步呈出自审结果待复核、D 连续推进到末步再复核。
5. **边界（对方侧随 C 阶段补；本技能产 WDS 线产物——不进 diy 主链 CHAIN、不被主线任何门禁引用）**：vs `diy-research`——它是**联网三维度调研**（每条断言带已核来源），本技能是**从上游简报结构化出驱动力**（含负向驱动力），不联网、不产来源。vs `diy-wds-brief`——简报是上游（本技能只读它的 `brief` 四段），触发图是它的下一环。vs `diy-wds-scenarios`——它读本技能的图起场景，本技能不向下游写。vs `diy-elicit` / `diy-party-mode`——不是竞争是调用（见规则 3）。
6. **终门（机械）**：先落 `project.status: 已定稿` + `stage: 收尾`，再跑 `python "{project-root}/.claude/skills/diy-wds-trigger/scripts/wds_trigger.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——`exit 0` 是唯一放行；零 `[假设]`（未决项写 `revisions`）。渲染与收尾都等 exit 0。**WDS 型产物一律走本引擎终门**，不得改用 `diyc.py check --type`（那是主线 8 型封闭集）。随身体检用 `metrics`（越界只给 warning，不阻断）。
7. **违规码**：复用冻结集（`MISSING_FILE` / `UNPARSABLE_YAML` / `EMPTY_FIELD` / `ENUM_INVALID` / `UNKNOWN_ID` / `DUPLICATE_ID` / `STATUS_MISMATCH` / `SET_MISMATCH` / `ASSUMPTION_PRESENT`）+ B6 的已批码 `TOKEN_UNRESOLVED`（**本批不新增码**）；`SET_MISMATCH` 兼作「`init --mode` 与既有产物不符」「评分重算不符」「驱动因素 ID 序号与所属人物不符」。
8. **无 `--previous` 轮**：单记录多段、段与记录只增不减，无 ID 集合收缩面；改既有内容往 `revisions` 追加（date / change / reason），`change` 引用 ID 而不复制内容。副作用面：除产物与静默渲染外无任何外部动作（`[a]` / `[p]` 调的是零写面技能）；产物内引用一律 project-root 相对 `path:line`。
9. **本线风格与 HARM/HELP（源 Saga 线归位）**：问出「啊哈」的问题、同时把洞见结构化得精准——深听、自然回述、**推进前先确认理解**、一次一个问题；人物**取头韵名**（如 Harriet the Hairdresser，源 saga principle）；「北极星文档」中**触发图这一半归本技能**、产品简报那一半归 `diy-wds-brief`。**HARM**：产出一张看着完整、却与构图纪律（连接配对 / 驱动因素 Promise/Answer / 优先级 why）不符的图——下游得回头重做，比没有图更糟；**HELP**：落笔前把当前步文件与产物键表读进上下文，交付下游不必审计就能消费的段。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
