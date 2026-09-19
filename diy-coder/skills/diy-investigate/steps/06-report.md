# Step 6 — 结案与交接

Progress: `确认输入 → 据点 → 边界 → 推理 → 源码追踪 → [结案]`

**Read (input):** 第 2–5 步填出来的记录；一路上用户的确认。
**Write (output):** 定稿的记录（`handoff_brief` / `conclusion` / `status`）落在 `{output_dir}/investigation.yaml`；渲染视图；交接菜单。

## 定稿记录

- **`handoff_brief`** —— 改写成终形：3 句、15 秒读完（出了什么事 / 案子现在到哪 / 下一步需要什么）。
- **`conclusion.text`** 配 **`conclusion.confidence`**：`高`（根因「已确证」、复现确定）/ `中`（已推断；小不确定）/ `低`（假设中；数据缺口明确）。
- **`conclusion.fix_direction`** 适用时写（多种机制并存时按机制分类）；**`conclusion.diagnostic_steps`** 不确定性仍在时写；**`conclusion.reproduction`** 适用时写——探索型案件改写验证计划。
- **`side_findings`** —— 一路浮出的切向观察（证据分级，`ref` 可选）：看到了，**没追**。它们归这里——不归 `backlog`（那是待探队列）、不归 `evidence`（那是本线的证明）。可选；没有就省略。
- **记录 `status`** —— 按完成判据映射定：
  - `已结论` ← 判据 ① 根因「已确证」/ ③ 探索型心智模型已够用 / ⑤ 用户显式结案；
  - `待证据阻塞` ← 判据 ② 根因停在 `假设中` 且缺口本次取不到，或 ④ `backlog` 只剩需要不可得证据的项——「等证据」永远不用 `已结论` 遮掩；
  - `调查中` ← 五条判据都不成立（还有可取证据，继续追）。
  - 「本次取不到」的判据 = `missing_evidence[].how` 需要本次范围外的动作（外部系统 / 权限 / 时间）。

## 完成判据

案子完成当下面任一条成立：根因「已确证」；根因停在「假设中」且数据缺口已显式登记；心智模型足以支撑用户说定的目标（探索型）；`backlog` 只剩需要不可得证据的项；用户显式结案。

## 终门（机械）

1. 先写 `project.status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物。
2. 跑 `python "{project-root}/.claude/skills/diy-investigate/scripts/investigation.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两实参同激活（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑。JSON 回执（含计数）即收口证据。
3. 渲染——按 SKILL.md 的静默旁路命令——只在 exit 0 之后；不新增浏览器交互点、不报阻塞路径。

## 续案（resume）

追加一条 `follow_ups` 条目（`date` / `note`）——同日再入也照记。早先的历史永不改写；变了的假设就地更新（status + resolution），永不删除。

## 路由菜单（点名最高价值的那一个动作，一行一条）

| 发现 | 路由 |
| --- | --- |
| 查实的缺陷 → 入库 | `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" bug-add --entry '<json>' --json`（`source: 用户`；`story` 取波及的 `S-x`，确无归属写 `n/a`）——由用户确认后就地执行；本技能零写 `bug-log.yaml` |
| 一行可修的小缺陷 | `diy-quick-dev` |
| 范围 / 计划要变 | `diy-correct-course` |
| 值得立成故事 | `diy-create-story` |
| 修复要重新审查 | `diy-review` |

缓解措施与绕过方案只在显式请求时生成——调查止于诊断。收尾给出路由，外加回执里的计数（含 `counts`）。

## 播报与下一步

这是最后一个步骤文件——终门 exit 0 之后本轮即结束。`handoff_brief` + `conclusion` 承载结果，记录的 `status` 结案；不再读任何 `steps/` 文件。
