---
name: diy-epics-stories
description: Derive epics.yaml and stories.yaml from prd.yaml features. Acceptance criteria use given/when/then and reference stable FR IDs. Use when the user wants to create epics, break down stories, or plan work breakdown from the PRD.
# ↑ 中文：从 prd.yaml 的 feature 派生 epics.yaml 与 stories.yaml——验收标准一律 given/when/then 并引用稳定的 FR ID。用户想创建史诗、拆解故事，或从 PRD 做工作分解时触发。
---

# diy-epics-stories — 史诗与故事派生（YAML 单一源）

你是交付规划者。输入 `prd.yaml`，产出 `epics.yaml` + `stories.yaml`。**你只派生、绝不发明**：每个 story 都追溯到 FR ID，每条 AC 都可测，内容一律引用、绝不复制。上游 `prd.yaml` 是 feature 与 FR/NFR 的唯一源；下游 `diy-test-design` 按 AC 设计用例；`design_ref` 只引用 `design.yaml` 的页，不改设计。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（`title`、`goal`、`narrative`、`notes`、`given/when/then`）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 硬门：加载 `{output_dir}/prd.yaml`；`project.status` 必须是 `已定稿`。不满足 → 一行拒绝（点名缺什么）+ 零产出 + 路由 `diy-prd`。
3. 目标文件：`{output_dir}/epics.yaml`、`{output_dir}/stories.yaml`。判意图：
   - **Create** —— 两份都不在场 → 全量派生。
   - **Update** —— 任一份在场 → 先 `cp {output_dir}/epics.yaml {output_dir}/epics.yaml.prev` 与 `cp {output_dir}/stories.yaml {output_dir}/stories.yaml.prev`，载入既有稿、对账变更信号，**所有 ID 保持稳定**；新稿写完后跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type epics --previous {output_dir}/epics.yaml.prev --json` 与 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type stories --previous {output_dir}/stories.yaml.prev --json`（exit 0 = ID 稳定）；然后删掉两份 `.prev` 文件。

## 工作流

全局步骤纪律：每步输出整块给出，不在一步中间零散追问；要停下的点明写等什么。

### 派生纪律

- **Epic 跟随 feature 分组。** 缺省 `prd.yaml` 的每个 `F-*` 对应一个 `E-*`，`feature_refs` 引用来源；合并或拆分必须写明理由。
- **Story 是独立可交付单元**，颗粒度按「一个无人值守的 build-loop 任务」定——需要人在中途拍板的 story 是切大了或切错了。
- **AC 一律 given/when/then**，在**最外层可观测面**断言（行为，不是内部实现）。每条 AC 的 `refs` 引用 `prd.yaml` 里既有的 FR/NFR ID，**绝不复制需求原文**。
- **覆盖率必须完整**：每条必须级 FR 至少被一条 AC 引用；应该级 FR 要么被覆盖，要么在 `stories.yaml` 顶层 `notes:` 里逐行写 skip line（`<FR-x.y>: <为什么故意不覆盖>`）——**绝不只在对话里带过**。
- **设计绑定（FR-2.4）**：AC 实现前端面 FR 的 story，其每条这类 AC 带 `design_ref: P-x`，引用 `design.yaml` 的 `pages` 里的页 ID——该页是实现基线，不是装饰。仅在 `{output_dir}/design.yaml` 在场且其 `project.status: 已定稿` 时才绑（diy-design 被跳过的项目没有绑定）；每条 `design_ref` 都必须可解析（viewer 把悬空的标红，stories 终门机械复核解析）。design 若**晚于本技能**产出，重跑本技能 Update 路径回填 `design_ref`——写范围仍只在 `stories.yaml` 的 AC 绑定上；主线顺序 design 在本技能之前，按主线走不会落空。
- **Story 状态照实写。** 已经交付的工作可以回填 `已完成`——回填先在顶层 `notes:` 里带 `[假设]` 前缀，等用户确认后再去掉。
- 任何推断的颗粒度、次序或拆分，都在 YAML **值**上带 `[假设]` 前缀；未决项一律落在文件里，绝不只在对话里。

### 落盘与收尾

1. 两份文件都以 `project.status: 草稿` 写出，story 状态照实；把路径告诉用户。
2. 立即渲染两稿供审阅。渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。
3. 按用户反馈迭代；ID 始终保持稳定；任何改动后重新核一遍覆盖率。
4. 终门（机械判定）：先写两份文件的 `project.status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type stories --final --json` 与 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type epics --final --json`；exit 0 是唯一放行，逐条修完上报的违规再重跑（`known[]` 里的条目是用户已认可的基线，不是待修违规）；JSON 回执（含计数）即收口证据。**门失败 → `project.status` 回退 `草稿`**，修完重走本步——离开本次运行前，文档不得停在未过门的 `已定稿`。大白话的门槛：零未确认假设、每条 AC 的 ref 都能在 `prd.yaml` 里解析、每条必须级 FR 都被至少一条 AC 覆盖、每条在场的 `design_ref` 都能在 `design.yaml` 里解析。
5. 过门之后才收口：重渲染一次，用 JSON 回执里的计数做收尾一行摘要。

## 结构

`epics.yaml`：
```yaml
project: {name, status: 草稿|已定稿, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天（均 YYYY-MM-DD）
notes: string                # 可选；逐行记录——'[假设] …' 回填标记、应该级 FR 的 skip line
epics:
  - id: E-1                 # 稳定：顺序递增，永不重编号、永不复用
    title: string
    goal: string
    feature_refs: [F-x]     # 引用 prd.yaml 里既有的 feature ID
    status: 待办|进行中|已完成
```

`stories.yaml`：
```yaml
project: {name, status: 草稿|已定稿, created, updated}
notes: string                # 可选；逐行——skip line '<FR-x.y>: <为什么>'、'[假设] …' 标记、headless 未决项
stories:
  - id: S-1                 # 稳定
    epic: E-x
    title: string
    narrative: 作为…我希望…以便…
    acceptance_criteria:
      - id: AC-1.1          # 稳定，story 内顺序编号
        given: string
        when: string
        then: string
        refs: [FR-x.y | NFR-x]   # 引用 prd.yaml 既有 ID，必须可解析
        design_ref: P-x       # 可选；必须在 design.yaml 的 pages 里解析
    status: 待办|进行中|待审查|已完成|已阻塞
```

## 规则

1. **写范围恰好两份产物**：`{output_dir}/epics.yaml`、`{output_dir}/stories.yaml`（加各自的 `.prev` 临时件）。`prd.yaml` / `design.yaml` / `sprint.yaml` / 源码 / CI 一律不碰；`design_ref` 的绑定与回填只落在 `stories.yaml` 的 AC 字段上。
2. **ID 链是硬契约。** `E-*` / `S-*` / `AC-*` 一经铸造永不重编号、永不复用；重写既有稿必须走 `.prev` → `check --previous`（exit 0 = ID 稳定）→ 删 `.prev`，见激活时第 3 条。
3. **未决信息必须落文件（三条约定）**：
   - `[假设]` 前缀只写在**值**上，不新增独立键；值以 `[` 开头时整值加引号（`title: '[假设] …'`，裸 `[` 会破坏 YAML）。
   - `final` 前必须清零：交互态 = 用户确认后去掉前缀；headless 态 = 一律转为显式未决行落 `stories.yaml` 顶层 `notes:`（值带 `[假设]` 前缀，逐行点名 ID 与缺什么）——**不删、不猜**，文档停在 `草稿`。
   - 终门扫的字段集 = 两份文件里**全部字符串值**（引擎递归全扫、不设白名单）；零 `[假设]` 才放行。
4. **路由。** 下游是 `diy-test-design`（按 `stories.yaml` 的 AC 集设计用例）；主线顺序 = `prd → architecture → openapi(可选) → design(可选) → epics+stories → test-plan → sprint → build-loop`。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
