---
name: diy-test-design
description: Derive test-plan.yaml from stories.yaml acceptance criteria using fault-based test design. For each AC, list fault hypotheses first, then derive cases via named techniques (等价类, 边界, 决策表, 状态迁移, 成对组合, 错误猜测, 蜕变测试, 属性测试); every case declares which fault it kills (kill_target). Uncovered ACs surface as explicit coverage gaps for user decision. Use when the user wants test cases designed before coding (TDD-first).
# ↑ 中文：从 stories.yaml 的验收标准按故障驱动法推导 test-plan.yaml——每条 AC 先列故障假设、再用点名技法推导用例，每条用例声明自己杀哪条故障（`kill_target`），未覆盖的 AC 显式记成覆盖缺口交用户裁决。用户想在编码前设计用例（TDD 先行）时触发。
---

# diy-test-design — 测试用例设计（YAML 单一源）

你是**测试用例设计师**。输入 `{output_dir}/stories.yaml` 的 AC 集合（外加 `prd.yaml` 的 FR 优先级与 NFR 清单、经验库），产出 `{output_dir}/test-plan.yaml`。用例一律从验收标准推导——绝不虚构覆盖：每条用例绑定一个 AC ID，每个缺口显式在案。两处**唯一权威出处**落在本技能：priority 映射（`diy-augment` / `diy-e2e-tests` 只引用不重定义）与 `static_checks` 链（下游按 `{output_dir}/test-plan.yaml` 的 `static_checks` 引用，不另造）。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（`title` / `reason` / `note` / `steps`）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 硬门：`{output_dir}/stories.yaml` 的 `project.status` 必须是 `已定稿`；不满足 → 一行说明缺什么、零产出，路由 `diy-epics-stories`。
3. 输入清单：`{output_dir}/stories.yaml` 的 AC 集合（`test_cases[].ac` 只能引用这里已有的 ID）；`{output_dir}/prd.yaml` 的 requirements `priority`（`必须` / `应该` / `可选`）与 `nfrs[]`——priority 与 NFR 映射的取值来源；经验库（`diy-coder.yaml` 的 `paths.experience_repo`，已配置且在场时）与 `{output_dir}/bug-log.yaml`（取数口径见「先列故障假设」）。
4. 目标文件：`{output_dir}/test-plan.yaml`。判意图：
   - **Create** —— 文件缺席 → 从零推导。
   - **Update** —— 文件在场 → 变更信号就地写死：`stories.yaml` 的 AC 集合与既有 `test_cases[].ac` 集合之差（有 AC 缺 TC → 补面；`ac` 悬空 → 走 `--previous` 的 ID 稳定门）；`stories.yaml` 的 `project.updated` 晚于 `test-plan.yaml` 的 `project.updated` → 提示可能有漂移；用户显式要求重设计 → 一律 Update。TC ID 保持稳定。
   - 二者都说不通 → 问用户一次，别猜。

## 工作流

全局步骤纪律：front-load——一步的输出整块给出，不在步骤中间零散提问；要停下的点明写等什么、给几个选项。

1. **规格证伪扫（终门前）。** 攻击规格，不是攻击代码：对每条 AC 问「我能不能构造这样一个输入——某个满足这条 AC 的实现，在这个输入上仍然违背用户的真实意图？」（经典例：AC 说「拒绝负数」——那 NaN、负零、`-1e5`、会被强转的字符串呢？）。每命中一处，要么是规格漏洞（→ `coverage_gaps` 配 `[SPEC-GAP]`，路由到 AC/PRD 修订），要么是漏掉的故障假设（→ 带 `kill_target` 的新用例）。运行时那一半（攻击真实实现）归 diy-review 的后置证伪轮。
2. 按「规则」的**先列故障假设**逐条非 `已完成` 故事的 AC 推导用例；写 `{output_dir}/test-plan.yaml`，`project.status: 草稿`；把路径告诉用户。
3. 立即渲染供审阅。渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。评审在 HTML 里进行。
4. 按用户反馈迭代；`stories.yaml` 有任何改动后按第 4 条激活项的变更信号重新对账。Update 时先 `cp {output_dir}/test-plan.yaml {output_dir}/test-plan.yaml.prev`，载入既有稿对账——**重写＝对账不是重建**：既有 TC（含 `diy-augment` / `diy-e2e-tests` 追加的后四值 `technique` 用例与其 `note`）原 ID 原样保留，只补面、不改绑。新稿写完后跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type test-plan --previous {output_dir}/test-plan.yaml.prev --json`，按 exit 码走三分支：`exit 0` → 直接删 `.prev`；`exit≠0` 且被报 TC 的 AC 仍在 `stories.yaml` → 判机械丢失，**按原 ID 改回**后重跑至 `exit 0`；`exit≠0` 且该 TC 的 AC 已从 `stories.yaml` 消失（合法退役）→ 允许带此违规删 `.prev`，但收尾摘要必须逐条登记「退役 TC ID + 对应 AC + 上游依据」，该 TC 只删、不改绑。
5. 终门（机械判定）：先写 `project.status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type test-plan --final --json`；`exit 0` 是唯一放行，逐条修完上报的违规再重跑（`known[]` 里的条目是用户批过的基线，不是待修违规）；JSON 回执（含计数）即收尾证据。**门失败 → `project.status` 回退 `草稿`**，修完重走本步。说人话的机械门槛：零 `[假设]`、零 `decision: 待办` 缺口、每个 `ac` 都能解析、每条用例都带 schema 枚举内的 `technique` 与非空 `kill_target`。
6. 重新渲染（同一条命令），收尾一行用 JSON 回执里的计数：用例数 / 覆盖的 AC 数 / 按决策分档的缺口数。

## 结构

`{output_dir}/test-plan.yaml`:
```yaml
project: {name, status: 草稿|已定稿, created: YYYY-MM-DD, updated: YYYY-MM-DD}   # created 建文件时设、此后不改；updated 每次写回刷今天
test_cases:
  - id: TC-5.1.1          # 稳定不变：AC ID 去前缀 + .{seq}；永不复用
    title: string
    ac: AC-5.1            # 必填：stories.yaml 中已存在的 AC ID（悬空即 UNKNOWN_ID）
    type: 单元|集成|端到端
    priority: P0|P1|P2    # 映射见「规则」——唯一权威出处就是本技能
    technique: 等价类|边界|决策表|状态迁移|成对组合|错误猜测|蜕变测试|属性测试|场景|覆盖分支|MC-DC 覆盖|白盒路径|变异杀伤   # 前 9 值编码前设计；后 4 值编码后补测，由 diy-augment 写入
    kill_target: string   # 本条用例要暴露的故障假设（必填）
    status: 待办|通过|失败   # 通过/失败 由 diy-dev / diy-build-loop 写回
    steps: [string]       # 具体验证步骤；写明预期结果（非空）
    note: string          # 可选：diy-augment 为追加用例记录的覆盖证据
static_checks:            # 有序滤网，先于任何用例执行；链的定义源就在本文件
  - order: 1              # 滤网：硬前置在前；每层给下一层降噪（不是按速度/成本）
    tool: string          # 具体命令全文——逐字执行（`diyc.py static` 用 shell 跑），不得带标记/前缀
    kills: string         # 本层能杀掉、而前序层杀不掉的问题类别；自造检查器在此写明
    gate: 阻断|记录不阻断    # 阻断 失败即停链（并挡下 diy-dev 的绿灯声明）
coverage_gaps:
  - ac: AC-x.y
    story: S-x
    reason: string
    decision: 待办|已豁免|接受缺口   # 判据轴 ＝ 这次要不要问用户：已豁免＝依据先前的用户确认；接受缺口＝本轮裁决接受不补；待办＝还没裁决
    note: string          # 已豁免 必填（留空即 EMPTY_FIELD）：引先前确认写日期 + 确认了什么；已完成 故事的自动豁免写依据
```

技法按故障假设挑，不按习惯挑；在 `technique` 里声明。下表是编码前技法（9 值）；编码后技法——`覆盖分支` / `MC-DC 覆盖` / `白盒路径` / `变异杀伤`——归 `diy-augment` 所有，实现之后才写入，设计期不挑：

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

## 规则

- **一个 AC 至少一条用例（五态穷举）。** 每条**非 `已完成`** 故事的 AC 都要拿到 ≥1 条用例——`待办` / `进行中` / `待审查` 三级同级（`待审查` 不豁免）；`已阻塞` 不例外：当前确实设计不了的 AC 记进 `coverage_gaps`、`decision: 待办` 留用户当轮裁决，**不得替用户写 `已豁免`**，更不许静默省略；只有 `已完成` 故事的 AC 豁免——照下面 gaps 规则记在 `coverage_gaps` 在案。
- **先列故障假设。** 为某条 AC 写任何用例之前，先穷举可能的故障假设——代码有可能真实包含的具体错误实现（如 off-by-one、吞掉的异常）。按顺序挖经验来源：(1) 全局经验库（`diy-coder.yaml` 的 `paths.experience_repo`，已配置且在场时——跨项目模式按 `subclass` 分桶存放在 `bugs/` 下，`type` 标签登记在 `taxonomy.yaml`）——先读 `taxonomy.yaml` 的 class→subclass→type 骨架，再**逐桶全读** `bugs/<subclass>.yaml`（投影文件、体量小，不做抽样）；(2) 本项目的 `{output_dir}/bug-log.yaml`。**相关性判据** ＝ 该 `type` 的 `trigger`（复现方法）/ `prevention`（根除机制）能否落在本故事任一 AC 的实现面上——能则成一条故障假设，不能则跳过并在 `note` 记一行；**不按关键词匹配**。两处来源里每一条相关历史模式都必须变成一条故障假设——既往缺陷是未来缺陷最强的预测器。每条用例声明自己的 `kill_target`：它要暴露的那条故障假设。失败也无法把正确代码与任一已列故障区分开的用例是装饰品——砍掉，或重新瞄准。
- **Oracle 纪律。** 用例必须给出从 AC 推导出的预期结果。AC 太含糊、推不出预期时，绝不要伪造 oracle——按 gaps 规则把该 AC 记进 `coverage_gaps`，`reason` 以 `[SPEC-GAP]` 开头；由用户把它打回 PRD/故事修订。AC 支持时，蜕变测试用例可以验证输出之间的关系，而不是绝对值。
- **静态检查是第一道滤网。** 按目标项目的技术栈（`architecture.yaml`）设计一条有序的 `static_checks` 链。排序原则是滤网关系，不是速度/成本：每一层存在的意义是 (a) 让下一层跑得起来——硬依赖在前（语法、导入、依赖、环境）；某层失败，它下面的一切要么跑不了、要么产出垃圾；以及 (b) 给下一层降噪——杀掉那些会污染下一层失败信号的问题类别。逐对相邻层做体检：某层失败要么挡住下一层，要么污染它的信号——两者皆无，说明两层之间没有净关系，重排或砍掉。`gate: 阻断` 失败即停链（并挡下 `diy-dev` 的绿灯声明）；`gate: 记录不阻断` 只记录不阻断。每个工具必须声明 `kills`——它杀掉哪些前序层杀不掉的东西；没有独立 kill 的工具砍掉，不许工具堆叠（与用例同一套 `kill_target` 纪律）。
- **与技术栈无关、可补缺；自造检查器三条。** 链从目标项目的技术栈推导——绝不预设某门语言的工具链。某个必需的滤网层在该技术栈下没有现成工具时，自己造：自定义检查器是**合法交付物**，以**可直接执行的**具体命令全文登记进 `tool`（供下游直接跑；`diyc.py static` 逐字执行它）；要标明「这层是自造」就写进 `kills` 的文字（如 `kills: "自造检查器：杀 <X>"`）——**不留 `[custom]` 标签**（标签会被当成命令的一部分，该层跑成 command not found）。三条边界：① **设计期只登记命令，不写脚本**——脚本写权归实现期，由 `diy-dev` 交付（其写面含项目代码）；② 自造检查器是**工具**不是**用例**——它的 trace 注释指向它服务的 AC（`# trace: S-x AC-x.y`），**不带 `TC-x.y.z`**（TC 正是本技能正在设计的东西，循环依赖由此消解）；③ 脚本交付状态由实现期回报，本技能不追。
- **用例可执行。** 用例写明具体验证方式（schema 断言、夹具渲染、命令 + 预期输出），不是 AC 散文的复述。说不出怎么验证，那就是覆盖缺口或坏 AC——标出来，别伪造用例。
- **type 映射到层**：`单元`（单组件代码检查，如 `viewer.py` / `runner.py` 的函数配夹具）、`集成`（跨产物检查，不靠 agent 也能脚本化跑）、`端到端`（由 agent 或操作者驱动的完整技能/工作流运行）。
- **priority 映射到风险（唯一权威出处就是本技能）。** `prd.yaml` 的 FR `priority` 决定其 AC 的用例档位：`必须`→P0 / `应该`→P1 / `可选`→P2；**NFR 引用的 AC→P0**（NFR 是必须满足的横切约束）；AC 最低要求之外的补充用例亦记 P2。`diy-augment` / `diy-e2e-tests` 只引用本映射，不重定义。
- **缺口是决策，不是遗漏。** 任何没有用例的 AC 都要出现在 `coverage_gaps` 里，带 `reason` 与 `decision: 待办`——由用户当轮裁决（补一条用例 / 接受缺口）。判据轴是「这次要不要问用户」：`已豁免` ＝ 依据**先前**的用户确认，`note` 写日期 + 确认了什么；`接受缺口` ＝ **本轮**用户裁决接受不补。`已完成` 故事的自动豁免是**另一类** `已豁免`——`note` 必须写明其**依据**而非用户确认（如「story S-x 已 `已完成`（源：`stories.yaml` `status: 已完成`）——用例缺席系历史交付，非本轮决定」），因为 `note` 留空的 `已豁免` 条目会被门拒（`EMPTY_FIELD`）。推导不出 oracle 的 AC 拿 `[SPEC-GAP]` reason。用户选「补一条用例」这一出口的归宿 ＝ **删掉该 gap 条目**（补了就没有缺口；`已豁免` 要引先前确认、`接受缺口` 意为「接受不补」，都不合用）。任何推断出来的豁免或优先级判断，都在 YAML 值里带 `[假设]` 前缀；未决事项落在文件里，绝不只存在于对话中。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
