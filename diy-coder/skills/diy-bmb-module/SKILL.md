---
name: diy-bmb-module
description: 'Plan a batch of skills before building any of them: run the ideation session (batch vision, creative exploration, architecture, per-skill self-contained brief), record it in module-plan.yaml, then validate the batch against the real diy registration surface — the six frontmatter fields of each planned skill SKILL.md. Planning only, never building; zero write surface on the skills it checks. Use when the user requests to "ideate module", "plan a module", "create module", "build a module", or "validate module".'
# ↑ 中文：批次规划器（只规划不造）——构思一批要造的技能（愿景 / 创意探索 / 架构建模 / 逐技能自足 brief），落 module-plan.yaml；再拿计划声明的技能清单去核 diy 真实注册面（SKILL.md frontmatter 六字段：齐备 / 引用闭包 / 双向对称）。零写面：校验绝不写任何被校验技能的文件（frontmatter 亦然）。造物归 diy-bmb-builder。用户说 "ideate module" / "plan a module" / "create module" / "validate module" 时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: module-plan.yaml
---

# diy-bmb-module — 批次规划器（只规划不造）

你是**批次规划器**。输入：一批要造的技能（愿景、边界、依赖关系）。产出：`{output_dir}/module-plan.yaml` 里的一条计划记录——逐技能自足 brief + 构建路线图，`diy-bmb-builder` 按 `build_order` 逐个消费。边界：**只规划不造**，本技能不建任何技能目录、不改任何技能文件。

**为什么需要它**：一批技能要一起想清楚才能少返工——谁先谁后、谁依赖谁、各自解决什么问题；而且「注册面」是散在各自 `SKILL.md` frontmatter 里的，批次层面的一致性（引用可解析、双向对称）没有任何单技能能看见。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 定位议题。用户给的技能清单、目标技能名、或一段「想补什么能力」都算议题。
   - 有议题 → 进第 3 步。没有 → HALT：问一次这批技能要解决什么，等用户回话。
   - 说不出这批技能解决什么问题（只有一串名字）→ 停并问，**零产出**：
     计划的价值在愿景与 brief，不在名录。
3. 硬门：既有愿景、又有可命名的目标技能，才继续；缺 slug（无头侧）→ 由 `new` 拒（一行 `missing_slug` 说明 + 零产出）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-ideate.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；每步输出整块给出，不在步骤中间提问；跨文档的每个事实都是 ID 引用或 project-root 相对 `path:line`，绝不转抄。

1. `steps/01-ideate.md` — 构思会话：愿景与批次身份 → 创意探索 → 架构建模 → 上下文与依赖 → 逐技能自足 brief → 能力评审。
2. `steps/02-plan.md` — 落 `module-plan.yaml`：`new` 铸骨架，再逐字段填；同 slug 就地更新，不新建。
3. `steps/03-validate.md` — 跑 `check`（含 `--previous` 留痕）读三档处置：违规 / warning / 过。
4. `steps/04-finish.md` — `check --final` 终门 + 渲染 + 按 `build_order` 交棒 `diy-bmb-builder` + 摘要。

写回纪律：计划记录在 step 2 建为 `草稿`，`--final` 通过后才改 `已定稿`。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/module-plan.yaml` —— 唯一产物。单记录产物（`sprint.yaml` 等）写 `project.status`；多记录产物（一份文件装 N 条记录）顶层不设 status，定稿态挂记录级 `status: 草稿|已定稿`。

```yaml
project: {name, created, updated}      # created 建文件时设、此后不改；updated 每次写回刷今天
plans:
  - id: MP-001                         # 引擎铸造（最大号 + 1，三位零填充），不重编不重用
    slug: <string>                     # 计划的身份键：同 slug 就地更新，不新建
    title: <string>
    status: 草稿|已定稿                 # `已定稿` 是 `check --final` 的检查对象
    date: YYYY-MM-DD
    vision: <string>                   # 一段：这批技能要解决什么
    skills:                            # 逐技能自足 brief（不靠对话上下文即可交棒）
      - {name: diy-<name>, kind: 工作流|工具, purpose: <string>, brief: <string>, depends_on: [diy-<name>], dropped: false, new: false}
    dependencies: [diy-<name>]         # 批次内依赖关系
    build_order: [diy-<name>]          # 构建路线图（builder 按序消费；本记录的技能名）
    open_questions: [<string>]
revisions: []                          # {date, change, reason} —— 改既有条目时追加
```

`skills[].name` 写**完整技能名（含 `diy-` 前缀）**——与 frontmatter 引用形态、安装目录名同一个空间，零前缀算术（`diy-` 前缀不由 builder 侧另补）。`new: true` 标记「本批新建」（六字段齐备的判定面）、`dropped: true` 标记「计划内移除」（`--previous` 判据），两者默认 `false`。

## 规则

- **只规划不造。** 本技能不建技能目录、不写任何技能的 `SKILL.md`；造物归 `diy-bmb-builder`，本技能按 `build_order` 指路并交棒。
- **零写面。** 校验全程只读——**不写任何被校验技能的文件，frontmatter 亦然**（frontmatter 是 `diy-help` 的读面，写入权不在本技能）；唯一写面是本技能自己的产物 `module-plan.yaml`（经引擎 `new` 落盘）。不扩 `diyc.py check` 的类型集，不写安装面（`install.py` 的分发面归主 agent 收口）。
- **校验对象与三档处置。** 对象 = 计划声明的技能 + 其直接引用的对端；对端在计划内 → 判；已装（套件内既有能力）→ warning；两边都不是 → 违规。
- **`--previous` 用法。** 改既有计划前 `cp {output_dir}/module-plan.yaml {output_dir}/module-plan.yaml.prev`，改完跑 `check --previous {output_dir}/module-plan.yaml.prev`（退出 0 = 技能清单无收缩），再删 `.prev`。收缩须留痕：条目保留并标 `dropped: true`。
- **引用式纪律。** 跨文档信息一律引用 ID 或路径（`path:<relative>`），禁止复制内容。
- 所有代码引用一律 project-root 相对 `path:line`（基准 = `{project-root}`，不随会话 CWD 变化；正斜杠；越界的文件用绝对路径）。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
