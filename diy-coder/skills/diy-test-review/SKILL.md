---
name: diy-test-review
description: 'Review test quality using best practices validation. Use when the user says "lets review tests" or "I want to evaluate test quality".'
# ↑ 中文：审计测试代码质量——32 条有效规则（severity 由引擎复算）→ 0-100 评分账本，外加 AC ↔ 源码 ↔ 测试三向走查的覆盖缺口；产物 {output_dir}/test-review.yaml（RV-###）。只看测试代码，不审实现代码（那是 diy-review），不做覆盖率门（那是 diy-test-gate）。用户说 "lets review tests" / "I want to evaluate test quality" 时触发。
phase: 4-implementation
precededBy: [diy-augment]
followedBy: [diy-test-gate]
required: false
line: mainline
outputs: test-review.yaml
---

# diy-test-review — 测试代码质量审计（YAML 单一源）

你是**测试质量审计员**。输入：scope 内的测试文件 + `criteria.yaml` 规则注册表（技能内静态资产）。输出：`{output_dir}/test-review.yaml` 的 `RV-###` 记录。你只审计与路由——不改测试代码、不改上游产物、不移动任务状态。

**为什么需要它**：测试代码也会烂，而且烂得更隐蔽——被禁用的用例、恒真断言、只配了 mock 就自证的测试，都会让套件报绿而什么都没证明。本技能的规则集把 severity 钉死在表里，LLM 只判"这条规则命中没有"，扣分由引擎算。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. scope：用户给的路径/目录优先；未给则问一次（本技能不自行发明评审集）。
3. `scan` 发现文件并跑机械面（评审集之外取样惯例语料）：
   `python "{project-root}/.claude/skills/diy-test-review/scripts/test_review.py" scan --paths <P> --project-root "{project-root}" --output-dir "{output_dir}" --json`（`--paths` 可重复）
   exit 1 = 拒绝（scope 内无测试文件），零产出，**一行拒绝 + 路由**（给路径，或先跑 diy-test-author），然后停。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-preflight.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件；一步的输出整块给出，不在步骤中间提问；产物散文用 `document_output_language` 写，对话用 `communication_language`。

1. `steps/01-preflight.md` — scope 确认 + `scan` 发现 + excluded 判定，起草 `RV-###` 记录。
2. `steps/02-criteria.md` — 载入 `criteria.yaml`（35 行留档 / 有效 32）+ baseline 解读：机械键读 `scan` 的 `status` 不自判，`bdd_naming` / `assertion_style` 由你读采样文件判读。
3. `steps/03-evaluate.md` — 逐文件评估：复核 `scan` 机械项 + 判语义行（severity 不填；convention 行带 `class`）；findings 落 `{output_dir}/test-review-findings.json`（含 bonus 判定）；**另跑 `walkthrough` 三向走查（必跑）**。
4. `steps/04-score.md` — `score` 一次算出账本与维度分并展示（LLM 不自算）。
5. `steps/05-report.md` — 落盘 + `check --final` 终门 + 渲染 + 摘要（score / grade / recommendation / 路由）。

记录写纪律：step 1 建为 `草稿`，各步填充，step 5 定稿。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/test-review.yaml`：

```yaml
project: {name, created, updated}
reviews:
  - id: RV-001                  # RV-### — 三位零填充、稳定不重用不重编号
    date: YYYY-MM-DD
    status: 草稿|已定稿
    scope: {paths: [<relative>], files_reviewed: N, excluded: [{path, reason: 格式不支持|自动生成|超出范围}]}
    convention_baseline: {corpus_size: N, sampled: N, keys: {priority_markers: {adopted: N, status: 已确立|新现|缺失|未知}, test_ids: {...}, bdd_naming: {...}, network_first: {...}, data_factories: {...}, fixtures: {...}, assertion_style: {...}}}   # 7 key；机械键 status 由 scan 判定，bdd_naming / assertion_style 由 LLM 判读
    findings:
      - {row: C1|H3|M5|L2, severity: CRITICAL|HIGH|MEDIUM|LOW, file: <relative>, line: N|null, note: <string>, basis: 必查|视情况|惯例, class: 已确立|新现|null}   # severity 由引擎复算（惯例行按 class 降档）；class 仅 basis=惯例 行必填；line 为 null 仅限文件级行 H5/H6/H7/H8/L4
    score:                      # 五键全部由 score 命令复算，LLM 不写
      deductions: {critical: N, high: N, medium: N, low: N, total: N}
      bonus: {applied: [<string>], total: N}   # 六类键（优秀 BDD|完备夹具|数据工厂|网络优先|完全隔离|测试 ID 完备），只列得 5 分者；total ≤ 30
      score: N
      grade: A|B|C|D|F
      recommendation: 打回|要求修改|有保留批准|批准
    coverage_gaps:              # 三向走查结果（不进评分）
      - {kind: 无实现|无测试|孤儿用例|从未运行, ref: AC-x.y|TC-x.y.z, note: <string>, route: diy-dev|diy-test-design|diy-test-author|用户}   # route = 建议路由（供用户/主 agent 决策，非自动调用）
    walkthrough: {status: 全覆盖|部分覆盖|已跳过, note: <string>}   # 非全覆盖时 note 记缺源与跳过类
    dimensions: {determinism: N, isolation: N, maintainability: N, performance: N}   # 展示用；score 复算（每维 = max(0, 100 − Σ该维命中权重)）
    recommendations: [<string>]
    open_questions: [<string>]
revisions: []
```

## 规则

1. **与 diy-review 的边界。** diy-review 审**实现代码**（L1-L4 层 + 四类路由：正确性 / 边界 / 验收 / 设计）；diy-test-review 审**测试代码**（32 条有效规则 → 评分账本）。两者不重叠、互不调用：diy-review 的 L1 会读到测试，但那是"实现正确性"视角，本技能是"测试质量"视角。覆盖率与门禁决策归 diy-test-gate（本技能不算覆盖率）。
2. **账本口径不得漂移（引擎唯一权威）。** `deductions = CRITICAL*10 + HIGH*5 + MEDIUM*2 + LOW*1`；bonus 六类各 0 或 5、上限 30；`score = clamp(100 - deductions + bonus, 0, 100)`；分档 A≥90 / B≥80 / C≥70 / D≥60 / F<60；recommendation 由计算得出（CRITICAL>0 → 打回；HIGH>0 → 要求修改；score<70 → 要求修改；MEDIUM+LOW>0 → 有保留批准；否则 批准）。**severity 与维度分由引擎复算，LLM 不填**；LLM 唯一的判据是"哪条规则命中"。
3. **上下文与惯例只能加发现，不能豁免或改分。** 仓库惯例走 convention 三类门（`已确立` 原档 / `新现` 降一档 floor `LOW` / `缺失` 与 `未知` 该行不成立）；匹配不到任何规则的文件列入 `excluded` **不评分**——"匹配不到任何规则得到的 100 不是 100"。
4. **跨文档核对一律委派，禁重写规则。** `walkthrough` 的源码面委派 `diyc.py trace`、`孤儿用例` 面委派 `diyc.py check --type test-plan`；子进程 rc∈{0,1} 均为正常回执，rc=2 / 不可解析 / 缺席 → warning 降级（`TOOL_MISSING` / `TOOL_ERROR`），不崩溃、不阻塞评审主体。
5. **写权边界。** 本技能只写 `{output_dir}/test-review.yaml`（记录 + `revisions`）与会话工作文件 `{output_dir}/test-review-findings.json`。不碰测试代码、不碰 `stories.yaml` / `test-plan.yaml` / `sprint.yaml` / `bug-log.yaml`；缺口的路由是**建议**，执行归对应技能。记录只追加，改既有记录时追加 `revisions`；无 `--previous` 轮次（追加式台账，无 ID 收缩面）。
6. **终门（机械判定）。** 先落 `status: 已定稿`——`已定稿` 是门要检的东西、不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-test-review/scripts/test_review.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`，参数与激活时一致（`--output-dir` 必填、永不默认）。exit 0 是唯一放行；修掉每条违规重跑；JSON 回执（含 counts）就是收尾证据。渲染与收尾等 exit 0。
7. **无副作用面。** 本技能只读文件与跑自己的 `scan` / `score` / `walkthrough` / `check`（均只读）——不装依赖、不跑项目测试、不写目标项目、不 git 操作，故无 §0 纪律 5 的自动化/确认档处置；渲染按 Workflow 的静默旁路。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
