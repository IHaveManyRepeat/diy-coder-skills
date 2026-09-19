# Step 3 — 集成模式（technical 维度）

Progress: `Scope → 02 Stack → [03 Integration] → 04 Architecture → 05 Implementation → Synthesis`

**Read (input):** `{output_dir}/research.yaml` 里本记录；第 2 步的 findings。
**Write (output):** 集成 findings 写进该记录；本步播报。

## 关注面

- API 设计模式与协议
- 通信协议与数据格式
- 系统互操作方案
- 微服务集成模式
- 事件驱动架构与消息

## 检索（并行跑）

- `"{topic} API design patterns protocols"`
- `"{topic} communication protocols data formats"`
- `"{topic} system interoperability integration"`
- `"{topic} microservices integration patterns"`

## 要写的 findings

每个 `area` 一条 `findings[]` 条目，随该次检索落地即写：

| `area` | 该断言说什么 |
| --- | --- |
| `api-design` | REST / GraphQL / RPC / webhook 模式及其取舍 |
| `protocols` | 在用的 HTTP(S)、WebSocket、消息队列、gRPC/Protobuf |
| `data-formats` | JSON/XML、二进制序列化、平面文件、领域标准 |
| `interoperability` | 点对点、API 网关、服务网格、ESB |
| `microservices` | 网关、服务发现、熔断、saga |
| `event-driven` | pub/sub、事件溯源、消息中间件、CQRS |
| `integration-security` | OAuth 2.0 / JWT、API key、双向 TLS、数据加密 |

## 方法

- 必须联网检索——API 指南、协议规范、案例研究。
- 协议与模式类断言必须引权威来源（规范、厂商文档、有记录的案例），不能只有博客二手总结。
- 每条 `critical claim` 两个独立来源；冲突照原样摆出来。
- 每条 finding 的 `confidence`：`高` / `中` / `低`。

## 小结与门禁

总结哪些集成路子适合所研主题、为什么，然后停下：

```
进入架构模式分析吗？

[C] Continue —— 确认并进入架构模式分析
```

HALT——等用户。收到 `C` 答复后读全并照做下一个文件；非 `C` 答复按 SKILL.md 的 `[Modify]` 惯例处理（收齐意见、更新记录、重新展示同一门禁）。

## 播报与下一步

读全 `steps/technical/04-architecture.md` 并照做。
