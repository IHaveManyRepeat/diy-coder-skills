# Step — [K] 草图解读（Analyse Sketches）

Progress: `[1 收草图（三形态）] → [2 整体读图定标尺] → [3 识别区块] → [4 结构确认（硬门）] → [5 逐区解释与修正] → [6 收尾路由]`

**Read (input):** 用户提供的草图（**描述 / 图片 / 文件引用**三形态之一，见第 1 步）；`{output_dir}/design.yaml` 的既有页记录与同场景其它页（跨页比对：导航、共享组件、布局约定）；`data/object-types/*.md`（逐区解释时按对象类型取参考层）。
**Write (output):** 该页的**分区结构与对象清单**（会话内定稿后并入 `design.yaml` 的 `pages[]`）；疑似复用组件的提议（转 `diy-wds-system` 处置）；草图原件落 `{output_dir}/prototypes/`；`design_status` 推进到 `discussed`（WDS 线：该场景全部页结构确认后写，场景级键，值域见主文件规则 1）。

你是**设计总监**。K 是**可选入口**：用户手里已经有草图（手绘 / 截图 / 线框）时走它——**整体读图 → 识别区块 → 用户确认结构 → 才进详细规格**。源侧该活动的 `STEP GOAL` 原文是 `User confirms structure before detailed specification begins`——**这正是「先草图后 HTML，大结构才更正确」的机制**。

**本段纪律**：① **结构确认是硬门**（源 `steps-k/step-01:37` `🚫 FORBIDDEN to generate detailed specifications without user confirmation of structure`，`:46` 同义重复）——没点头不许进 `[P]`；② **K 只做识别，不写终稿规格**（源 `:52` `Limits: Do not generate final specifications — that is the Specify activity`）；③ **跨页比对不可省**（源 `:83-87` Cross-Page Pattern Matching）。

## 第 1 步 —— 收草图（三形态）

源 `steps-k/step-01:61-67` 三选项**照收**：

| 形态 | diy 侧处置 |
| --- | --- |
| **描述**（用户口述） | 直接进入第 2 步，把描述当图读 |
| **图片**（截图 / 拍照 / 手绘扫描） | 走多模态**直读**（不转文字再读，避免两跳失真） |
| **文件引用**（文件名 / 路径） | 读该文件（多模态或文本）；**原件复制/落到 `{output_dir}/prototypes/`**（裁定 4 / X12 的落点归一：源侧 `Sketches/` 与 `sketches/` 两派大小写一律废止，统一 `prototypes/`） |

## 第 2 步 —— 整体读图定标尺

源 `steps-k:71-75` 的 `Establish Scale First` **照译**：

1. 先看**本项目已分析的页**有没有既定字阶/间距（`design.yaml.tokens` 是唯一风格源，直接取）；
2. 再看图里的 **UI 锚点**（浏览器边框、滚动条、按钮、图标）校准比例；
3. 两者都没有 → 用一个可问的锚点问用户一次（如「这张图的宽度大约是几栏」），**不猜**。

## 第 3 步 —— 识别区块

把图切成逻辑区块（header / hero / features / cards / footer…），逐区块判**边界**（留白、视觉分组、布局）与**用途**（从视觉语境判，不从文字判——文字可能还没写）。

**条件分支**（源 `:159` 的 `<check if="any_sections_look_like_components">` 直译）：某个区块像**复用组件**（同场景其它页也有类似形态）→ **提议提为组件**，用户同意则转 `diy-wds-system`（组件身份与 token 归它，本技能只报候选，**不自行铸组件**）。

## 第 4 步 —— 结构确认（硬门）

呈出**分区图 + 每区一行用途 + 跨页比对结论**，然后**等确认**。

- 用户点头 → 进第 5 步；
- 用户改分区（拆/并/删/加）→ 改完**重呈**，循环到点头为止（源 `:152` `Loop until user confirms structure`）；
- **没点头不许往下走**——这一步是 K 存在的意义，**不得省略**（源 `:37` 的 FORBIDDEN 句）。

## 第 5 步 —— 逐区解释与修正循环

对每个已确认的区块，逐区解释（源 `:152-282` 的 3A 递归解释 + 3B 用户修正循环）：

1. **解释什么在这里**：区块内有哪些对象（按对象类型：button / heading-text / text-input / image / link…），每个对象的作用与大致规格；
2. **对象级规格清单**：解释到某类对象时，读 `data/object-types/<类型>.md` 取该类型的**规格项清单**（这些清单是参考层，**不产独立产物、不铸三级 ID**——对象级载体是 `src` 的框架代码 + `states[].signals`）；
3. **用户修正**：不对就改，改完**重述该区**，循环到用户确认（源 `:282` `Loop until user confirms`）；
4. **文案与翻译**：图上可读的实际文字**原样取用**（当起始建议，可改）；图上是占位线时不编造文案——文案留到 `[P]` 的 `states[].signals` 与 `direction` 里逐条确认。

### 极简草图约定（承裁定 4 改判）

用户给的是**极简手绘**（几根线代替文字）时，可用源侧 `TEXT-DETECTION-PRIORITY.md` 的核心判据：

- **两横线成对 = 一行文字**（一对线 = 一行）；
- **单横线 = 装饰**（分隔线 / 边框 / 下划线），**不是**文字；
- 例外：极简缩略图可能用单线代替文字，但**默认按「单线 = 装饰」判**。

**语义可辨的草图直接读，不用此约定**——约定只在「图里没有可辨文字、只有线条」时启用（源侧全文 391 行只取这一小段，其余笔画推理按裁定 4 裁撤）。

## 第 6 步 —— 收尾路由

结构已确认、对象清单已出 → 读 `./p-specify.md` 把识别结果写成规格（源的回报路径 `workflow-sketch.md:39` `After sketch analysis, the page returns to step-01-exploration.md's flow` 直译：K 结束后**交回主流程**，主流程决定下一步是 `[P]` 还是 `[W]`）。

**检查点**：① 生成 ② 落盘（分区结构 + 对象清单 + 草图落 `prototypes/`）③ 分隔 ④ 呈出 ⑤ 给选项 ⑥ 等响应。

WDS 线附带：该 `SC-<nn>` 的**全部页**结构确认（第 4 步硬门过）后，把 `scenarios[].design_status` 推到 `discussed`（**从当前值推进即可**，不假定 `not-started`；**只写这一个键**，其余字段只读；该键是场景级，页级进度写 `pages[].status`）。

**裁撤登记（裁定 4 / 裁定 2）**：源 `SKETCH-TEXT-ANALYSIS-GUIDE.md`（532）+ `SKETCH-TEXT-QUICK-REFERENCE.md`（222）**整块裁撤**（笔画厚度→字重、间距→字号、行长→字容量的推理链是给手绘图用的；diy 的规格真源是 `design.yaml.tokens` 与 `states[].signals`，不靠线宽反推）；上文「极简草图约定」是这两份文件唯一被救的判据。

本文件到此结束，不再回头。
