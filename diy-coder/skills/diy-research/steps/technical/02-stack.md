# Step 2 — 技术栈（technical 维度）

Progress: `Scope → [02 Stack] → 03 Integration → 04 Architecture → 05 Implementation → Synthesis`

**Read (input):** `{output_dir}/research.yaml` 里本记录（`topic` / `goals` / `scope`）。
**Write (output):** 技术栈 findings 写进该记录；本步播报。

## 关注面

- 编程语言及其演进
- 开发框架与库
- 数据库与存储技术
- 开发工具与平台
- 云基础设施与部署平台

## 检索（并行跑）

彼此独立的关注面——可用并行检索或调研子代理（可用时）：

- `"{topic} programming languages frameworks"`
- `"{topic} development tools platforms"`
- `"{topic} database storage technologies"`
- `"{topic} cloud infrastructure platforms"`

## 要写的 findings

每个 `area` 一条 `findings[]` 条目，随该次检索落地即写：

| `area` | 该断言说什么 |
| --- | --- |
| `languages` | 主流与新兴语言、演进、性能特征 |
| `frameworks` | 主导框架与用例、微框架、生态成熟度 |
| `databases` | 关系型、NoSQL、内存、数仓方案 |
| `dev-tools` | 编辑器/IDE、版本控制、构建系统、测试工具链 |
| `cloud-infra` | 云厂商、容器、serverless、CDN/边缘 |
| `adoption-trends` | 迁移模式、新兴与遗留技术、社区趋势 |

## 方法

- 必须联网检索——趋势报告、开发者调查、官方文档、开源项目及其技术选型。
- 每条 `critical claim` 两个独立来源；来源打架时（基准测试尤其）两边都摆出来。
- 每条 finding 的 `confidence`：`高` / `中` / `低`。
- 优先取当前版本与采用事实；版本敏感的断言必须带日期。

## 小结与门禁

总结技术栈图景与采用趋势往哪走，然后停下：

```
进入集成模式分析吗？

[C] Continue —— 确认并进入集成模式分析
```

HALT——等用户。收到 `C` 答复后读全并照做下一个文件；非 `C` 答复按 SKILL.md 的 `[Modify]` 惯例处理（收齐意见、更新记录、重新展示同一门禁）。

## 播报与下一步

读全 `steps/technical/03-integration.md` 并照做。
