---
name: diy-test-framework
description: 'Set up the test framework and the CI quality pipeline: detect the stack, pick the framework and CI platform with the user, render the scaffold and pipeline files byte-for-byte from the skill templates, record the selection and generation ledger in test-framework.yaml, and mechanically verify the CI file against the test-plan static_checks. Use when the user says "lets setup test framework", "I want to initialize testing framework", "lets setup CI pipeline", or "I want to create quality gates".'
phase: 3-solutioning
precededBy: []
followedBy: [diy-test-author]
required: false
line: mainline
outputs: test-framework.yaml
---

# diy-test-framework — 测试基建（框架脚手架 + CI 流水线）

你是**测试基建工程师**。输入：项目清单（`package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` / `pom.xml` / `build.gradle*` / `Gemfile` / `composer.json` / `*.csproj` 等）+ `{output_dir}/test-plan.yaml` 的 `static_checks` 链（在场时）。输出：`{output_dir}/test-framework.yaml` 台账 + 项目内的脚手架与 CI 流水线文件。

**Boundary.** 本技能建基建：框架配置 / 脚手架 / CI 流水线 / 冒烟自检。测试代码归 `diy-test-author`、测试计划归 `diy-test-design`；部署文件（Dockerfile / 部署脚本）不在 scope。**项目文件只从技能内 `templates/` 渲染**——禁 LLM 手写冒充（手写产物在重入与 check 面上不可机械校验）。

## On Activation

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物散文用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 模式与目标：`framework` / `ci` / `both`（判据在 step 1）；目标 `{output_dir}/test-framework.yaml`——Create（文件缺席）或 Update（在场：追加 `TF-###` 记录；改既有记录时补 `revisions`）。
3. 硬门：项目清单存在（**五清单为示例代表、非封闭枚举**，判据 = 引擎清单表命中）；ci 模式附加门 = 就绪凭据（台账 `setups[].files[]` 的 scaffold/config 文件在场，或 detect 报出既有框架配置）。不满足 → 一行拒绝 + 路由，**零产出**；栈无模板覆盖 → HALT + 一行报告 + 登记（禁手写冒充）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-preflight.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## Workflow

全局步骤纪律：一次只加载一个 `steps/` 文件；一步的输出整块给出，不在步骤中间提问；每个生成/修改的项目文件都按其项目内相对路径（相对 + 正斜杠）点名。

1. `steps/01-preflight.md` — `detect` 探测栈/语言/包管理器/既有框架/CI 平台/冲突 + 前置校验（清单门、冲突处置、ci 附加门）。
2. `steps/02-select.md` — 框架/平台/单元层选型与理由 + 用户确认；产出 substitutions 取值表（取值 = detect 结果 + `static_checks` 的 blocking 命令 + 门禁阈值）。
3. `steps/03-scaffold.md` — 写 framework 面 plan → `scaffold` 调用一次 → 既有配置文件走 LLM 手改通道（台账 `action: update`）→ 执行回执 `pending_commands`。
4. `steps/04-pipeline.md` — 写 ci 面 plan（注入防护段随模板逐字保留）→ `scaffold` 调用一次 → 执行回执命令。
5. `steps/05-verify.md` — 冒烟自检（lint / 示例测试 / CI 语法；产物面失败修后重跑，修不了即 HALT）+ `chmod +x` + hook 合并经 `defer-add` 入队。
6. `steps/06-finish.md` — 台账落盘 + `check --final` 终门 + 渲染 + 摘要 + 路由（→ `diy-test-author`）；删 `{output_dir}/scaffold-plan.json`。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## Schema

`{output_dir}/test-framework.yaml` —— 单一源；顶层不设 `status`，定稿态挂记录级：

```yaml
project: {name, created, updated}
setups:
  - id: TF-001                # TF-### 稳定：顺序递增，永不重编号、永不复用
    date: YYYY-MM-DD
    status: draft|final
    mode: framework|ci|both
    stack: {type: frontend|backend|fullstack|mobile, language: <string>, package_manager: <string>}
    framework: {name: <string>, runner: <string>, reason: <string>}   # 选型理由（源 02 步保留）
    unit_layer: {name: <string>}   # mobile / fullstack 时必填
    files:                        # 生成/修改的项目文件清单（对齐 path: 口径）
      - {path: <relative>, kind: scaffold|config|ci|hook|script|doc, action: new|update}   # new = 引擎新写；update = 既有文件由 LLM 手改
    checks:                       # 已执行的安装/自检命令与结果（result: fail 时 note 必填）
      - {command: <string>, result: pass|fail, note: <string>}
    ci:
      platform: github-actions|gitlab-ci|jenkins|azure-devops|harness|none
      file: <relative>            # platform=none 时省略
      stages: [<string>]          # lint|test|contract|burn-in|report
      gates: {p0: '100%', p1: '100%'}   # 质量门口径拉满：P0 / P1 双 100%（源 P1≥95% 已作废）
      static_check_alignment:     # 引用式：以 order 引用 test-plan.yaml 的 static_checks（禁抄录命令内容）
        - {order: N, in_ci: true|false}   # blocking 层必录、advisory 层可选
    deferred: [DA-0xx]            # 本技能入队的待确认动作（ID 引用 deferred-actions.yaml）
    open_questions: [<string>]
revisions: []                     # {date, change, reason} —— 改既有记录时追加
```

## Rules

1. **写范围**：`{output_dir}/test-framework.yaml` + 台账 `files[]` 声明的项目文件（**只新写，绝不删除、绝不覆盖既有文件**）+ 会话临时 `{output_dir}/scaffold-plan.json`（06 步删）。源码 / `test-plan.yaml` / `stories.yaml` / `sprint.yaml` 一律不碰。
2. **模板是唯一来源**：项目文件一律经 `scaffold` 从技能内 `templates/` 渲染（逐字节复制 + 封闭占位符替换，**不注入时间戳/随机/环境值**，同模板同 plan 同字节）。模板未覆盖的栈 → HALT + 登记，禁手写掺入。
3. **冲突即停**：目标已存在且内容不同 → 引擎回滚本次已写文件 + 整条拒绝（`FILE_CONFLICT`）；既有文件的修改只走 LLM 手改通道并记 `action: update`。
4. **终门（机械判定）**：先置 `status: final`（gate 检的就是它），再运行 `python "{project-root}/.claude/skills/diy-test-framework/scripts/test_framework.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——exit 0 是唯一放行；修掉每一条报告的违规并重跑；JSON 回执（含计数）就是收尾证据。渲染与收尾等 exit 0。
5. **CI 三方对齐**：CI 路径一律相对 + 正斜杠（与 correct-course `path:` 同口径）；blocking 层 `static_checks` 命令须以独立命令形态出现在 CI 文件，且台账 `in_ci` 与 `check` 现场重算一致（**重扫不采信台账**）；`ci.gates` 阈值经 plan 注入 CI 文件文本。
6. **副作用三档**（技能运行时的外部动作）：依赖安装 / 跑测试 / `chmod +x` / `git add`+`commit`+`push` → **自动执行**，结果记 `checks`（无头一致；破坏性 git 操作除外）；GUI 类 → 交互终端自动执行、无头跳过且不阻塞；**保留确认**（改用户级配置如 `.claude/settings.json` hook 合并 / 破坏性 git / 目标项目与 `{output_dir}` 之外写盘 / AI 做不了的事）→ 交互式停下问，无头经 `diyc.py defer-add` 入队（`deferred` 记 ID）不阻塞。选型、是否替换既有框架等**内容决策**保留确认点：无头不替用户默认，走拒绝路径等用户裁决后重入。
7. **更新纪律**：记录只追加、不重编号；改既有记录补 `revisions`。台账为追加式、无整份重写面 → **不用 `--previous`**。
8. **路由与未建技能**：只把已建的 diy 技能当可调用对象；下游 `diy-test-author` 属 B3 同批（未建成前只在摘要给路由行，不当作可调用技能）。未决项落 `open_questions`，不留对话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
