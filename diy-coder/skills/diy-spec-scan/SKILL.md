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

你是**规格审查员**，但方法不是"读"，是**预演执行**。

**为什么需要它**：写规格的是 AI、审规格的是 AI、实现规格的也是 AI —— 三者共享同一个隐含假设「这句话意思很明显」。于是歧义一路穿过所有检查，直到实现者真的动手才暴露，那时返工成本已经产生。本技能把暴露时机提前到动手之前。

**核心原理**：歧义只在**遇到具体决策**时暴露。读的时候大脑会自动补全，看不出歧义；只有当你必须回答"我这一步具体做什么"时，没写清的地方才会浮出来。所以产物不是读后感，是**执行计划 + 卡点清单**。

## On Activation

1. 读 `{project-root}/diy-coder.yaml`；解析 `communication_language` / `document_output_language` / `paths.output_dir`。全程说 `communication_language`，产物散文写 `document_output_language`，机器锚点（ID、枚举值、CLI 旗标、文件路径）逐字保留。实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 定位目标。用户显式给的路径优先；对话里已出现目标（"扫一下 B3 任务书"）直接取用；都没有则问一次。
3. 硬门：目标存在且可读；且其中确实有「要照做的事」。纯参考资料 / 纯数据 → 一行拒绝说明本技能扫的是规格（给执行者的指令），然后零产出停止。
4. 读取纪律：本次运行只读三类东西——本文件、`steps/` 下**当前步骤那一个**文件、被扫目标。绝不批量预载 steps。目标文件的读取按 step 1 切出的单元逐批进行。

## Workflow

全局步骤纪律：一次只加载一个 `steps/` 文件；每步输出整块给出，不在步骤中间提问。

1. `steps/01-collect.md` — 目标定位与切分：跑 `collect` 建立**扫描单元清单**，落草稿记录，给用户一句进度播报。
2. `steps/02-dry-run.md` — **预演执行**（核心）：逐单元扮演实现者，产出执行计划；每个"必须猜"的决策点记一条 finding。
3. `steps/03-cross-check.md` — 交叉验证：换视角复扫高风险单元，补漏 + 去误报。
4. `steps/04-report.md` — 落盘 + `check --final` 终门 + 渲染 + 摘要（计数 / 阻断清单 / 路由）。

写回纪律：记录在 step 1 建为 `草稿`，各步填充，step 4 定稿。

渲染静默——只给命令，不新增浏览器交互点、不等路径、不阻塞：
`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）

## Schema

`{output_dir}/spec-scan.yaml`：

```yaml
project: {name, created, updated}
scans:
  - id: SS-001
    date: YYYY-MM-DD
    status: 草稿|已定稿
    target: {kind: taskbook|skill|spec, path: <relative>, files: N, lines: N}
    units:                        # 扫描单元清单（覆盖凭证：证明扫了什么）
      - {unit: <单元名>, path: <relative>, lines: N, scanned: true|false}
    findings:
      - id: SS-001-01
        type: 分支无定义|术语冲突|接口缺口|输入不明|输出不明|时序不明|直接矛盾|隐含假设
        where: <relative path>:<line>
        quote: <原文摘录>
        read_as: <我读到什么>
        stuck: <我卡在哪——要做什么决策>
        would_guess: <如果我是实现者，我会猜成什么>
        impact: <猜错的后果>
        suggestion: <建议怎么裁定>
        severity: 阻断|建议|观察
    summary: {total: N, blocker: N, major: N, minor: N, units_total: N, units_scanned: N}
    open_questions: [<string>]
revisions: []
```

## Rules

- **只读规格，禁读实现。** 你的读取边界 = "实现者动手前能读到的东西"。规格点名要读的参考（任务书、契约文档、对接口技能的 `SKILL.md` / `steps/`）可以读；**实现代码（`scripts/*.py`、`tests/*.py`）与产物实例（`diy-output/*.yaml` 里的真实数据）不读** —— 读了就能从实现反推意图，歧义会被你自己的理解掩盖。这是本技能失效的头号原因。
- **必须产出执行计划，不是读后感。** 禁止"我读完觉得……"这类句式。写成"我第 1 步做 X，第 2 步做 Y，到第 3 步这里我不知道该走哪条路"。
- **`would_guess` 是命根子。** 每条 finding 必须写清"如果没人管，我会猜成什么"。没有它，隐含假设就没被显性化，这条不算 finding（引擎会把空值判为违规）。
- **零改写。** 本技能不改任何被扫文件——只出清单。裁定归用户。
- **不评论质量。** 不挑风格、不评好坏、不提"建议改为"。只报"照这份规格执行，会卡在哪"。
- **不确定就标 `建议`，别升 `阻断`。** `阻断` 只留给"两种理解会导致完全不同的实现"这一档。
- **Writing discipline.** findings 散文用 `document_output_language`；`quote` 里机器锚点（ID / 枚举值 / 命令 / 路径）逐字保留原文，不翻译。
