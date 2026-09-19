---
name: diy-review
description: 'Review a sprint task in 待审查 state with layered audits - L1 correctness, L2 boundary, L3 acceptance-coverage, plus L4 design adoption for UI tasks whose ACs carry design_ref. Every finding routes to exactly one of 意图缺口 / 规格缺陷 / 小修 / 后置. Verdict 通过 moves the task to 已完成 after backfilling stories.yaml and test-plan.yaml; a 失败 with 规格缺陷 blocks the task for upstream spec repair, any other 失败 sends it back to 进行中. Real defects found are also logged into bug-log.yaml (three-level classification) to feed future fault hypotheses. Optional falsification round after 通过 (--falsify <story|all>, accepted on 已完成 targets): attack the finished work with bug-log patterns and non-functional dimensions. Use when the user wants to review/audit a finished implementation or when diy-dev hands off.'
# ↑ 中文：审查 `待审查` 状态的冲刺任务——分层审计 L1 正确性 / L2 边界 / L3 覆盖审计；AC 带 `design_ref` 的 UI 任务加 L4 设计采用。每条 finding 恰好路由到「意图缺口 / 规格缺陷 / 小修 / 后置」之一。判决 `通过` 时由 `done` 原子写回 `stories.yaml` / `test-plan.yaml` 两个真源并把任务送进 `已完成`；带 `规格缺陷` 的 `失败` 阻塞任务待上游修规格，其余 `失败` 打回 `进行中`。发现的真缺陷另入 bug-log.yaml（三级分类）喂养后续故障假设。`通过` 后可跑可选证伪轮（`--falsify <story|all>`，接受 `已完成` 目标）：用 bug-log 模式与非功能维度攻击已完成的工作。用户想审查/审计完成的实现，或 diy-dev 交棒时使用。
---

# diy-review — 分层审查与路由（YAML 单一源）

你是审查者。输入：`sprint.yaml` 与一个 `待审查` 任务、本任务的实现面（取数口径见规则第 2 条）、`stories.yaml`（AC 明细）、`test-plan.yaml`（已声明的覆盖）。你审查、你路由，绝不亲手改实现——返工归 diy-dev，规格修复归上游技能。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（finding 的 `note`、收尾播报）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 硬门：`{output_dir}/sprint.yaml` 的 `project.status: 已定稿`；目标任务必须在 `status: 待审查`——其他状态一律拒绝并点明其状态（`待办` → 先走 diy-dev；`进行中` → dev 环未收尾）。例外：`--falsify <story|all>` 也接受 `已完成` 目标——该次运行只跑工作流第 6 步（证伪轮），绝不跑层审查。`已阻塞` 永远拒绝。
3. 材料：开场行点名的那些输入；实现面的取数口径见规则第 2 条。

## 工作流

全局步骤纪律：一次给全（front-load）——本轮输出整块给出，不在步骤中间提问；要停下时一行说明原因。

1. 载入材料，一行复述审查范围。（带 `--falsify` 且目标是 `已完成` → 直接跳到第 6 步。）
2. 按序跑 L1 → L2 → L3 → L4；L4 只有任务 AC 带 `design_ref` 时才跑——跳过要在报告里点名，绝不静默。收集 findings；逐条对照规则第 4 条的表格核验——每条恰好一个路由。

### 四层（L1–L4）

- **L1 正确性。** 实现是否恰好做到了 AC 说的——没有漏掉的 then 子句、没有没被要求的多余行为？逐条 AC 对照。trace 纪律是抓手：diff 里每个方法都要带 `# trace:` 注释（见 diy-dev），其 ID 必须能在 stories / test-plan 里解析——跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" trace --src <本任务实现文件/目录> --json`（`--src` 可重复、相对 project-root；不给则扫全项目），把回执 `unresolved` 里的每一条当 finding（路由 `小修`）——该列表是**该扫描面**上的结果；`# trace:` 整行缺席仍属人对 diff 的目读。对被追踪的方法逐条核行为：声明 `AC-9.1` 却没兑现其 then 子句的代码，是一条点名该 trace 行的 L1 finding。
- **L2 边界。** 走 AC 暗示却没写明的失败模式：坏输入、空/None、并发、错误路径、静默兜底。只报真会咬人的未处理情形。
- **L3 覆盖审计。** 你不手动重验。跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type review --story <S-x> --json`——机械核对四项台账：每个 `test_refs` 的 TC 都有 `evidence` 条目；红线在绿线之前；证据结论与 test-plan 的 TC `status` 一致；绑定本任务的每个 TC 都带非空 `kill_target` 与对 test-plan schema 枚举合法的 `technique`（缺声明或出枚举 = 用例可能是装饰品——区分不了正确代码与它该杀的故障——点名 TC ID 报出）。本步时点 `review` 块尚未写、**其缺席不是违规**：此处回执里的每条违规都是台账 finding（`EVIDENCE_MISSING` / `STATUS_MISMATCH` / 声明类），按本条处置；块结构校验（verdict / layer / route 枚举、通过-失败一致性）发生在第 3 步写块后跑的**同一条命令**上。重开复审时，`test_refs` 里由 diy-augment 追加的后编码用例若无 `evidence`，`EVIDENCE_MISSING` 就是「该周期未重跑它们」的信号 → 挂 diy-dev 补 red/green，**不当豁免**。仍属目读的：TC 步骤是否真断言了 AC 的 then 子句。任何不一致——脚本报的或目读发现的——是一条点名 TC ID、声明与实际记录的 finding（AC-8.2）；回执 `known[]` 里的条目是用户已认可的基线，不是待修违规。
- **L4 设计采用（FR-3.7/D-10 —— 仅 UI 任务）。** 任务 AC 带 `design_ref` 时核验**采用**——设计交付（diy-design 写出的框架页）是实现必须在其上生长的基线。像素比对已弃用（不可靠；`compare` 引擎 2026-09-12 已删）。核四件事，每项违规一条 `小修` finding、任务打回 `进行中`（HALT）：(a) 结构对照——实现页面结构须与线框（wireframe/HTML）结构稿（design.yaml 的 `prototype`）一致：小节、层级、landmark 次序；(b) 零重写——实现长在设计稿代码（design.yaml 的 `implementation` 路径）**之上**，不是它的再实现；重写 UI 即使看着像也是一条 finding；(c) token 单一源——`python "{project-root}/.claude/skills/diy-design/scripts/design.py" audit --design "{output_dir}/design.yaml" --src <impl>` 的每条 `one-off-*` 违规即 finding；(d) 无障碍——`python "{project-root}/.claude/skills/diy-design/scripts/design.py" check --design "{output_dir}/design.yaml"` 的违规即 finding。绝不静默跳层——跳过要用户的明确裁断。

3. 把 `review` 块写进任务条目；跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type review --story <S-x> --json`——exit 0 确认块结构合法后，再按规则第 5 条落状态与回填（`通过` 走 `done`；`失败` / `已阻塞` 走 `transition`；这些命令都 bump `project.updated`）。
4. 渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）；报出审查面（路径）、判决与已路由的 findings。
5. `失败` 时点名下一步（diy-dev 的返工项；`已阻塞` → 上游改 stories.yaml / test-plan.yaml）；`通过` 时用 JSON 回执的计数收尾（按层 / 按路由的 findings、判决）。
6. **证伪轮（可选 —— `--falsify <story|all>`，接受 `已完成` 目标；`all` = 本冲刺全部已完成任务）。** 目标：打破已完成的工作——假定它就有 bug。用 `bug-log.yaml` 的模式瞄准本实现，走非功能清单（性能、用户体验、安全、兼容性、可靠性、边界）问「这个会怎么坏」，并跑临时攻击。命中即经 `bug-add` 入库、路由（`意图缺口` / `小修`），任务离开 `已完成` → `进行中`（HALT 写：`transition --story <S-x> --to 进行中 --json`——入口不变，引擎在该边上 `pop("augment")` 清掉旧判定，与 `runner.py --reopen-failed` 同语义）。干净一轮：任务 `note` 记一行（日期 + 「证伪轮通过」）。

## 结构

`sprint.yaml` 的任务条目新增：
```yaml
    review:
      at: 2026-09-05              # 该次审查动作的日子，不随 project.updated 变
      verdict: 通过|失败
      findings:                  # 干净通过时可为空
        - layer: 正确性|边界|覆盖审计|设计采用   # 设计采用 = L4；证伪轮命中用它所属的层
          route: 意图缺口|规格缺陷|小修|后置
          note: 一行 finding（覆盖类 finding 点名 TC ID + 「声明 vs 记录」）
```

## 规则

1. **写范围。** 只写：本任务的 `review` 块与收尾 `note`、任务 `status`（`通过` 经 `done`，`失败` / `已阻塞` 经 `transition`）、`{output_dir}/bug-log.yaml`（经 `bug-add`）。`stories.yaml` / `test-plan.yaml` 只随 `done` 的原子批次回填；其他任务、源码与其余产物零写入。任何判断性取值都在 YAML 值上带 `[假设]` 前缀。
2. **实现面（diff 口径）。** 实现面 ＝ `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" trace --json` 回执 `references[].file` 里引用了本任务 `S-x` 的文件集合（扫面用 `--src` 收窄），加上 `git status --porcelain` 里本任务的未跟踪实现文件；开场一行声明本次采样的实现面。L1 的 `--src` 就指这个集合。
3. **缺陷入库（喂经验环）。** 暴露**真缺陷**（非规格问题）的 finding 另经 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" bug-add --entry '<json 对象>' --json` 追加进 `{output_dir}/bug-log.yaml`（长条目用 `--entry-file PATH`）；命令校验分类、铸下一个序号 `id`（`BUG-0xx`）、原子写入，被拒条目（exit 1）不落盘。字段：`source story class subclass type symptom root_cause trigger fix prevention pattern`（`date` 可选，缺省今天）。三级分类（`type` 是自由扩展标签——现象吻合就复用既有名，真新才铸新）：
   - `class`：`功能型 | 非功能型`
   - `subclass`：功能型 → `逻辑 | 边界 | 数据 | 状态 | 集成`；非功能型 → `性能 | 用户体验 | 安全 | 兼容性 | 可靠性`
   - `source`：`开发 | 审查发现 | 证伪轮 | 用户`（本技能写的多为 `审查发现` / `证伪轮`）
4. **路由（每条 finding 恰好一个）。**

   | 路由 | 含义 | 处置 |
   |---|---|---|
   | `意图缺口` | 实现漏掉或违背了已声明的意图 | 打回 diy-dev |
   | `规格缺陷` | 规格本身错或含糊——代码没问题 | 改 stories.yaml / test-plan.yaml，不改代码 |
   | `小修` | 一处局部的修就能解决 | 打回 diy-dev（一行范围） |
   | `后置` | 真实但当下不值得阻断 | 唯一落点 ＝ 本任务 `sprint.yaml` 的 `review.findings[]`（`route: 后置`）；**不**入 `deferred-actions.yaml`（那是副作用确认队列，语义不同）；消费方是 diy-retrospective 的技术债读面；不阻断 |

5. **判决规则。** 任一 finding 路由 `意图缺口` / `小修` / `规格缺陷` → `失败`，findings 写进任务条目，处置走 `transition`：有 `规格缺陷` → `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to 已阻塞 --reason "<finding 引文>" --json`（规格由上游修，绝不由执行者改——与 diy-build-loop 同口径）；否则 → `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to 进行中 --json`（打回 dev 环）。findings 为空或全 `后置` → `通过`：写 `review` 块 + `note`（引审查日期）进任务条目，再 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" done --story <S-x> --json`。
6. **真源回填（BUG-012）。** `done` 把 `待审查 → 已完成` 与回填当一个原子批次做完：任务 `status: 已完成`、`stories.yaml` 里该故事 `status: 已完成`、`test-plan.yaml` 里本次 L3 确认绿的每个 TC `status: 通过`（TC 行由 `diy-dev` 按绿线写，终态写做对账），并 bump 所有被触及的 `project.updated`。`已阻塞` 两个文件都不写——什么都没交付，什么也不算通过。**为什么：** 2026-09-13 质量分析发现该独立路径报 `已完成` 而真源停在 `待办`（与无头链 BUG-012 同类）。
7. **任务状态写入权（`sprint.yaml`）。** `待审查 → 已完成`（`通过`——只经 `done`，`transition` 拒绝这条边）、`待审查 → 进行中`（`失败`）、`待审查 → 已阻塞`（`规格缺陷`）、`已完成 → 进行中`（证伪轮命中——第 6 步），后三条经 `transition`，别无其他。重开入口不变：单条证伪命中走 `transition`（引擎在该边上清掉旧判定）；批量的 `runner.py --reopen-failed` 归 diy-sprint。
8. **经验上行。** 配了 `paths.experience_repo` 且在场时，提醒用户在项目根运行（**由人手动执行**，安装形态 `.claude/skills/diy-tools/scripts/exp-sync.py`）`python "{project-root}/.claude/skills/diy-tools/scripts/exp-sync.py" push`——实例运行加 `--instance <name>`（bug-log 在实例目录里）。经验库是投影；本任务的 `bug-log.yaml` 始终是真源。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
