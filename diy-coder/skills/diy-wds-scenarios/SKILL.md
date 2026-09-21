---
name: diy-wds-scenarios
description: 'WDS line third stage — turn the Trigger Map into scenario outlines with linear sunshine paths, page records and a page coverage matrix. Use when the user says "create the scenarios" / "outline the scenarios" / "build the page tree".'
# ↑ 中文：WDS 线第三环（触发图 → 场景大纲 + 页面树）——产物落 `wds-scenarios.yaml`（顶层 `project.status`），逐场景写 `scenarios[]` 记录、其下写 `pages[]`；场景 ID `SC-<nn>`、页面 ID `SC-<nn>.P<n>`。**只产 YAML，不建目录树、不建 `Sketches/`**（那是 C·3 `diy-design` 的产物位）。门禁 = 读 `wds-trigger.yaml` 且 `project.status: 已定稿`；缺失 → 零产出停止并路由 `diy-wds-trigger`。用户说 "create the scenarios" / "outline the scenarios" / "build the page tree" 时触发。
phase: 2-wds-design
precededBy: [diy-wds-trigger]
followedBy: []
required: true
line: wds
outputs: wds-scenarios.yaml
---

# diy-wds-scenarios — WDS 线第三环（触发图 → 场景大纲与页面树）

你是**场景大纲的主持人**。输入：一份已定稿的触发图（每条场景 = 一条战略链：业务目标 → 人物 → 驱动因素 → 交易）。产出：`{output_dir}/wds-scenarios.yaml`——逐场景的 8 问大纲 / 线性阳光路径 / 页面记录 / 页面覆盖矩阵。边界：**WDS 线与 diy 主线（prd → design → dev）并行不交汇**——只写自己的产物，不读也不写 `prd.yaml` 等主线产物；深挖某条场景时调用 `diy-elicit`、要多视角审视时调用 `diy-party-mode`（零写面：增强结果在会话内呈现，落盘归本记录）。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：跑 `list` 看有没有已在做的场景——**只回 `id` / `name` / `persona` / `pages` / `priority` / `status` 六字段，不读正文**：
   `python "{project-root}/.claude/skills/diy-wds-scenarios/scripts/wds_scenarios.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json`
   有记录 → 播报六字段并问「① 接着做 / ② 复审调整 / ③ 推倒重来」，**HALT 等选择**；无记录 → 进第 3 步。
3. 门禁（零产出退出）：读 `{output_dir}/wds-trigger.yaml`——**缺失 → 一行说明并零产出停止，路由 `diy-wds-trigger`**；其 `project.status: 已定稿` 不成立 → 同样零产出停止（`init` 会把两者机械兜住：`MISSING_FILE` / `STATUS_MISMATCH`）。门禁过 → 按它只读取 `business_goals[]` / `personas[]`（`TG-<n>` + 其驱动因素）/ `priority`；`{output_dir}/wds-brief.yaml` 可选读（SEO 关键词与站点上下文，缺则记 gap）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-context.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；除检查点外每步产出整块给出；`scenarios[]` 与 `pages[]` 由你直接编辑 `wds-scenarios.yaml`（内容型产物，写权归会话），骨架与校验归引擎。

1. `steps/01-context.md` — 载上下文与续接检测 → 规模分析与页清单（**用户关卡 1**）→ `init` 铸骨架 + `SC-01` 铸号。
2. `steps/02-strategy.md` — 战略链与 7 问决策矩阵 → 页面分配（每页恰属一条链）→ 优先级三层 → 覆盖核查。
3. `steps/03-plan.md` — 场景计划呈批（**用户关卡 2**）→ 命名铁律（场景名必须含人物名）→ ID 定稿 → 计划记录落盘。
4. `steps/04-outline.md` — 逐场景循环（8 问 + 7 道质量闸）→ 落 `scenarios[]` 与 `pages[]` → 逐页串行与循环判定。
5. `steps/05-overview.md` — 场景索引呈出 → 页面覆盖矩阵与覆盖率核对（机械取 `show` 回执）。
6. `steps/06-finish.md` — 质检四维 + 五维校验并入 → 交接与设计意图拍定 → 定稿与终门（含源 32 闸抽取清单）。

写回纪律：骨架由第 1 步的 `init` 铸为 `project.status: 草稿`，首条记录 `SC-01` 同时铸号；逐场景把 `status` 从 `草稿` 推到 `已大纲`；定稿 = `project.status: 已定稿` + 全部记录 `已大纲`。`project.name` / `created` 与铸出的 `id` 由 `init` 铸造后**不再由你改**；`design_status` 只设初值 `not-started`（推进归 C·3 的 `diy-design`）。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/wds-scenarios.yaml` —— 唯一源头；顶层设 `project.status`（母本 §8 两值口径）：

```yaml
project: {name, created, updated, status}   # status: 草稿|已定稿；created 建文件时设、此后不改
scope: {site_type: presentation|dynamic|mixed, scale: small|medium|large, approach: 对话|建议,
        scenario_format: screen-flow|storyboard|mixed, page_strategy: {individual: [], templated: []}}
page_inventory: [{name, purpose}]           # 完整页清单；name 是覆盖矩阵的连接键（须唯一）
scenarios:                                  # 每条 = 一条战略链
  - id: SC-01                               # 两位序号、顺序递增、不重编不复用
    name: "<人物名> 的 <目的>"                # 骨律：场景名必须含人物名
    priority: 1|2|3                         # 关键路径 / 支撑 / 边角
    status: 草稿|已大纲                      # 记录级推进锚点
    trigger_map_context: {target_group: TG-<n>, drivers: [DF-<n>.<m>+|-], business_goal: BG-<n>}
    design_intent: K|C|S|D|L                # 交接契约（C·3 的 diy-design 按它预选活动）
    design_status: not-started              # 初值；推进归设计线
    transaction / situation / driving_forces{hope,worry} / device / entry / success{user,business}
    pages:                                  # Q8 的线性阳光路径（有序、页号连续、零分支）
      - {id: SC-01.P1, slug: 01.1-<页 slug>, name, purpose, entry_context,
         exit_action, on_page_interactions: []}
revisions: []                               # {date, change, reason}
```

**只产本 YAML**：不建 `C-UX-Scenarios/` 目录树、不建页面文件夹与 md、不建 `Sketches/`（裁定 12——那是 C·3 `diy-design` 的产物位）。下游 `diy-design` 按 `design_intent` 预选设计活动，按 `trigger_map_context`（目标 / 人物 / 2–4 条驱动）取锚——**三方唯一契约**。

## 规则

1. 写范围：只写 `{output_dir}/wds-scenarios.yaml`（`scope` / `page_inventory` / `scenarios[]` / `revisions`）；不碰 `wds-brief.yaml` / `wds-trigger.yaml`（**上游只读——要修正走 `revisions` 建议或路由回上游技能重跑**）、不碰 `prd.yaml` / `design.yaml` / 源码，也不建任何散文件与目录树。
2. **检查点四选项**（每步产出后，六拍不得省）：① 生成本步产出 → ② 落盘（编辑对应键/记录 + 推进记录级 `status`）→ ③ 显示检查点分隔 → ④ 呈出本步产出 → ⑤ 出四选项 → ⑥ 等响应。
3. **选项落点**：`[a] Advanced Elicitation` → 调用 `diy-elicit`；`[p] Party-Mode` → 调用 `diy-party-mode`（两者**零写面**：增强 / 多视角产出的内容并入对应记录，调用返回后回到第 ② 拍重落盘）；`[c] Continue` → 直接进下一步；`[y] YOLO` → 后续步骤跳过 ⑤⑥（不停等），**②③④ 照旧**。无头 / 非交互 = 全程 `[y]`（摘要一行明示），**不入 `deferred-actions` 队列**。
4. **两个用户关卡不得省**：`01-context.md` 的规模分析呈批（用户关卡 1）与 `03-plan.md` 的场景计划呈批（用户关卡 2）——**没拿到明确点头不许往下走**。
5. **三条骨律（源 step-05，全保）**：① **阳光路径零分支**（`pages[]` 有序、页号连续）；② **场景名必须含人物名**；③ **每页恰属一条战略链**（`page_inventory[]` 的每一页在全部 `scenarios[].pages[]` 里恰出现一次——漏配 / 重复分配 / 清单外的页各判违规）。
6. **ID 体系（裁定 8）**：场景 `SC-<nn>`、页面 `SC-<nn>.P<n>`（**废止独立的 `P-*` 前缀**）、人物引用 `TG-<n>`；页面 `slug` 保留源侧 `NN.<p>-<页 slug>` 形态作**展示名**，但它必须与 ID 同源（引擎机械核）；**ID 是唯一引用键**，记录之间一律引 ID 不复制内容。
7. **终门（机械）**：先落 `project.status: 已定稿`，再跑 `python "{project-root}/.claude/skills/diy-wds-scenarios/scripts/wds_scenarios.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——`exit 0` 是唯一放行；零 `[假设]`（未决项写 `revisions` 或就地补问）。渲染与收尾都等 exit 0。**WDS 型产物一律走本引擎终门**，不得改用 `diyc.py check --type`（那是主线 8 型封闭集）。
8. **违规码**：复用冻结集（`MISSING_FILE` / `UNPARSABLE_YAML` / `DUPLICATE_ID` / `UNKNOWN_ID` / `EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` / `SET_MISMATCH` / `ASSUMPTION_PRESENT`）+ B6 的已批码 `TOKEN_UNRESOLVED`（**本批不新增码**）；`SET_MISMATCH` 承载 ID 跳号 / 页号不连续 / slug 与 ID 不同源 / 覆盖矩阵违规四类。
9. **无 `--previous` 轮**：`scenarios[]` 与 `pages[]` 只增不减，无 ID 集合收缩面；改既有记录往 `revisions` 追加（date / change / reason，`change` 点名 `SC-<nn>` 而不复制内容）。副作用面：除产物与静默渲染外无任何外部动作；产物内引用一律 project-root 相对 `path:line`。
10. **边界（对方侧随 C 阶段补；本技能产 WDS 线产物——不进 diy 主链 CHAIN、不被主线任何门禁引用）**：vs `diy-design`——它吃主线 `prd.yaml` 的 `已定稿` 并产 `design.yaml`，**WDS 线止于本技能**（`diy-design` 接本线是 **C·3** 的事）。vs `diy-epics-stories`——`SC-*`（场景 / 页面树）与 `S-*` / `AC-*`（主线故事）**不互译、不互替**。vs `diy-wds-brief` / `diy-wds-trigger`——它们是本技能的上游（触发图那份是硬门禁，只读）。vs `diy-elicit` / `diy-party-mode`——不是竞争是调用（见规则 3）。
11. **本线风格与 HARM/HELP（源 Freya 线归位）**：把页面当成要被设计审视的对象摆出来——**规格必须完整**（源原则：不完整的规格到设计阶段一定要返工）、**先原型后生产**、**设计系统从实际使用中长出**。**HARM**：场景读起来顺、但页面上没有一页能承接这条交易（页清单与交易脱节，下游只能重做）；**HELP**：每条场景落盘前把「人物 → 驱动 → 交易 → 页」串一遍，交付一份不按键表也能读懂的记录。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
