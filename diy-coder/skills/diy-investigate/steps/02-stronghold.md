# Step 2 — 据点确立与立案

Progress: `确认输入 → [据点] → 边界 → 推理 → 源码追踪 → 结案`

**Read (input):** 第 1 步确认过的输入集；`collect` 回执（`vcs.commits` 近期变更、`files` 区域清单含行数、`candidates` 同名族并行实现与测试文件）。
**Write (output):** `{output_dir}/investigation.yaml` 里的记录草稿——`id` / `slug` / `date` / `status` / `mode` / `evidence_light` / `handoff_brief`（粗稿）/ `case_info` / `problem_statement` / `stronghold` / 初始 `evidence`。

## 找据点

据点是**一条「已确证」证据**：一条错误消息、一个函数名、一条 HTTP 路由、一个配置参数、一个测试用例。锚在这里；第 3 步的边界从这里向外扩。

绝不从理论出发去找支持。用户的假设（`H-001`）不是据点——据点是直接观察到并被引用的东西（`path:line`、时间戳或 commit）。

## 无据分支

可达不到任何「已确证」证据时：

1. 记录里置 `evidence_light: true`；
2. 用排好序的数据采集项填 `backlog`；
3. 把「要推进，我需要其中一样：…」写成 `missing_evidence` 行（`what` / `would_resolve` / `how`）——`evidence_light` 案件而 `missing_evidence` 为空，终门拒绝放行；
4. 停下等用户补证据，或授权扩大扫描（第 3 步）。

## 起草记录

向 `{output_dir}/investigation.yaml` 追加一条记录。文件缺席时先建它：`project: {name, status: 草稿, created, updated}`（`name` 取自 `diy-coder.yaml` 的 `project.name`；`created` 建文件时设、此后不改，`updated` 每次写回刷今天）加空 `cases` 列表与 `revisions: []`。

**文件已在场时**（上一次结案可能留着 `project.status: 已定稿`），追加新 case 前先把 `project.status` 退回 `草稿`；该 case 走完 `./06-report.md` 的终门后，再按 SKILL.md 规则 11 置回 `已定稿`。

```yaml
  - id: IV-001                 # 下一个 = 既有最大号 + 1，三位；永不重编号、永不复用
    slug: {已定的 slug}
    date: YYYY-MM-DD           # 本条 case 自己的日子，不随 updated 变
    status: 调查中
    mode: 症状驱动|探索
    evidence_light: false
    handoff_brief: {粗稿，一行}
    case_info: {inputs: [{kind, ref}], scope: ..., time_window: ...}
    problem_statement: {用户的描述，逐字}
    stronghold: {ref: ..., why: ...}       # 只在无据分支省略
    evidence:
      - {id: EV-001, grade: 已确证, ref: ..., note: ..., availability: 可得}
    hypotheses:
      - {id: H-001, statement: ..., status: 待验证, test: ..., resolution: ''}
    timeline: []
    backlog: []
    missing_evidence: []
    conclusion: {text: '', confidence: '', fix_direction: '', diagnostic_steps: [], reproduction: ''}
    follow_ups: []
```

ID 在这里铸出（`IV-001`、`EV-001`、`H-001` …）且永不复用。**作用域**：`IV-###` 在整份 `investigation.yaml` 内递增（文件级唯一）；`EV-###` / `H-###` 在**本 case 内**各自从 001 起——新 case 重新计数。机器锚点一律照抄 `collect` 回执，绝不凭记忆重打；空章节写空列表，绝不编内容。

向用户呈报 scope、据点与拟走的路线；停下等他确认再继续。

## 播报与下一步

完整读 `./03-perimeter.md` 并照做。
