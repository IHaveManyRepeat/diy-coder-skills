---
name: diy-e2e-tests
description: 'Generate end to end automated tests for existing features — detect the project test framework, target implemented features, generate API and E2E cases against the real system, execute them, and append the executed cases to test-plan.yaml (type: 端到端 / technique: 场景, status 通过|失败) with the test code landing in the project test directory. Generates tests ONLY — the artifact type stays test-plan.yaml, tasks are never moved, and code review or story validation is out of scope. Use when the user says "create qa automated tests for [feature]" or "generate e2e tests".'
# ↑ 中文：为已实现的特性生成端到端自动化测试——探测项目测试框架，锁定已实现的被测特性，对着真实系统生成 API 与 E2E 用例并实跑，把跑过的用例追加进 test-plan.yaml（`type: 端到端` / `technique: 场景` / `status: 通过|失败`），测试代码落项目测试目录。只生成测试：产物类型仍是 test-plan.yaml，任务状态从不移动，代码评审与故事验收不归它管。用户说 "create qa automated tests for [feature]" 或 "generate e2e tests" 时触发。
phase: 4-implementation
precededBy: [diy-dev]
followedBy: []
required: false
line: mainline
outputs: test-plan.yaml
---

# diy-e2e-tests — 实现后系统级测试生成（追加 TC）

你是 QA 自动化工程师。输入：一个已实现的特性（一条故事、一个目录，或自动发现的实现面）。产出：项目测试目录里的 API/E2E 测试代码，外加追加进 `{output_dir}/test-plan.yaml` 的**实跑过**的用例。你只生成测试——不做代码评审、不做故事验收、不新建产物类型。

**边界。** 本技能在实现之后、黑盒、系统级：驱动真实系统，记录真正跑过的东西。编码前的用例设计（九种技法）归 diy-test-design；编码后的覆盖补缺（三种技法）归 diy-augment；编码前的红相脚手架（消费既有 TC、从不执行）归 diy-test-author——没有 TC 前提的缺口落在本技能或 diy-augment，绝不落在它那里。代码评审与故事验收是别的技能的活（diy-review / diy-epics-stories）——此处绝不做。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（用例的 `title` / `kill_target` / `steps` 与收尾摘要）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 目标文件：`{output_dir}/test-plan.yaml`——只追加 `test_cases` 条目，从不建文件、从不改写既有条目。
3. 硬门：`{output_dir}/test-plan.yaml`（追加目标）与 `{output_dir}/stories.yaml`（每条追加用例的 `ac` 都要解析回它）必须在场。
   - 满足 → 继续第 4 步。
   - 缺任一件 → 停下，一行点名缺哪个文件、说明追加目标未就绪，路由 `diy-test-design`；**零产出，此检之外零探测**。绝不新建空的 `test-plan.yaml`——本技能只追加，从不初始化。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-detect.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只载一个 `steps/` 文件——绝不预载；前置给全（front-load）——一步的输出整块给出，不挤牙膏；机器锚点（框架名、命令、ID）逐字保留；产物叙述用 `document_output_language` 写、对话讲 `communication_language`。

1. `steps/01-detect.md` — 探测框架（`e2e.py detect`）；无框架 → 摆出 `suggested` 取用户确认；**绝不安装任何东西**。硬门见激活段第 3 条。
2. `steps/02-targets.md` — 识别被测特性（点名 / 目录扫描 / 自动发现），逐条绑到一条故事 + AC；无 AC 可绑 → 交互态问用户裁定，headless 经 `diyc.py defer-add` 入队。
3. `steps/03-generate-api.md` — 按项目既有的框架模式生成 API 用例（状态码、响应形状、happy path + 1–2 条错误用例）。
4. `steps/04-generate-e2e.md` — 生成 E2E 用例（语义定位器、用户旅程、可见结果断言、线性简单），随后对着真实系统实跑；失败当场修，修不动就记 `失败`。
5. `steps/05-record.md` — 把用例写成 JSON 文件并追加（`e2e.py record`）；exit 0 是唯一放行；以回执计数收尾。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/test-plan.yaml` 的追加条目——沿用 diy-test-design 的既有 schema，不新建产物：

```yaml
test_cases:
  - id: TC-5.1.2            # AC ID 去前缀 + 该 AC 的下一个序号；永不重编号、永不复用
    title: string           # 层轴的唯一落点（`api | e2e`）——`type` 字段不带层信息
    ac: AC-5.1              # stories.yaml 里已存在的单条 AC
    type: 端到端             # 本技能恒为此值（`e2e.py` 实核）
    priority: P0|P1|P2      # 档位映射唯一权威出处 = diy-test-design「priority 映射到风险」；本技能只引用，不重定义
    technique: 场景          # 本技能恒为此值：端到端旅程那一种技法
    kill_target: string     # 本条用例要暴露的故障假设
    status: 通过|失败         # 实测结果——只有真正跑过的用例才被追加
    steps: [string]         # 具体验证步骤，含预期结果
```

追加成功时 `record` 把 `project.updated` 刷成今天（`YYYY-MM-DD`）；其余 `project` 键与既有条目一律不动——本技能不建文件、不写 `created`。

## 规则

1. 写范围恰好三个面：`{output_dir}/test-plan.yaml` 的追加用例；项目测试目录里的测试代码；收尾会话摘要（不另写 YAML）。`sprint.yaml`、`stories.yaml`、其它产物与既有的 `test_cases` 条目零写入；任务状态绝不移动。
2. 每条追加用例都是 `type: 端到端` + `technique: 场景`，绑一条已存在的 AC，且 `kill_target` 非空；只追加跑过的用例，带实测 `status`。`api | e2e` 是生成层轴，只决定走第 3 步还是第 4 步与收尾摘要的分层计数，**不写进 `type` 字段**（`type` 恒为 `端到端`）——层信息落用例 `title`。`priority` 按 diy-test-design 的「priority 映射到风险」取值，本技能只引用、不重定义。
3. 终门（机械）：跑 `python "{project-root}/.claude/skills/diy-e2e-tests/scripts/e2e.py" record --tc-file <cases.json> --project-root "{project-root}" --output-dir "{output_dir}" --json`——exit 0 是唯一放行；逐条修完上报的违规再重跑；回执（含计数与 `diyc` 交叉核对块）即收口证据。`diyc` 块带违规是**要转述的 warning**（可能早于本次运行），不是写权失败。
4. 边界声明：编码前设计 → diy-test-design；编码后按覆盖补缺 → diy-augment；编码前红相脚手架（只消费既有 TC、从不执行）→ diy-test-author。
5. 渲染命令要求宿主 Python 有 PyYAML。它以 `ModuleNotFoundError` 失败时，报出该错并建议 `pip install pyyaml`——绝不静默回落。
6. 不需要 `--previous` 轮——本技能只往 `test-plan.yaml` 追加用例：既有条目永不改写、重编号或删除，故 TC 集只增不减，没有 ID 集合会缩水。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
