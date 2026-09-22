# EX — 视频解说版式

## Overview
按拍写的视觉脚本：每一拍画面是什么、用来留人的钩子在哪几秒。

## Format Characteristics

| Property | Value |
|----------|-------|
| **Aspect** | 16:9（横屏）/ 9:16（竖屏短视频） |
| **Frames** | 按**拍**计：`0s` 钩子 → `3s` 承诺 → 每 `15–30s` 一个再钩子 → 收尾兑付 |
| **Density** | 每拍一个画面 + 一句旁白；屏上文字 ≤ 8 字（短视频常见） |
| **Type scale** | 屏上文字为「扫读」服务：大字、粗体、高对比 |
| **Transition** | 拍与拍之间用画面变化做节拍（切换即节拍） |
| **Chart treatment** | 数据用动效逐项出现，不做一次性铺满 |

## Prompt Recipe

```
Design a YouTube explainer layout. Produce a visual script with engagement hooks at 0s, 3s, and every 15-30s; specify on-screen visuals per beat; apply bold, casual typographic style appropriate to the platform.
```

> **diy 机制的改动（裁定 7）**：**去平台绑定**（源句里的平台专属字体与缩略图规格不迁移），保留**钩子时间线**与「逐拍画面」。**交界约定**：内容脚本（钩子节拍 / 逐拍画面 / 旁白）归第 9 活动；**动效与视频落盘走 `[V]` 的 `assets/motion/` 通道**——EX 是两个活动的交界配方，不是 `[V]` 的子项。

## Best For
- 产品解说 / 教程 / 概念科普等「讲一遍」的场合
- 需要在开头 3 秒决定观众去留的分发场景

## Review Gate
- 钩子节拍：0s / 3s / 15–30s 各有明确钩子，且钩子回答「你为什么继续看」
- 逐拍画面：每拍都能说出画面上是什么（写「画面丰富」等于没写）
- 故事结构：钩子 → 张力 → 兑付这条弧在整片成立
