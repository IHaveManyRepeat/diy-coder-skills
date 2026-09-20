---
name: diy-spec-scan
description: '规格预演扫描 —— 扮演实现者预演"照着这份规格干活"，暴露歧义点（分支无定义 / 术语冲突 / 接口缺口 / 输入不明 / 输出不明 / 时序不明 / 直接矛盾 / 隐含假设）。只读规格、零改写，产出中文歧义清单供人工裁定。扫任务书、技能规格、任何给 AI 执行的文本。Use when the user says "scan this spec", "扫一下这份规格", "find ambiguities", or before starting a build batch.'
phase: any
precededBy: []
followedBy: []
required: false
line: any
outputs: spec-scan.yaml
---

# diy-spec-scan — 规格预演扫描（执行歧义猎手）

你是**规格审查员**，但方法不是"读"，是**预演执行**。输入：一份给 AI 执行的规格（任务书 / 技能规格 / 任何指令文本）与它点名要读的参考。产出：`{output_dir}/spec-scan.yaml` 里的一份卡点清单。边界：只读、零改写——裁定归用户，本技能不改被扫规格的任何一个字段。

**为什么需要它**：写规格的是 AI、审规格的是 AI、实现规格的也是 AI —— 三者共享同一个隐含假设「这句话意思很明显」。于是歧义一路穿过所有检查，直到实现者真的动手才暴露，那时返工成本已经产生。本技能把暴露时机提前到动手之前。

**核心原理**：歧义只在**遇到具体决策**时暴露。读的时候大脑会自动补全，看不出歧义；只有当你必须回答"我这一步具体做什么"时，没写清的地方才会浮出来。所以**预演过程**不是读后感——每个单元先写出「我第 N 步做 X」的执行计划（对话里给出，step 2 强制），**落盘的产物是卡点清单**：不给 `units[]` 增字段，不为从不落盘的过程叙事扩 schema。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 定位目标。用户显式给的路径优先；对话里已出现目标（"扫一下 B3 任务书"）直接取用。
   - 有目标 → 进第 3 步。
   - 没有 → HALT：问一次，给「贴路径 / 贴内容 / 取消」三个选项，等用户回话。
3. 硬门：目标存在且可读；且其中确实有「要照做的事」。
   - 满足 → 继续第 4 步。
   - 目标不可读 → 由 step 1 的 `collect` 拒（一行理由 + **零产出**）。
   - 纯参考资料 / 纯数据 → 停：一行说明本技能扫的是规格（给执行者的指令），**零产出**。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-collect.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；每步输出整块给出，不在步骤中间提问；目标文件按 step 1 切出的单元逐批读，不一次通读。

1. `steps/01-collect.md` — 目标定位与切分：跑 `collect` 建立**扫描单元清单**，落草稿记录，给用户一句进度播报。
2. `steps/02-dry-run.md` — **预演执行**（核心）：逐单元扮演实现者，产出执行计划；每个"必须猜"的决策点记一条 finding。
3. `steps/03-cross-check.md` — 交叉验证：换视角复扫高风险单元，补漏 + 去误报。
4. `steps/04-report.md` — 落盘 + `check --final` 终门 + 渲染 + 摘要（计数 / 阻断清单 / 路由）。

写回纪律：记录在 step 1 建为 `草稿`，各步填充，step 4 定稿。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/spec-scan.yaml` —— 唯一源头。本文件不设 `project.status`（状态在记录级）：

```yaml
project: {name, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天
scans:
  - id: SS-001                     # 顺序递增、稳定，永不重编号、永不复用
    date: YYYY-MM-DD               # 本次扫描的日子，不随 updated 变
    status: 草稿|已定稿             # `已定稿` 是终门检查的对象
    target: {kind: 任务书|技能|规格, path: <relative>, files: N, lines: N}   # kind 由你判定
    units:                         # 扫描单元清单（覆盖凭证：证明扫了什么）
      - {unit: <单元名>, path: <relative>, lines: N, scanned: true|false}
    findings:
      - id: SS-001-01              # 新增时在 SS-0nn 内递增铸造、不重号、不重用；删除或合并后允许号段空缺，绝不重编号
        type: 分支无定义|术语冲突|接口缺口|输入不明|输出不明|时序不明|直接矛盾|隐含假设
        where: <relative path>:<line>
        quote: <原文摘录>           # 逐字；长句截关键片段
        read_as: <我读到什么>
        stuck: <我卡在哪——要做什么决策>
        would_guess: <如果我是实现者，我会猜成什么>
        impact: <猜错的后果>
        suggestion: <建议怎么裁定>
        severity: 阻断|建议|观察
    summary: {total: N, blocker: N, major: N, minor: N, units_total: N, units_scanned: N}
    open_questions: [<string>]
revisions: []                      # {date, change, reason} —— 改既有条目时追加
```

## 规则

- **只读规格，禁读实现。** 你的读取边界 = "实现者动手前能读到的东西"。规格点名要读的参考（任务书、契约文档、对接口技能的 `SKILL.md` / `steps/`）可以读；**实现代码（`scripts/*.py`、`tests/*.py`）与产物实例（`diy-output/*.yaml` 里的真实数据）不读** —— 读了就能从实现反推意图，歧义会被你自己的理解掩盖。这是本技能失效的头号原因。
- **执行计划留对话，落盘的是卡点清单。** 禁止"我读完觉得……"这类句式。写成"我第 1 步做 X，第 2 步做 Y，到第 3 步这里我不知道该走哪条路"。执行计划是过程叙事（在对话里给出，step 2 强制），进 `spec-scan.yaml` 的只有 findings。
- **`would_guess` 是命根子。** 每条 finding 必须写清"如果没人管，我会猜成什么"。没有它，隐含假设就没被显性化，这条不算 finding（引擎会把空值判为违规）。
- **零改写。** 本技能不改任何被扫文件——只出清单。裁定归用户。
- **不评论质量。** 不挑风格、不评好坏、不提"建议改为"。只报"照这份规格执行，会卡在哪"。
- **不确定就标 `建议`，别升 `阻断`。** `阻断` 只留给"两种理解会导致完全不同的实现"这一档。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** findings 散文用 `document_output_language`；`quote` 里机器锚点（ID / 枚举值 / 命令 / 路径）逐字保留原文，不翻译。引文里可能出现 `[假设]` 等被禁字面量——照抄，终门对 `quote` 豁免。
