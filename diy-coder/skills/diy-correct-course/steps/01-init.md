# Step 1 — 触发确认与立案

Progress: `[立案] → 分析 → 改动 → 提案 → 路由 → 收尾`

**Read (input):** 激活段 `collect` 回执；用户对问题的描述；来自 diy-retrospective 时读 `{output_dir}/retrospective.yaml` 的 `significant_changes[]`。
**Write (output):** `{output_dir}/change-proposal.yaml` 的草稿记录（`id` / `date` / `status` / `trigger` / `mode` / `scope` / 空列表）。

## 先看门（零产出拒绝）

`collect` 已经跑过门。exit 1 时本轮在开始前就结束：转述回执的一行理由与它的 `gate.route`（`diy-prd` / `diy-epics-stories`），停下，什么都不写。拒绝永不变成记录；上游文档缺席，绝不靠「改去分析别的」绕开。

## 确认触发

问要导航什么，然后听——用户原话就是记录的 `trigger`：

- **要改的是什么？** 一句话，先按用户的说法记。
- **什么显示出来的？** 报错、干系人的信号、实施中发现的硬约束——它成为锚定分析的证据。
- **哪条故事暴露的？** 故事 ID（存在时）带进第 2 步。

来自 diy-retrospective 的交接，**具名来源**是 `{output_dir}/retrospective.yaml` 的 `significant_changes[]`：每条 `{change, impact, recommended_action}`，diy-retrospective 记录级 `id` 形如 `RT-yy`。整批**只开一条 proposal**——N 条变化进同一条记录的 `impacts`（必要时加 `edits`），绝不拆成 N 条记录；`trigger` 写「来自 <RT-id> 的 significant_changes：<各条 change 的摘句>」，并把 `recommended_action` 与 `impact` 带进 `why` / `rationale` 的取材面。diy-retrospective 那批条目本身就是证据，不再要求用户重述一遍。

来自 diy-investigate 的交接，**具名来源**是 `{output_dir}/investigation.yaml` 的 `cases[]`——用户点名或按 `slug` / `id` 命中的那一条，取值键 `handoff_brief` / `conclusion`（`text` / `confidence` / `fix_direction`）/ `evidence[]`（`grade` / `ref`）。引用它、绝不转抄，证据分级口径归 diy-investigate。

**触发不清就 HALT**：要用户给出「要改什么、为什么改」的具体细节，加至少一条具体证据（报错 / 信号 / 约束）。没有具体证据的触发不开工，也绝不拿自己的假设填空——建立在猜测触发上的提案，会把真实工作路由到错处。

## 定 mode

- **`增量`**（推荐）——每处改动提案单独呈现、单独打磨，再做下一处。
- **`批量`**——全部改动提案收齐，第 3 步末尾一次性呈现。

记进 `mode`；它只改第 3 步的呈现方式，别的都不动。

## 立案

往 `{output_dir}/change-proposal.yaml` 追加一条记录（文件缺席时先建：`project: {name, created, updated}`——`name` 取 `diy-coder.yaml` 的 `project.name`——加空的 `proposals` 列表与 `revisions: []`）：

```yaml
  - id: CP-001                  # 下一条 = 现有最大值 + 1，三位零填充；永不重编号、永不复用
    date: YYYY-MM-DD            # 本条动作的日子（今天）
    status: 草稿
    trigger: <用户原话；来自 diy-retrospective 时写 RT-id + change 摘句>
    mode: 增量                  # 或 批量
    scope: 轻微                 # 暂定；第 5 步定夺，终门强制它与 handoff.route 配对
    impacts: []
    edits: []
    open_questions: []
```

暂定的 `scope` 只为让记录在起草各步里保持可加载；第 5 步在终门前改正它。

## 播报与下一步

读 `./02-analysis.md` 并照做。
