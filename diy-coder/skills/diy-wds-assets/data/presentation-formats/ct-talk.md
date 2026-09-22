# CT — 大会演讲 / 工作坊

## Overview
为**现场听众**设计：大字号、少字、逐页演讲者备注——页面上写的是提示，不是讲稿。

## Format Characteristics

| Property | Value |
|----------|-------|
| **Aspect** | 16:9（会场投屏；后排可读性是底线） |
| **Frames** | 钩子 → 建立张力 → 兑付三段；工作坊版另加「动手环节」页 |
| **Density** | 一页一个字：页面文字 ≤ 6 字（大字号），完整意思进 `notes` |
| **Type scale** | 后排可读：标题 ≥ 60pt；正文尽量不进画面 |
| **Transition** | 每页一个节拍；不出现「过渡页凑数」 |
| **Chart treatment** | 现场讲的数据图**一次只说一条**；复杂图拆成多页 |

## Prompt Recipe

```
Build a conference talk or workshop presentation. Include speaker notes per slide, design for a live audience (large type, minimal text), and structure a hook-build-payoff narrative.
```

> **纯增量能力**（源侧 8 活动无任何「备注 / 旁白」字段）：`notes` 是本活动对源资产的净增——逐页的演讲者备注写进 `frames[].notes`，`CT` 配方**必填**。

## Best For
- 行业大会演讲 / 内部分享 / 工作坊教学
- 一切「有真人在讲」的场合（页面是给听众看的，不是给讲者念的）

## Review Gate
- 大字号少字：把页面缩小到 1/4 还能读清标题（后排模拟）
- 逐页备注：每页 `notes` 非空，且能直接念出来（不是提纲词）
- 钩子 → 张力 → 兑付：三段弧在整场成立
