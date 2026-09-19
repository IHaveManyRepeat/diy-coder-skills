# Step 2 — 行业分析（domain 维度）

Progress: `Scope → [02 Industry] → 03 Competitive Landscape → 04 Regulatory → 05 Trends → Synthesis`

**Read (input):** `{output_dir}/research.yaml` 里本记录（`topic` / `goals` / `scope`）。
**Write (output):** 行业 findings 写进该记录；本步播报。

## 关注面

- 市场规模与估值指标
- 增速与市场动态
- 市场分层与结构
- 行业趋势与演进路径
- 经济影响与价值创造

## 检索（并行跑）

彼此独立的关注面——可用并行检索或调研子代理（可用时）：

- `"{topic} market size value"`
- `"{topic} market growth rate dynamics"`
- `"{topic} market segmentation structure"`
- `"{topic} industry trends evolution"`

## 要写的 findings

每个 `area` 一条 `findings[]` 条目，随该次检索落地即写：

| `area` | 该断言说什么 |
| --- | --- |
| `market-size` | 当前规模、增速（CAGR）、经济贡献 |
| `dynamics-growth` | 增长动因、壁垒、周期特征、成熟阶段 |
| `structure-segmentation` | 主细分与子细分、地域分布、价值链 |
| `trends-evolution` | 新兴趋势、近期演进、技术对行业的影响 |
| `competitive-dynamics` | 集中度、竞争烈度、进入壁垒、创新压力 |

## 方法

- 必须联网检索——具名研究机构或行业协会的市场报告与行业分析。
- 规模与增速数字必须带来源与年份；数字打架的两边都摆。
- 每条 `critical claim` 两个独立来源；外推要明确标注为外推。
- 每条 finding 的 `confidence`：`高` / `中` / `低`。

## 小结与门禁

总结行业图景——规模、方向、结构——然后停下：

```
进入竞争格局分析吗？

[C] Continue —— 确认并进入竞争格局分析
```

HALT——等用户。收到 `C` 答复后读全并照做下一个文件；非 `C` 答复按 SKILL.md 的 `[Modify]` 惯例处理（收齐意见、更新记录、重新展示同一门禁）。

## 播报与下一步

读全 `steps/domain/03-competitive-landscape.md` 并照做。
