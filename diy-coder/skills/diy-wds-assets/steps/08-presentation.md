# Step 8 — 演示 / 视觉传达（S，第 9 活动）

Progress: `[1 载受众与战略] → [2 盘点与选配方] → [3 视觉语言] → [4 逐帧骨架与提示词] → [5 帧级自检：8 原则] → [6 成套评审]`

**Read (input):** `{output_dir}/wds-brief.yaml` 的 `brief.core`（愿景 / 定位 / 产品概念）与 `{output_dir}/wds-trigger.yaml` 的 `personas[]` 与驱动因素——**二者任一在场即可**（本活动的输入灵活度高于页面资产：演示版式的输入不硬性要求 `已定稿`）；`data/presentation-formats/` **目录**（7 张配方卡，按名列出后取选中的一张）；`data/styles/design-styles/` 目录（视觉语言仍从这一轴取）。
**Write (output):** `wds-assets.yaml` 的 `activities[AS-08]` 与其 `presentation[]` 记录；`{output_dir}/assets/presentation/` 与 `prompts/`。

你是**演示生产的主持人**（源 `presentation-master` 人设的 7 配方 + 8 原则，B6 移交、B7b 落地）。这个活动与前面七个**不同域**：前七个产的是**站点构建的输入**，本活动产的是**给人看的交付物**（幻灯片 / 路演 / 演讲 / 信息图 / 概念图）。**这个跨域是被承认的**——`assets/presentation/` 是资产目录里唯一的非页面成员（同源 `[E]` 的 Figma 先例）。

**本段纪律**：① **不 1:1 建 7 条流**（裁定 7）——**一条 6 步共享骨架 × 7 个配方子模式**，配方只改「帧结构 / 必带件 / 评审侧重」三处；② **8 原则是评审门**（第 5 步）——不进人设字段、不写成口号；③ **不接外部服务**（裁定 6）——产 HTML / YAML 与提示词；**不得宣称与产品设计令牌兼容**（演示的视觉语言 ≠ 产品组件令牌，这是普查实测的硬结论）。

## 第 1 步 —— 载受众与战略（源 `presentation-master` 原则 1「懂受众」）

**先问清**：「这份东西给谁看、在什么场合看？」——**路演 / 视频缩略图 / 大会演讲是三种手艺**（源原则 1 的原话），选错受众后面全错。

**读两样**（任一在场即可，缺则回落问答并在 `revisions` 记 gap）：
1. **战略简报**——`wds-brief.yaml` 的 `brief.core`：愿景 / 定位 / 产品概念 / 目标用户 / 成功标准——**这是叙事弧的素材源**（`PD` 的 problem → solution → traction → ask 逐项对得上）；
2. **人设与驱动因素**——`wds-trigger.yaml` 的 `personas[]` 与其正负驱动因素：**听众是哪个群、他盼什么怕什么**（`CT` 的听众、`IN` 的数据叙事、`EX` 的钩子时间线同源于这一份）。

**受众画像四件**（会话内呈出）：给谁看 / 场合与时长 / 他已有的认知（会不会已经懂你的产品）/ 你要他看完之后做什么。

**产出键**：`presentation[].audience` + `activities[AS-08].status: 进行中` + `stage: 演示`。

**检查点（六拍）**：① 生成受众画像 → ② 落盘 `audience` / 活动 `status` / `stage` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 盘点与选配方`。

## 第 2 步 —— 盘点与选配方（7 配方子模式的入口）

**先问清**：「这份东西要什么形态？」——**7 个配方就是 7 种交付物形态**，选配方 = 定形态。读 `data/presentation-formats/` 目录，按名列出 7 张卡让用户挑**一张**（一张卡 = 一个 `recipe`）：

| `recipe` | 配方卡 | 交付物形态 |
| --- | --- | --- |
| `SD` | `data/presentation-formats/sd-slides.md` | 多页幻灯片（专业版式 + 视觉层级） |
| `EX` | `data/presentation-formats/ex-explainer.md` | 视频解说版式（视觉脚本 + 留人钩子） |
| `PD` | `data/presentation-formats/pd-pitch.md` | 投资人路演（数据可视化 + 叙事弧） |
| `CT` | `data/presentation-formats/ct-talk.md` | 大会演讲 / 工作坊（演讲者备注） |
| `IN` | `data/presentation-formats/in-infographic.md` | 信息可视化（视觉叙事） |
| `VM` | `data/presentation-formats/vm-concept-illustration.md` | 概念插画（鲁布·戈德堡 / 旅程地图 / 创意流程） |
| `CV` | `data/presentation-formats/cv-concept-visual.md` | 单张概念图（3 秒可懂） |

**按配方盘点**（源侧口径的落地）：`SD`/`PD`/`CT` 按**页/帧**盘——写出每一帧要干什么；`EX` 按**拍**盘（0s / 3s / 每 15–30s 一个钩子）；`IN`/`VM`/`CV` 按**张**盘（一张 = 一件）。

**配方与 `[V]` 的交界**（裁定 7 明确）：`EX` 是**两活动的交界配方**——**内容脚本（钩子时间线 / 逐拍画面）归本活动**，动效与视频落盘**走 `steps/06-motion.md` 的 `motion/` 通道**；本活动不重复实现视频通道。

**产出键**：`presentation[]` 铸条目（`id: AS-08.<m>` 递增；`recipe` 取七值之一、`format_card` 指到卡文件、`frames[]` 骨架先立起来）。

**检查点（六拍）**：① 生成配方选择与盘点表 → ② 落盘 `presentation[]` / `recipe` / `format_card` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 视觉语言`。

## 第 3 步 —— 视觉语言（设计风格轴，**不是**产品令牌）

**先问清**：「这套版式什么气质？」——读 `data/styles/design-styles/` 目录（6 张卡：`brutalist` / `corporate` / `editorial` / `minimal` / `organic` / `playful`），选一张写进 `activities[AS-08].style.design`。

**三条边界（源侧与普查的双重结论，逐条守）**：
1. **视觉语言走 design-styles，不碰产品令牌**——同一个 deck 可以是 Minimal 也可以是 Brutalist，**产品设计令牌约束不了路演版式**（用令牌约束演示是伪约束）；`items[].token_ref` **本活动留空**；
2. **插图技法走 `content-styles`**——`VM` / `CV` 的插画用 `data/styles/content-styles/` 的卡（如实测的 `isometric` 与信息可视化直接重叠），写进 `.style.content`；
3. **排版硬约束按配方卡走**——每张配方卡的属性表（帧比 / 密度 / 字阶 / 转场 / 图表处理）**逐条兑现**，不自行改写。

**产出键**：`activities[AS-08].style`（`design` 必填、`content` 按配方需要）+ `presentation[].format_card` 的属性值回填到 `frames[].notes`。

**检查点（六拍）**：① 生成视觉语言选择 → ② 落盘 `style` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 逐帧骨架与提示词`。

## 第 4 步 —— 逐帧骨架与提示词（6 步共享骨架的生成段）

**先问清**：「一帧一帧过，还是你先把骨架搭完我再看？」

**逐帧落四件**（`frames[]` 的四个键，**这是共享骨架的产物形态**）：`n`（帧号）｜ `job`（**这一帧干什么**——inform / persuade / transition，源原则 4：**没有职责的帧就剪掉**）｜ `headline`（这一帧的那句话——**一句话，不是一段**）｜ `notes`（演讲者备注 / 画面说明 / 数据来源——`CT` 必填、其余按需）。

**逐帧拼提示词**（`presentation[].prompt` 或按帧分条进 `activities[AS-08].items[]`）：配方卡的 `Prompt Recipe`（**源配方全文逐字保留英文**，见配方卡的 `## Prompt Recipe` 段）→ 受众与场合 → 帧结构与每帧职责 → 视觉语言关键词（所选 design-styles 卡的 `Prompt Keywords`）→ 画幅比（配方卡 `Aspect`）→ 密度上限（配方卡 `Density`）→ 输出形态（**HTML 优先**；几张静态图时出 HTML 拼版）。

**`SD` 配方的改机制**（裁定 7）：**保「一帧 = 一页 + 3 秒规则」**，**弃 Excalidraw 帧文件格式**——diy 侧产物是 YAML / HTML，不是 `.excalidraw`。

**产出键**：`frames[]`（四键齐）+ `presentation[].prompt` / `items[].prompt`；`prompts[]` 追加（`file: assets/presentation/prompts/<name>.md`）。

**检查点（六拍）**：① 生成逐帧表与提示词 → ② 落盘 `frames[]` / `prompt` / `prompts[]` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 5 步 —— 帧级自检：8 原则`。

## 第 5 步 —— 帧级自检：8 原则（**本活动的评审门**）

**先问清**：「逐帧看一遍——哪一帧可以砍？」

**八条视觉传达原则**（源 `presentation-master/principles` 逐字迁移；**这是评审检查表，不是人设字段**——逐条打勾，打不上的帧回去改）：

- [ ] **1 懂受众**——路演 / 缩略图 / 演讲是三种手艺：本件的画幅、字号、信息密度**匹配第 1 步的受众画像**
- [ ] **2 视觉层级驱动注意力**——眼睛的旅程是**设计出来的**：每帧有明确的第一眼、第二眼、第三眼
- [ ] **3 清晰优先于机巧**——炫技必须在**服务讯息**的前提下才留
- [ ] **4 每帧都有职责**——inform / persuade / transition，**说不出职责的帧剪掉**
- [ ] **5 三秒规则**——**三秒内能抓住核心意思吗**（逐帧计时，不是整体感觉）
- [ ] **6 留白构建焦点**——堆砌扼杀理解：密度上限按配方卡兑现
- [ ] **7 一致性即专业**——画幅 / 字号阶 / 色 / 版心**跨帧同一套视觉语言**
- [ ] **8 故事结构普适**——钩子 → 张力 → 兑付：整件从头到尾有这条弧

**配方侧重（共享骨架的子模式差异，逐条只在评审时生效）**：`PD` 重点查第 8 条（叙事弧 problem → solution → traction → ask）｜ `CT` 重点查第 3 条（大字号少字）与 `notes` 逐帧在场｜ `IN` 重点查第 4 条（**不 inform / persuade / transition 的像素一律剪**）｜ `VM` / `CV` 重点查第 5 条（可记忆性优先于全面性，第 3 秒能懂）｜ `EX` 重点查第 8 条的钩子节拍｜ `SD` 重点查第 2 条（逐页版式与视觉层级）。

**不通过时的动作**：回第 4 步改帧的 `job` / `headline`，或回第 3 步换视觉语言；**不许「先过后面再补」**。

**产出键**：`presentation[].review.principles`（八条逐条结论）+ 修订后的 `frames[]`。

**检查点（六拍）**：① 生成八条自检表 → ② 落盘 `review.principles` / 修订 `frames[]` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 6 步 —— 成套评审`。

## 第 6 步 —— 成套评审

**先问清**：「（成件放进来后）整件是通过、还是回去重做某几帧？」

**成套三查**（与源 `[U]`/`[V]` 的评审步同构）：
- [ ] **全局一致**——画幅 / 字号阶 / 色 / 版心跨帧同一套（源原则 7 的整体版）
- [ ] **叙事完整**——从钩子到兑付没有断点（把 `headline` 逐帧连起来读一遍，读不通就是断的）
- [ ] **交付可用**——导出形态能直接用（HTML 能在浏览器打开、备注能直接念）

**落盘口径**：产物落 `{output_dir}/assets/presentation/`（**子目录、不入库**，裁定 12）；`presentation[].assets[].path` 与 `items[].assets[].path` 存相对路径。
**已知缺口（登记）**：`viewer.py` 只扫顶层 `*.yaml` → `assets/presentation/` 下的成件**渲染不到**；另：本活动是资产目录里**唯一的非页面成员**，不得在文档里假装它与站点构建同域。

**产出键**：`presentation[].assets[]` + `presentation[].review.verdict` + `activities[AS-08].status: 已评审`。

**收尾动作**：更新活动级 `status` 到 `已评审`；一句话说明演示活动与其余七个是**跨域**关系（不进站点构建），`EX` 配方的动效落盘走 `steps/06-motion.md`；本文件到此结束——读 `steps/09-finish.md` 继续，或回活动菜单。

**检查点（六拍）**：① 生成成套评审表 → ② 落盘 `assets` / `review` / 活动 `status` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。
