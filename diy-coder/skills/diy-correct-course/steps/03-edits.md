# Step 3 — 具体改动提案

Progress: `立案 → 分析 → [改动] → 提案 → 路由 → 收尾`

**Read (input):** 记录的 `impacts`；被改 ID 处的产物当前取值（按 ID 查，绝不整篇重读）。
**Write (output):** 记录里的 `edits`。

## 一处改动一条提案

每条在记录里答四个问题：改什么（`artifact` + `target` + `field`）、从什么改（`old`）、改成什么（`new`）、为什么（`rationale`）。

**只引用、不复制** —— 把 old → new 全文摆出来那一步的 diy 改写。`old` / `new` 引最小决定性取值，不粘贴整段：

```
artifact: stories
target: AC-1.1
field: acceptance_criteria
old: AC-1.1 当前只断言邮箱密码登录成功
new: AC-1.1 追加 2FA 启用分支（given/when/then 三键同改）
rationale: 安全评审将 2FA 列为 必须，AC 不覆盖则测试设计无处落点
```

新增型没有当前值：写 `old: (absent)`——字段仍须非空，且 `old` 必须与 `new` 不同（引擎拒绝空改动）。

## 按产物分镜（是清单，不是模板）

- **stories** —— 点名故事 ID 与被触及的段；AC 改动三键同改（given/when/then），覆盖移动时连 `refs` 一起改。
- **prd** —— 点明确切的 FR/NFR ID 与 MVP 范围后果（`F-*` 保持稳定；新需求拿新的 `FR-x.y`，永不重编号）。
- **architecture** —— 受影响的 `D-*` 决策、组件或技术选型，以及它向下游的波及面；新决策是 `新增`，不是改写已采纳的决策。
- **design / openapi** —— 被触及的页面 `P-*` 或 `operationId`，以及用户可见面或契约面的后果。
- **test-plan** —— 绑在被改 AC 上的 `TC-*` 用例；工具或 CI 门本身移动时一并改 `static_checks`。
- **infra** —— 部署脚本 / CI 配置 / IaC 文件：`target: path:<relative>`，`field` 写它内部的配置路径（如 `jobs.test.steps`）；待新建文件写 `old: (absent)`。

## 呈现前逐条核对

- 目标 ID 在 `collect` 回执里存在（文档摘要或 chain）；`infra` 的 `path:` 目标免此查（文件可能待建），改查形态——相对路径、正斜杠、无 `..`；
- `field` 指向该产物 schema 里真实存在的东西（产物所有者技能的 SKILL.md schema 是权威）；
- `old` 反映当前值——若它取自回执摘要而非产物本身，就说明这一点并保持摘要形态，绝不编造逐字原文。

## 按 mode 呈现

**`增量`** —— 逐条单独呈现；保留循环：**批准 [a] / 改 [e] / 跳过 [s]**。按反馈打磨，迭代到人往下走。被跳过的改动就是丢掉，绝不悄悄留着。

**`批量`** —— 收齐全部改动提案，在本步末尾一次性呈现；人标出要改哪些，循环对标记集只跑一遍。

## 播报与下一步

读 `./04-proposal.md` 并照做。
