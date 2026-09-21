---
name: diy-eval-runner
description: 'Run a skill''s evals and report results. Use when the user wants to evaluate a skill, run evals, benchmark a skill, validate triggers, optimize a description, or grade skill outputs.'
# ↑ 中文：技能评测器——四模式真跑（baseline 打得过裸模型吗 / variant 这节值不值 / quality 达 rubric 吗 / trigger 描述在该触发的问句上真触发吗），产物 = `{output_dir}/eval-runs/<YYYYMMDD-HHMMSS>-<label>/` run 目录（run.json 等全是 JSON，**零 YAML 主产物**）。评测对象是技能提示词（技能目录 + cases），不是测试代码（那是 diy-test-review）、不算覆盖率（那是 diy-test-gate）、零任务状态写面（那是 diy-review / diy-test-gate）。用户说 "run evals" / "benchmark a skill" / "validate triggers" / "grade skill outputs" 时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: run 目录（`{output_dir}/eval-runs/`）——零 YAML 产物
---

# diy-eval-runner — 技能评测器（四模式真跑）

你把一个技能的用例**真跑**一遍，如实汇报结果——要的是信号不是戏。输入：一个技能目录（含 `SKILL.md`）+ 它的用例文件；输出：`{output_dir}/eval-runs/` 下的一个 run 目录。

**为什么需要它**：提示词的好坏平时只能靠感觉。四模式把四个问题变成可运行的事实——baseline 打得过裸模型吗（打不过该退休，不是打补丁）；variant 这一节到底值不值（全量 vs 精简最小版同输入对比）；quality 产物达到 rubric 了吗（只读 grader 逐条判）；trigger 描述在该触发的问句上真触发吗（合成技能 + **只认 `tool_use`**）。

**不硬编码模型名**：怎么调技能、认证从哪来、transcript 长什么样，全在 adapter 缝后面。运行时差异只经 `--invocation`（命令模板）与 `--adapter`（配置 JSON）注入——**绝不写死任何模型名或 CLI**。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 硬门（缺一即拒、**零产出**）：target 目录存在且含 `SKILL.md`（否则 `MISSING_FILE`）；用例文件在场（`--evals` > `<技能>/evals/cases.json` > `<project-root>/evals/<技能名>/cases.json`；找不到就停——**运行器不发明用例**）；`--mode` 是四值之一（否则 `ENUM_INVALID`）；trigger 的 `load_signal` 不是子串式（否则拒跑）。
3. 路径参数纪律：`{project-root}` 由引擎按 `--project-root` 自解析（唯一例外），其余任何 `{...}` 令牌一律拒绝（`TOKEN_UNRESOLVED`）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-scope.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不预载；每步输出整块给出；机器锚点（命令、ID、旗标、路径）逐字保留；对话用 `communication_language`，产物散文用 `document_output_language`。

1. `steps/01-scope.md` — target 定位 + 用例发现 + adapter 解析 + 运行摘要确认（不给确认就不跑）。
2. `steps/02-run.md` — 四模式执行（`run` 子命令）+ 清场环境契约 + quality 的 grader 派发。
3. `steps/03-report.md` — `aggregate` 出均值与离散度 + 终门 `check --run-dir` + 摘要与路由。

运行 trail 走 `mlog`（`--dir <run 目录> --file .memlog.md`，只追加、恒发一行 ack）；run 目录**永不删除、覆盖、轮转**——磁盘占用由用户决定，清理归用户。

## 结构

`{output_dir}/eval-runs/<YYYYMMDD-HHMMSS>-<label>/`（**零 YAML 主产物**，下列全是 JSON / 文本）：

- 公共根：`run.json`（`run_id` / `skill_path` / `mode` / `configs` / `runs_per_case` / `adapter` / `started_at` / `case_count`）+ `execution-summary.json`（`total` / `executed` / `skipped` / `failures` / `results[]`）+ `.memlog.md`。
- baseline / variant / quality：`<config>/<case-id>/{prompt.txt, case.json, cwd/, transcript.jsonl, timing.json}`，quality 另加 `grading.json`；`--runs>1` 时在 `<case-id>/` 下再下钻 `run-N/`。
- trigger：`queries/q{idx}-r{run}/`（含合成技能与 `.home`）+ `triggers-result.json`，**无 `<config>/<case-id>/` 层**。

## 规则

1. 四模式语义照引擎：baseline = 同一输入跑 `skill`（已 stage 技能）与 `bare`（什么都不 stage，裸模型即长期地板）两 config；variant = 全量 vs `--variant-path` 精简最小版；quality = 单 config + 只读 grader 逐条判 rubric；trigger = 合成技能（唯一名后缀）+ 逐问句真跑，算触发率对阈值判 pass。
2. **反自欺硬规则①：trigger 只认 `tool_use`。** 禁止整篇 transcript 子串匹配——运行时的 init 事件会列出每个被发现的技能名，子串匹配会让触发率恒为 100%。`load_signal` 为子串式时直接拒跑。
3. **反自欺硬规则②：grader 三纪律。** **不给部分分**（每条 expectation 只有过/不过）；**举证责任在通过方**（无证据不得判过，证据不确定即判不过）；**反向批评 rubric**（标出「错输出也会通过」的弱断言与被漏掉的重要结果）。grader 只读 run 目录、只写 `grading.json`；出错记 `grading_error`，绝不代入默认判决。
4. adapter 纪律：`--invocation` / `--adapter` 是唯一注入位（真跑与夹具同一注入位）。`invocation` 解析为空 → **只 stage、结果记 `skipped`**（既不崩也不静默）；命令不在 PATH（无头下即 `runner.py` 白名单未覆盖该命令族）→ warning + 跳过该 mode 并明示，**不入队**——确认是当场决策；需额外命令族时经 `runner.py --allow` 传入。
5. **run 目录永不删除、覆盖、轮转**（同名已存在则另铸后缀目录）；run 目录不进 git、清理归用户决定，`check` 报累计目录数（自动化不清理）。同名未完成 run 只提示、不自动续跑、不自动合并。
6. 写面恰好两处：`{output_dir}/eval-runs/` 内的 run 目录、收尾会话摘要。零任务状态写面（不改 `sprint.yaml`）、零缺陷入库（不写 `bug-log.yaml`）、不碰被测技能的任何文件、不写用例（用例归 `diy-bmb-builder` 的 eval beat 或用户）。
7. 边界四对：**vs `diy-test-review`**——被评对象不同，本技能评技能提示词（产物 = run 目录），它评测试代码（`test-review.yaml` 的 RV-###）；**vs `diy-test-gate`**——本技能不触项目实现、不算覆盖率、零门禁决策，它以 story 的 AC 为覆盖基准；**vs `diy-review`**——它审实现代码（L1–L4）并改任务状态，本技能零任务状态写面；**vs `runner.py`**（工具非技能）——`runner.py` 是 headless 循环编排，本技能是技能评测，引用编排器一律写 `runner.py` 全名。

- **零渲染。** 本技能**零 YAML 主产物**（run 目录全是 JSON / 文本）→ 无渲染步骤：不调用 viewer、不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点（母本 §5 不适用）。

所有代码引用一律 project-root 相对 `path:line`（基准 = `{project-root}`，不随会话 CWD 变化；正斜杠；越界的文件用绝对路径）。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
