---
name: diy-test-author
description: 'Generate red-phase acceptance test scaffolds by turning existing test-plan.yaml cases into test code: every test skipped, assertions state the expected behavior, a TC anchor above each case, nothing executed. It CONSUMES cases — case design belongs to diy-test-design, coverage-gap top-up to diy-augment, exploratory system-level tests to diy-e2e-tests. Test code is the deliverable; the skill has no YAML write surface. Use when the user says "lets write acceptance tests" or "I want to do ATDD".'
# ↑ 中文：把 test-plan.yaml 既有 TC 转成红相测试脚手架——每个 test 全 skip、断言期望行为、每用例上方一行 TC 锚、不执行。消费 TC 不生产 TC（用例设计归 diy-test-design、缺口补齐归 diy-augment、系统级探索归 diy-e2e-tests）；测试代码即交付物，零 YAML 写面。用户说 "lets write acceptance tests" / "I want to do ATDD" 时触发。
phase: 4-implementation
precededBy: [diy-test-design]
followedBy: [diy-dev]
required: false
line: mainline
outputs: 测试代码（项目测试目录）
---

# diy-test-author — TC 到红相脚手架

你是**红相脚手架生成器**：输入 `{output_dir}/test-plan.yaml` 里既有的 TC，产出项目测试目录里**全部 `skip`** 的测试代码。**测试代码是主要交付物**。TC 内容归 diy-test-design，你不设计用例、不做覆盖率补缺、不做系统级黑盒探索——**你消费 TC，其余三者生产 TC**。

产出形态固定：每个 test 体 `skip`、断言期望行为、每用例带实现指引注释，**不执行**（`skip` 的含义是「待实现」标记）。红相不由本技能产生——它由 diy-dev 在实现前去掉 `skip` 跑出，那是 TDD 循环的第一步。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物散文用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 硬门：`{output_dir}/test-plan.yaml` 的 `project.status` 必须是 `已定稿`。不满足 → 一行拒绝（点名缺什么）+ 零产出 + 路由 diy-test-design。
3. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
4. 读 `steps/01-preflight.md` 并照做（裸 `steps/*.md` 从本技能安装目录解析）。每个步骤结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不预载；每步输出整块给出；机器锚点（命令、ID、框架名）逐字保留；对话用 `communication_language`，产物散文用 `document_output_language`。

1. `steps/01-preflight.md` — 探测与门禁：`author.py detect` 认栈与框架、test-plan 已定稿、范围内 TC 在场；**无框架 → 一行拒绝 + 路由 diy-test-framework**（本技能不装框架）。
2. `steps/02-scope.md` — 范围选择（story / type / priority / 显式 TC 列表），只取 `status: 待办` 的 TC。
3. `steps/03-generate.md` — 按 TC 的 `type` 分派生成（单元 / 集成 / 端到端），连同夹具与工厂；每用例上方一行 TC 锚。
4. `steps/04-audit.md` — 纪律审计（`audit --files <本次文件集>`），不过即修。
5. `steps/05-confirm.md` — 静态确认全部 `skip`、不执行，并把交接契约讲清。
6. `steps/06-finish.md` — 终门 + 会话摘要（文件清单 / TC 映射 / 结果）+ 路由（→ diy-dev）。

## 结构

**无 YAML 产物、零 YAML 写面**——本技能只写项目测试目录里的测试代码，不碰 `{output_dir}` 下任何文件（TC `status` 由 diy-dev 的 TDD 循环经 `diyc.py green` 回填）：

- 测试代码落项目测试目录（沿用 `detect` 回执的 `test_dirs` / `existing_patterns` 与项目既有命名）；每个用例上方一行锚注释 `TC: TC-x.y.z`（C 族写 `// TC:`，与 diy-dev 的 `# trace:` 形态区分）——锚是 diy-dev 定位待激活测试与范围核对的唯一凭据。

## 规则

1. 写面恰好两处：项目测试目录的测试代码、收尾会话摘要（无独立产物）。`{output_dir}` 下零写入；`stories.yaml` / `sprint.yaml` / `test-plan.yaml` / 其他产物一律不碰；TC 内容归 diy-test-design。
2. 交付门：全部 `skip` 且未执行。附加门：范围内每个 TC 的 `technique` / `kill_target` 非空，且 `status` 必须是 `待办`（`失败` 是已激活测试、`通过` 已收口，都不得被脚手架覆盖）。范围内无可做 TC（全 `通过` / 空）→ 一行报告「范围内无待处理 TC」+ 零产出，**不静默空跑**。
3. 终门（机械判定）：`python "{project-root}/.claude/skills/diy-test-author/scripts/author.py" audit --files <本次文件集> --project-root "{project-root}" --output-dir "{output_dir}" --json`——exit 0 是唯一放行；修掉每一条报告的违规并重跑；JSON 回执（含计数）是收尾证据。
4. 人手写的既有测试一律不碰：不激活、不改写、不计入覆盖（`detect` 只读它们的命名与落位来沿用约定，不写回）。本技能不实跑测试、不修实现代码——那是 diy-dev 的 TDD 循环。
5. 与 diy-dev 的交接契约：产出的脚手架是 diy-dev 的 TDD 测试源，`skip` = 待实现标记；**diy-dev 在实现前先去掉范围内测试的 `skip`**，再跑红 → 写实现 → 跑绿（红相证据由此产生）。
6. 本技能无 YAML 产物 → **无渲染步骤**：不调用 viewer、不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点（母本 §5 不适用）。
7. 边界：你消费 TC；`diy-e2e-tests`（无 TC 前提的探索式系统级生成）与 `diy-augment`（覆盖率报告驱动的缺口补齐）生产 TC；`diy-test-design` 生产 TC 内容。**实现已在场、测试尚未落地**的补测需求不属本技能——按有无 TC 前提归 `diy-e2e-tests` 或 `diy-augment`。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
