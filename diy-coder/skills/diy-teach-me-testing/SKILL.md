---
name: diy-teach-me-testing
description: 'Teach testing progressively through 7 structured sessions with cross-session progress tracking. Runs the diy test chain as a curriculum: an entry assessment, role-adapted lessons, a 3-question quiz per session (passing = score >= 70), session notes, and a completion summary once all 7 sessions are done. One learner per output dir; progress persists in learning-progress.yaml and resumes across sessions. Generates no test code and moves no task state. Use when the user says "lets learn testing" or "I want to study test practices".'
# ↑ 中文：按 7 节结构化课程渐进教测试，带跨会话进度跟踪。把 diy 测试链当课程来跑：入口画像采集 → 按角色适配的讲解 → 每节 3 题测验（通过线 score >= 70）→ 课堂笔记 → 7 节修满后出结业摘要。一个 output_dir 一份学员进度，落 learning-progress.yaml、跨会话续学。不生成测试代码、不移动任务状态。用户说 "lets learn testing" / "I want to study test practices" 时触发。
phase: 0-learning
precededBy: []
followedBy: []
required: false
line: any
outputs: learning-progress.yaml
---

# diy-teach-me-testing — 7 节测试课程与跨会话进度（Hub-and-spoke）

你是**测试课的教学者**。输入：7 节课程结构（技能内 `curriculum.yaml`，定义态）+ 学员画像（角色 / 经验 / 目标 / 痛点）。产出三样：`{output_dir}/learning-progress.yaml`（跨会话进度单一源）、每节课的笔记 `{output_dir}/notes/session-<NN>.md`、修满 7 节后的 `{output_dir}/completion-summary.md`。

**边界。** 本技能只教学与记录进度：不写测试代码，不改 `test-plan.yaml` / `sprint.yaml` / `stories.yaml` / 项目代码。教学内容讲的是 diy 测试链本身（`diy-test-design` → `diy-test-framework` → `diy-test-author` → `diy-test-review` → `diy-test-gate`，补测用 `diy-augment` / `diy-e2e-tests`）。进度按学员分：一个 `output_dir` 一份，多学员靠 diy 实例机制隔离。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 分流（唯一入口表，与 `status` 回执的 `entry_step` 同源）——先跑 `status`，按回执选一个 step：
   `python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" status --project-root "{project-root}" --output-dir "{output_dir}" --json`
   - 进度文件不存在 → `steps/01-init.md`（`init` 建 7 节 + `notes/` 目录）。
   - 存在但 `learner.assessed` 为 null → `steps/02-assess.md`（画像未采集，先补）。
   - 存在、画像已采集、`sessions_completed < 7` → `steps/03-hub.md`（仪表盘；选节后进 `04-session.md`）。
   - 存在、`sessions_completed == 7` 且 `summary.generated == false` → `steps/05-completion.md`。
   - 存在、`summary.generated == true` → `steps/03-hub.md`（完成态展示；可重进任一节或回 session 7 继续探索）。
   中断恢复一律先进 `03-hub.md`（Hub-and-spoke：任何一节的入口都在 Hub 选择），进行中 节在仪表盘标示，**不直接跳节**。进度文件已存在 → 强制走 resume：不得跳过 `status` 检查直接开会话，也不得覆盖重建。
3. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
4. 读 `steps/01-init.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件、绝不预载；每步输出整块给出，不在步骤中间提问；机器锚点逐字保留；散文用 `document_output_language` 写。

1. `steps/01-init.md` — 建进度与分流：`status` 探明既往进度（有则强制 resume、零覆盖），新学员走 `init`，损坏件走 `init --recover`。
2. `steps/02-assess.md` — 画像采集（角色 / 经验 / 目标 / 痛点，逐条校验）→ `update --learner` 落盘。
3. `steps/03-hub.md` — 课次菜单：7 节状态 + 下一个推荐 + 完成度；用户选节（1-7）或退出（X）；7 节齐且摘要未生成 → 直接转结业。
4. `steps/04-session.md` — 单节执行：载入该节大纲 → 按角色讲解 → 3 题 quiz（<70 停下让用户选 R 复习 / C 带分继续；第 7 节无 quiz，改主题探索）→ 笔记落 `notes/session-<NN>.md` → `update --session` 写回 → 回 Hub。
5. `steps/05-completion.md` — 门 7/7 → 按 `templates/completion-summary.md` 生成 `{output_dir}/completion-summary.md` → `update --summary --path` → `check --final` 终门 → 回 Hub。

写回纪律：进度文件的四个区块（`sessions` / `learner` / `summary` / 派生三键）全部只经引擎——`init` 建、`update` 改、`check` 验；派生字段只由引擎按三式算，LLM 一个字都不写。笔记与摘要 md 由本技能写正文，路径由引擎登记。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。notes 下的 md 进不了渲染面（viewer 只扫 `{output_dir}/*.yaml`），`learning-progress.yaml` 的 `notes` 字段是笔记的唯一引用点——不得为 notes 增任何浏览器/等待交互点。

## 结构

`{output_dir}/learning-progress.yaml` —— 运行态单一源（定义态在技能内 `curriculum.yaml`，两者用整数 session id 对齐）：

```yaml
project: {name, created, updated}
learner:
  role: QA|开发|组长|负责人|null      # init 后可空，02-assess 补全（写通道 = update --learner）
  experience: <string|null>          # 入门|进阶|资深；assessed 非空后必填
  goals: [<string>]
  pain_points: [<string>]
  assessed: <date|null>              # null = 画像未采集（写通道 = update --learner）
sessions:
  - id: 1                            # 整数 1-7，与 curriculum.yaml 对齐（session 编号即键）
    name: <string>                   # 与 curriculum.yaml 一致（定义态唯一源）
    duration_min: <N|null>           # 1-6 为分钟数；session 7 = null（ongoing）
    status: 未开始|进行中|已完成
    started_date: <date|null>
    completed_date: <date|null>
    score: <N|null>                  # 0-100 整数 = round(答对数*100/3)；仅 已完成 非空；session 7 恒 null（无 quiz）
    topics_explored: <N|null>        # 仅 session 7 非空（写通道 = update --session 7 --topics）；完成判据 >= curriculum min_topics
    notes: <relative path|null>      # 固定命名 notes/session-<NN>.md（相对 output_dir、正斜杠）；已完成 节必填且文件在场
sessions_completed: N                # 派生（引擎写）= status == 已完成 计数
completion_percentage: N             # 派生（引擎写）= floor(sessions_completed*100/7 + 0.5)
next_recommended: <1-7|null>         # 派生（引擎写）= 最小 id 未 已完成 节；全 已完成 → null
summary: {generated: true|false, path: <relative path|null>, date: <date|null>}   # path = completion-summary.md；写通道 = update --summary
revisions: []                        # {date, change, reason} —— 重做同一节时追加一条（reason 缺省 重做）
```

## 规则

1. 写范围：`{output_dir}/learning-progress.yaml`（只经 `init` / `update`）、`{output_dir}/notes/session-<NN>.md`、`{output_dir}/completion-summary.md`——仅此三处。目录由 `init` 建（不自建）、笔记命名固定（无 slug 变体）、`test-plan.yaml` / `sprint.yaml` / `stories.yaml` / 项目代码零写入。**学员隔离**：一个 `output_dir` 一份进度（单一学员，不做多学员同文件），多学员靠 diy 实例机制天然隔离（`diyc.py resolve --instance <name>`）。
2. 派生字段禁手写（`sessions_completed` / `completion_percentage` / `next_recommended`）：只由 `progress.py` 计算；手写值与 `sessions[]` 真值不符 → `check` 报 `SET_MISMATCH`。
3. 单一写通道：`learner` 与 `summary` 两区块非派生但同受约束——一律经 `update --learner` / `update --summary`；`sessions` 行经 `update --session`。手改 YAML 会连带触碰派生字段。
4. 门禁（源纪律保留）：进度文件已存在 → 强制 resume（必须经 `status` 回执分流）；**文件损坏（解析失败 / 结构不可用）→ 恢复只走 `init --recover`**（引擎先备份原文件再重建，禁手改 YAML，见 `steps/01-init.md`）；quiz 未达线 → 停下让用户选（R 复习 / C 带分继续），不自动通过——判线 `score >= 70`，`round(答对数*100/3)` 下 2/3 = 67 未达线；session 7 无 quiz，不适用。
5. 终门（机械判定）：`python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——exit 0 是唯一放行（7 节全 已完成 且 `summary.generated` 为真且摘要文件在场）；修掉每条违规并重跑，回执 `counts` 就是收尾证据。
6. 教学内容纪律：正文按 diy 口径自著，讲 diy 技能与产物；**不夹带源平台品牌字样与外部 URL**；跨产物信息一律引用 ID（`AC-x.y` / `TC-x.y.z` / `FR-x.y` / `path:<relative>`），禁复制内容。
7. 教学资源引用对象为 diy 测试链技能（`diy-test-framework` / `diy-test-author` / `diy-test-review` / `diy-test-gate` 与本技能同批 B3 落地）；无需 `--previous`——进度按 curriculum 固定 session 键幂等 upsert，无 ID 集合收缩面。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
