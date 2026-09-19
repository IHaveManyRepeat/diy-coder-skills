# Step 3 — 承诺跟踪与下一 epic 预览

Progress: `epic 发现 → 深度分析 → [连续性] → 回顾讨论 → 行动 → 就绪度 → 收尾`

**Read (input):** 回执的 `prev_actions` / `first_retro` / `next_epic`；本 epic 的 `sprint.yaml` 任务证据（兑现与否的凭据）。
**Write (output):** 记录里的 `prev_followup` 与 `next_epic`。

## 第一段——上一个 retro 的承诺（源技能 step-3）

`prev_actions` 带上一个 epic 那份 retro 的行动项，每条形如 `{retro, id, action, owner, done_when, category}`——`retro` 直接取该条自带的 `retro` 键（`RT-###`），不必回读 `retrospective.yaml`。（`first_retro: true` 表示没有上一份——说「首份 retro，无承诺可跟」，`prev_followup` 省略。）

对每条带过来的行动，**从本 epic 的证据、不凭记忆**判实际兑现：

- `已完成` — 有产物显示它发生了（引出来：某条 `AC-x.y` 已覆盖、某个 `BUG-0xx` 的预防已就位、某条 `blocked_reason` 不再复现）。
- `部分完成` — 可见进展、可见缺口；说清缺的是哪部分。
- `未完成` — 本 epic 证据里毫无踪迹；陈述后果、不追责（源主持纪律：对系统，不对人）。

```yaml
    prev_followup:
      - {retro: RT-yy, action: <承诺，一行>, status: 已完成|部分完成|未完成, evidence: <锚点>}
```

证据判不了的行动记 `未完成`，并点名缺什么证据——绝不靠乐观上调。首份 retro 整个省略 `prev_followup`。

## 第二段——下一 epic 预览（源技能 step-4）

回执的 `next_epic` 带 `{id, exists, title, stories, shared_frs}`；`shared_frs` 是机械耦合——本 epic 与下一 epic 都引用的需求。本步的活是读，不是查表：

- **对本 epic 成果的依赖。** 从 `shared_frs` 加上前面的分析读数点名（如「E-4 复用 S-7 建的校验路径」）。每条依赖都要说清必须**稳定**的是什么，而不只是在场。
- **需要做的准备**——第 5 步 `prep_items` 的原材料：技术设置、知识缺口、重构、文档、测试基础设施、外部依赖。这里不列举；清单归第 5 步。
- **不准备的代价**——源技能的关键一问。每条风险带一句话进第 5 步的关键路径推理。

```yaml
    next_epic: {id: E-y, exists: true, dependencies: [<上面点名的耦合>]}
```

- **没有下一个 epic**（`exists: false`）→ `next_epic: {id: null, exists: false, dependencies: []}`，跳过预览讨论，并明说：将来规划下一 epic 时这些教训照样成立。不要因此跳过 retro。

## 第三段——重大变更检测的输入

记下（先不裁定）任何表明**计划已经错了**的证据：架构假设被证伪、范围移动、没人规划过的依赖、改变做法的性能或安全发现。第 5 步拿这些笔记跑完整检测清单——本步只确保原材料在手。

## 播报与下一步

读 `./04-review.md` 并照做。
