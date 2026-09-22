---
name: diy-wds-evolution
description: 'WDS line, brownfield increment — run one Kaizen cycle (Analyze → Scope → Design → Implement → Test → deliver) against an existing product, one improvement at a time. Use when the user says "improve this product" / "run a kaizen cycle" / "next increment".'
# ↑ 中文：WDS 线·棕地增量——在一件**已存在的产品**上跑一轮 Kaizen 迭代（A 分析 → S 范围 → D 设计 → I 实现 → T 验证 → 交付），一次只做一条改进。产物落 `wds-evolution.yaml`（顶层 `project.status`，逐轮写 `rounds[]` 六相 + 顶层 `kaizen_priority`），每轮 ID `EV-<nn>`。**入口技能**（`precededBy: []`，裁定 9）：门禁 = 既有产物**任一**在场（`design.yaml` / `sprint.yaml` / `wds-*.yaml`），缺失 → 零产出停止。用户说 "improve this product" / "run a kaizen cycle" / "next increment" 时触发。
phase: 3-wds-build
precededBy: []
followedBy: []
required: false
line: wds
outputs: wds-evolution.yaml
---

# diy-wds-evolution — 棕地增量的 Kaizen 迭代流水线

你是**Kaizen 迭代的主持人**。输入：一件**已存在的产品**（其产物在场即可）与一个选定目标。产出：`{output_dir}/wds-evolution.yaml`——逐轮的六相记录（分析 / 范围 / 设计 / 实现 / 验证 / 交付）+ 顶层 Kaizen 优先级清单。边界：**WDS 线与 diy 主线（prd → design → dev）并行不交汇**——只写自己的产物；深挖某步产出时调用 `diy-elicit`、要多视角审视时调用 `diy-party-mode`（零写面：增强结果在会话内呈现，落盘归本记录）。**本技能的不可替代内容是 Kaizen 方法论**（`data/kaizen-principles.md` + `data/priority-framework.md`）——六个活动本身与 `diy-dev` 同构，方法论不同构。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：跑 `list` 看有没有已在做的轮次——**只回 `id` / `target` / `status` / `entry` 四字段，不读正文**：
   `python "{project-root}/.claude/skills/diy-wds-evolution/scripts/wds_evolution.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json`
   有记录 → 播报四字段并问「① 接着做 / ② 开新的一轮 / ③ 复审调整」，**HALT 等选择**；无记录 → 进第 3 步。
3. 门禁（零产出退出）：**本技能是入口技能**（`precededBy: []`，裁定 9）——门禁 = `{output_dir}` 下**既有产物任一在场**（`design.yaml` / `sprint.yaml` / `wds-*.yaml`，**本技能自己的产物不算**）。一个都没有 → 一行说明并**零产出停止**（新建项目走 `diy-wds-brief` / `diy-prd`）；`init` 把它机械兜住（`MISSING_FILE`）。门禁过 → 按 `entry` 分轨读取（`存量接入` = 首次接手，`上线后持续` = 线上迭代）。读 `steps/01-analyze.md` 并照做（裸 `steps/*.md` 与 `data/` 路径从本技能安装目录解析；每步结尾点名下一个要读的文件）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；除检查点外每步产出整块给出；`rounds[]` 与 `kaizen_priority` 由你直接编辑 `wds-evolution.yaml`（内容型产物，写权归会话），骨架与校验归引擎。
1. `steps/01-analyze.md` — 载上下文与入口门禁 → 双轨上下文与五源目标清单 → Kaizen 排序与选定目标（**用户关卡 1** + `init` 铸骨架）→ 分析落盘。
2. `steps/02-scope.md` — 载分析 → 定义变更 → 微旅程映射 → 范围估算 → 场景落盘与呈批（**用户关卡 2**）。
3. `steps/03-design.md` — 载场景 → 择法三选一 → 设计变更 → 写规格（mini page-spec）→ 规格签核。
4. `steps/04-implement.md` — 载规格 → 建分支 → 读懂现状代码 → 实施变更 → 自检。
5. `steps/05-test.md` — 载测试上下文 → 备环境 → 逐条执行（**只验本轮增量**）→ 报告落盘 → 失败三路处置。
6. `steps/06-finish.md` — 预交付清单与交付摘要 → 可选 PR 与下轮计划 → 质检、定稿与收尾（含终门）。

写回纪律：骨架由 `01-analyze.md` 第 3 步的 `init` 铸为 `project.status: 草稿` + 首轮 `EV-01`；逐轮把 `status` 从 `草稿` 推到 `已交付`；定稿 = `project.status: 已定稿` **且全部轮次 `已交付`**（开新轮次即回到 `草稿`）。`project.name` / `created` 由 `init` 铸造后**不再由你改**。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/wds-evolution.yaml` —— 唯一源头；顶层设 `project.status`（母本 §8 两值口径）：

```yaml
project: {name, created, updated, status}   # status: 草稿|已定稿；created 建文件时设、此后不改
kaizen_priority:                            # 本技能独有的方法签名（`data/priority-framework.md`）
  {formula: "Priority = Impact × Effort × Learning", scale: {impact: {high: 5, medium: 3, low: 1},
   effort: {…}, learning: {…}}, candidates: [{target, impact: high|medium|low, effort: …, learning: …, score, rationale}]}
rounds:                                     # 每轮 = 一次 Kaizen 迭代；追加式，不重编不复用
  - {id: EV-01, target: <本轮选定目标>, status: 草稿|分析|范围|设计|实现|验证|已交付,
     entry: 存量接入|上线后持续}    # target 须在 candidates[].target 内；status = 记录级推进锚点
    analysis: {snapshot, sources[], root_cause, hypothesis, validation_plan, current_state,
               targets_considered[], selected_rationale}                                    # A
    scope: {target, page, current_state, desired_state, journey, success_criteria, pages_affected[],
            components_touched{new,modified,removed}, data_changes, risk: Low|Medium|High}   # S
    design: {approach: quick-fix|sketch-first|generate, change_summary, before, after, components[],
             responsive, acceptance_criteria[], assets_needed[], hypothesis{…}, approved{by,on,notes}}   # D
    implement: {branch, files[], self_review{diff_checked,criteria_addressed[],side_effects[],cleanup}}   # I
    test: {scope: 本轮增量, environment, summary, issues[], recommendation, failures_handled[],
           criteria[{kind: HP|REG|EC|A11Y, criterion, how, expected, actual, verdict: 通过|未通过}]}       # T
    delivery: {summary, artifacts{analysis,scope,design,implement,test,pr}, impact, effort, notes, next,
               monitoring{metrics[],period,watch_for[]}}                               # P：增量纪律内核
revisions: []                               # {date, change, reason}
```

**只产本 YAML**：不建 `evolution/` 目录树、不建 `deliveries/` / `test-reports/` / `specs/` 散 md（源侧活动文件与步骤件的两套路径互不覆盖，diy 归一为单一源）。`[I]` 的代码改动落**目标项目**、不进本产物（`rounds[].implement.files[]` 存路径）。

## 规则

1. 写范围与副作用三档：只写 `{output_dir}/wds-evolution.yaml`（`project` / `kaizen_priority` / `rounds[]` / `revisions`）+ `[I]` 阶段在目标项目里按 `scope.pages_affected[]` 改的实现文件；不碰 `design.yaml` / `sprint.yaml` / `wds-*.yaml`（**既有产物只读**——要修正走 `revisions` 建议或路由回其生产技能）、不建任何散文件与目录树。① 自动档 = 本产物 + `[I]` 的代码改动 / 建分支 / 本地构建与测试 / `git add`+`git commit`；② 保留确认档 = `push --force` / 删分支 / 目标项目与 `{output_dir}` 之外写盘（无头经 `diyc.py defer-add` 入队，不阻塞）；③ **本技能不接任何外部服务**（无 MCP、无外部生成 API）。非 git 仓库 → 不做任何 git 动作、**不替用户 `git init`**。
2. **检查点四选项**（每步产出后，六拍不得省）：① 生成本步产出 → ② 落盘（编辑对应相段 + 推进轮次 `status`）→ ③ 显示检查点分隔 → ④ 呈出本步产出 → ⑤ 出四选项 → ⑥ 等响应。
3. **选项落点**：`[a] Advanced Elicitation` → 调用 `diy-elicit`；`[p] Party-Mode` → 调用 `diy-party-mode`（两者**零写面**：增强 / 多视角产出的内容并入对应相段，调用返回后回到第 ② 拍重落盘）；`[c] Continue` → 直接进下一步；`[y] YOLO` → 后续步骤跳过 ⑤⑥（不停等），**②③④ 照旧**。无头 / 非交互 = 全程 `[y]`（摘要一行明示），**不入 `deferred-actions` 队列**。
4. **两个用户关卡不得省**：`01-analyze.md` 的候选排序与选定目标（**用户关卡 1**）、`02-scope.md` 的场景呈批（**用户关卡 2**）——**没拿到明确点头不许往下走**；`--entry` 与择法三选一同样必须由用户显式选，不代选。
5. **Kaizen 差异化（源 `data/kaizen-principles.md`，全保）**：`Priority = Impact × Effort × Learning` 三因子三档（5/3/1）+ Kaizen vs Kaikaku 对比 + 四条原则（盯过程 / 消除 Muda 無駄 / 尊重他人洞见 / 先标准化再改进）+ 何时暂停三情形——**落 `data/`，是本技能相对 `diy-dev` 的唯一不可替代内容**。**一次只做一条**：未选中的目标进 `candidates[]`，是本轮之外的原料。
6. **ID 与产物（裁定 2/3）**：轮次 `EV-<nn>`（两位、递增、不重编不复用、由 `check` 机械核连续性）；`kaizen_priority` 是本技能独有的顶层段。**`target` 的 `score` 必须重算一致**——三因子判定**是人工的**（框架只保证排序自洽，不保证判定正确），故每个因子的判定理由写进候选的 `rationale` 备查。
7. **终门（机械）**：先落 `project.status: 已定稿` + 本轮 `status: 已交付`，再跑 `python "{project-root}/.claude/skills/diy-wds-evolution/scripts/wds_evolution.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——`exit 0` 是唯一放行；零 `[假设]`（未决项写 `revisions` 或就地补问）。渲染与收尾都等 exit 0。**WDS 型产物一律走本引擎终门**，不得改用 `diyc.py check --type`（那是主线 8 型封闭集）。
8. **违规码**：复用冻结集（`MISSING_FILE` / `UNPARSABLE_YAML` / `DUPLICATE_ID` / `UNKNOWN_ID` / `EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` / `SET_MISMATCH` / `ASSUMPTION_PRESENT`，**本批不新增码**）；`MISSING_FILE` 承载「入口门禁：无任何既有产物」，`STATUS_MISMATCH` 承载「`--final` 时非 `已定稿`」「轮次未 `已交付`」「本轮判据有 `未通过`」三类。
9. **无 `--previous` 轮**：`rounds[]` 与 `candidates[]` 只增不减，无 ID 集合收缩面；改既有内容往 `revisions` 追加（date / change / reason，`change` 点名 `EV-<nn>` 或键名而不复制内容）。产物内引用一律 project-root 相对 `path:line`。
10. **边界（对方侧随 C 阶段补；本技能产 WDS 线产物——不进 diy 主链 CHAIN、不被主线任何门禁引用）**：vs `diy-dev`——它走主线的 `sprint.yaml` 全量 TDD 与**全量验收**；本技能走**一轮一增量**，`[T]` **只验本轮增量**（裁定 10，全量验收归 C 阶段的 `diy-dev`）。vs `diy-correct-course`——**变更提案**（范围与路线要不要改）归它；本技能承接的是**在已定路线上的小步改进**。vs `diy-design` / `diy-dev` 的 WDS 模式——那是 C·3 的事，本批不接。vs `diy-elicit` / `diy-party-mode`——不是竞争是调用（见规则 3）。
11. **本线风格与 HARM/HELP（源 Kaizen/Freya 线归位）**：一次一条、小步快跑、**每个数字都带出处**——问「这个数从哪来」，答不出的先别写进产物（源原则「盯过程，不只盯结果」）。**HARM**：一轮里塞进三条改进（范围悄悄膨胀），`[T]` 的判据表泛化成「大致符合预期」——下一轮无从分辨是哪条起了作用；**HELP**：落笔前把 `candidates[]` 的 score 与 `acceptance_criteria[]` 念一遍，交付一份「不看后台也能读懂改了什么、指望什么、该盯什么」的轮次记录。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
