# Step — [P] 写规格（Specify）· 九步

Progress: `[1 页面基础] → [2 区块与排序] → [3 对象与类型] → [4 内容与语言] → [5 交互] → [6 状态] → [7 表单校验] → [8 间距与字阶] → [9 合成与落盘] → 收尾路由`

**Read (input):** `{output_dir}/design.yaml` 的 `direction` / `tokens` / 该页 `pages[]` 记录；`{output_dir}/wds-scenarios.yaml` 该页记录（WDS 线：`purpose` / `entry_context` / `exit_action` / `on_page_interactions[]`，只读）；`{output_dir}/prd.yaml` 的承接 FR 与用户可见文案要求（主线）；`data/object-types/<类型>.md`（第 3 步按对象类型取参考层）；用户在本文件各步的回答。
**Write (output):** 该页 `design.yaml` 记录的全部规格键（`name` / `route` / `states[]` 与文案）；`direction` 与 `tokens` 的**增补**（若本页暴露出 token 缺口）；`revisions`（有改动时）；`design_status` 推进到 `specified`（WDS 线：该场景**全部页**规格落定后写，场景级键，值域见主文件规则 1）。

你是**设计总监**。这一段把「这一页长什么样、怎么动、什么态」**钉死成规格**。产出**只有一处**：`{output_dir}/design.yaml`——**不生成独立规格 md**（源侧那套 314 行页面规格模板 `templates/page-specification.template.md` 的内容，逐节落进 YAML 的既有键，见下表）。

〔**关键裁撤声明**〕源 `step-09` 是「合成整份规格文档并落盘 `{page}/{page}.md`」；diy 侧**该动作整块裁**——`design.yaml.pages[]` 就是规格本体，第二份 md 即第二份源（违单一源），且它与 YAML 必然漂移。

## 九步 → diy 键位映射（源 `steps-p/` 9 文件 1,323 行）

| 源步 | 源文件 / 行 | 做什么 | diy 落点 |
| --- | --- | --- | --- |
| 1 | `step-01-page-basics.md` 129 | 页面标题 / 路由 / 用户目标 / 出入口 | `pages[].name` / `route`；出入口引上游 `entry_context` / `exit_action` |
| 2 | `step-02-layout-sections.md` 124 | 区块划分与排序 | `prototypes/<页 id>.html` 的区块顺序（`[W]` 段）+ 第 9 步的摘要 |
| 3 | `step-03-components-objects.md` 176 | 逐对象定类型、分配 Object ID | `states[].signals` + `src` 的框架代码；**对象级三级 ID 裁**（见下「ID 处置」） |
| 4 | `step-04-content-languages.md` 127 | 全部文案 × 全部语言 | `document_output_language` 下的文案串；多语言项目逐语言确认（**不编造翻译**） |
| 5 | `step-05-interactions.md` 121 | 逐组件交互行为 | `states[]` 的 `悬停` 等态 + 结构稿里的行为；行为契约归 `stories.yaml` 的 AC（引用不复述） |
| 6 | `step-06-states.md` 149 | 页面级 + 组件级状态 | `pages[].states[]`（**四态不许省**，每态 ≥1 条非色彩信号） |
| 7 | `step-07-validation.md` 149 | 表单校验规则与错误文案 | 错误态信号（`错误: {signals: [...]}`）+ `diy-test-design` / `diy-e2e-tests` 的测试面（本技能不持校验实现） |
| 8 | `step-08-spacing-typography.md` 210 | 间距对象与字阶 token | `tokens.spacing.scale` / `tokens.typography.scale`（**值不在表里就不该出现**，见下「间距/字阶纪律」） |
| 9 | `step-09-generate-spec.md` 138 | 合成整份规格 + 更新设计日志 | **裁**（见上）；改为**回读自检**：跑 `check` 逐条比对本页 `states[]` 与结构稿 |

## 第 3 步的专述 —— 对象与类型（对象级规格清单的接入）

逐对象定类型（button / heading-text / text-input / image / link…），**每定一类就读一次** `data/object-types/<类型>.md`，按它的**规格项清单**逐项写该对象的规格。

**五件清单**（源 `data/object-types/templates/` 五件，1,689 行，按裁定 4 改判**保留为参考层**）：`button.md` · `heading-text.md` · `text-input.md` · `image.md` · `link.md`。

**ID 处置（裁定 7 订正后的口径）**：

- **对象级三级 ID 不进 diy**——源格式 `{page}-{section}-{element}-button`（`Object Registry` 双向核对的键）**不铸**：diy 里对象级的载体是 `src` 的框架代码本身 + `states[].signals`，再铸一层 ID 是 YAGNI；
- **页级 ID 按来源线定**：主线 `P-n`、WDS 线 `SC-<nn>.P<n>`（**上游废止 `P-*` 前缀，不得另铸**）；稳定 ID 纪律（永不重编号、永不复用）两线同守；
- **净损失登记**：源侧「全部 Object ID 100% 进登记表、无孤儿」的双向核对能力（`steps-v/step-06`）**净损失**，入能力损失台账（裁定 7 连带）；替代物是结构稿的 HTML 语义 + `states[].signals` 的可读性。

**对象级不产独立产物**：五件清单是**参考层**（怎么问、问什么），产物仍是 `design.yaml` + `prototypes/` + `src`。

## 间距 / 字阶纪律（源最有价值的设计约束，直译）

1. **specs 永不写裸 px**——间距值只能取自 `tokens.spacing.scale`（源 `DESIGN-LOOP-GUIDE.md:83-101` 原文 `If a spacing value isn't in the scale, it doesn't belong in the spec`）；
2. **非默认间距必须是有理由的显式项**，零间距（重叠 / 贴合）**也要写明**（源模板 `:157-179`）；
3. **光学微调走 token 算术且必须注明理由**（`space-lg - space-3xs` 而不是裸像素；跨超过一档说明基准 token 选错了）；
4. 字号同理：值必须逐字命中 `tokens.typography.scale`，否则 `audit` 判 `one-off-font-size`。

## ID 与 token 的两条硬约束

- **token 是唯一风格源**：本步新增的任何色值/字号都要先登记进 `tokens.*`，再在结构稿里引用（`var(--color-*)`）；不然 `audit` 的 `one-off-*` 会在收尾拦住你——**在这里改便宜，在收尾改贵**。
- **继承外部 UI 系统**时：把第三方库的默认色值**显式登记**进 `tokens.color`，或把库目录写进 `token_scope` 让 `audit` 跳过（两条出口二选一，写清选了哪条）。

## meta 内容键（C·7 · 两层判据）

- **机械层（`validate` 判）**：`pages[].meta` 三子键 `title` / `description` / `og_image` **全可选**；在场则必须非空字符串（空串与非字符串 → `EMPTY_FIELD`）；缺失不违规——内部工具可整体省略。
- **引导层（模型判，不进 validate）**：公开站点应填齐三子键——`title` 简练（建议 ≤60 字符）、`description` 一句价值主张（≤160 字符）、`og_image` 指向项目内可访问的图片资源路径（WDS 线项目常见于 `assets/`，**不限死该目录**——主线项目无 assets 时指向实际资源位置）。

判据值定案（SS-030-08）：以本三条为准（60 / 160 / 图片路径）；源 `_bmad/wds/data/agent-guides/freya/meta-content-guide.md`（495 行）仅作对照登记、不逐字迁。

## 收尾与路由

规格落盘 → 读 `./prototype-loop.md`（结构稿按段建）或 `./h-delivery.md`（规格已够、直接进框架实现）。

WDS 线附带：该 `SC-<nn>` 的**全部页**规格落定后，把 `scenarios[].design_status` 推到 `specified`（**只写这一个键**，其余字段只读；该键是场景级，页级进度写 `pages[].status`）。

**检查点**：① 生成 ② 落盘本页规格键（+ 该场景全部页规格落定后的 `design_status: specified`）③ 分隔 ④ 呈出规格摘要（页 ID / 状态数 / 承接 ID / token 缺口）⑤ 给选项 ⑥ 等响应。

**裁撤登记（源侧缺陷台账）**：源 `step-03:86` 的 `Load and execute object-types/object-router.md` 是**缺前缀的错路径**（普查 D12，实测 `steps-p/object-types` 不存在）——diy 侧改用 `data/object-types/<类型>.md` 的**直读**，不复制那套 router 流程（router 三件：`object-router.md` 349 / `ROUTER-FLOW-DIAGRAM.md` 275 / `workflow.md` 127 按裁定 4 裁撤）。源 `step-03:93` 的跨技能路径 `workflows/wds-7-design-system/design-system-router.md` **实测不存在**（普查 D13 / X11），**裁**。

本文件到此结束，不再回头。
