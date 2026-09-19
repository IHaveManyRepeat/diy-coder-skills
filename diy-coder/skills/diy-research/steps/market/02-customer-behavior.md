# Step 2 — 客户行为与分层（market 维度）

Progress: `Scope → [02 Behavior] → 03 Pain Points → 04 Decisions → 05 Competitive → Synthesis`

**Read (input):** `{output_dir}/research.yaml` 里本记录（`topic` / `goals` / `scope`）。
**Write (output):** 客户行为 findings 写进该记录；本步播报。

## 关注面

- 客户行为模式与偏好
- 人口统计画像与分层
- 心理特征与价值观
- 行为动因与影响因素
- 客户互动模式与参与度

## 检索（并行跑）

彼此独立的关注面——可用并行检索或调研子代理（可用时）：

- `"{topic} customer behavior patterns"`
- `"{topic} customer demographics"`
- `"{topic} psychographic profiles"`
- `"{topic} customer behavior drivers"`

## 要写的 findings

每个 `area` 一条 `findings[]` 条目，随该次检索落地即写——绝不攒到末尾批量写。`area` 值是稳定句柄：

| `area` | 该断言说什么 |
| --- | --- |
| `customer-behavior` | 行为模式、偏好、决策习惯 |
| `demographics` | 年龄 / 收入 / 地域 / 教育分层 |
| `psychographics` | 价值观与信念、生活方式、态度、人格特质 |
| `segments` | 具名细分画像（人口统计 + 心理特征 + 行为） |
| `behavior-drivers` | 情感、理性、社会、经济层面的影响 |
| `interaction-patterns` | 调研与发现、购买过程、购后、忠诚 |

## 方法

- 每条断言都必须联网检索——只靠训练数据是失败模式，不是捷径。
- 每条 `critical claim` 两个独立来源；来源不一致时两边都摆，不许平均掉。
- 每条 finding 的 `confidence`：`高`（多个权威来源一致）/ `中`（一个可信来源或局部覆盖）/ `低`（不确定或过时）。
- 在断言里注明数据时效及其局限。
- 聚焦可行动的客户洞察；权威研究来源优先于聚合站的噪音。

## 小结与门禁

总结关键发现——验实了什么、哪块仍然单薄——然后停下：

```
进入客户痛点分析吗？

[C] Continue —— 确认并进入痛点分析
```

HALT——等用户。收到 `C` 答复后读全并照做下一个文件；非 `C` 答复按 SKILL.md 的 `[Modify]` 惯例处理（收齐意见、更新记录、重新展示同一门禁）。

## 播报与下一步

读全 `steps/market/03-pain-points.md` 并照做。
