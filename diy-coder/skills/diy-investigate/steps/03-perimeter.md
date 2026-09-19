# Step 3 — 证据边界测绘

Progress: `确认输入 → 据点 → [边界] → 推理 → 源码追踪 → 结案`

**Read (input):** 第 2 步的记录草稿；`collect` 回执。
**Write (output):** 记录的 `evidence` / `missing_evidence` / `backlog` 三节。

## 巡场

按六类清点证据——一条消息里并发发出去：

1. 诊断归档；2. 工单系统；3. 版本控制（回执的 `vcs.commits`）；4. 测试结果；5. 静态分析；6. 源码（回执的 `files` + `candidates`）。

六类是**测绘顺序**，不是记录形状：记录只存逐条 `evidence`（`id` / `grade` / `availability` / `ref` / `note` 全非空）；某类拿不到源时按下方「分类与记录」落一条 `missing_evidence` 行——**不为凑类别造空壳证据**。

**委派：** 按 `SKILL.md` 规则 7 的**分层闸值**派子代理（单文件 >10K tokens / 一次 ≥5 个文件 / 一个类别合计 >10K tokens，任一命中即派）。本步特有动作：派的是命中的那个文件 / 批次 / 类别；回执只要一份 JSON 清单——路径、体量、时间窗，关键片段以 `path:line` 引用。引用从结果里取，父上下文绝不重读源。

## 分类与记录

每个源判一个 `availability`：

- `可得` —— 现在能完整读；
- `部分可得` —— 能读但不完整（截断的日志、多个分片里只有一个）；
- `缺失` —— 现在拿不到。

**`缺失` 本身就是发现**：每个缺口落一条 `missing_evidence` 行（`what` / `would_resolve` / `how`）——这个缺口能解答什么、怎么取得。绝不静默丢一类。两处分工写死：**`missing_evidence` 是缺口的载体**；`availability: 缺失` 只用于**已有条目跑丢**（曾经可得的一条证据现在取不到了），不用来表示整类缺失。

新发现的路径进 `backlog`（`item` / `priority: 高|中|低` / `status: 待办`）——`priority` 的自然刻度就是这三档（引擎常量 `BACKLOG_PRIORITIES` 按它校验；不复用 FR 优先级的 `P0`–`P2`，那是 diy-test-design 的单一定义面）；留在当前线上，不追这里浮出来的一切。

向用户呈报边界（`可得` / `部分可得` / `缺失` + 缺口行）；停下等他确认再继续。

## 播报与下一步

完整读 `./04-reasoning.md` 并照做。
