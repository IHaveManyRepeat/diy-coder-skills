# Step 5 — 实现路径与技术采用（technical 维度收尾）

Progress: `Scope → 02 Stack → 03 Integration → 04 Architecture → [05 Implementation] → Synthesis`

**Read (input):** `{output_dir}/research.yaml` 里本记录；前三个步骤的 findings。
**Write (output):** 实现路径 findings 写进该记录；本步播报。

## 关注面

- 技术采用策略与迁移模式
- 开发工作流与工具生态
- 测试、部署与运维实践
- 团队组织与技能要求
- 成本优化与资源管理

## 检索（并行跑）

- `"{topic} technology adoption strategies migration"`
- `"{topic} software development workflows tooling"`
- `"{topic} DevOps operations best practices"`

## 要写的 findings

每个 `area` 一条 `findings[]` 条目，随该次检索落地即写：

| `area` | 该断言说什么 |
| --- | --- |
| `adoption-strategies` | 迁移模式、渐进与一次性切换、遗留系统现代化、选型 |
| `workflows-tooling` | CI/CD、代码质量与评审、协作工具 |
| `testing-qa` | 测试策略、框架、质量门 |
| `deployment-ops` | 监控与可观测性、事故响应、IaC、安全运维 |
| `team-skills` | 团队形态与技能要求、招聘或技能升级的影响 |
| `cost-optimization` | 成本动因与资源管理手法 |
| `risk-mitigation` | 实现风险与团队的应对 |
| `recommendations` | 实现路线图、技术栈建议、技能建设、成功度量 |

`recommendations` 是通往综合步的桥：照旧写成带来源的 findings，第 6 步把最重要的几条提进 `synthesis.key_points`。

## 方法

- 必须联网检索——实现案例、迁移复盘、工具评估、成熟度模型。
- 采用类断言优先取有文字记录的经验（复盘、案例），不取厂商营销。
- 每条 `critical claim` 两个独立来源；冲突两边都摆、都引。
- 每条 finding 的 `confidence`：`高` / `中` / `低`。

## 小结与门禁

总结落地路径及其风险，然后停下：

```
technical 维度四个分析步已全部完成。

[C] Continue —— 确认并进入综合成文
```

HALT——等用户。收到 `C` 答复后读全并照做下一个文件；非 `C` 答复按 SKILL.md 的 `[Modify]` 惯例处理（收齐意见、更新记录、重新展示同一门禁）。

## 播报与下一步

读全 `steps/06-synthesis.md` 并照做。
