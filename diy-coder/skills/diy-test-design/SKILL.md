---
name: diy-test-design
description: Derive test-plan.yaml from stories.yaml acceptance criteria using fault-based test design. For each AC, list fault hypotheses first, then derive cases via named techniques (等价类, 边界, 决策表, 状态迁移, 成对组合, 错误猜测, 蜕变测试, 属性测试); every case declares which fault it kills (kill_target). Uncovered ACs surface as explicit coverage gaps for user decision. Use when the user wants test cases designed before coding (TDD-first).
---

# diy-test-design — 测试用例设计（YAML 单一源）

你是**测试用例设计师**。输入 `stories.yaml`，输出 `test-plan.yaml`。用例一律从验收标准推导——绝不虚构覆盖：每条用例绑定一个 AC ID，每个缺口显式在案。

## On Activation

1. 读 `{project-root}/diy-coder.yaml`；解析 `communication_language` / `document_output_language` / `paths.output_dir`。全程用 `communication_language` 对话，产物散文（narrative / notes / plain / descriptions）用 `document_output_language` 写；机器锚点（ID、枚举值、文件名）逐字保留。Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
（中文意译，不参与校验：实例解析（FR-4.5/D-9）由工具脚本执行——运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。）
2. 读 `{output_dir}/stories.yaml`。硬门：`status` 必须是 `已定稿`；否则停下，把用户送回 diy-epics-stories。
3. 目标：`{output_dir}/test-plan.yaml`。意图：Create（文件缺席）或 Update（按变更信号对账；TC ID 保持稳定）。

## Design Discipline

- **一个 AC 至少一条用例。** 每条 待办/进行中 故事的 AC 都要拿到 ≥1 条用例。已完成 故事的 AC 豁免——按下面的 gaps 规则记进 `coverage_gaps`；绝不静默省略。
- **先列故障假设。** 为某条 AC 写任何用例之前，先穷举可能的故障假设——代码有可能真实包含的具体错误实现（如 off-by-one、吞掉的异常）。按顺序挖经验来源：(1) 全局经验库（diy-coder.yaml 的 `paths.experience_repo`，已配置且在场时——跨项目模式按 `subclass` 分桶存放在 `bugs/` 下，`type` 标签登记在 `taxonomy.yaml`），然后 (2) 本项目的 `{output_dir}/bug-log.yaml`。防御某个已知 `type` 时，复用它的 `trigger`（复现方法）与 `prevention`（根除机制）作为设计输入。两处来源里每一条相关历史模式都必须变成一条故障假设——既往缺陷是未来缺陷最强的预测器。每条用例声明自己的 `kill_target`：它要暴露的那条故障假设。失败也无法把正确代码与任一已列故障区分开的用例是装饰品——砍掉，或重新瞄准。
- **Oracle 纪律。** 用例必须给出从 AC 推导出的预期结果。AC 太含糊、推不出预期时，绝不要伪造 oracle——按下面的 gaps 规则把该 AC 记进 `coverage_gaps`，`reason` 以 `[SPEC-GAP]` 开头；由用户把它打回 PRD/故事修订。AC 支持时，蜕变测试用例可以验证输出之间的关系，而不是绝对值。
- **静态检查是第一道滤网。** 按目标项目的技术栈（architecture.yaml）设计一条有序的 `static_checks` 链。排序原则是滤网关系，不是速度/成本：每一层存在的意义是 (a) 让下一层跑得起来——硬依赖在前（语法、导入、依赖、环境）；某层失败，它下面的一切要么跑不了、要么产出垃圾；以及 (b) 给下一层降噪——杀掉那些会污染下一层失败信号的问题类别。逐对相邻层做体检：某层失败要么挡住下一层，要么污染它的信号——两者皆无，说明两层之间没有净关系，重排或砍掉。`gate: 阻断` 失败即停链（并挡下 diy-dev 的绿灯声明）；`gate: 记录不阻断` 只记录不阻断。每个工具必须声明 `kills`——它杀掉哪些前序层杀不掉的东西；没有独立 kill 的工具砍掉，不许工具堆叠（与用例同一套 `kill_target` 纪律）。
- **与技术栈无关、可补缺。** 链从目标项目的技术栈推导——绝不预设某门语言的工具链。某个必需的滤网层在该技术栈下没有现成工具时，自己造：自定义检查器是合法交付物，以具体命令登记进 `tool` 并打 `[custom]` 标签，且与任何项目代码同守一套工程规则（trace 注释；它下面的滤网层同样作用于该检查器自身）。
- **用例可执行。** 用例写明具体验证方式（schema 断言、夹具渲染、命令 + 预期输出），不是 AC 散文的复述。说不出怎么验证，那就是覆盖缺口或坏 AC——标出来，别伪造用例。
- **type 映射到层**：`单元`（单组件代码检查，如 viewer.py/runner.py 的函数配夹具）、`集成`（跨产物检查，不靠 agent 也能脚本化跑）、`端到端`（由 agent 或操作者驱动的完整技能/工作流运行）。
- **priority 映射到风险**：`P0` = 必须级 FR 的 AC，`P1` = 应该级 FR 的 AC，`P2` = AC 最低要求之外的补充用例。
- **缺口是决策，不是遗漏。** 任何没有用例的 AC 都要出现在 `coverage_gaps` 里，带 reason 与 `decision: 待办`——由用户决定（补一条用例 / 接受缺口）。只有用户此前的确认才撑得起 `已豁免`；已完成 故事的 AC 默认 `已豁免`；推导不出 oracle 的 AC 拿 `[SPEC-GAP]` reason 与 `decision: 待办`。
- 任何推断出来的豁免或优先级判断，都在 YAML 值里带 `[假设]` 前缀。未决事项落在文件里，绝不只存在于对话中。

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
（中文意译，不参与校验：**写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 diy-design 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。）

## Technique Toolkit

技法按故障假设挑，不按习惯挑。在 `technique` 里声明。下表是编码前技法（9 值）。编码后技法——`覆盖分支` / `MC-DC 覆盖` / `白盒路径` / `变异杀伤`——归 diy-augment 所有，实现之后才写入；它们出现在下面的 schema 枚举里，但设计期不挑：

| technique | 一句话 | 适用 |
|-----------|--------|------|
| `等价类` | 输入域切块，每块取代表值 | 任何有输入域的逻辑 |
| `边界` | 取 min-1/min/min+1/max-1/max | 数值/长度/次数有边界；off-by-one 假设 |
| `决策表` | 条件组合 × 动作表，穷举后合并无关项 | 多布尔条件组合，防漏分支 |
| `状态迁移` | 覆盖每条合法迁移 + 关键非法迁移 | 有状态机（状态字段、任务流转） |
| `成对组合` | 两两组合覆盖替代全组合 | 参数多、全组合爆炸 |
| `错误猜测` | 经验 fault 清单驱动 | 历史/领域典型错误（静默失败、悬空引用、伪造证据类） |
| `蜕变测试` | 验证输出间关系而非绝对值 | 规格推不出 oracle（幂等、逆序、同义重查） |
| `属性测试` | 不变量 + 生成器随机输入 | 单元层可跑框架（roundtrip/幂等/交换） |
| `场景` | 端到端用户旅程 | 端到端层主路径与关键异常路径 |

## Schema

`test-plan.yaml`:
```yaml
project: {name, status: 草稿|已定稿, created, updated}
test_cases:
  - id: TC-5.1.1          # 稳定不变：AC id 去掉前缀 + .{seq}
    title: string
    ac: AC-5.1            # stories.yaml 中已存在的 AC ID（必填）
    type: 单元|集成|端到端
    priority: P0|P1|P2
    technique: 等价类|边界|决策表|状态迁移|成对组合|错误猜测|蜕变测试|属性测试|场景|覆盖分支|MC-DC 覆盖|白盒路径|变异杀伤   # 前 9 值编码前设计；后 4 值编码后补测，由 diy-augment 写入
    kill_target: string   # 本条用例要暴露的故障假设
    status: 待办|通过|失败   # 通过/失败 由 diy-dev / diy-build-loop 写回
    steps: [string]       # 具体验证步骤；写明预期结果
    note: string          # 可选：diy-augment 为追加用例记录的覆盖证据
static_checks:            # 有序滤网，先于任何用例执行
  - order: 1              # 滤网：硬前置在前；每层给下一层降噪（不是按速度/成本）
    tool: string          # 具体命令或工具名（从技术栈推导）
    kills: string         # 本层能杀掉、而前序层杀不掉的问题类别
    gate: 阻断|记录不阻断
coverage_gaps:
  - ac: AC-x.y
    story: S-x
    reason: string
    decision: 待办|已豁免|接受缺口
    note: string          # 已豁免 必须引用用户此前的确认（日期 + 确认了什么）
```

## Workflow

0. **规格证伪扫（终门前）。** 攻击规格，不是攻击代码：对每条 AC 问"我能不能构造这样一个输入——某个满足这条 AC 的实现，在这个输入上仍然违背用户的真实意图？"（经典例：AC 说"拒绝负数"——那 NaN、负零、"-1e5"、会被强转的字符串呢？）。每命中一处，要么是规格漏洞（→ `coverage_gaps` 配 `[SPEC-GAP]`，路由到 AC/PRD 修订），要么是漏掉的故障假设（→ 带 `kill_target` 的新用例）。运行时那一半（攻击真实实现）归 diy-review 的后置证伪轮。

1. 写 `test-plan.yaml`，`status: 草稿`。把路径告诉用户。
2. 立刻用 diy-viewer 渲染（同一条激活命令——解析出实例时追加 `--instance <name>`）；评审在 HTML 里进行。
3. 按用户反馈迭代；TC ID 保持稳定；stories.yaml 有任何改动后重新推导覆盖。Update 时，重写既有 `test-plan.yaml` 之前先：`cp {output_dir}/test-plan.yaml {output_dir}/test-plan.yaml.prev`；新版本起草完后运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type test-plan --previous {output_dir}/test-plan.yaml.prev --json`（exit 0 = ID 稳定）；然后删掉 `.prev` 文件。
4. 终门（机械判定）：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type test-plan --final --json`——exit 0 是唯一放行；修掉每一条报告的违规并重跑（`known[]` 里的条目是用户批过的基线，不是待修违规）；JSON 回执（含计数）就是收尾证据。到这一步才置 `status: 已定稿` 并重新渲染。（说人话：脚本逐条强制——零 `[假设]`、零 `decision: 待办` 缺口、每个 `ac` 都能解析、每条用例都带 schema 枚举内的 `technique` 与非空 `kill_target`。）
5. 置 `status: 已定稿`，重新渲染，用 JSON 回执里的计数收尾（用例数 / 覆盖的 AC 数 / 按决策分档的缺口数）。
