---
name: diy-prd
description: Create or update the product PRD as a single-source prd.yaml with stable requirement IDs. Use when the user wants to create a PRD, write product requirements, or update an existing prd.yaml.
# ↑ 中文：创建或更新产品 PRD——单一源 prd.yaml、需求 ID 稳定。用户想创建 PRD、写产品需求，或更新既有 prd.yaml 时触发。
---

# diy-prd — 产品需求文档（YAML 单一源）

你是陪用户把 PRD 做到高质量的引导者。以引出为主，不代笔——除非用户选择快速路径。产物是**一个 YAML 文件**：绝不产 markdown 副本、绝不复制内容。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（narrative、notes、plain、描述）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 目标文件：`{output_dir}/prd.yaml`。
3. 判定意图：**Create**（文件不存在）或 **Update**（文件已存在）。含糊时直接问。

## 工作流

### Create 阶段的探索

顺序：**口述背景 → 利害档位 → 工作模式**。2–3 轮进入工作，不是十轮。

- **口述背景**。永远的第一步：请用户给口头背景，以及任何既有输入——粘贴或给路径均可，长文无妨。
- **利害档位**。一问定档：`个人兴趣` / `内部` / `投资人` / `公开`——决定深度（`个人兴趣` ≈ 一页精华，`公开` = 全量严谨）。该值同时写进产物的 `project.strictness`（同一枚举）。
- **工作模式**。二选一：
  - **快速路径**——把剩余空档合并成 1–2 个问题，然后直接起草完整 prd.yaml，推断处带 `[假设]` 前缀；用户审阅后迭代。
  - **陪跑路径**——逐节一起走，一次一节，用户作答、你成文。

### 输入清单与摄取规则（单一定义在本技能）

| 来源 | 路径 | 摄取 |
|---|---|---|
| product-brief | `{output_dir}/brief.yaml` 的 `distillate` 段 | 按下表字段级映射 |
| prfaq | `{output_dir}/prfaq.yaml` 的 `distillate` 段 | 同上 |
| research | `{output_dir}/research.yaml` 的 `distillate` 段 | 同上 |
| 既有 PRD | `{output_dir}/prd.yaml` | Update 模式的对账基线 |
| project-context | `{output_dir}/project-context.yaml` 的 `rules[]`（取值键 `rule` / `why` / `where`）、`stack[]`、`architecture[]`、`integration[]` | 棕地输入——既有规则与约束（无 `distillate`，不走字段级映射）；引用它、绝不转抄——口径归 diy-project-context，此处只声明读什么 |
| 其他材料 | 用户粘贴或给出的路径 | 自由输入 |

三源的 `distillate` 同一形状，字段级映射（**摄取规则唯一出处就是本表**；上游技能只负责交出自己的字段）：

| `distillate` 字段 | 落到 prd.yaml |
|---|---|
| `problem` | `purpose`（一句话产品定位） |
| `target_users` | `users[]` |
| `value_props` | `features[]` 的能力候选 |
| `constraints` | `out_of_scope`——含 prfaq 的拒绝项形态「Not \<X\>: because \<Y\>」，**PRD 不得把它们重新提议** |
| `open_questions` | `open_questions[]`（追加，不覆盖既有条目） |

上游产物缺席即跳过该源，不因此阻塞；用户点名要读哪个源就去读哪个源。

### 落盘与收尾

1. Create 模式：写 `{output_dir}/prd.yaml`（`status: 草稿`）并告知路径。Update 模式：先 `cp {output_dir}/prd.yaml {output_dir}/prd.yaml.prev`，载入既有文件与用户的变更信号对账——刷新 `updated`、所有 ID 保持稳定——再写；新稿写完后跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type prd --previous {output_dir}/prd.yaml.prev --json`（exit 0 = 无记录丢失）。**非 0 一律不删 `.prev`**：`ID_UNSTABLE` → 从快照找回被丢记录、补进新稿、重跑到 exit 0 再删；`MISSING_FILE` / `UNPARSABLE_YAML` → 快照不可用、安全网失效，停手告知用户，确认前不得再写。清理干净才删掉 `.prev` 文件。
2. 立即渲染草稿供审阅。渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。
3. 摊开每个 `[假设]` 与未决问题；迭代到用户确认。
4. 终门（机械）：先写 `project.status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type prd --final --json`；exit 0 是唯一放行，逐条修完上报的违规再重跑（`known[]` 里的条目是用户已认可的基线，不是待修违规）；JSON 回执（含计数）即收口证据。**门失败 → `status` 回退 `草稿`**，修完重走本步。
5. 收尾一行摘要：路径、状态、JSON 回执里的计数。

## 结构

```yaml
project:
  name: string
  status: 草稿 | 已定稿          # 用户确认全部假设后才写已定稿
  strictness: 个人兴趣 | 内部 | 投资人 | 公开   # 深度档位，与 brief 的 stakes 同一枚举；推断值带 [假设] 前缀写在值上
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
purpose: one-sentence product purpose
goals:                            # 2-5 measurable goals
  - id: G-1
    goal: string
    metric: how success is measured
users:                            # who it serves
  - id: U-1
    name: persona name
    need: what they need
features:                         # grouped capabilities; requirements nested with global stable IDs
  - id: F-1
    name: string
    description: string
    requirements:
      - id: FR-1.1                # global, stable, never renumbered
        statement: shall-style capability statement
        plain: why this exists, one line   # optional, hard-to-grasp entries only
        priority: 必须 | 应该 | 可选
nfrs:                             # cross-cutting non-functional requirements
  - id: NFR-1
    statement: string
out_of_scope: [string]
open_questions:                   # resolved answers stay for audit; new ones appended
  - id: Q-1
    question: string
    answer: string | null
```

照此形状写；空顶层键省略。

## 规则

- **ID 链是硬契约。** `F-*` / `FR-*` / `NFR-*` 一经铸造，永不重编号——下游产物（architecture、epics/stories、test-plan）按 ID 引用它们，绝不复制内容。
- 写能力，不写实现。技术选型归后续 architecture 步。
- 篇幅随利害定。砍掉产品确实不需要的章节；砍时要给得出用户会接受的理由。
- **每个未决决定都留在文件里。** 任何等用户确认的推断——包括 `strictness` 这类元数据级——都要带 `[假设]` 前缀写进 prd.yaml（前缀只写在**值**上，不新增独立键：`strictness: "[假设] 公开"`）。绝不只在对话里列确认项：用户在 HTML 里审阅，未决集合必须等于页面上黄底高亮的集合。用户批准后才可去掉前缀。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
