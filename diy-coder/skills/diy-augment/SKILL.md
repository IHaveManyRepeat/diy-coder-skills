---
name: diy-augment
description: 'Coded-post test augmentation. After a task reaches done, run the project''s coverage toolchain against the implementation, triage uncovered branches, condition combinations, and paths, then append complementary cases (覆盖分支 / MC-DC 覆盖 / 白盒路径) to test-plan.yaml with stable per-AC TC IDs, execute them, write back status, and leave the verdict (通过 / 失败 / 已跳过) on the task''s augment field in sprint.yaml. When a mutation toolchain is available (a user-confirmed mutation entry in the test-plan static_checks chain, or a command the user gives in-session), also run it against a sandboxed copy and close survivors with 变异杀伤 cases, recording the run in mutation-report.yaml. Report-only on failures — this skill never reopens a task; reopening is a user verdict run by a human via .claude/skills/diy-tools/scripts/runner.py --reopen-failed. Invoked by runner.py after each done task; standalone invocation with a task ID is equivalent.'
# ↑ 中文：编码后补测——任务到 `已完成` 后，对实现面跑项目覆盖率工具链，分类未覆盖分支 / 条件组合 / 路径，按稳定的每-AC TC ID 把互补用例追加进 test-plan.yaml，执行并逐条回写 status，判定（`通过` / `失败` / `已跳过`）落在 sprint.yaml 该任务的 `augment` 字段上。变异工具链在场时（test-plan 的 static_checks 链里用户确认的变异条目，或本会话用户显式给出的命令）另对沙箱副本跑一遍，用 `变异杀伤` 用例收口幸存体，运行记录落 mutation-report.yaml。失败只出判定——本技能绝不重开任务；重开是用户裁断，由人手动执行 `.claude/skills/diy-tools/scripts/runner.py --reopen-failed`。runner.py 在每个 `已完成` 任务后调用本技能；带任务 ID 独立调用等价。
---

# diy-augment — 编码后补测（覆盖率驱动追加 TC）

你是覆盖率缺口的收口者。输入：一个 `已完成` 任务及其实现面。产出：追加进 `{output_dir}/test-plan.yaml` 的用例——杀掉编码前计划预见不到的故障。绝不发明覆盖：每条追加用例绑定既有 AC、引用驱动它的覆盖证据、声明自己的 `kill_target`。零缺口 → 不写用例、**判定照落**。九种编码前设计技法归 `diy-test-design`；重开任务归用户裁断——本技能只出判定。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（note、收尾播报）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 载入 `{output_dir}/sprint.yaml`，定位激活提示点名的任务。硬门：该任务在 `tasks[]` 里的 `status` 必须是 `已完成`（任务级字段——`project.status` 是文件水位线，不是本门的读取层）；补测只在编码后发生，其他状态 → 一行说明并停下，零产出。任务 `augment` 字段若在场（`通过` / `失败` / `已跳过`）＝ 既往判定：本轮与它对账，不重复造用例。
3. 输入：`{output_dir}/test-plan.yaml`（用例、`static_checks` 链、覆盖证据的落点）与 `{output_dir}/stories.yaml`（AC 索引）；解析该故事的 AC 集合与既有每-AC TC 序列（每个 AC 当前的最大 seq）。
4. 写范围恰为四个面（`test-plan.yaml` 的追加用例及其 `status`、改既有用例时的顶层 `revisions` 追加条、本任务的 `augment`、本任务的 `test_refs`、`mutation-report.yaml`）；任务的 `status` 与 `evidence` 都不在写面——细则见规则第 1、9、10 条。

## 工作流

全局步骤纪律：一次给全（front-load）——本轮输出整块给出，不在步骤中间提问；要停下时一行说明原因。

1. 建覆盖率基线：对实现面跑项目覆盖率命令（工具链取值路径见规则第 2 条）。工具缺失或未获许可 → 落 `augment: 已跳过`、一行说明原因并停下；不安装任何东西。
2. 分类缺口：每条未覆盖项按规则第 3 条落技法；低于项目覆盖率门槛的条目丢弃，除非它落在 AC path 上（门槛取值顺序与 `AC path` 判据见规则第 4 条）。**变异工具链在场时，另对沙箱副本跑一遍（作用域限本任务实现面），幸存体照同法分类（`变异杀伤`；等价体登记待裁、永不成为用例），运行落 `{output_dir}/mutation-report.yaml`——工具链缺席是一行 note，不是判定。** 重跑（任务已带判定）先对账：等价用例就地更新，不重复追加。
3. 推导并追加用例到 `test-plan.yaml`（`status: 待办` + `technique` / `kill_target` / `note` / 具体可执行的 `steps`；schema 同 `diy-test-design`）；新 TC ID 并入本任务的 `test_refs`。
4. 执行用例：逐条回写 `通过` / `失败`，再把任务判定（`通过` / `失败` / `已跳过`）落在 `augment` 上。
5. 渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。收尾报计数：按技法追加的用例数 / 通过 / 失败 / 判定，以及剩余缺口。

## 结构

`{output_dir}/mutation-report.yaml`（本技能自有产物；只在真跑过变异时写）：

```yaml
project: {name, status: 草稿|已定稿}
runs:
  - date: YYYY-MM-DD          # 该次动作的日子，不随 project.updated 变
    task: S-x
    scope: <本任务实现面>       # 本次采样的实现面（开场声明的那一行）
    killed: <int>
    total: <int>
    score: <killed / (total − equivalents)>   # 等价体不计入分母
    survivors: [{mutant, file, line}]        # 没被杀掉的变异体——每条派生一条 变异杀伤 用例
    equivalents: [{mutant, reason}]          # 等价体（幸存体的子集）——供用户裁定，永不成为用例
revisions: []                 # {date, change, reason}——改既有条目时追加
```

追加用例落 `{output_dir}/test-plan.yaml`（schema 归 `diy-test-design`，本技能不重定义）：只写它的后四值技法 `覆盖分支` / `MC-DC 覆盖` / `白盒路径` / `变异杀伤` 加 `status` / `kill_target` / `note` / `steps`；`priority` 沿用所在 AC 的既有档位。
`{output_dir}/sprint.yaml` 只写两个字段：本任务的 `augment: 通过|失败|已跳过`，以及并入追加 TC ID 的 `test_refs`。

## 规则

1. **写范围恰为四个面。** `{output_dir}/test-plan.yaml`（追加的用例及其 `status`、改既有用例时顶层 `revisions` 追加条）、本任务的 `augment` 字段、本任务的 `test_refs`（并入追加 TC ID）、`{output_dir}/mutation-report.yaml`（只在真跑过变异时）。任务的 `status` / `blocked_reason` / `note` 永不触碰；`stories.yaml`、源码与其他产物零写入。
2. **覆盖率工具链与实现面。** 工具链取值路径 ＝ `{output_dir}/test-plan.yaml` 的 `static_checks` 链（链的定义源在 `diy-test-design`，此处只引用不重定义）；链里没有覆盖率条目 → 一行 note，落 `已跳过`。实现面 ＝ `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" trace --json` 回执 `references[].file` 里引用了本任务 `S-x` 的文件集合（扫面用 `--src` 收窄），加上 `git status --porcelain` 里本任务的未跟踪实现文件；开场一行声明本次采样的实现面。只有被工具报出的缺口才成用例——从不被报出的未测项不在范围内。
3. **技法映射（四值）。** 未覆盖分支 → `覆盖分支`；未覆盖条件组合（MC/DC）→ `MC-DC 覆盖`；未覆盖执行路径 → `白盒路径`；变异幸存体 → `变异杀伤`。编码前的九种设计技法归 `diy-test-design`，此处永不选。`priority` 沿用该 AC 的既有档位——映射（`必须`→P0 / `应该`→P1 / `可选`→P2 / NFR 引用的 AC→P0）唯一权威出处 = `diy-test-design`，只引用不重定义。
4. **覆盖率门槛取值顺序与 `AC path`。** 门槛顺序：① 用户本次给出的阈值 > ② `{output_dir}/test-plan.yaml` 的 `static_checks[]` 里覆盖率条目命令自带的阈值 > ③ 都没有 → **不过滤**（全量缺口入列），并把「本项目无覆盖率门槛」一行记进收尾。`AC path` ＝ 该未覆盖项位于某条 AC 的 TC `steps` 点名的文件/符号内，或位于带该 AC `# trace:` 行的文件内；落在 AC path 上的条目即使低于门槛也保留。
5. **变异：取值路径、兜底与沙箱基线。** 配置载体 ＝ ① `{output_dir}/test-plan.yaml` 的 `static_checks[].tool` 中用户确认为变异工具的条目，或 ② 本会话里用户显式给出的变异命令；两者皆无 → 按「未配置」处置（一行 note，不写 `mutation-report.yaml`、不设判定）。沙箱 ＝ 该命令自身建立的一次性副本（本技能不复制工作树，**永不跑在工作区**）；执行前用 `git status --porcelain` 留基线，执行后工作区出现改动即停并报。幸存体 = 代码被执行过、却没有断言区分对错的缺口——一条派生一条用例（变异的故障即其 `kill_target`）。等价体不进用例：登记在该 run 的 `equivalents[]`（`mutant` + `reason`）供用户裁定，且不计入 `score` 分母：`score = killed / (total − equivalents)`。
6. **序列续号、`kill_target` 必填、零缺口不写用例。** 新 TC ID ＝ AC ID 去前缀 + 该 AC 的下一个 seq（AC-5.1 已有 TC-5.1.1 → TC-5.1.2）；永不重编号、永不复用。`kill_target` 点名用例要杀的具体故障——失败也无法把正确代码与该故障区分开的用例是装饰品，砍掉。**零缺口 → 不写用例、只落判定**；绝不写「为将来保底」的猜测性用例。
7. **判定必落。** 每轮结束恰落一个 `augment` 值：`通过`（执行的用例全绿）/ `失败`（至少一条红——缺陷为真、等用户裁断）/ `已跳过`（覆盖率工具链不可用或未获许可；什么都没执行）。判定是 runner 的汇报依据、也是 `--augment-only` 的恢复点——缺判定与「从未跑过」不可区分。
8. **失败只出判定。** 用例上写 `status: 失败`、任务上落 `augment: 失败`、收尾列出该用例的复现证据（命令 + 实测 vs 预期），然后停下。任务的 `status` 保持 `已完成`——本技能绝不重开任务。重开是用户裁断：由**人手动执行** `python "{project-root}/.claude/skills/diy-tools/scripts/runner.py" --project-root "{project-root}" --reopen-failed`（安装形态 `.claude/skills/diy-tools/scripts/runner.py`）批量重开、修复、重新补测。
9. **证据交接点。** 追加用例的 `evidence`（红/绿行）不是本技能的写面：它由**下一次 `进行中` 周期**经 `diyc.py green` 写入（该命令只对 `进行中` 任务生效）——唯一写者是 `diy-dev` / `diy-build-loop`。故 `已完成` 现场的追加件暂缺 `evidence` 是正常状态：`diy-review` L3 报出的 `EVIDENCE_MISSING` 是**信号**（下一次修复周期补齐），不是豁免、也不是本技能可代写的字段——绝不编造 red。
10. **重跑对账、永不重复。** 与既有追加用例等价（同 AC、同技法、同 `kill_target`）的用例就地更新——从本轮刷新其 `status`，绝不追加孪生；新 ID 只给真正的新缺口；判定被本轮结果覆盖。就地更新即改既有条目：往 `{output_dir}/test-plan.yaml` 顶层的 `revisions` 追加一条 `{date, change, reason}`（`change` 引用 `TC-x.y.z` 与刷新了什么）——引擎不写该键，由本技能补写。
11. **证据进 `note`。** 每条追加用例的 `note` ＝ 驱动它的覆盖证据（工具 + 未覆盖项；`变异杀伤` 用例 ＝ 变异体身份与故障），用 `document_output_language` 的散文写；机器锚点（命令、ID）逐字保留。
12. **渲染与降级。** 渲染命令需要宿主 Python 有 PyYAML；`ModuleNotFoundError` 时报错并建议 `pip install pyyaml`，绝不静默降级。覆盖率工具、用例执行、渲染三处的失败一律降级为一行报告——绝不阻断，也绝不回退或作废已落盘的写回。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
