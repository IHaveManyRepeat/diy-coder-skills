# Step 5 — 行动项与重大变更检测

Progress: `epic 发现 → 深度分析 → 连续性 → 回顾讨论 → [行动] → 就绪度 → 收尾`

**Read (input):** 第 4 步的 `challenges` / `insights`；`next_epic.dependencies` 与回执的 `next_epic.stories`（下一 epic 的故事 ID 清单）及第 3 步的准备材料；回执的 `bugs` 与 `coverage`。
**Write (output):** 记录里的 `action_items` / `prep_items` / `critical_path` / `significant_changes`。

## 行动项——SMART、有人认领、不写工期（源技能 step-8）

每条行动项关上 retro 浮出的一个缺口（一条 challenge、第 3 步的一条未兑现承诺、一个缺陷类别、一条未覆盖的 AC）：

```yaml
    action_items:
      - {id: AI-001, action: <一行，祈使句>, owner: <谁>, done_when: <可观测的完成判据>, category: 流程|技术|文档|团队}
```

- **`id`** ——`AI-###`，记录内顺序递增，永不复用。
- **`action`** ——具体可做；「改进测试」不是行动，「下一 sprint 开始前给每条必须 FR 的 AC 补一条用例」才是。
- **`owner`** ——点名责任人（一个人或一个明确的角色）。没有责任人的行动是许愿；门会拒绝该记录。
- **`done_when`** ——可观测的完成判据，**不是日期、不是估计**：「AC-4.2 有一条带 kill_target 的用例」「`blocked_reason` 模板已进 diy-sprint」。源技能禁止一切工期预测——这条规则就在此咬合。
- **`category`** ——`流程` / `技术` / `文档` / `团队`。

定稿的 retro 上零行动项是门失败——retro 的全部意义就在这些承诺。

## 准备项（源技能 step-7，下一 epic 的准备）

每个准备需要：一个责任人、一个关键度档、一个真实的力气词（绝不写小时 / 天）：

```yaml
    prep_items:
      - {item: <下一 epic 开工前必须存在什么>, class: 关键|可并行|锦上添花, owner: <谁>, effort: <小|中|大>}
```

- `关键` ——下一 epic 开工前必须完成；`可并行` ——可以在它的早期故事里跑；`锦上添花` ——有帮助但不挡路。
- 源技能的折中保留：早期故事不依赖它的 `关键` 项可以降到 `可并行`——但降级前**逐条读 `next_epic.stories`**，确认该准备项不被这些故事引用；清单为空（`exists: false` 或 `stories: []`）时保持 `关键`，不凭乐观降级。

## 关键路径（下一 epic 之前的阻塞项）

准备项里「跳过就要返工」的子集——各带自己的 *why*：

```yaml
    critical_path:
      - {item: <项>, why: <跳过会坏什么>, owner: <谁>}
```

第 6 步被判定为阻塞的就绪度项落这里，不只留在 `readiness`。

## 重大变更检测（源技能 step-8 的 CRITICAL ANALYSIS）

拿这张清单逐条走本 epic 的证据。任何命中都意味着下一 epic 的计划建立在本 epic 证伪过的假设上：

1. 规划期的架构假设被证伪；2. 重大范围变化或砍需求；3. 技术路线需要根本调整；4. 下一 epic 没有考虑的依赖；5. 用户需求与原理解有实质出入；6. 改变设计的性能 / 扩展性发现；7. 改变做法的安全或合规发现；8. 集成假设被证伪；9. 团队产能或技能缺口比计划更严峻；10. 技术债到了不干预就不可持续的水平。

```yaml
    significant_changes:
      - {change: <什么变了>, impact: <影响哪份计划>, recommended_action: <一行>}
```

- **命中即提案，不是改动。** 本技能绝不改 `epics.yaml` / `stories.yaml` / `prd.yaml` / `architecture.yaml`；该变更在第 7 步路由 diy-correct-course，且**一条 proposal 承载整批条目**。
- **零命中** → 省略该键（或写 `[]`），并在**收尾摘要**里说明下一 epic 的计划仍然成立；源技能明写这一点，我们也明写。
- 空担忧不算重大变更——它要证据，这里的一切都要。

## 播报与下一步

读 `./06-readiness.md` 并照做。
