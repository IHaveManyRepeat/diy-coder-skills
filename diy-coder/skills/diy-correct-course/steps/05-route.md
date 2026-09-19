# Step 5 — 批准与交接

Progress: `立案 → 分析 → 改动 → 提案 → [路由] → 收尾`

**Read (input):** 呈现过的草稿记录；人的裁决。
**Write (output):** 记录里的 `status`（批准时写 `已批准`）、`scope`、`handoff`。

## 取显式批准

问一句：**这条变更提案可以按此实施吗？（批准 [y] / 不批 [n] / 返修 [r]）**

- **批准** → 写 `status: 已批准`，继续下面的路由。
- **不批 / 返修** → 收集要调整之处。改改动集退回 `./03-edits.md`；改影响集、路径或结构在此处理后回退。返修过的记录往 `revisions` 追加 `{date, change, reason}`——绝不把旧理由从记录里抹掉。
- **既不批准、也不返修**（人放弃这次变更）→ 写 `status: 已驳回`，保留记录作审计轨迹，不做交接路由，按 `./06-finish.md` 的 `已驳回` 出口收口。

批准是本步路由的硬前提：未批准的提案绝不交接——终门的状态检查强制这一点。

## 判 scope

按实际记录的影响集定 `scope`（第 1 步的值只是暂定）：

- **`轻微`** —— 一个产物所有者技能直接可落，无需重规划。
- **`中等`** —— backlog 必须重组（故事增删或重排；sprint 门重算）。
- **`重大`** —— 计划本身失效；恢复实施前规划层必须重规划。

## 定交接

`handoff.route` 点名执行的 diy 技能；`handoff.note` 一行写明它继承什么、成功判据是什么。路由必须落在该 scope 的 allow-list 内（终门强制配对）：

| Scope | 粗筛 allow-list | 该级要做的事 |
| --- | --- | --- |
| `轻微` | `diy-dev` / `diy-quick-dev` / `diy-prd` / `diy-architecture` / `diy-epics-stories` / `diy-openapi` / `diy-design` / `diy-create-story` / `diy-test-design` / `diy-e2e-tests` / `diy-review` | 被点名的技能直接落实 edits，再跑它自己的门 |
| `中等` | `diy-sprint` / `diy-epics-stories` / `diy-prd` | 重组 backlog（`reconcile` 重算门），重推覆盖 |
| `重大` | `diy-prd` / `diy-architecture` / `diy-epics-stories` | 重规划：先改需求 / 决策 / 拆解 |

**真判据 = 被改产物的唯一所有者。** allow-list 只是粗筛：`handoff.route` 必须是 `edits[].artifact` 的产物所有者技能——`prd` → `diy-prd`；`epics` / `stories` → `diy-epics-stories`；`architecture` → `diy-architecture`；`openapi` → `diy-openapi`；`design` → `diy-design`；`test-plan` → `diy-test-design`；`infra` → `diy-dev`。改动落在谁的写面内就交给谁；名单里有、写面却接不住这批 edits 的技能不是合法路由——改路由或改提案，绝不硬塞。`edits` 跨多个产物时按主产物路由，并在 `note` 里点名其余产物由谁接手。

本技能自己什么都不执行：真源产物的改写发生在被点名技能的 update 模式里、过它自己的门。两个候选都说得通时与人确认谁接手，并把这次交流记进 `note`。

## 收束路由消息

一条消息：scope、路由、路由继承什么（记录里的 edits）、成功判据（交接完成的判据与下一步）。然后进终门。

## 播报与下一步

读 `./06-finish.md` 并照做。
