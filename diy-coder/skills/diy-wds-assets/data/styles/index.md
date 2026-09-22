# 风格库索引（两轴）

> **为什么有这份索引**：源侧风格卡**没有 index、没有 manifest、没有 README**，注册表只存在于散文里（源 `workflow.md:107–122` 与 `:126–133`），实测已漂移过——`workflow.md:112` 只列了 5 个设计风格名 + `etc.`（漏 `Editorial`），实际有 6 张卡（census-4 缺陷 #18）。本索引把注册表变成**一份机械可核的清单**。
>
> **卡的原样**：16 张卡**逐字迁移**（源 `data/styles/`，413 行；卡是纯文本、无平台耦合、无 frontmatter）。卡里的 `Prompt Keywords` 是**英文的**——**不要翻译**，它们要被整段贴进外部生成服务的提示词。

## 一、`design-styles/`（6 张）—— 页面级视觉语言

| 卡 | 一句话气质 | 典型用处 |
| --- | --- | --- |
| [`brutalist.md`](design-styles/brutalist.md) | 高对比、重描边、故意粗糙 | 态度强的品牌站、作品集 |
| [`corporate.md`](design-styles/corporate.md) | 稳重、可信、结构清晰 | 金融 / 医疗 / 企业官网 |
| [`editorial.md`](design-styles/editorial.md) | 杂志式排版、强标题层级 | 内容站、媒体、博客 |
| [`minimal.md`](design-styles/minimal.md) | 大量留白、克制的元素 | 作品集、奢侈品牌、SaaS |
| [`organic.md`](design-styles/organic.md) | 自然曲线、柔和色、手作感 | 康养 / 食品 / 生活方式 |
| [`playful.md`](design-styles/playful.md) | 活泼、圆润、鲜艳 | 消费级产品、教育、儿童 |

**谁读**：`[W]` 线框（取「布局原则与间距感」）· `[P]` 页面稿（与令牌三向合并）· `[S]` 演示（**整件气质**，不碰产品令牌）。**谁不读**：`[U]` `[I]` `[V]` `[C]`（源侧实测：风格库实际只覆盖 3/6 个视觉活动）。

## 二、`content-styles/`（10 张）—— 单图形的成像技法

| 卡 | 一句话气质 |
| --- | --- |
| [`3d-render.md`](content-styles/3d-render.md) | 三维渲染质感 |
| [`comic-book.md`](content-styles/comic-book.md) | 美漫线描 + 网点 |
| [`flat-design.md`](content-styles/flat-design.md) | 纯平面、零阴影 |
| [`hyper-realistic.md`](content-styles/hyper-realistic.md) | 超越写实的细节密度 |
| [`illustration.md`](content-styles/illustration.md) | 通用插画 |
| [`isometric.md`](content-styles/isometric.md) | 等距视角（**数据可视化 / 流程图**的最优解） |
| [`line-art.md`](content-styles/line-art.md) | 单线描 |
| [`pencil-sketch.md`](content-styles/pencil-sketch.md) | 铅笔草图 |
| [`photorealistic.md`](content-styles/photorealistic.md) | 写实摄影 |
| [`watercolor.md`](content-styles/watercolor.md) | 水彩晕染 |

**谁读**：`[P]` 页面稿（**按需**，纯摄影站可整项跳过）· `[M]` 图片（**按批分配**——一批一卡，不同批可不同卡）· `[S]` 演示的 `VM` / `CV` 配方（概念插画 / 单张概念图）。**谁不读**：`[W]` `[U]` `[I]` `[V]` `[C]`。
每张卡末尾的 `Dimensions Guide` 给的是**参考比例**（hero `16:9` / `1:1` 等）——与页面规格冲突时**以页面规格为准**。

## 三、第三轴不在本目录

`data/presentation-formats/`（7 张配方卡）是**交付物形态**轴，不是视觉语言轴——索引见 [`../presentation-formats/index.md`](../presentation-formats/index.md)（裁定 7）。
