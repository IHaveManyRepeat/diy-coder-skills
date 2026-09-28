# 对象类型：Image（对象级规格清单 · 参考层）

**用途**：`[P] Specify` 第 3 步与 `[M]` 活动逐对象定类型时，按本清单**逐项写规格**。
**规则**：本件是**参考层**——**不产独立产物、不铸对象级 ID**（对象级载体是 `src` 的框架代码 + `design.yaml` 的 `states[].signals`）。**本件不含对象级 ID、不含 Figma 字段**；§7 对照表里的「删」行是**源侧对账痕迹**，不是待办。
**改写说明**：源 `wds-4-ux-design/data/object-types/templates/image.md`（165 行）按裁定 4 改写——① **删 `OBJECT ID` 段**（源格式 `{page}-{section}-{element}-image`）；② **删 Figma 字段**（本件源侧实测 **0 处**；Design System 的组件字段一并归 `diy-wds-system`）；③ 交互问答脚手架（`<ask>Choice [1/2/3]:</ask>` + 「哪个既有 pattern / 新 pattern 叫什么」两分支）**改为下方规格项清单**；④ 「`Return to 4c-03`」幽灵步骤号引用**删**（普查 D3，该步骤号在本体系不存在）。

---

## 1. 类型判定

一个对象是图片，当且仅当：**它的语义是「视觉内容本身」**（插画 / 照片 / 图标之外的大图）。近亲要分清：

| 近亲 | 与图片的区别 | 处置 |
| --- | --- | --- |
| **图标（icon）** | 尺寸小、随文字基线、常是 SVG 符号 | 按图标记（随所属对象）；**纯图标按钮的 `aria-label` 见 `button.md`** |
| **背景图** | 是装饰，不承载信息 | 按装饰处理：`role="presentation"` + **空 `alt`**（不是省略 `alt`） |
| **图表 / 数据可视化** | 承载数据，有数值语义 | 单列一类；必须给**文字摘要**作等价物 |
| **视频 / 动图** | 有时序 | 单列一类；必须给**静态回退** |

## 2. 规格项清单

| # | 项 | 必填 | 取值 / 判据 | 落点 |
| --- | --- | --- | --- | --- |
| 1 | **用途** | 是 | 内容图（承载信息） / 插画（氛围） / 装饰（无信息）——三选一，**决定 `alt` 怎么写** | 规格叙述 + 结构稿 `alt` |
| 2 | **来源** | 是 | 文件路径 / 远程 URL / 生成物——**写清是哪种** | 结构稿 `src`，或 `diy-wds-assets` 的 `assets[]` 引用（横切产出面） |
| 3 | **替代文本（`alt`）** | 是 | 内容图：一句话说清**它传达什么**（不是「一张图」）；装饰图：**空 `alt` + `role="presentation"`** | 结构稿元素属性——`check` 的 `semantic-html` 判据面 |
| 4 | **尺寸与宽高比** | 是 | 宽 / 高 / 比例 / 适配方式（`cover` / `contain` / `fill`） | 结构稿 CSS；**必须给宽高**（否则布局抖动） |
| 5 | **响应式尺寸** | 否 | 窄 / 中 / 宽三档各自的尺寸 | 结构稿 CSS + 断点行为叙述 |
| 6 | **高清（@2x）** | 否 | 有无 2 倍图；有则写路径 | 结构稿 `srcset` |
| 7 | **加载策略** | 是 | 首屏关键图 / 懒加载；是否给低清占位 | 结构稿 `loading` / `fetchpriority` |
| 8 | **加载态** | 是 | 占位形态（纯色 / 骨架 / 模糊） | `states[].signals` 的 `加载中` 态 |
| 9 | **错误态** | 是 | 回退图 / 是否显示错误提示 | `states[].signals` 的 `错误` 态 |
| 10 | **色与风格约束** | 否 | 是否必须与 `direction` 的调性一致（暖冷、颗粒、对比） | 规格叙述（评审四项里的「氛围」） |

## 3. 替代文本的写法（本件最容易做错的一条）

| 用途 | `alt` 写法 | 反例 |
| --- | --- | --- |
| **内容图** | 说清它**传达的信息**：「趋势图显示 9 月留存回落到 40%」 | `alt="图片"` / `alt="chart.png"` |
| **插画（氛围）** | 一句话点功能：「忙碌一天后打开应用放松的场景」 | 长篇描述画面细节 |
| **装饰** | **空 `alt`**（`alt=""`）+ `role="presentation"` | 省略 `alt` 属性（`check` 会判 `semantic-html` 违规） |
| **图标（随按钮）** | 由**按钮**承载名称（`aria-label`），图标自身 `aria-hidden="true"` | 图标自己写 `alt` 导致读两遍 |

**判据**：把图拿掉、只读 `alt`，用户能不能知道这里有什么信息——不能就重写。

## 4. 状态清单（三态 + 加载策略）

| 态 | 必须写清 | 备注 |
| --- | --- | --- |
| **加载中** | 占位形态 + 是否懒加载 | 占位必须与最终尺寸**同比例**（否则布局抖动，CLS 超标） |
| **加载完成** | 是否需要淡入 / 动效时长 | 动效不是必须；有就写时长与缓动 |
| **错误** | 回退图 / 错误提示 / 是否隐藏 | 内容图**必须**给回退（否则信息直接丢） |

**懒加载判据**：首屏内 → **不懒加载**（`loading="eager"`，首图可加 `fetchpriority="high"`）；首屏外 → `loading="lazy"`。

## 5. 交互与无障碍

| 项 | 判据 |
| --- | --- |
| 可点击吗 | 图片**本身不承载点击**；要点击就包一层链接或按钮（`link.md` / `button.md`），并给链接/按钮名称 |
| 放大 / 查看大图 | 若支持，写清触发方式（点击 / 悬停放大）与**键盘可达性**（必须能 Tab 到并 Enter 打开） |
| 对比度 | 图上的叠加文字要有可读性保障（加遮罩层或用 `tokens.color` 的实底），**不靠碰运气** |
| 减少动效 | 用户的 `prefers-reduced-motion` 生效时，跳过淡入 |

## 6. 示例

```html
<!-- 内容图：有描述性 alt、有宽高、首屏不懒加载 -->
<img src="/assets/hero-trend.png" width="960" height="540"
     alt="趋势图显示 9 月留存回落到 40%" fetchpriority="high" />

<!-- 纯装饰：空 alt + role -->
<img src="/assets/grain.png" alt="" role="presentation" />

<!-- 首屏外的照片：懒加载 + 低清占位 -->
<img src="/assets/team.jpg" width="800" height="600" loading="lazy"
     alt="团队在会议室讨论下一步排期" />
```

```yaml
# design.yaml 该页记录片段（图片错误态必须有回退）
pages:
  - id: P-1
    states:
      - {name: 悬停,  signals: [遮罩淡入]}
      - {name: 空态,  signals: [文字: 还没有图片，拖一张进来]}
      - {name: 加载中, signals: [形状: 同比例灰色占位]}
      - {name: 错误,  signals: [文字: 图片没能载入, 图标: 破图]}
```

## 7. 落点对照表（源字段 → diy 键）

| 源字段（image.md） | diy 落点 | 说明 |
| --- | --- | --- |
| `image_description` | 用途项（§2 第 1 项） | — |
| `object_id` | **删** | 裁定 7 |
| `design_system_component` / `component_status` | **归 `diy-wds-system`** | 图片 pattern（Hero / Avatar / Card）若成库，归它的 `components[]` |
| 图片文件名 / 路径 | 结构稿 `src`；资产落点见 `diy-wds-assets` | **不复制**远程资源的本地副本到技能目录 |
| `alt_text_en` / `alt_text_sv` | 替代文本项（逐语言一条） | §3 的写法表 |
| `is_decorative` | 用途项 = 装饰 → 空 `alt` + `role` | — |
| `width` / `height` / `aspect_ratio` / `object_fit` | 尺寸与宽高比项 | 宽高必填（防抖动） |
| `mobile_size` / `tablet_size` / `desktop_size` / `retina_path` | 响应式尺寸项 / 高清项 | 可选 |
| `placeholder_type` / `lazy_loading` | 加载态项 / 加载策略项 | — |
| `loading_state` / `error_fallback` / `loaded_animation` | `pages[].states[]` 三态信号 | 错误态回退必填 |
| `Return to 4c-03`（源 `:165` 末行） | **删** | 幽灵步骤号（普查 D3）；diy 的回报路径由 `steps/` 的路由句承担 |
