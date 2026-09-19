---
name: diy-sprint
description: Generate sprint.yaml task state machine from stories.yaml and test-plan.yaml. One task per story (exact set equality), five states (待办/进行中/待审查/已完成/已阻塞), TDD gate marks test-less tasks blocked with reason. Use when the user wants a sprint queue to drive the build loop.
# ↑ 中文：从 stories.yaml 与 test-plan.yaml 生成 sprint.yaml 任务状态机——一故事一任务（集合精确相等）、五态（待办/进行中/待审查/已完成/已阻塞）；TDD 门把缺用例的任务标为已阻塞并写明理由。用户想要一条驱动 build loop 的冲刺队列时触发。
---

# diy-sprint — 任务状态机生成（YAML 单一源）

你是冲刺规划者。输入 `stories.yaml` + `test-plan.yaml`，产出 `sprint.yaml`。你把故事投影成可执行的任务队列——绝不发明任务、绝不丢故事、绝不让缺用例的故事无阻入队；推进由 diy-dev / diy-review 在 diy-build-loop 的循环里完成，本技能只写初始状态与对账结果。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（`note`、`blocked_reason`）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 硬门（按序）：`{output_dir}/stories.yaml` 的 `project.status: 已定稿`；`{output_dir}/test-plan.yaml` 的 `project.status: 已定稿`。不满足 → 一行说明缺什么并停下，路由回属主技能（diy-epics-stories / diy-test-design）；零产出。
3. 目标文件：`{output_dir}/sprint.yaml`。判意图：
   - **Create** —— 文件缺席 → 从工作流第 1 步走，任务集由 `reconcile --apply` 落盘。
   - **Update** —— 文件在场 → 按工作流第 2 步对账，进度照保。
   - 二者都说不通 → 问用户一次，别猜。

## 工作流

全局步骤纪律：一步的输出整块给出，不在步骤中间零散追问；要停下的点明写等什么。

### 任务纪律

- **一故事一任务，集合精确相等。** 任务 `story` 引用的集合 == stories.yaml 里 story ID 的集合。
- **绝不新造 ID。** 任务由 `story` 引用标识；ID 链是 story → test case，本技能只加引用，绝不复制上游内容。
- **TDD 门是默认姿态。** `待办` / `进行中` 的故事，只要有一个 AC 没有用例即「缺覆盖」——除非该缺口条目裁为 `已豁免` 或 `接受缺口`。缺覆盖产出 `已阻塞` 任务，`blocked_reason` 点名缺什么（如 `AC-x.y 无用例（decision: 待办）`）。阻塞是信息，不是失败——照实上报，绝不粉饰。（门由 `reconcile` 机械计算、`check --type sprint` 复核；本句只是那条共享规则的人读表述。）
- **已完成的故事落成已完成。** 故事 `status: 已完成` → 任务 `status: 已完成`，`note` 引述先前的确认（日期 + 裁断）。其 `已豁免` / `接受缺口` 的 AC 不触 TDD 门。
- **Update 保进度（机制：`reconcile`）。** 重跑时对账器保留既有任务的 `status`——`待审查` / `已完成` 是审计产物，一律不动；为新增故事加任务、删掉故事已消失的任务；只对 `待办` / `进行中` / **`已阻塞`** 重算门与 `test_refs`——障碍（缺覆盖）解除后 `已阻塞` **自动**归位 `待办` 并清掉 `blocked_reason`，不需要人工改文件；最后刷 `updated`。
- 任何推断的豁免或排序判断，都在 YAML **值**上带 `[假设]` 前缀；未决项一律落在文件里，绝不只在对话里。

### 状态机

```
待办 → 进行中 → 待审查 → 已完成
              ↑           |
              +-----------+   （待审查 打回）
任意态 → 已阻塞（障碍：用例缺失 / 依赖故障） → 待办（障碍解除后重算）
```

状态归属：diy-dev 走 待办→进行中→待审查；diy-review 走 待审查→已完成（或打回）；diy-build-loop 用 runner 驱动整个循环。本技能只写初始状态与对账结果。

`augment` 是正交裁断字段，由 diy-augment 在 `已完成` 之后写，定义以 diy-augment 为唯一出处（此处只引用）：`通过` = 验证完成；`失败` = 缺陷待用户裁断；`已跳过` = **未验证**（覆盖率工具链缺席或未获许可，零执行）——既非通过也非失败，不得读成「已验证完成」，`--augment-only` 不会自动重跑它，只有用户裁断或重跑补测才覆盖；缺席 = 尚未补测。它永不改变五态状态机。

唯一被许可的跨状态机迁移是重开 `已完成` → `进行中`。**两个入口、一条不变量**：批量裁断收集到的失败走 `python "{project-root}/.claude/skills/diy-tools/scripts/runner.py" --project-root "{project-root}" --reopen-failed`（由人手动执行）；单条证伪命中走 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to 进行中 --json`。两者都必须清掉旧 verdict（引擎在 `已完成 → 进行中` 这条边上 `pop("augment")`，与 `runner.py --reopen-failed` 同语义）；重开后修复由常规循环驱动，重新补测覆盖结论。

### 落盘与收尾

1. 机械交叉核对：`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type sprint --json` 核对 ID 链（每个 `story` 在 stories.yaml 可解析；每条 `test_refs` 在 test-plan.yaml 可解析）。**Create 路径**：sprint.yaml 尚不存在时回执是 `MISSING_FILE`（exit 1）——那是「暂无可核对面」，不是坏引用，放行进入第 2 步；`reconcile --apply` 落盘后**再跑同一命令**，此时的非 0 才是真坏链（修好再迭代）。Update 路径：非 0 即坏引用，先修再出稿。
2. 用对账器建/改任务集：先跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" reconcile --json`（干跑：打印 `add` / `remove` / `changed` 动作计划，exit 0 = 可落盘），审阅计划，再跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" reconcile --apply --json` 原子落盘。门、`test_refs`、增删与重算全由脚本机械完成（任务纪律就是它的白话说明）。sprint.yaml 若是新建，脚本已写入 `project.status: 草稿`；把路径告诉用户。
3. 立即渲染供审阅。渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。
4. 按用户反馈迭代；任务顺序跟随故事顺序，除非用户重排。
5. 终门（机械）：**先写 `project.status: 已定稿`**——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type sprint --final --json`；exit 0 是唯一放行，逐条修完上报的违规再重跑（`known[]` 里的条目是用户已认可的基线，不是待修违规）；JSON 回执（含计数）即收口证据。**门失败 → `project.status` 回退 `草稿`**，修完重走本步。白话义务：零 `[假设]`；任务 `story` 集 == stories.yaml 的 story ID 集（双向）；每个 `已阻塞` 任务都有 `blocked_reason`；`待办` 任务的 `test_refs` 为空，**只有**在该 story 于 test-plan.yaml 中确有 TC 时才算违规（引用集未同步）——AC 缺口全部裁 `已豁免` / `接受缺口` 的故事没有 TC，`test_refs: []` 是合法记录。
6. 收口：重渲染一次，用 JSON 回执里的计数做收尾一行摘要（按状态的任务数 / 阻塞理由 / TDD 门结果）。

## 结构

`{output_dir}/sprint.yaml` 的唯一源头：
```yaml
project:
  name: string
  status: 草稿 | 已定稿            # 用户确认全部假设后才写已定稿
  created: YYYY-MM-DD             # 建文件时设、此后不改
  updated: YYYY-MM-DD             # 每次写回刷今天
tasks:
  - story: S-1                    # stories.yaml 里既有的 story ID（必填、唯一）
    status: 待办|进行中|待审查|已完成|已阻塞
    test_refs: [TC-1.1.1]         # 覆盖该故事 AC 的用例 ID（来自 test-plan.yaml）；零 TC 的故事留 []
    augment: 通过|失败|已跳过       # diy-augment 的编码后裁断（可选；缺席 = 尚未补测；定义见 diy-augment）
    blocked_reason: string        # 当且仅当 status: 已阻塞 时必填
    note: string                  # 回填引述、假设、排序说明
```

## 规则

1. **写范围恰好一份产物**：`{output_dir}/sprint.yaml`（`reconcile` 的原子写）。`stories.yaml` / `test-plan.yaml` / 源码一律不碰；任务只引用上游 ID，绝不复制内容。
2. **状态写入面窄。** 本技能只写初始状态与对账结果；`待审查→已完成` 归 diy-review，重开 `已完成→进行中` 是用户裁断（两个入口见上）——本技能永不自行重开，永不改 `已完成` 任务的 `evidence` / `augment` 审计痕迹。
3. **未决信息必须落文件。** 推断的豁免或排序判断在 YAML **值**上带 `[假设]` 前缀（值以 `[` 开头时整值加引号）；`final` 前必须清零；未决集合 = viewer 页面上黄底高亮的集合，绝不只列在对话里。
4. **路由。** 过门后交给 `diy-build-loop`（用 runner 驱动 待办→…→已完成 的循环）；`已阻塞` 任务指明人工解除路径；缺用例需补设计时路由 `diy-test-design`。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
