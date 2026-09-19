# Step 4 — 监管与合规（domain 维度）

Progress: `Scope → 02 Industry → 03 Competitive Landscape → [04 Regulatory] → 05 Trends → Synthesis`

**Read (input):** `{output_dir}/research.yaml` 里本记录；此前各步的 findings。
**Write (output):** 监管 findings 写进该记录；本步播报。

## 关注面

- 具体法规与合规框架
- 行业标准与最佳实践
- 许可与认证要求
- 数据保护与隐私法规
- 环境与安全要求

## 检索（并行跑）

- `"{topic} regulations compliance requirements"`
- `"{topic} standards best practices"`
- `"data privacy regulations {topic}"`

## 要写的 findings

每个 `area` 一条 `findings[]` 条目，随该次检索落地即写：

| `area` | 该断言说什么 |
| --- | --- |
| `regulations` | 适用法规（点名）、执法主体、近期变化 |
| `standards` | 行业技术标准、指南、认证要求 |
| `compliance-frameworks` | 框架、质量保证、审计义务 |
| `data-privacy` | GDPR / CCPA 及行业特定隐私义务、同意与数据处理 |
| `licensing-certification` | 执照、认证及持证主体 |
| `implementation-considerations` | 合规在实践中的成本（流程、工具、人力） |
| `regulatory-risk` | 监管与合规风险、罚则、时限 |

## 方法

- 必须联网检索——法规原文、监管机构官网、政府与行业协会官方来源优先于评论文章。
- 引生效日期与合规时限；辖区差异要点名。
- 每条 `critical claim` 两个独立来源；含糊或尚在草案的规则要在断言里标出。
- 每条 finding 的 `confidence`：`高` / `中` / `低`——没有一手来源的监管断言只能停 `低`。

## 小结与门禁

总结有约束力的要求与其造成的实际负担，然后停下：

```
进入技术趋势分析吗？

[C] Continue —— 确认并进入技术趋势分析
```

HALT——等用户。收到 `C` 答复后读全并照做下一个文件；非 `C` 答复按 SKILL.md 的 `[Modify]` 惯例处理（收齐意见、更新记录、重新展示同一门禁）。

## 播报与下一步

读全 `steps/domain/05-trends.md` 并照做。
