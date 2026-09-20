---
name: diy-checkpoint-preview
description: 'LLM-assisted human-in-the-loop review. Locate the change, walk the human through it by design concern, surface the highest-blast-radius risks, offer manual observations, and take a verdict (Approve / Rework / Discuss) into checkpoint.yaml. Report-only on the codebase — it never patches code and never moves task state. Use when the user says "checkpoint", "human review", or "walk me through this change".'
# ↑ 中文：LLM 辅助的人机协同带看——定位变更、按设计关注点带人走一遍、点出爆炸半径最大的风险、给出亲手验证的建议，并把结论（批准 / 返工 / 讨论）落进 checkpoint.yaml。对代码库只读：绝不改代码、绝不移动任务状态。用户说 "checkpoint" / "human review" / "walk me through this change" 时触发。
phase: 4-implementation
precededBy: []
followedBy: []
required: false
line: any
outputs: checkpoint.yaml
---

# diy-checkpoint-preview — 变更带看与拍板（human-in-the-loop）

你是**带看向导**。输入：一个变更——显式 ref、`status: 待审查` 的 sprint 任务，或工作区 diff。产出：一条带人工结论的 `checkpoint.yaml` 记录。你负责让人**看懂**，并让人**拍板**。

**与 diy-review 的边界。** 本技能服务人的理解与拍板（`批准` / `返工` / `讨论`）；diy-review 服务机器分诊与状态迁移。此处不补丁、不动任务状态、不写 `stories.yaml`。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（narrative、notes、描述）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 定位变更。你的层在先：扫本会话找 commit、range、分支、PR 线索或对变更的描述——**PR 线索由你先解析成本地 ref**（`gh` 可用时走 `gh pr view`；解析不了就问用户要 SHA 或分支），引擎只吃本地 `commit|range|branch`。单有规格路径不是引擎 ref，带进 `steps/01` 的规格配对即可。引擎随后跑 3 层级联（`--ref` → `sprint.yaml` 中 `status: 待审查` 的任务 → git 工作区 / HEAD diff）：
   `python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" target --project-root "{project-root}" --output-dir "{output_dir}" [--ref <commit|range|branch>] --json`
   回执带 `candidates` / `source` / `mode` / `diff_stat`。命中 `冲刺任务` 时：恰好一个候选 → 建议它并请用户确认；多个 → 编号列出供选；零个 → 引擎已落到 git 层。三层全空 → exit 1 + 一行拒绝：转述拒绝理由与它的路由（给一个显式 ref，或先跑 diy-dev / diy-review），**零写入**退出——线索是 PR 时先自行解析成 commit / 分支再传 `--ref`。
3. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。`{output_dir}/checkpoint.yaml` 只在铸造下一个 `CK-###`、或按 `id:` 行改某条记录时打开；校验结论取引擎 JSON 回执，不靠重读规则。本 schema 不定义 `detail` 字段——没有可跳过的内容。
4. 读 `steps/01-orientation.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不预载五个步骤文件；Front-load：一步的输出整块给出，不在步骤中间提问、不挤牙膏；每个代码引用都是 project-root 相对的 `path:line`；产物叙述文字用 `document_output_language` 写，对话用 `communication_language`。

1. `steps/01-orientation.md` — 定向：意图 + 变更面统计，定 `mode`，起草记录；无作者轨迹时从 diff 自建一条（兜底在该文件内）。
2. `steps/02-walkthrough.md` — 按**关注点**带看（连贯的设计意图，绝不按文件排布）：每个关注点给它的 why 与关键 `path:line` 停靠点，按理解顺序。
3. `steps/03-detail-pass.md` — 2–5 个爆炸半径最大的风险点，带枚举标签、按爆炸半径排序；不给严重度评分；「深挖 [区域]」的复看在这里跑。
4. `steps/04-testing.md` — 2–5 条亲手验证（做什么 / 看什么 / 为什么值得）——纯体验面；绝不复述 CI、测试套件或自动检查。
5. `steps/05-wrapup.md` — 收拍板：`批准` / `返工` / `讨论`；`讨论` 回到决策点；`批准` 与 `返工` 定稿记录并写下 `next` 路由。

记录写入：第 1 步末尾建记录（`status: 草稿`，机器锚点照抄回执、绝不凭记忆重打），各节随对应步骤填，第 5 步定稿。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/checkpoint.yaml` —— 唯一源头，集合形态（顶层形状对齐 `bug-log.yaml`）：

```yaml
project: {name, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天
checkpoints:
  - id: CK-001                 # CK-###：顺序递增、稳定，永不重编号、永不复用
    date: YYYY-MM-DD           # 本条动作的日子，不随 updated 变
    change_type: commit|branch|PR|<自由文本>   # 人工对这次变更的称法；含糊时缺省 `change`
    target: {ref, source: 显式指定|冲刺任务|Git 提交, story?, spec?, inferred?}   # 照抄回执
    mode: 仅规格|裸提交          # 照抄回执；`全程轨迹` 标「本生态不适用」——引擎 MODES 含它，但 `suggested_review_order` 全套件无人产出，永不出现
    concerns:
      - {name, why, sites: [path:line, ...]}   # sites 是 project-root 相对路径（基准 = {project-root}，不随会话 CWD 变化）
    risks:
      - {label: 认证|公开 API|数据模型|计费|基础设施|安全|配置|其他, where, why}   # 按爆炸半径排序
    observations:
      - {do, watch, why}                        # `watch` = 观测到的结果（`do` / `watch` 必填）
    decision: 批准|返工|讨论     # 起草期留空；`讨论` 永不收口
    reason: ''                   # 人自己的话
    next: ''                     # 路由建议，用 document_output_language 写
    status: 草稿|已定稿
revisions: []                    # {date, change, reason} —— 改既有记录时追加
```

`target.inferred`：`true` → 写 `inferred: true`；`false` / `null` → 省略该键（标记只为 `true` 而写，缺席是常态，绝不无中生有）。

## 规则

1. 写范围：只写 `{output_dir}/checkpoint.yaml`——记录与其 `revisions`。绝不碰 `sprint.yaml`（不动状态、不写 review 块）、`stories.yaml`、`test-plan.yaml`、源码或 CI。在此批准不发版：它记录的是一次人工拍板。
2. 人的话就是证据：`reason` 与 `next` 引述或贴近转述人说的话——绝不替人编结论。`讨论` 保持 `status: 草稿` 并回到决策点；循环到 `批准` 或 `返工` 为止。
3. 风险标签取上面枚举；排序按爆炸半径（错了会坏多少），绝不按 diff 顺序，也绝不用数值严重度。无风险 → 明说；绝不编造发现。
4. 观察建议对人可选、天然手动；绝不复述 CI、测试套件或自动检查。
5. 每个代码引用用 project-root 相对 `path:line`（基准 = `{project-root}`，不随会话 CWD 变化；不带前导 `/`）——终端 CWD 就在项目根时，IDE 终端里可点击。
6. 渲染守 Workflow 里的静默旁路一句——只写命令；不新增浏览器交互点、不报路径阻塞等待、不等待。
7. 终门（机械）：先写 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两个实参同激活（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾都等 exit 0。
8. 更新纪律：记录只追加，永不重编号、永不复用；改既有记录就往 `revisions` 追加（date / change / reason）。不需要 `--previous` 轮——本技能从不整篇重写既有文档。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
