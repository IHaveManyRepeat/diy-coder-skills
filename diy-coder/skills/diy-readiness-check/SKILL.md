---
name: diy-readiness-check
description: 'Validate PRD, UX, Architecture and Epics specs are complete. Use when the user says "check implementation readiness". Produces one verdict record in readiness.yaml.'
# ↑ 中文：开工前校验 PRD、UX、架构与史诗/故事规格是否齐备。用户说 "check implementation readiness" 时触发。产出一条判定记录，落在 readiness.yaml。
phase: 3-solutioning
precededBy: [diy-epics-stories]
followedBy: []
required: true
line: mainline
outputs: readiness.yaml
---

# diy-readiness-check — 开工前对齐体检（YAML 单一源）

你是需求追溯专家——成功与否，看的是在实现开工前揪出别人留下的规划失误。输入：`prd.yaml` + `epics.yaml` + `stories.yaml`（`architecture.yaml` / `design.yaml` 在场则一并核对）。产出：`{output_dir}/readiness.yaml` 里的一条记录。你只评估与路由——**绝不修补上游文档**。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（消息、证据、路由）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 目标文件 `{output_dir}/readiness.yaml`：只在铸下一个 `IR-###`、或按 `id:` 行修订一条记录时才打开；需求计数与覆盖一律取 `collect` 回执，绝不重读 `prd.yaml` 手数。本 schema 不定义 `detail` 字段——没有可跳过的内容。
3. 硬门（`collect` 机械判定）：`{output_dir}/prd.yaml` 必须在场，且 `{output_dir}/epics.yaml` / `{output_dir}/stories.yaml` 的 `project.status: 已定稿`。
   - 满足 → 继续第 4 步。
   - 不满足 → `collect` exit 1、**零产出**：转述它的一行理由与 `gate.route`，然后停下——拒绝永不成为记录。
4. 确定性开场——门禁 + 需求清点 + 覆盖矩阵 + 委派 diyc 的跨文档核对：
   `python "{project-root}/.claude/skills/diy-readiness-check/scripts/readiness.py" collect --project-root "{project-root}" --output-dir "{output_dir}" --json`
5. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
6. 读 `steps/01-document-discovery.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只载一个 `steps/` 文件——绝不预载或批量载六个步骤文件；前置给全（front-load）——一步的输出整块给出，不挤牙膏；每条 finding 都带证据锚点；产物叙述用 `document_output_language` 写、对话讲 `communication_language`。

1. `steps/01-document-discovery.md` — 从回执清点真实文档集；与人把重复或游离版本落定；起草记录。
2. `steps/02-requirement-inventory.md` — 需求清点取自回执（结构化 `prd.yaml`，不手工重抽 markdown），并报告清点缺口。
3. `steps/03-coverage-validation.md` — FR 覆盖矩阵对 AC 引用；`diyc.check.violations` 是机械证据；每个缺口写清影响与建议。
4. `steps/04-ux-alignment.md` — design/UX 的在场与对齐；无 `design.yaml` → 判 UX 是否被隐含并告警。
5. `steps/05-epic-quality-review.md` — 史诗的用户价值、独立性、依赖、故事粒度、AC 质量；技术型史诗是错误。
6. `steps/06-final-assessment.md` — 汇总裁决、定 `verdict`、定稿记录并过终门。

记录写入：第 1 步末尾先建 `status: 草稿` 的记录（计数与覆盖照抄回执，绝不凭记忆重打），各节随对应步骤填，第 6 步定稿。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/readiness.yaml` —— 唯一源头，集合形态（顶层形状对齐 `bug-log.yaml`）：

```yaml
project: {name, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天；本文件不设 project.status
checks:
  - id: IR-001                  # IR-###：顺序递增、稳定，永不重编号、永不复用
    date: YYYY-MM-DD            # 本条动作的日子，不随 updated 变
    status: 草稿|已定稿          # 记录级；`已定稿` 是终门检查的对象
    scope: [prd, architecture, epics, stories, design]   # 实际清点到的文档，取其子集（不得为空）
    verdict: 就绪|有风险就绪|未就绪   # 起草期留空
    findings:
      - {area: prd|epics|stories|ux|architecture, severity: 严重|高|中|低, message, evidence, route?}
    coverage: {must_frs: 0, covered: 0, gaps: []}   # 必须级 FR 覆盖，取 collect 回执
    counts: {frs: 0, nfrs: 0, epics: 0, stories: 0, acs: 0, findings_by_severity: {}}
revisions: []                   # {date, change, reason} —— 改既有条目时追加
```

## 规则

1. 写范围：只写 `{output_dir}/readiness.yaml`——记录与其 `revisions`。绝不编辑 `prd.yaml`、`epics.yaml`、`stories.yaml`、`architecture.yaml`、`design.yaml`：finding 的 `route` 点名由谁修，本技能一个补丁都不打。
2. verdict 一致性：`就绪` ⇒ 零 `严重`|`高` finding；`未就绪` ⇒ 至少一条。每条 finding 带 `evidence` 锚点（文件、ID 或引述原句）——绝不编造发现；干净的面就明说干净。起草期未确认的推断带 `[假设]` 前缀；终门要求零——要么落定，要么把它写成显式路由。
3. 需求事实取自 `collect` 回执：`counts` 与 `coverage` 照抄，绝不手工重新推导。跨文档机械判定（ID 链、FR 覆盖、跨文件真值）归 diyc——绝不靠肉眼重查。
4. 记录只追加，永不重编号、永不复用；改既有记录就往 `revisions` 追加（date / change / reason）。不需要 `--previous` 轮——本技能从不整篇重写既有文档。
5. 渲染按工作流里的静默旁路句执行——只写命令；不新增浏览器交互点、不报阻塞路径、不等待。
6. 终门（机械）：先写记录级 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-readiness-check/scripts/readiness.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两个实参同激活（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾都等 exit 0。
7. 上游保持原样、不被顶替：`未就绪` 时 finding 的 `route` 点名归属技能（diy-prd / diy-architecture / diy-epics-stories / diy-design）——修是它们的活儿，记录是你的。通过后的下一步主线是 diy-test-design。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
