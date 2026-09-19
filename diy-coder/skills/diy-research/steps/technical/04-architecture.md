# Step 4 — 架构模式（technical 维度）

Progress: `Scope → 02 Stack → 03 Integration → [04 Architecture] → 05 Implementation → Synthesis`

**Read (input):** `{output_dir}/research.yaml` 里本记录；第 2/3 步的 findings。
**Write (output):** 架构 findings 写进该记录；本步播报。

## 关注面

- 系统架构模式及其取舍
- 设计原则与最佳实践
- 扩展性与可维护性考量
- 集成与通信模式
- 安全、数据与部署架构

## 检索（并行跑）

- `"{topic} system architecture patterns best practices"`
- `"{topic} software design principles patterns"`
- `"{topic} scalability architecture patterns"`

## 要写的 findings

每个 `area` 一条 `findings[]` 条目，随该次检索落地即写：

| `area` | 该断言说什么 |
| --- | --- |
| `system-architecture` | 单体 / 微服务 / serverless / 事件驱动，及其取舍 |
| `design-principles` | SOLID、整洁 / 六边形架构、API 与数据设计原则 |
| `scalability` | 横向与纵向扩展、负载均衡、缓存、共识、容量与性能模式 |
| `integration-communication` | 服务与模块之间的边界决策 |
| `security-architecture` | 信任边界、认证授权架构、威胁态势 |
| `data-architecture` | 存储策略、一致性、数据归属 |
| `deployment-architecture` | 部署拓扑、环境、可运维性 |

## 方法

- 必须联网检索——架构文档、模式目录、会议案例、ADR。
- 点出取舍，不只点模式：不带成本的模式断言是残缺的。
- 每条 `critical claim` 两个独立来源；冲突两边都摆、都引。
- 每条 finding 的 `confidence`：`高` / `中` / `低`。

## 小结与门禁

总结本主题的架构可选路及其取舍，然后停下：

```
进入实现路径调研吗？

[C] Continue —— 确认并进入实现路径调研
```

HALT——等用户。收到 `C` 答复后读全并照做下一个文件；非 `C` 答复按 SKILL.md 的 `[Modify]` 惯例处理（收齐意见、更新记录、重新展示同一门禁）。

## 播报与下一步

读全 `steps/technical/05-implementation.md` 并照做。
