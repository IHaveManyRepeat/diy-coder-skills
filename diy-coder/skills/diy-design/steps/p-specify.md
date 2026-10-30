# Step — [P] 写规格（Specify）· 九步

Progress: `[1 页面基础] → [2 区块与排序] → [3 对象与类型] → [4 内容与语言] → [5 交互] → [6 状态] → [7 表单校验] → [8 间距与字阶] → [9 合成与落盘] → 收尾路由`

**Read (input):** `{output_dir}/design.yaml` 的 `direction` / `tokens` / 该页 `pages[]` 记录；`{output_dir}/wds-scenarios.yaml` 该页记录（WDS 线：`purpose` / `entry_context` / `exit_action` / `on_page_interactions[]`，只读）；`{output_dir}/prd.yaml` 的承接 FR 与用户可见文案要求（主线）；`data/object-types/<类型>.md`（第 3 步按对象类型取参考层）；用户在本文件各步的回答。
**Write (output):** 该页 `design.yaml` 记录的全部规格键（`name` / `route` / `states[]` 与文案）；`direction` 与 `tokens` 的**增补**（若本页暴露出 token 缺口）；`revisions`（有改动时）；`design_status` 推进到 `specified`（WDS 线：该场景**全部页**规格落定后写，场景级键，值域见主文件规则 1）。

你是**设计总监**。这一段把「这一页长什么样、怎么动、什么态」**钉死成规格**。产出**只有一处**：`{output_dir}/design.yaml`——**不生成独立规格 md**（页面规格内容逐节落进 YAML 的既有键）。

## 第 3 步的专述 —— 对象与类型（对象级规格清单的接入）

逐对象定类型（button / heading-text / text-input / image / link…），**每定一类就读一次** `data/object-types/<类型>.md`，按它的**规格项清单**逐项写该对象的规格。

**五件清单**（**保留为参考层**）：`button.md` · `heading-text.md` · `text-input.md` · `image.md` · `link.md`。

**ID 处置**：

- **对象级三级 ID 不进 diy**——对象级格式（如 `{page}-{section}-{element}-button`）**不铸**：diy 里对象级的载体是 `src` 的框架代码本身 + `states[].signals`，再铸一层 ID 是 YAGNI；
- **页级 ID 按来源线定**：主线 `P-n`、WDS 线 `SC-<nn>.P<n>`（**上游废止 `P-*` 前缀，不得另铸**）；稳定 ID 纪律（永不重编号、永不复用）两线同守；

**对象级不产独立产物**：五件清单是**参考层**（怎么问、问什么），产物仍是 `design.yaml` + `prototypes/` + `src`。

## 间距 / 字阶纪律（源最有价值的设计约束，直译）

1. **specs 永不写裸 px**——间距值只能取自 `tokens.spacing.scale`；
2. **非默认间距必须是有理由的显式项**，零间距（重叠 / 贴合）**也要写明**；
3. **光学微调走 token 算术且必须注明理由**（`space-lg - space-3xs` 而不是裸像素；跨超过一档说明基准 token 选错了）；
4. 字号同理：值必须逐字命中 `tokens.typography.scale`，否则 `audit` 判 `one-off-font-size`。

## ID 与 token 的两条硬约束

- **token 是唯一风格源**：本步新增的任何色值/字号都要先登记进 `tokens.*`，再在结构稿里引用（`var(--color-*)`）；不然 `audit` 的 `one-off-*` 会在收尾拦住你——**在这里改便宜，在收尾改贵**。
- **继承外部 UI 系统**时：把第三方库的默认色值**显式登记**进 `tokens.color`，或把库目录写进 `token_scope` 让 `audit` 跳过（两条出口二选一，写清选了哪条）。

## meta 内容键（两层判据）

- **机械层（`validate` 判）**：`pages[].meta` 三子键 `title` / `description` / `og_image` **全可选**；在场则必须非空字符串（空串与非字符串 → `EMPTY_FIELD`）；缺失不违规——内部工具可整体省略。
- **引导层（模型判，不进 validate）**：公开站点应填齐三子键——`title` 简练（建议 ≤60 字符）、`description` 一句价值主张（≤160 字符）、`og_image` 指向项目内可访问的图片资源路径（WDS 线项目常见于 `assets/`，**不限死该目录**——主线项目无 assets 时指向实际资源位置）。

判据值定案：以本三条为准（60 / 160 / 图片路径）；外部指南仅作对照登记、不逐字迁。

## 无障碍判据（两层分写）

- **机械层（`check` 判）**：`a11y-touch-target` 触控下限按 `form_factor` 分档——移动端 44 / 桌面 24 / 响应式 Web 与多端按最严端 44 / 缺键或表外值 44；`a11y-keyboard`——交互元素须可 Tab 到达（`tabindex="-1"` 移出 Tab 序、挂 `onclick` 而无 `role` 即违规）；`a11y-focus-order`——不得用正 `tabindex` 强改焦点序（`tabindex="0"` 自然序合法不报）；`a11y-reduced-motion`——动效声明（`animation`/`transition`）在场则全文须带 `prefers-reduced-motion` 降级。
- **引导层（模型判，不进 check）**：①**播报**——每个交互元素带可播报文案/语义（`role` + 状态，屏幕阅读器能念出「是什么、处于什么态」）；②**动态字号**——字号按 `tokens.typography.scale` 可放大到最大档，不截断、不塌控件（最大字号设置下 UI 仍可用）。

判据源对照（不逐字迁）：Accessibility Floor 五条——①播报、②动态字号落本条引导层；③Reduce Motion 进 check 机械层；④点击目标已落 `a11y-touch-target`（分档化）；⑤焦点遍历的键盘可达面已落 `a11y-keyboard`，正 tabindex 强改序为判据增强（`a11y-focus-order`，非五条原项）。

## 收尾与路由

规格落盘 → 读 `./prototype-loop.md`（结构稿按段建）或 `./h-delivery.md`（规格已够、直接进框架实现）。

WDS 线附带：该 `SC-<nn>` 的**全部页**规格落定后，把 `scenarios[].design_status` 推到 `specified`（**只写这一个键**，其余字段只读；该键是场景级，页级进度写 `pages[].status`）。

**检查点**：① 生成 ② 落盘本页规格键（+ 该场景全部页规格落定后的 `design_status: specified`）③ 分隔 ④ 呈出规格摘要（页 ID / 状态数 / 承接 ID / token 缺口）⑤ 给选项 ⑥ 等响应。

本文件到此结束，不再回头。
