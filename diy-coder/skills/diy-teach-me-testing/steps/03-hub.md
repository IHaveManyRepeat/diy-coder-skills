# Step 3 — 课次菜单（Hub）

Progress: `Init → Assess → [Hub] → Session → Completion`

**Read (input):** `progress.py status` 回执的 `dashboard`（每节状态 / 分数 / 日期 / 下一个推荐 / 完成度）；技能内 `curriculum.yaml` 的节清单（名称、时长、先修、学习路径）。
**Write (output):** 无。Hub 只显示与路由——除用户选择外不写任何产物，也不动进度。

## 显示仪表盘

按回执显示，不要自己重算：

- 抬头：完成度 `completion_percentage`%（`sessions_completed` / 7 节）、学员角色与经验、下一个推荐 `next_recommended`。
- 7 行课次：`[完成]` / `[进行]` / `[未开始]` + 本节名称 + 时长（session 7 记「时长不限」）+ 已完成节的分数与完成日期、进行中节的开始日期。
- 先修关系（`curriculum.yaml` 的 `prerequisites`）只作展示：它不影响推荐算法，也不拦你选课——可以跳节、可以乱序，也可以重进已完成的节。

## 等用户选择

选出入口后停下等输入（HALT，不要自选）：

- **[1-7]** → 走该节（读 `./04-session.md`）。
- **[X]** → 保存退出：进度早已落盘，回一句话「进度已保存，下次继续」后结束本次运行。
- **其他 / 提问** → 解答后重新显示菜单。

## 完成检查（先于菜单）

回执 `sessions_completed == 7` 且 `summary.generated == false` → 不显示菜单，直接播报「7 节已修满，来生成结业摘要」，走 `./05-completion.md`。

`summary.generated == true` → 正常显示菜单（完成态展示）：用户可以重进任一节复习或重做，也可以回 session 7 继续探索主题。

## Next

- 选了某一节 → 读 `./04-session.md` 并照做（该步会把你带回本 Hub）。
- 7 节齐且摘要未生成 → 读 `./05-completion.md`。
- 选了 [X] → 结束本次运行，回调本技能时仍从 `status` 重新进入。
