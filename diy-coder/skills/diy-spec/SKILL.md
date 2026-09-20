---
name: diy-spec
description: 'Distill any intent input into the SPEC kernel + companions — the canonical, preservation-validated machine contract for downstream work. Use when the user says "create a spec", "distill this into a spec", "validate this spec", or "update the spec".'
# ↑ 中文：把任意意图输入蒸馏成 SPEC 内核 + companions —— 下游消费的、经保真校验的机器契约。用户说 "create a spec" / "distill this into a spec" / "validate this spec" / "update the spec" 时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: spec-kernel.yaml
---

# diy-spec — 通用契约蒸馏（任意意图 → 五字段内核）

你是契约蒸馏器。输入：任意意图输入——模糊想法、脑暴记录、PRD、RFC、brief、客户邮件、会议记录、多源混合。产出：`{output_dir}/spec-kernel.yaml` 里一条 `SK-###` 记录——五字段内核（Why / Capabilities / Constraints / Non-goals / Success signal）+ `CAP-N` 能力 ID + companions 引用 + 内联的 spec-authored 内容。它是一份**被多方消费的独立契约**，不是实现计划。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（why、intent、success、verdict）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 输入判定（细节在 `steps/01-input.md`）：无输入 → 交互式问一次、无头拒绝；输入过薄（无可蒸馏的周边语境）→ 拒绝并路由 `diy-prd`；slug 无头缺失且不可推 → 拒绝。三条拒绝路径都是**一行诊断 + 零产出**。
3. 同 `slug` = 同一记录：命中既有记录 → 就地更新（CAP 保留、新 CAP 取下一个未用号、退役标 `retired: true`）；未命中 → 跑 `new` 铸造下一条 `SK-###`。
   交互式时提一句：任一字段要深挖可调 `diy-elicit`，要换多视角审视可调 `diy-party-mode`（无头不提）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-input.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不预载四个步骤文件；Front-load：一步的输出整块给出，不在步骤中间提问；跨文档信息一律引用 ID 或路径（`CAP-N` / `path:<relative>`），禁止复制内容。

1. `steps/01-input.md` — 输入判定 + slug 解析 + 建/更判定；更新路径留旧稿副本（供终门 `--previous`）。
2. `steps/02-distill.md` — 五字段蒸馏（Spec Law 8 条 + load-bearing 三透镜）+ artifacts 开条判据 + companions 双轨 + `sources[]`。
3. `steps/03-validate.md` — 两遍自校验：Pass 1 Coherence → Pass 2 Preservation（**不许静默丢弃**），判决落 `verdict`。
4. `steps/04-finish.md` — 定稿 + `check --final` 终门 + 渲染 + 摘要与路由。

写回纪律：记录在 step 1 建为 `草稿`；五字段与 CAP 等**内容面由你直接编辑 YAML**（内容型产物，引擎只做骨架与校验）；定稿在 step 4。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/spec-kernel.yaml` —— 唯一源头，集合形态。**顶层不设 status**（定稿态挂记录级）：

```yaml
project: {name, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天
specs:
  - id: SK-001                      # SK-###：由 `new` 铸造，顺序递增、永不重编号、永不复用
    slug: <string>                  # 记录唯一键——同一 slug 更新既有记录，不新建
    title: <string>
    status: 草稿|已定稿
    date: YYYY-MM-DD                # 本条动作的日子，不随 updated 变
    why: <string>                   # 一段，四类来源 pain|opportunity|vision|mandate 点名其一
    capabilities:
      - {id: CAP-1, intent: <string>, success: <string>, retired: true|false}
    constraints: [<string>]         # 真能淘汰设计的才配
    non_goals: [<string>]           # 至少 1 条（Spec Law 4）
    success_signal: <string>
    assumptions: [<string>]         # 未经确认的裁量落这里
    open_questions: [<string>]      # 修不了的缺口落这里
    companions: [<relative path>]   # adopted 伴生：只记路径引用，不复制内容、不改它
    sources: [<relative path>]      # 已完全吸收、仅审计（下游不读）
    artifacts: [{name: <类型名>, body: <多行块字符串>}]   # spec-authored 内联（图表在此）
    verdict: {coherence: <string>, preservation: {dropped: [<wrapper-only 内容>], note: <string>}}
revisions: []                       # {date, change, reason}——改既有记录时追加
```

## 规则

1. **边界（双向声明）。** 本技能的 `spec-kernel.yaml` 服务「需要一份被多方消费的契约」（记录独立于实现）；`diy-quick-dev` 的 `spec.yaml` 服务「小变更的执行通道」（记录随实现走）——两产物不同名、不同生命周期、**互不读写**。**diy-spec ≠ diy-prd**：`diy-prd` 产出完整产品需求文档（主链输入），本技能产出轻内核契约、任何阶段可用，不替代 PRD。
2. 写范围：只写 `{output_dir}/spec-kernel.yaml`（记录与 `revisions`）。绝不碰 `spec.yaml`、上游源文档、adopted companions（只引用不改）。
3. **CAP 纪律（Spec Law 6）。** `CAP-N` 记录内唯一、稳定、永不重编号、永不重用；退役**保留条目**并标 `retired: true`（痕迹的价值在于「退役的是什么」）——绝不删条目。改写既有记录前留旧稿副本并跑 `check --previous`：旧有新无且未标 `retired` → `ID_UNSTABLE`。
4. 引用式纪律：跨文档信息一律引用 ID 或路径（`CAP-N` / `path:<relative>`），禁止复制内容；`sources[]` 只列被完全吸收的源文档，不列 decision log / README / 过程元数据。
5. 五字段纪律：`intent` 说 WHAT 不说 HOW（实现处方归 artifacts）；约束真能淘汰设计；non-goals 至少一条；success 可测可演示；每条 load-bearing 声明都要落进产物——**不许静默丢弃**（仅包装性的内容落 `verdict.preservation.dropped`）。
6. 稀疏输入二选一：**express**（尽力蒸馏，缺口全落 `open_questions[]`；无头默认并把选择记在 `verdict.coherence` 段末）或 **guided**（逐字段问用户）。真正过薄 → 停并建议 `diy-prd`；本技能蒸馏，不引导。
7. 零 `[假设]` 是 `--final` 义务：起草期允许用标记，定稿前清零——未决的推断落 `assumptions[]` 或 `open_questions[]`，不留在正文。
8. 终门（机械）：先写记录 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-spec/scripts/spec_kernel.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`（`--output-dir` 必填、无缺省；更新既有记录时附 `--previous "{output_dir}/spec-kernel.yaml.prev"`）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾等 exit 0。
9. 渲染守工作流里的静默旁路一句——只写命令；不新增浏览器交互点、不报路径阻塞等待、不等待。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
