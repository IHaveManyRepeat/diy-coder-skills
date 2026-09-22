# 演示格式库索引（第三轴 · `data/presentation-formats/`）

> **这一轴是什么**：**交付物形态**。7 张卡各自描述一种「做出来是什么东西」——幻灯片 / 解说脚本 / 路演 / 演讲 / 信息图 / 概念插画 / 单张图。
>
> **为什么单开一轴（裁定 7）**：`data/styles/design-styles/` 是**页面级视觉语言**（留白 / 描边 / 影），`data/styles/content-styles/` 是**单图形的成像技法**（写实 / 插画 / 水彩）——两轴是**视觉语言**。7 配方描述的是**交付物形态**（同一个 deck 可以是 Minimal 也可以是 Brutalist），塞进那两轴会把两种不同的维度混在一个目录里，未来第四类（小程序 / 邮件）会继续污染。故本轴独立。

| `recipe` | 卡 | 交付物形态 | 尺寸基准 | 评审侧重（8 原则里的哪几条） |
| --- | --- | --- | --- | --- |
| `SD` | [`sd-slides.md`](sd-slides.md) | 多页幻灯片 | 16:9 | 视觉层级 / 3 秒规则 / 每帧有职责 |
| `EX` | [`ex-explainer.md`](ex-explainer.md) | 视频解说版式 | 16:9 或 9:16 | 故事结构（钩子节拍） |
| `PD` | [`pd-pitch.md`](pd-pitch.md) | 投资人路演 | 16:9 / A4 横 | 故事结构（四拍叙事弧） |
| `CT` | [`ct-talk.md`](ct-talk.md) | 大会演讲 / 工作坊 | 16:9 | 清晰优先（大字号少字）+ `notes` 逐页 |
| `IN` | [`in-infographic.md`](in-infographic.md) | 信息可视化 | 1:1 / 1:3 / 16:9 | 每帧有职责（无冗余像素） |
| `VM` | [`vm-concept-illustration.md`](vm-concept-illustration.md) | 概念插画 | 16:9 / 1:1 / 1:4 | 3 秒规则 + 留白 |
| `CV` | [`cv-concept-visual.md`](cv-concept-visual.md) | 单张概念图 | 1:1 / 16:9 / 4:5 | 3 秒规则 + 单一焦点 |

**卡的用法**（与另两轴**同构**：读目录 → 按名列出候选 → 取关键词拼提示词）：
1. 选**一张**卡（= 一个 `recipe`），写进 `presentation[].recipe` 与 `format_card`；
2. 卡里的 `## Prompt Recipe` **整段粘贴**（英文原样——翻成中文会给生成服务喂错语言）；
3. 卡里的 `## Format Characteristics` **逐条兑现**（帧比 / 密度 / 字阶 / 转场 / 图表处理是硬约束，不自改）；
4. 卡里的 `## Review Gate` 是**该配方的评审侧重**——8 原则是总门，这里是重点项。

**视觉语言与插图技法仍从另两轴取**：`data/styles/design-styles/`（整件气质）· `data/styles/content-styles/`（`VM` / `CV` 的成像技法）。

**源与出处**：7 条配方逐字取自 `docs/bmad-skill-map/review/b6-fidelity.md` §九（源 `bmad-cis-agent-presentation-master/customize.toml:38–:71`），由 B6 移交、B7b 落地。**8 条视觉传达原则**（源 `customize.toml:27–:36`）落 `steps/08-presentation.md` 第 5 步的评审门——**不落人设字段**（人设条目不占批次）。
