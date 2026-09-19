# Step 1 — 定向

Progress: `[定向] → 带看 → 风险详查 → 亲手验证 → 拍板`

**Read (input):** 激活段 `target` 回执；其 `spec` 字段点名的规格（存在时）；diff 与变更文件。
**Write (output):** 定向消息；`{output_dir}/checkpoint.yaml` 的草稿记录（`id` / `date` / `change_type` / `target` / `mode`）。

## 定位变更

激活之前的对话就是起点——不是白纸。定位分两层。

**你的层——最近的对话。** 扫最近几条消息找 commit、range、分支、PR 线索或对变更的描述。把 commit / range / 分支线索变成显式 `--ref` 交给引擎；**PR 线索由你先在本地解析**（`gh` 可用时走 `gh pr view` 取 head SHA 或分支；解析不了就问用户要 SHA 或分支）——引擎只吃本地 ref。单有规格路径不是引擎 ref，带进下面的规格配对即可。运行：

```
python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" target --project-root "{project-root}" --output-dir "{output_dir}" [--ref <commit|range|branch>] --json
```

**引擎的层——3 级机械判定加拒绝：**

1. 显式 `--ref` → `source: 显式指定`
2. `sprint.yaml` 里 `status: 待审查` 的任务 → `source: 冲刺任务`（可解出时带 `story` 与 `spec`）。按候选数分支：恰好一个 → 建议它并请用户确认；多个 → 编号列出供选；零个 → 落到 git 层。
3. git 工作区 / HEAD diff → `source: Git 提交`
4. 三级皆无 → exit 1 + 一行拒绝

从回执取 `candidates` / `source` / `story` / `spec` / `mode` / `diff_stat`。不在这套级联之外提问。

exit 1 时本轮即结束：转述拒绝的一行理由与它的路由（给一个显式 ref，或先跑 diy-dev / diy-review），停下，零写入——拒绝是零产出退出，不是一条记录。

## 规格配对（Enrich）

配对是机械的，唯一入口是冲刺任务层：`sprint.yaml` 里 `status: 待审查` 的任务带 `story` 锚，该 id 解到 `stories.yaml` 的同 id 条目，它就是这次变更的规格（回执 `spec` 即该文件的路径）；解不到 → `spec` 为空、`mode` 落 `裸提交`。

- 本生态没有 `baseline_commit` 之类的规格 frontmatter——不要去找；显式 `--ref` 与 git 层候选都没有规格配对面，diff 基线一律取引擎的 git 层（工作区 / HEAD）。
- 用户单独给的规格路径不是引擎 ref，不进 `--ref`——当附加材料带进带看。

## 定 `mode`

`mode` 取自回执；此处只确认，并让它驱动第 2–4 步：

1. **`仅规格`** —— 有规格（`stories.yaml` 的 story 条目），但该条目不带 `suggested_review_order` 字段。意图来源：条目的 `narrative`（配合 `acceptance_criteria`）。
2. **`裸提交`** —— 无规格。意图来源：提交信息。信息过短（少于 10 词）→ 扫 diff 找主要变更形态，起草一句话意图。回执会报出你处在哪种情形：`target.inferred: true`——意图从 diff 推断；`false`——提交信息本身承载意图（≥10 词或显式提交引用），无可推断；`null`——不可判定（比如 WORKTREE 或 range 目标），与 `inferred_reason` 字符串配对给出。推断来的意图在输出里标 `[inferred]` 供人纠正；`null` 情形把 `inferred_reason` 用大白话转述——意图取自 diff，需人工核对。
3. **`全程轨迹`** —— **本生态不适用（不可达）**：引擎只在 story 条目带 `suggested_review_order` 字段时才判它，而全套件无人产出该字段（`diy-epics-stories` 的 stories schema 里没有它）→ 引擎永不产出这个值。回执若给出它，照抄回执值并在定向消息里说明异常——规格是 YAML，别去里面找 markdown 段。

记 `change_type`——承载「人怎么称呼这次变更」的记录字段：`PR`、`commit`、`branch`，或人自己的词（如 `认证重构`）；含糊时缺省 `change`。第 2–5 步的提示语都以「这个 {change_type}」收尾，值从记录里读，使说法贯穿整轮。

## 产出定向消息

**意图。** 来自 story 条目的 `narrative` 时：原样展示，不论长短——它本来就是照简练写的。来自其他来源（提交信息、缺陷报告、人自己的话）时：≤200 token → 原样；更长 → 压到 ≤200 token 并给出全文出处（文件路径或 URL）。格式：`> **意图：** {意图摘要}`。

**变更面统计。** 从回执的 `diff_stat` 与 diff 内容推：

- **变更文件数** —— 数 `git diff --stat`。
- **触及模块数** —— 变更路径里去重后的顶层目录数。
- **逻辑行数** —— 增 / 改行，剔除空行、import 与格式化；带 `~` 表示约数。
- **跨界次数** —— 跨越一个以上顶层模块的改动；单模块写 `0`。
- **新公开接口数** —— diff 里新增的 export、端点、公开方法；没有写 `0`。

算不出来的指标就省掉，不要猜。

整块消息呈现：

```
[定向] → 带看 → 风险详查 → 亲手验证 → 拍板

> **意图：** {意图摘要}

N 个文件变更 · M 个模块被触及 · ~L 行逻辑 · B 次跨界 · P 个新公开接口
```

## 兜底轨迹生成（仅在 story 条目不带 `suggested_review_order` 时）

生成的轨迹质量低于作者产出的轨迹，但远好于没有。从 diff 建：

1. 通读变更文件——只看 hunk 会漏掉它周围的意图。总量超过约 50k token 时，通读 hunk 最大的那几个文件，其余看 hunk。
2. 认 2–5 个关注点：能解释一组变更**为什么**的连贯设计意图。优先功能分组与架构边界，不按文件切。有规格在场时，关注点的锚就是 story 条目的 `narrative`（配合 `acceptance_criteria`）。一个关注点也行——不要硬凑分组。
3. 每个关注点给 1–4 个 `path:line` 停靠点——入口、决策点与跨界点优先于机械改动。入口最先（杠杆最大的停靠点）；关注点内部按「每条建立在前一条之上」排序；外围（测试、配置、类型）收尾。
4. 每个停靠点这样写：

```
**{关注点名}**

- {一行框定，≤15 词}
  `src/path/to/file.ts:42`
```

只有一个关注点时省掉粗体标签，直接列停靠点。

播报它——「我为这个 {change_type} 自建了一条带看轨迹（未找到作者产出的轨迹）：」——再呈现轨迹。**兜底只决定本轮的呈现顺序，不写回 `mode`**：`mode` 始终照抄引擎回执；下游按「本轮是否已生成轨迹」分支。

diff 取不到时（git 不可用）：一行说明「无法生成轨迹——git 不可用。」，**零写入退出**，路由同引擎级联全落空（给一个显式 ref，或先跑 diy-dev / diy-review）。绝不凭规格与意图凭空带看。

## 写草稿记录

往 `{output_dir}/checkpoint.yaml` 追加一条记录（文件缺席时先建：`project: {name, created, updated}`——`name` 取 `diy-coder.yaml` 的 `project.name`——加空的 `checkpoints` 列表与 `revisions: []`）：

```yaml
  - id: CK-001                 # 下一条 = 现有最大值 + 1，三位零填充；永不重编号、永不复用
    date: YYYY-MM-DD           # 本条动作的日子（今天），不随 updated 变
    change_type: {人怎么称呼它，如 commit|branch|PR|认证重构}
    target: {ref, source, story?, spec?, inferred?}   # 照抄回执，绝不凭记忆重打
    mode: 仅规格|裸提交          # 照抄回执；`全程轨迹` 本生态不适用（无产出方，永不出现）
    concerns: []
    risks: []
    observations: []
    decision: ''               # 起草期未定
    reason: ''
    next: ''
    status: 草稿
```

`inferred` 对应回执的三种值：`true` → 写 `inferred: true`；`false` → 省略该键（标记只为 `true` 而写，缺席是常态，绝不无中生有）；`null`（不可判定——比如 WORKTREE 或 range 目标）→ 同样省略该键，回执带 `inferred_reason` 时用大白话转述——意图取自 diff，需人工核对。

## 播报与下一步

读 `./02-walkthrough.md` 并照做。人在任一步（本步或后续任一步）给出拍板信号时，先与其确认意图，再改走 `./05-wrapup.md`。
