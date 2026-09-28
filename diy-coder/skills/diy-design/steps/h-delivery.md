# Step — [H] 交付（Handover）· 框架实现段

Progress: `[1 完成度核对] → [2 框架实现] → [3 交接摘要] → 收尾路由`

**Read (input):** `{output_dir}/design.yaml` 全部记录（含 `implementation` 目标路径）；`{output_dir}/prototypes/*.html`；`{output_dir}/architecture.yaml` 的 `stack[]`（框架取值）；`{output_dir}/stories.yaml` 的 `AC[].design_ref`（悬空检查，只读）；用户在本文件各步的回答。
**Write (output):** `src` 里的框架实现稿（每页一份）；`design.yaml` 的 `pages[].implementation` 路径与 `project.updated`；收尾交接摘要（会话内，不落独立 md）；`design_status` 推进（WDS 线，场景级键，值域见主文件规则 1）：实现开工写 `building`、该场景全部页实现完毕写 `built`、拿到用户明确批准后写 `approved`。

你是**设计总监**。H 段是**交付**：把设计稿落成**项目前端框架里的页面实现**（D-10）。纯 HTML 项目**止于结构稿**，本段省略（写 `html` 时直接收尾）。

## 第 1 步 —— 完成度核对

出实现前先核对三组清单（源 `steps-h/step-01` 的三组，diy 侧收编为三行）：

1. **规格完整性**：每页 `states[]` 四态齐、每态 ≥1 条非色彩信号、`prototype` 文件在场；
2. **token 单一源**：`audit` 零 `one-off-*`（含 `token_scope` 之外的第三方目录）；
3. **可测性**：每页 `states[].signals` 能被写成可核对判据（后面 `diy-dev` WDS 模式的浏览器门就从这里取判据）。

**不完整不许交付**（源 `step-01:38` `🚫 FORBIDDEN to proceed with incomplete flows`）；缺什么，**路由回对应技能**而不是在本段硬凑——缺设计规格回 `./p-specify.md`；缺故事/AC 回 `diy-epics-stories`；缺架构回 `diy-architecture`。

## 第 2 步 —— 框架实现

在 `{output_dir}/architecture.yaml` 的 `stack[].choice` 选定的框架里实现每页，代码落 `src`：

- **零翻译、零还原损耗**（D-10）：框架页**就是**设计稿，不是「照着画」；
- **token 经 CSS 变量注入**，与结构稿同一套 `--color-*` / `--space-*`；`audit` 必须过（`--src` 指项目根 `src`）；
- 每页路径记进该页的 `implementation`（校验器要求该文件存在）；
- **语义 HTML 三条不放松**（`h1` 唯一 / `img` 带 `alt` / `input` 带 label）。

WDS 线附带：本步**开工**（首份框架实现稿落笔前）把该 `SC-<nn>` 的 `design_status` 推到 `building`；该场景**全部页**实现完毕（`implementation` 全在场且 `audit` 过）推到 `built`——两档都在本步写，别留到收尾。

〔**源侧裁撤声明**〕源 `steps-h`（6 文件 906 行）里的三块**整块裁**：

| 裁撤块 | 源侧位置 | 理由 |
| --- | --- | --- |
| 设计交付契约 `deliveries/DD-XXX-name.yaml`（104 行模板） | `step-02:45,61,119` | 与 `design.yaml` 大面积重叠（`delivery.*` ≈ `project.*`；`design_artifacts.scenarios[].path` ≈ `pages[].prototype`；`technical_requirements.platform.frontend` ≈ `frontend_framework`）；且用了**无 `{output_folder}` 前缀的裸相对路径**（普查 §6.6），基址未定义 |
| 测试场景 `test-scenarios/TS-XXX-name.yaml`（192 行模板） | `step-03:45,61,128` | 责任归位：设计系统校验 + 无障碍 → `design.py check`（判据面 = 回执 `violations[].code`：`contrast` / `color-only-signal` / `semantic-html` · `a11y-touch-target` / `a11y-keyboard` · `ds-token-*` 族）；其余 → `diy-test-design` / `diy-e2e-tests` |
| BMad 平台耦合（十段交接对话 276 行台词、`assigned_to: 'bmad-architect'`、`created_by: "wds-ux-expert"`） | `workflow-handover.md:6`、`step-04:100`、`data/handoff-dialog-scripts.md` | 平台耦合（X9）；diy 侧交接对象是 `diy-dev`，不是某个角色 |

**保留的是判据不是文件**：三组完成度清单（第 1 步）+ 「不完整不许交付」的禁令 + 「交接后并行开下一条流程」的续接语义（源 `step-06`，diy 侧 = 逐页串行，页级 `status` 说清进度）。

## 第 3 步 —— 交接摘要

呈出（会话内，**不落盘**）：逐页一行（页 ID / `implementation` 路径 / 状态）；`audit` 与 `check` 的回执摘要；悬空 `design_ref` 清单（若有，路由 `diy-epics-stories`）；未决项（`open_questions` 的 `待办` 条数与去向）。

**定稿条件**（与主文件「工作流」第 6 步一致，此处只重申判据）：三命令全过 + `[假设]` 清零 + `open_questions` 零 `待办` → 才写 `project.status: 已定稿`。

**WDS 线附带（`approved`）**：该 `SC-<nn>` 全部页 `built` 后，**先拿到用户对该场景设计的明确批准**（人裁——`diy-review` 不代批，本技能也不代批），才把 `scenarios[].design_status` 推到 `approved`；**没有明确批准不得预写**。它是场景级键，与页级 `pages[].status: 已批准`（用户逐页批准）是两回事。纯 HTML 项目省略本段时，本档在 `./prototype-loop.md` 第 3 步的同一条件下写（**二者二择一，不重复写**）。

**检查点**：① 生成 ② 落盘 `implementation` 与 `project.updated`（WDS 线：+ `design_status` 的 `building` / `built` / 用户批准后的 `approved`）③ 分隔 ④ 呈出交接摘要 ⑤ 给选项 ⑥ 等响应。

**收尾与路由**：本技能到此结束——下游是 `diy-dev`（主线：`sprint.yaml`；WDS 线：`design.yaml` 的 `project.status: 已定稿` 门禁 + 该页 `states[].signals` 作测试源）。

**裁撤登记（其余）**：源 `delivery-templates.md`(188) / `handoff-dialog-scripts.md`(276) / `design-deliveries-guide.md`(489) 合计 953 行随本段裁；源 `templates/design-delivery.template.yaml`(104) 与 `templates/test-scenario.template.yaml`(192) 同批裁（合计 296 行）。

本文件到此结束，不再回头。
