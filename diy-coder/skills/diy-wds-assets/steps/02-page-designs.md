# Step 2 — 页面稿（P）

Progress: `[1 载四源上下文] → [2 就绪度评估] → [3 双库合并令牌] → [4 桌面先行生成] → [5 合规与跨页评审]`

**Read (input):** `{output_dir}/wds-scenarios.yaml` 的 `scenarios[].pages[]`；`{output_dir}/wds-design-system.yaml`（**全量令牌**：色 / 字阶 / 组件 / 间距 / 边影——这一步必须读全，不是可选）；`{output_dir}/wds-brief.yaml` 的 `brief.visual`（视觉方向：品牌 / 情绪 / 摄影 / 插画）；`{output_dir}/assets/wireframes/` 的已批准线框（自产回读）；`data/styles/design-styles/` + `data/styles/content-styles/` 目录。
**Write (output):** `wds-assets.yaml` 的 `activities[AS-02]`；`{output_dir}/assets/page-designs/` 与 `prompts/`。

你是**页面稿生产的主持人**（源 `steps-p/` 五步）。页面稿回答的是**长相**问题——同一个结构，配色、字体、组件、图像怎么落。**它必须压在上一步的线框上**，不能另起一套布局。

**本段纪律**：① **不接外部服务**（裁定 6）——第 4 步产提示词与 HTML，不调任何生成服务；② **令牌是唯一风格源**（裁定 5 的连带：`design.yaml.tokens` 是主线单一源，本线的 `wds-design-system.yaml` 由它派生）——提示词里的色值 / 字阶**逐值引用令牌键**，不凭手感写 hex；③ **就绪度不合格的页先别做**（第 2 步），硬做出来的稿子回头一定要重做。

## 第 1 步 —— 载四源上下文（源 `steps-p/step-01`）

**先问清**：「这批页面稿要做哪几页？线框都批过了吗？」

**四源读全**（源侧口径，缺一源就在摘要里点出缺口、别装作齐了）：
1. **页面规格**——`wds-scenarios.yaml` 的 `scenarios[].pages[]`（这次读的目的 / 入口 / 离页动作 / 页内交互都要）；
2. **完整设计系统**——`wds-design-system.yaml`：色板 / 字阶 / 组件定义 / 间距阶 / 边影；**这一步是全量读，不是可选读**；产物不存在时**先停下来路由 `diy-wds-system`**（页面稿没有令牌就没有单一风格源），除非用户明确要走「无设计系统的独立定义」降级；
3. **视觉方向**——`wds-brief.yaml` 的 `brief.visual`（品牌 / 情绪板 / 摄影方向 / 插画风格）；缺则记 gap；
4. **已批准线框**——扫 `{output_dir}/assets/wireframes/`：能对上的页标 `线框已批`，对不上的标 `无线框`（进第 2 步的就绪度）。

**产出键**：上下文摘要为会话内产出（不落盘）；`activities[AS-02].status: 进行中` + `stage: 页面稿`。

**收尾动作**：呈出四行摘要——页清单 / 令牌数 / 线框数 / 文案就绪情况，**四个数字都要是真数出来的**。

**检查点（六拍）**：① 生成摘要 → ② 落盘活动 `status` / `stage` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 就绪度评估`。

## 第 2 步 —— 就绪度评估与依赖阻断（源 `steps-p/step-02`）

**先问清**：「这几页里，哪一页的料还没齐？」

**就绪度四问**（逐页过，写下结论）：① 线框已批？（未批的页**建议先回 `steps/01-wireframes.md`**）② 真实文案有了？（没有就先跑文案活动，别用 `Lorem ipsum` 充数）③ 源图有了？④ 组件齐了？

**依赖阻断页标记**：源图缺 → **建议先跑 `steps/05-images.md`**；图标缺 → **建议先跑 `steps/04-icons.md`**；组件缺 → 回 `diy-wds-system` 补组件定义。**阻断页不进本轮 `items[]`**（做一半的稿子比没做更耗），标 `已跳过` 并写明阻断原因。

**范围选择**：`all` / `select` / `missing`——写进 `activities[AS-02].scope`。

**产出键**：`activities[AS-02].items[]`（只收就绪的页；`id: AS-02.<m>` 递增铸号；`name` / `pages` / `size` / `spec` 非空）+ 阻断页清单（会话内呈出，写进 `revisions` 一条）。

**检查点（六拍）**：① 生成就绪度表 + 阻断清单 → ② 落盘 `items[]` / `scope` / `revisions` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 双库合并令牌`。

## 第 3 步 —— 双库合并令牌（源 `steps-p/step-03`）

**先问清**：「这批页面稿走哪张设计风格卡？成像技法要不要指定？」

**设计风格**（`data/styles/design-styles/` 6 张卡，逐名列出）：`brutalist` / `corporate` / `editorial` / `minimal` / `organic` / `playful`——写进 `activities[AS-02].style.design`。
**内容风格**（`data/styles/content-styles/` 10 张卡，**按需**选，纯摄影站可整项跳过）：`3d-render` / `comic-book` / `flat-design` / `hyper-realistic` / `illustration` / `isometric` / `line-art` / `pencil-sketch` / `photorealistic` / `watercolor`——写进 `.style.content`。

**三向合并**（源侧口径，这是本步的实质）：**设计风格卡（间距感 / 描边 / 影） + 内容风格卡（成像技法） + 设计系统令牌（色 / 字 / 间距）**。冲突时**令牌赢**——风格卡说的是气质，令牌说的是这个项目的具体值。逐条 `items[].token_ref` 写清这条稿压的是哪几个令牌键（如 `color.primary` / `typography.heading-1` / `spacing.md`）。

**尺寸**：桌面 / 移动两档与线框同值（`"1440x900"` / `"390x844"`）——不一致就等于换了一套栅格。

**产出键**：`activities[AS-02].style`（`design` 必填）+ `items[].token_ref`（可空：无设计系统降级时留空）+ `items[].size`。

**检查点（六拍）**：① 生成选择与映射表 → ② 落盘 `style` / `token_ref` / `size` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 桌面先行生成`。

## 第 4 步 —— 桌面先行生成（源 `steps-p/step-04`）

**先问清**：「桌面稿先出，还是桌面移动一起出？」——**默认桌面先行**（源侧口径：批准的桌面件作移动端的参考，跨端不漂）。

**逐页拼提示词**（`items[].prompt` 一整段，可整段粘贴）：布局（按线框的结构，写清区块顺序与高度关系）→ **hex 色板**（从令牌取，逐色写明用途，如「主色 `#2563EB` 用于主行动）」→ 字体（字族 + 字重 + 字号从令牌取）→ 风格关键词（所选卡的 `Prompt Keywords`，**逐词保留英文**）→ **真实文案**（贴本页的实际文字，不写「heading text」）→ 组件（用完的组件名与变体）→ 图区（尺寸 + 内容描述 + 成像技法）→ 尺寸。

**桌面批准后再做移动端**：移动端提示词**带上已批准的桌面件作参考**（源侧口径），不是重写一遍——差异只写响应式塌陷规则。

**产出键**：`items[].prompt` / `prompt_lang`；`prompts[]` 追加 `{id, activity: AS-02, target, file: assets/page-designs/prompts/<name>.md, exported: false}`；提示词文件落 `{output_dir}/assets/page-designs/prompts/`。

**检查点（六拍）**：① 生成提示词 → ② 落盘 `prompt` / `prompts[]` / 提示词文件 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 5 步 —— 合规与跨页评审`。

## 第 5 步 —— 合规与跨页评审（源 `steps-p/step-05`）

**先问清**：「（生成件放进来后）这批页面稿哪几页要返工？」

**设计系统合规五查**（源侧原口径，逐条过）：
- [ ] **色**：稿上出现的每个色值都能在令牌里找到（**出现令牌外的色 = 不合规**，这是 `design.py audit` 会抓的同一个病）
- [ ] **字**：字阶未自造级（只用令牌里的字号）
- [ ] **间距**：用间距阶的档位，不出现 13px 这类手改值
- [ ] **组件**：页上组件与设计系统的组件定义对得上（变体 / 态没有自造）
- [ ] **响应式**：移动档是塌陷出来的，不是另一套布局

**跨页一致五查**：导航 / 页脚 / 主色 / 字阶 / 视觉节奏——五样跨页必须一致，**逐对页核对**（不是抽样）。

**四个分支**：`[A]` 全批通过 ｜ `[R]` 重生指定 ｜ `[S]` 调风格重生全部（回第 3 步）｜ `[D]` 细节编辑 ｜ `[C]` 并排对比呈出。

**落盘口径**：产物落 `{output_dir}/assets/page-designs/`（**子目录、不入库**）；`items[].assets[].path = assets/page-designs/<name>.html`。
**已知缺口（登记）**：`viewer.py` 只扫顶层 `*.yaml` → `assets/` 下的页面稿**渲染不到**，评审结论只在 `wds-assets.yaml` 里可见。

**产出键**：`items[].assets[]` + `items[].review`（合规五查 + 跨页五查结论 + `verdict`）+ `activities[AS-02].status: 已评审`。

**收尾动作**：更新活动级 `status` 到 `已评审`；一句话说明页面稿之后通常接 UI 件与图标（页面稿会把用到的组件与图标清单抛给后两个活动）；本文件到此结束——读 `steps/03-ui-elements.md` 继续，或回活动菜单。

**检查点（六拍）**：① 生成评审表 → ② 落盘 `assets` / `review` / 活动 `status` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。
