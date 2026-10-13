# IN — 信息可视化

## 概述
先选图型、再让数据讲故事：图型选对了一半的活就干完了。

## Format Characteristics
> **格式特征**——本节标题被流程引用，英文原文逐字保留。

| 属性 | 值 |
|----------|-------|
| **Aspect** | 按投放位：竖版长图 1:3 / 方版 1:1 / 横版 16:9 |
| **帧数** | 单张为主，长图按「节」分段（每节一个结论） |
| **Density** | 一图一结论；每个像素都要 inform / persuade / transition |
| **字阶** | 主标题 ≥ 3 倍正文；数据标签不小于正文 |
| **转场** | 长图里用留白与色块切换节，不靠分割线 |
| **图表处理** | **图型先定**：比较用条形 / 趋势用折线 / 构成用堆叠 / 关系用散点或弦图；层级靠视觉编码，不靠报表默认样式 |

## Prompt Recipe
> **提示词配方**——配方整段贴入外部生成服务的提示词，保留英文原文。

```
Design a creative information visualization. Choose the chart/diagram type that lets the data tell the story, layer visual storytelling on top of the data, and cut every pixel that doesn't inform-persuade-or-transition.
```

> **与 `content-styles` 的接续**：`VM` / `CV` 之外的插画技法从 `data/styles/content-styles/` 取——源侧实测 `isometric` 卡的 `适用场景` 已直接写「数据可视化、流程图」，两轴天然接续，无需新机制。

## Best For
> **适用场景**——英文原文保留。
- 数据故事长图 / 年度总结 / 报告插图
- 需要把一张表讲成一句话的场合

## Review Gate
> **评审门**——本节标题被流程引用，英文原文逐字保留。
- 图型选对：换一种图型会不会更清楚（会 → 换）
- 一图一结论：这张图能一句话说出结论吗
- 无冗余像素：剪掉不 inform / persuade / transition 的一切装饰
