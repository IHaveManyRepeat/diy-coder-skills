# SD — 多页幻灯片

## 概述
一帧 = 一页的专业版式，用视觉层级把观众的眼睛按顺序牵过去。

## Format Characteristics
> **格式特征**——本节标题被流程引用，英文原文逐字保留。

| 属性 | 值 |
|----------|-------|
| **Aspect** | 16:9（投屏标准） |
| **帧数** | 一帧 = 一页；帧数按叙事弧给，不按内容量给 |
| **Density** | 一页一个概念；正文不超过 6 行、每行不超过 12 字 |
| **字阶** | 标题 ≥ 正文字号的 2 倍；正文在 3 米外可读（≥ 28pt） |
| **转场** | 帧间一次推进一个概念，不做并列铺陈 |
| **图表处理** | 数据作图，不做装饰性图表；一图一个结论 |

## Prompt Recipe
> **提示词配方**——配方英文段整段贴入外部生成服务，保留英文原文；段后中文对照仅供理解。

```
Design a multi-slide presentation using Excalidraw frame-based layout. Apply audience-appropriate visual hierarchy, enforce the 3-second rule on every frame, and use consistent visual language throughout.
```

中文对照：使用 Excalidraw 基于画框的版式设计多页演示。运用适合受众的视觉层级，每一帧执行 3 秒规则，全程使用一致的视觉语言。

> **diy 机制的改动（裁定 7）**：保留「逐页版式 + 视觉层级 + 3 秒规则」，**弃 Excalidraw 帧文件格式**——本套件产物是 YAML / HTML，不是 `.excalidraw`。上句可作为提示词的风格段整段粘贴；「一帧 = 一页」由 `frames[]` 的 `n` 承载。生成物请要求 HTML / 图片，忽略 Excalidraw 文件格式那一句。

## Best For
> **适用场景**——英文原文保留。
- 产品发布 / 方案汇报 / 培训材料等一切「逐页讲」的场合
- 需要在无讲解的情况下也能自解释的材料（3 秒规则负责这一条）

## Review Gate
> **评审门**——本节标题被流程引用，英文原文逐字保留。
- 3 秒规则：每帧单独截图，看 3 秒能不能说出这一帧的意思
- 每帧有职责：`job` 打不上 inform / persuade / transition 的帧剪掉
- 一致性：画幅 / 字阶 / 色 / 版心跨帧同一套
