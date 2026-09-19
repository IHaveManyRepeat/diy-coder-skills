# Step 2 — 结构化证据深度分析

Progress: `epic 发现 → [深度分析] → 连续性 → 回顾讨论 → 行动 → 就绪度 → 收尾`

**Read (input):** `collect` 回执（`stories` / `metrics` / `bugs` / `coverage` / `warnings`）；它指向的任务块——本 epic 的 `sprint.yaml` 任务（`note` / `evidence` / `loop` / `review.findings`）、`bug-log.yaml` 条目、`test-plan.yaml` 覆盖。
**Write (output):** 记录里的 `patterns`——带证据与计数的跨故事主题。

## 先读：diy 化改造

源技能逐个读故事的 markdown，从「Dev Notes」「Review」「Lessons Learned」「Technical Debt」「Testing」等小节里挖料。在 diy 里这些叙述小节并不以散文形式存在——同一批证据已经结构化，且按 ID 取用，不靠读文档：

| 源证据类别 | diy 来源（结构化） |
|---|---|
| 开发笔记与挣扎 | `sprint.yaml` 里任务 `note` + `loop.rounds` / `loop.outcome` + `blocked_reason` |
| 审查反馈模式 | `sprint.yaml` 里任务 `review.findings[]`（`layer` / `route` / `note`） |
| 经验教训 | `note` 字段 + `bug-log.yaml` 的 `prevention` / `pattern` 列 |
| 欠下的技术债 | `blocked_reason`、`route: 后置` 的 findings、bug `root_cause` |
| 测试与质量洞察 | `test-plan.yaml` 的 TC `status` + `coverage_gaps` + 任务 `evidence` 账本 |
| 速度模式 | `loop.rounds` 汇总 = 回执的 `metrics.rounds_total` |

两个后果：绝不重推回执已经带有的计数；绝不复述产物的散文——引 ID。`metrics` 含全部原始数字；`pattern` 是在它之上加的解释。

## 四副分析镜片（源技能的发言角色，保留为视角）

源技能用五个发言角色跑分析。角色本身的对白不继承；它们的作用——对同一批证据的不同读法——继承。四副镜片都要过一遍：

- **开发镜片**——实现在哪里顶回来了？读 `loop.rounds` 的离群值（轮数 ≫ epic 中位数）、`blocked_reason`、被重新打开的任务、`augment: 失败`。轮数高就是 diy 版的「源技能说的低估复杂度」信号。
- **产品镜片**——epic 交付了故事承诺的东西吗？读 `stories.pending`（没落地的）、被延后的 findings、`coverage_gaps` 里 `decision: 待办` 的 AC。
- **QA 镜片**——缺陷会从哪里漏过去？读 `coverage`（无用例的 AC）、`bug-log` 的 `subclass` 聚类、事后补写的 `evidence` 账本。
- **架构镜片**——哪些决策过期了？读 `bug-log` 的 `root_cause` / `pattern` 找重复类别、点名结构问题的延后 findings、任何引用上游规格的 `blocked_reason`。

每副镜片**在本步的输出消息里**给出读数（第 4 步以它为输入；记录里只落结论）；只有经得起交叉检验的读数才变成 pattern、challenge 或行动项。

## 归并规则（源技能 step-2）

- **pattern 需要 ≥2 个故事**——只有一个故事作证的主题是轶事。每条 `patterns[]`：`theme`（一行）、`evidence`（`S-x` 与 `BUG-0xx`，都要可解析）、`count`（多少个故事显示它，≥2，且与所列证据一致）。
- **归并键：先按 `route` 分桶**（`意图缺口` / `规格缺陷` / `小修` / `后置`，机械可复现）；同桶内 `note` 明显分属不同主题时，再按 `note` 语义细分，并把归并依据写进 `theme`（一句话 + 括号注明依据）。`count` = 该桶涉及的不同 story 数，`evidence` 取桶内代表性的 `S-x` / `BUG-0xx`。**反复出现的审查反馈按主题算一条 pattern**，不是每个 finding 一条；引代表性 ID。
- **`wins` / `challenges` / `insights` 是本步的分析产出，不是讨论记录。** 这里先作为原材料填好，第 4 步定稿；保持证据锚定、不追责。
- **全文不出现工期估计**——pattern 里没有，行动里也没有。轮次与计数就是 diy 的速度代理；小时与天被源技能禁止，继续禁止。

## 一个 pattern 都没找到

干净的 epic 可以真的没有。写 `patterns: []`，并在**本步的输出消息里**明说——绝不为了填满小节而编 pattern，绝不把单故事观察注水成主题。

## 播报与下一步

读 `./03-continuity.md` 并照做。
