# Step 6 — 一次成型（零爆炸半径快通道）

Progress: `[Clarify & Route] → One-Shot`（由 step 1 的早期出口抵达；steps 2–5 永远不读）

**Read (input):** `route: 一次成型` 的草稿记录；它承载的意图。
**Write (output):** 代码；记录的 `baseline`、`status`、`tasks[].done`、`verification[].result`、`review`、`deferred`、`review_order`。

只有零爆炸半径才走这里：没有任何可信路径会让这次改动在别处造成非预期后果，意图清楚，无架构决策。这一条一旦不再成立——改动原来会触及共享状态、某个接口或某个决策——停下并改走 `./02-plan.md`；一次错路由的快通道，正是「小改动」搞坏东西的方式。

## 实现

先记 `baseline`（HEAD 或 `NO_VCS`）并把记录置 `status: 进行中`，然后直接实现澄清后的意图——最少代码、项目约定、留在 `code_map` 内、守 `boundaries`（`先问` 仍然 HALT 交人）。

## 验证

跑每一条 `verification` 命令并写下真实 `result`。`status` 前进到 `审查中` / `已完成` 而命令为空，引擎一律拒绝（`EMPTY_FIELD`）——本通道没有红/绿台账，但也没有未经验证的主张。

## 审查（一遍对抗）

跑一遍假定改动**就是**坏的审查：用 diy-review 的镜头攻它——L1 正确性对验收判据，L2 判据隐含的边界情况。**L1 / L2 由本节显式跑；L3 由上面的「验证」段承担**——每条 acceptance 的命令级 `verification` 加实测 `result`，本就是引擎硬底；出现覆盖类问题时用 `layer: 覆盖审计` 落进 `review.findings`，使同一 `review` 块在两条路线上语义等价。子代理可用时用它，且不许带对话上下文。只三种处置：

- **小修** —— 顺手能修。现在就修。
- **后置** —— 真但既有。把 `{finding, why, date}` 追加进 `deferred`。
- 其他一切——静默丢弃。
- 本次改动造成、又大到不是顺手一修的 finding → **HALT**，先呈给人决定再往下走；绝不悄悄把改动做大。

写 `review` 块（`rounds: 1`，`findings` 可为空）并把每条 `tasks[]` 都置 done。

## 建轨迹

把记录填到能独立充当这次改动的轻量轨迹：`title` 取自澄清后的意图，`type`、`route: 一次成型`、`date`，以及完全照 `./05-present.md` 所述构建的 `review_order`（按关注点不按文件；入口点领读；外围收尾；每看点 `{path, line, why}`）。其中 `code_map` ＝ 改动文件一行一条（`path` / `role`）；`tasks` ≥1 条——能过终门的最小集：`--final` 要求 tasks 非空且全 `done: true`，改动即任务、写完置 done。这比源技能的一次成型轨迹更厚（源只有 frontmatter + intent + 带看顺序）：diy 的记录要过与全路线同一道机械门，故 acceptance、verification 与 review 也住在这里。

## 落定与收尾

1. 写 `{output_dir}/spec.yaml` 的 `project.status: 已定稿` 与记录的 `status: 已完成`。
2. 跑终门：`python "{project-root}/.claude/skills/diy-quick-dev/scripts/spec.py" check --final --id SP-xxx --project-root "{project-root}" --output-dir "{output_dir}" --json`（`--output-dir` 必填、无缺省）——exit 0 是唯一放行；否则修完重跑。
3. 用 diy-viewer 渲染（静默旁路，只写命令）并展示摘要：改动文件各配一行说明（CWD 相对 `path:line`）、findings——已打的补丁、已延后项、已丢弃项（全被丢弃就直说）——以及承载其 `review_order` 的 spec 路径。
4. **不 commit、不 push、不开编辑器。** 收尾给一条人自己能跑的 conventional 提交信息，外加一句「要不要我起草 PR 描述」。然后 HALT 等人。

## 播报与下一步

这是 一次成型 路线的最后一步——终门 exit 0 后本次运行到此结束；不再读任何 `steps/` 文件。
