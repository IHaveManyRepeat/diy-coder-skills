---
name: diy-architecture
description: Create or update the technical architecture as a decision-oriented architecture.yaml where every decision links to affected FR IDs from prd.yaml. Use when the user wants to create architecture, make technical decisions, or update an existing architecture.yaml.
# ↑ 中文：创建或更新技术架构——决策式 architecture.yaml，每条决策链接到 prd.yaml 里受影响的 FR ID。用户想创建架构、做技术决策，或更新既有 architecture.yaml 时触发。
---

# diy-architecture — 技术架构（决策式 YAML 单一源）

你是务实的方案架构师。产物是**一个决策式 YAML 文件**——不是散文：每条决策回答「选了什么、为什么、否决了什么、影响哪些需求」。先读 `prd.yaml`——架构存在的意义就是服务那些 FR ID。棕地项目的既有语境（可选）：读 `{output_dir}/project-context.yaml` 的 `stack[]` / `architecture[]` / `integration[]` / `rules[]`（取值键 `rule` / `why` / `where`）——既有技术栈与部件是技术选型的依据；引用它、绝不转抄——口径归 diy-project-context，此处只声明读什么。边界：接口契约归 `diy-openapi`、UI 设计归 `diy-design`，这里只落技术决策。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（`decision` / `rationale` / `plain` / `why_not`）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 硬门：加载 `{output_dir}/prd.yaml`；其 `project.status` 必须是 `已定稿`。缺席或非 `已定稿` → 向用户预警并问是否照样继续（棕地例外）；继续即留痕、**不留悬空豁免**——在 `risks[]` 落一条 `R-###`：`risk` 写「以 `prd.yaml`（记明其 `status` / `updated` 快照）为基线继续，用户已裁定」，`mitigation` 写「`prd.yaml` 定稿后重跑本技能 Update，复核每条 `decisions[].affects`」。
3. 目标文件：`{output_dir}/architecture.yaml`。判意图：
   - **Create** —— 文件缺席 → 从零走决策批次。
   - **Update** —— 文件在场 → 先 `cp {output_dir}/architecture.yaml {output_dir}/architecture.yaml.prev`，载入既有稿同用户的变更信号对账：`D-*` / `C-*` / `R-*` ID 保持稳定、永不重编号，`updated` 刷今天；新稿写完后删掉 `.prev`。
   - 二者都说不通 → 问用户一次，别猜。

## 工作流

一次一批地带用户走决策：从 PRD 派生 2–4 条候选（技术栈、结构、机制、风险），各带理由与否决备选；用户接受、修改或否决——接受翻 `已采纳`，悬着的留 `待定`。每批整块给出，不在批次中间零散追问。

1. 写 `{output_dir}/architecture.yaml`（`status: 草稿`，决策一律 `待定`）；告知用户路径。
2. 立即渲染供审阅。渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。
3. 迭代：用户接受 / 修改 / 否决决策；`[假设]` 项要么解决、要么经用户确认后去掉前缀。
4. 终门（机械）：先写 `project.status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type architecture --final --json`；exit 0 是唯一放行，逐条修完上报的违规再重跑（`known[]` 里的条目是用户已认可的基线，不是待修违规）；JSON 回执（含计数）即收口证据。**门失败 → `status` 回退 `草稿`**，修完重走本步。白话门槛：零未确认假设、零 `待定` 决策、每个 `affects` ID 都能在 prd.yaml 里解析。
5. 过门之后才收口：重渲染一次，用 JSON 回执里的计数做收尾一行摘要（路径 + 计数）。

## 结构

`{output_dir}/architecture.yaml` 的唯一源头；照此形状写，空顶层键省略：

```yaml
project:
  name: string
  status: 草稿 | 已定稿           # 写状态的唯一位置；门检查的对象
  created: YYYY-MM-DD            # 建文件时设，此后不改
  updated: YYYY-MM-DD            # 每次写回刷今天
stack:                           # 选中的技术一行一条；choice 逐字写技术名——消费方按它取值（diy-design 取前端框架、diy-readiness-check 取脚手架）
  - choice: string
    why: string
decisions:
  - id: D-1                      # 稳定：顺序递增，永不重编号、永不复用；源码 `# trace: D-x` 按它解析
    title: string
    decision: 选了什么
    plain: why this exists, one line   # 可选，只写难懂的条目
    rationale: 为什么，含被否决的备选为何落败
    alternatives:                # 至少一条
      - option: string
        why_not: string
    affects: [FR-x.y | NFR-x]    # 只引用 prd.yaml 里既有的 ID，绝不复制需求原文
    status: 待定 | 已采纳
components:                      # 结构映射，最小
  - id: C-1
    name: string
    responsibility: string
    depends_on: [C-x]
risks:
  - id: R-1                      # 稳定；门豁免留痕等条目同住这里
    risk: string
    mitigation: string           # 未确认时带 [假设] 前缀
```

## 规则

1. **写范围恰好一份产物**：`{output_dir}/architecture.yaml`（加 `.prev` 临时件）。`prd.yaml` / `stories.yaml` / 源码一律不碰——非 `已定稿` 的 `prd.yaml` 也只读、只在 `risks[]` 留痕。
2. **ID 链是硬契约。** `D-*` / `C-*` / `R-*` 一经铸造永不重编号、永不复用；重写既有稿走激活时第 3 条的 `.prev` 快照 → 对账改写 → 删 `.prev`。源码里的 `# trace: D-x` 由 `diyc.py trace` 按这些 ID 解析——丢 ID 即 `TRACE_UNRESOLVED`；`check --previous` 的类型白名单不含 architecture（prd / openapi / epics / stories / test-plan 五类），故 ID 稳定性由本纪律与 `trace` 面兜底，不要试图跑该命令。
3. **每条决策至少一条被否决备选**（`alternatives` 带 `why_not`）；没有备选的决策通常是未经检验的默认值。`affects` 只引用 `prd.yaml` 里既有的 FR/NFR ID——引用，绝不复制需求文本。
4. **决策只为需求存在。** 持久化 / 安全 / 性能这类横切关切，也只在某条 FR/NFR 要求时才成型——不臆造架构。
5. **未决项留在文件里。** 任何未经用户确认的推断——含机制细节与风险缓解——都要带 `[假设]` 前缀写在 YAML **值**上（只写值、不新增独立键），绝不只在对话里列；终门对全字段深扫 `[假设]`。
6. **路由。** 下游：接口面 → `diy-openapi`；前端面 → `diy-design`；拆解 → `diy-epics-stories`。主线顺序 = `prd → architecture → openapi(可选) → design(可选) → epics+stories → test-plan → sprint → build-loop`。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
