# Step 1 — 模式选择与入口（Mode & Entry）

Progress: `[1 模式选择、门禁与铸骨架] → 2 从既有产物起步（可选） → ./02-goals.md`

**Read (input):** 激活段 `list` 回执（八字段）；`{output_dir}/wds-brief.yaml`（只读——门禁读 `project.status`，正文在进入后取用）；用户对模式与入口的回答；用户点名的既有 diy 产物（只读取用）。
**Write (output):** `{output_dir}/wds-trigger.yaml` 的顶层骨架（经 `init` 铸造）——`project` + `stage` + `mode` + `entry` + `business_goals` 首条记录（`BG-1` 愿景空位）+ 其余五段空位 + `revisions`；给用户的播报。

你是**触发图的主持人**（源 step-01 的模式选择 + 门禁）。两拍：选定模式与入口 → 铸骨架。**模式是整条管线的参与方式**——源侧硬规则：模式必须由用户显式选择，**禁止代选、禁止默认**。

**本文件承载两个源步**：源主步 1「Mode Selection」（`step-01-overview.md`）与源主步 2「Documentation Synthesis」（`step-00a`…`00f`，**可选替代入口**）。源侧的第三个入口 `validate`（`workflow-validate.md` + `steps-v/`）**已裁**（任务书裁定 15）——其五维校验并入 `06-finish.md` 的质检查表，复检 = 重跑 `check`。

## 第 1 步 —— 模式选择、门禁与铸骨架（源 step-01）

**先讲清这一段要干什么**：触发图把**业务目标**和**用户心理**接起来（源侧方法出处：Effect Mapping，Balic & Domingues / inUse；WDS 的改法是**去特征、强化负向驱动因素**）。这一段要产出的是：业务目标 → 目标群 → 驱动因素 → 优先级。用你自己的话讲，别照读。

**一、选模式**（源 `step-01-overview.md:68-86` 的三选项，**逐字保留时长口径**）：

```
[W] 工作坊   —— 我主持、你提供洞察（45-60 分钟）
[S] 建议     —— 我给建议、你逐步复核（20-35 分钟）
[D] 代做     —— 我自主走完全部步骤、你复核最终结果（15-25 分钟）
```

**用户说不清时**用一句话问清：「你要一步步被访谈着做（W），还是我出草稿你改（S），还是我全做完你只看结果（D）？」——**仍不明确就不代选**，进「二、门禁」按拒答处置。

| 选定 | 管线 | diy 落点 |
| --- | --- | --- |
| **W**（默认、能力完整） | 逐问引导，四个工作坊（业务目标 / 目标群 / 驱动因素 / 优先级）**一次问一个** | 02–03 两个步骤文件按本文件选定后逐节走 |
| **S**（降级） | **自审循环**：保留 5 层管线的**第 2–5 层**（项目上下文 → 领域研究 → 生成 → 自审），每步呈出自审结果待复核 | 同上，但每步是「出稿 + 自审报告」而非问答 |
| **D**（降级） | 同 S，但**连续推进到末步**再一次性复核 | 同上，检查点全程等价 `[y]` |

**★ 第 1 层「Learn WDS Form」标为不可用（裁定 9）**：源侧该层的唯一输入是 5 条**不存在的**文档（`docs/method/phase-wds-2-trigger-mapping-guide.md`、`docs/quick-start/0wds-2-trigger-mapping.md`、`src/data/agent-guides/saga/trigger-mapping.md`、`docs/models/impact-effect-mapping.md`、`docs/method/dream-up-rubric-phase-2.md`——全仓 `find` 实测不存在）。**本技能不新建方法层文档、也不假装它存在**：S / D 的自审基准改由**本技能自带的键表与 `06-finish.md` 的质检查表**充当（它们是可核对的机械基准）。**这条源侧缺陷登记为能力损失，不登记为偏离。**

**二、选入口**（源 `workflow.md:57-62` 的分支，第三个 `validate` 分支见文首的裁撤说明）：

- **默认**：从零工作坊——直接进「三、门禁」。
- **从既有产物起步**（源侧叫 "existing" / from docs）：用户手里已经有 diy 既有产物（简报 / PRD / 调研 / 头脑风暴…）→ 选 `entry: 既有产物`，铸骨架后读 `./01-mode.md` 的 `## 第 2 步`。

**W 模式的二次菜单**（源 `:80-86`）：问一句「四个工作坊**一次跑完** [A]，还是**一个一个来** [O]？」——选 `[O]` 时每走完一个工作坊就停下来问「继续下一个 / 存着下次接着来」。

**三、门禁（零产出退出，§2.3.1 冻结）**：读 `{output_dir}/wds-brief.yaml`——

- **缺席** → 一行说明并**零产出停止**：本技能的门禁 = 上游简报的 `project.status: 已定稿`；可路由 **`diy-wds-brief`**。不建文件、不代拟。
- **`project.status ≠ 已定稿`** → 同样停止（简报走了一半，触发图没有可对齐的战略地基；先回去把它定稿）。
- 模式**拒答** → 停止（**不代拟模式**，可路由 `diy-prfaq` 点火）。
- 引擎侧同款兜底：`init` 的 `--mode` 空值 → `EMPTY_FIELD`；上游缺席 → `MISSING_FILE`；上游未定稿 → `STATUS_MISMATCH`——**三者都零写入**。

**四、铸骨架（`init`）**：复述确认（模式 + 入口各一句）→ 用户点头后调引擎：

```
python "{project-root}/.claude/skills/diy-wds-trigger/scripts/wds_trigger.py" init --mode "<W|S|D>" [--entry <工作坊|既有产物>] --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `--mode` **必填**（空值 → `EMPTY_FIELD`、非法值 → `ENUM_INVALID`，两者都零产出）。
- 骨架落 `project.status: 草稿` / `stage: 模式` + **首条记录 `BG-1`（`kind: 愿景` 空位）**；`project.name` / `created` 与 `mode` / `entry` 由 `init` 铸造后**不再由你改**。
- **已有产物 → 不覆盖**：同值重跑只刷 `project.updated` 并给一行 warning；`--mode` 与产物不符 → `SET_MISMATCH` 且零写入（**要改判先与用户确认，再往 `revisions` 记一条 `change`**）。
- 路径旗标不得省（引擎不自解析实例、不私读 `diy-coder.yaml`）。

**落盘**：`mode` / `entry` / `stage: 模式` / `business_goals[0]`（`init` 一次铸成）。

**检查点（六拍）**：① 生成 → ② 落盘（`init`；`stage` 留在 `模式`）→ ③ 分隔 → ④ 呈出回执与骨架摘要 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角）｜ `[y]` YOLO → 跳过后续检查点，连续推进（首次选中时一行明示）。

**收尾与路由**：走了「从既有产物起步」→ 读全并照做本文件 `## 第 2 步 —— 从既有产物起步`；否则本文件到此结束，直接读 `./02-goals.md`。

## 第 2 步 —— 从既有产物起步（源 step-00a–00f 的改写版，裁定 11）

**先说清为什么**：讲清「为什么可以不从头问」——你手上已经有一批产物，重复问一遍既浪费时间、也让两边说法漂移。这一步做的是**把既有材料翻译成触发图的键**，翻不出来的地方才回工作坊问。用你自己的话讲。

**源侧形态与 diy 的改法**：源侧这一步要**用户往会话里塞文档**（900 行，零落盘，终点还要二次询问——工作成果不被默认路径消费）。diy 侧**改写为「读 diy 既有产物」**：只读、按下面的字段映射表取值，找不到的键**当场回工作坊问**（不是编）。

### 2.1 覆盖图：七维 × diy 产物（源 `step-00a:74-87` 的七维，逐一给落点）

| 源 00a 的覆盖维 | diy 既有产物（只读） | 取哪些键 |
| --- | --- | --- |
| 愿景 / 战略陈述 | `wds-brief.yaml` | `brief.core.vision` · `brief.core.positioning` · `brief.core.product_concept` |
| 业务目标 / 可量指标 | `prd.yaml` · `brief.yaml` | `goals[].goal` · `goals[].metric` · `goals[].id`；`brief.distillate.value_props[]` |
| 用户研究结论 | `research.yaml` | `researches[].findings[]`（`area` / `claim` / `confidence`）· `synthesis.key_points[]` |
| 目标群描述 | `prd.yaml` · `brief.yaml` · `research.yaml` | `users[]`（`id` / `name` / `need`）· `brief.users[]`（`who` / `need`）· `distillate.target_users` |
| 用户痛点 / 需求 / 渴望 | `prfaq.yaml` · `brief.yaml` | `prfaq.essentials.problem` · `customer_faq[].q/a` · `brief.problem` |
| 项目计划 / 功能清单 | `prd.yaml` · `spec-kernel.yaml` | `features[]`（`id` / `name` / `description` / `requirements[]`）· `specs[].capabilities[]` |
| 用户心理洞察 | `research.yaml` · `brainstorm.yaml` | `findings[]`（`area` 取行为/心理类，`confidence` 必须非空）· `sessions[].open_questions[]` |

**读法纪律（硬）**：**只读取用、引用式提及**（写 `path:<relative>` 或键名，**禁复制内容**）。产物缺席或键为空 → 记一笔 **gap**，进工作坊问——**不推断、不代拟**。`wds-brief.yaml` 之外的产物**只读**，写权 100% 归其生产技能。

### 2.2 翻进触发图的键（七维 → 本产物的段）

| 覆盖维 | 落到本产物的 | 备注 |
| --- | --- | --- |
| 愿景 | `business_goals[0]`（`BG-1` / `kind: 愿景`） | **逐字符相同**（源 `07a:80` 的硬规则：找不到原文就问用户，不得转述） |
| 业务目标 | `business_goals[1..]`（`kind: 目标`，3–5 条） | 每条补齐 `metric` / `target` / `timeline`（非 SMART 的**退回工作坊问**） |
| 目标群描述 | `personas[].name` / `role` / `context` | **行为特征而非人口统计**（源 `step-00c:64-68`） |
| 用户心理洞察 | `personas[].driving_forces.{positive, negative}[]` | 每条补 `why`；正补 `promise`、负补 `answer` |
| 痛点 / 渴望 | `driving_forces.negative[]` | 源侧的改法：**痛点 → 心理化的负向驱动因素**（不是照抄痛点） |
| 功能清单 | `feature_impact[].name` | 只取**战略相关**的（跳过基础登录 / 标准 CRUD，源 `step-06a:62-72`） |
| 研究结论 | `story` 之外只作 `why` 的依据 | **本技能不产来源**——引 `research.yaml` 的 `RS-###`，不复述断言 |

### 2.3 差距分析与对齐核查（源 step-00f）

1. **强项 / 缺口各列一遍**（哪些维材料足、哪些是会话补的），**缺口给用户三选**：① 现在就补（跑一次定向工作坊）② 记为待查（写进 `revisions`）③ 就这样接受。
2. **对齐核查**（源 `step-00e` 的逆向工程）：把 `prd.yaml` 的 `goals[]` 与 `wds-brief.yaml` 的 `brief.core.vision` 对一次表——**计划与愿景不一致时当场呈出**，由用户裁，不静默择一。
3. 本步**不产新文件**，成果是 `business_goals` / `personas` 的骨架位与一份会话内的差距清单。

**检查点（六拍）**：① 生成 → ② 落盘（覆盖图结论进 `revisions` 的待查条目；键值在 02 / 03 两文件落）→ ③ 分隔 → ④ 呈出「已有 / 会话补 / 缺口」三栏 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

**收尾与路由**：`entry: 既有产物` 的会话在 02 / 03 两文件里**按覆盖图取值优先、只问缺的**；本文件到此结束，读 `./02-goals.md`。
