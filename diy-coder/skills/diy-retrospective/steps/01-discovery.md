# Step 1 — epic 发现与收尾校验

Progress: `[epic 发现] → 深度分析 → 连续性 → 回顾讨论 → 行动 → 就绪度 → 收尾`

**Read (input):** `{output_dir}/epics.yaml` 与 `{output_dir}/stories.yaml`（epic 清单）；其后跑出的 `collect` 回执。
**Write (output):** `{output_dir}/retrospective.yaml` 里的草稿记录（`id` / `epic` / `status` / `date` / `partial` / 各空节）。

## 选 epic——三级，按序（源自源技能的 step-1 选取逻辑）

1. **引擎侧建议。** 扫 `stories.yaml`，取编号最大、且至少有一条 `status: 已完成` 故事的 epic——那就是刚做完的 epic；作为建议呈现。
2. **用户说了算。** 用户点名另一个 epic → 就是它，不再争论。
3. **什么都扫不到。** 列出任何有 `已完成` 故事的 epic，附 `done/total` 计数作为编号选项并问。绝不凭空猜一个 epic。

第 3 级若**列表为空**（全库没有任何 `已完成` 故事）→ 一行说明 + **零写入停止**，按引擎 `gate.route` 的口径点名 diy-epics-stories / 先把故事做完（diy-dev）——不要凭名字造一个 epic 去撞门。

## 跑确定性开场

```
python "{project-root}/.claude/skills/diy-retrospective/scripts/retrospective.py" collect --epic <E-x> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

引擎管门与数字：

- **门（exit 1，零产出）：** `{output_dir}/stories.yaml` 与 `{output_dir}/epics.yaml` 在场且各自 `project.status: 已定稿`；epic 在 `epics.yaml` 可解析；其下至少一条 `已完成` 故事。被拒时转述回执的一行理由与 `gate.route`（diy-epics-stories），然后停下——拒绝永不变成记录。
- **其余一切取回执，绝不手工重读产物：** `stories`（total / done / pending）、`metrics`、`bugs`、`coverage`、`prev_actions`、`first_retro`、`next_epic`。这就是源技能「读遍每个故事文件再数」那一步的 diy 化——结构化产物加一趟机械跑批，不是手工点数。

## 收尾校验与 partial 分支（源技能 step-1，三选项）

读回执的 `stories[].pending`：

- **空** → epic 已收尾；说明后继续。
- **非空** → epic 未完成。引擎已发出 `PENDING_DECISION` warning。把选择交给用户：
  1. **先把剩余故事做完**（推荐）→ 停在此处，什么都不写，点名 pending 的故事 ID 并路由 diy-dev / diy-build-loop。
  2. **部分回顾** → 仅在用户明确确认后；草稿写 `partial: true`，pending 的 ID 记进 `challenges`。
  3. **改刷新 sprint 队列** → 跟踪已不符现实时路由 diy-sprint。

`partial: true` 是用户的裁定，绝不是主持人的便利。同 epic **只有一条** `RT-###`：partial 之后补做完整 retro 时，在**原记录**上原地更新（`partial` 改 `false`、`metrics` 用新一次 `collect` 回执重取、`revisions` 追加 `{date, change: partial → full, reason}`），不新铸记录。

## 起草记录

往 `{output_dir}/retrospective.yaml` 追加一条记录（文件缺席时先建：`project: {name, created, updated}`——`name` 取 `diy-coder.yaml` 的 `project.name`——加空的 `retros` 列表与 `revisions: []`）：

```yaml
  - id: RT-001                    # 下一条 = 现有最大值 + 1，三位零填充；永不重编号、永不复用
    epic: E-x                     # 照抄回执
    status: 草稿
    date: YYYY-MM-DD              # 本条动作的日子（今天）
    partial: false                # 仅用户确认的部分回顾写 true
    metrics:                      # 照抄回执，绝不凭记忆重打
      stories_total: 0
      stories_done: 0
      rounds_total: 0
      blocked_count: 0
      augment_fail: 0
      bugs: {功能型: 0, 非功能型: 0}
    patterns: []
    wins: []
    challenges: []
    insights: []
    action_items: []
    prep_items: []
    critical_path: []
    readiness: {testing: '', deployment: '', acceptance: '', tech_health: '', blockers: ''}
    next_epic: {}                 # 第 3 步填
```

机器锚点（ID、计数、文件名）一律照抄回执——绝不凭眼睛重算。`partial: true` 蕴含 epic 未完成；未完成却没有 `partial: true` 是起草错误。

## 铺陈 epic（源技能 step-5 的指标块）

任何讨论之前，用一条消息把 epic 摆出来——全部取自回执，绝不重打：

- 完成度：`stories_done / stories_total`（设了 `partial` 时一并给出），pending 的 ID；
- 交付形态：`rounds_total`、`blocked_count`、`augment_fail`、按类别分的缺陷（`bugs`）；
- 质量形态：AC 覆盖（`coverage`）与 epic 的缺陷清单（按 ID）；
- 接下来是什么：`next_epic` 一行（id / title / stories 数）——预览在第 3 步分析。

叙述纪律：数字配上下文才成叙述（「6 个任务烧了 5 轮」，不是「5」）。第 2 步用四副镜片读完之前，不要对指标先行评论。

## 播报与下一步

读 `./02-deep-analysis.md` 并照做。
