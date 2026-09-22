# SD — 多页幻灯片

## Overview
一帧 = 一页的专业版式，用视觉层级把观众的眼睛按顺序牵过去。

## Format Characteristics

| Property | Value |
|----------|-------|
| **Aspect** | 16:9（投屏标准） |
| **Frames** | 一帧 = 一页；帧数按叙事弧给，不按内容量给 |
| **Density** | 一页一个概念；正文不超过 6 行、每行不超过 12 字 |
| **Type scale** | 标题 ≥ 正文字号的 2 倍；正文在 3 米外可读（≥ 28pt） |
| **Transition** | 帧间一次推进一个概念，不做并列铺陈 |
| **Chart treatment** | 数据作图，不做装饰性图表；一图一个结论 |

## Prompt Recipe

```
Design a multi-slide presentation using Excalidraw frame-based layout. Apply audience-appropriate visual hierarchy, enforce the 3-second rule on every frame, and use consistent visual language throughout.
```

> **diy 机制的改动（裁定 7）**：保留「逐页版式 + 视觉层级 + 3 秒规则」，**弃 Excalidraw 帧文件格式**——本套件产物是 YAML / HTML，不是 `.excalidraw`。上句可作为提示词的风格段整段粘贴；「一帧 = 一页」由 `frames[]` 的 `n` 承载。

## Best For
- 产品发布 / 方案汇报 / 培训材料等一切「逐页讲」的场合
- 需要在无讲解的情况下也能自解释的材料（3 秒规则负责这一条）

## Review Gate
- 3 秒规则：每帧单独截图，看 3 秒能不能说出这一帧的意思
- 每帧有职责：`job` 打不上 inform / persuade / transition 的帧剪掉
- 一致性：画幅 / 字阶 / 色 / 版心跨帧同一套
