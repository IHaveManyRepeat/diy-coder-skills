# 复杂度路由与分解教练（COMPLEXITY-ROUTER 的 [M] 侧收编）

- **源**：`wds-4-ux-design/data/object-types/COMPLEXITY-ROUTER.md`（842 行，独占资产）
- **引用方**：`wds-4/steps-m/step-02-define-component.md:77`（「Reference `../data/object-types/COMPLEXITY-ROUTER.md`」）
- **本批归属（自检打回后裁定）**：**归 `diy-wds-system`**——它是 `[M]` 活动的复杂度路由，且是 842 行独占资产（丢了即净损失）。
  **只落 `[M]` 一侧**；`[K]`（`data/object-types/workflow.md`）/`[P]` 侧的引用在 **C·3 按需回接**，本批不建那两侧。
- **收编口径**：源是「单组件定义过程中」的教练对话流；diy 侧**去掉对话壳与三文件扇出**（那三份文件是 [P] 的模块化产物位，属 C·3），**保留判定表、三条路由与内容放置规则**——它们是可执行的能力本体。

## 1. 复杂度判定（源 STEP 2 的指标表；[M] step-02 收成三级）

源侧只分两档（simple / complex）；`[M]` 的 `step-02:79–81` 分三级（Simple / Moderate / Complex）。**diy 取三级**，指标沿用源表：

| 档 | 源指标（命中任一即落该档） |
| --- | --- |
| **Simple** | 单状态（无 hover / active / loading 变体）· 无用户交互（纯展示）· 无数据依赖 · 无业务规则 |
| **Moderate** | 多元素 + 若干状态（2 个）· 有交互但无状态机 · 有数据依赖但不跨组件 |
| **Complex** | 3+ 状态（empty / loading / active / completed / error）· 时间驱动变化（倒计时、定时器、实时）· 多步交互（预约 → 开始 → 完成）· 业务规则（校验、权限、阻断）· 数据同步（改动其他组件）· 状态机（有定义的迁移路径） |

源给的三个标定例（`COMPLEXITY-ROUTER.md:430–495`）逐字保留：**Simple** = 静态文字 / 图片 / 基础按钮；**Complex** = 日历组件 / 预约系统 / 带筛选的搜索 / 多步表单；**Moderate** = 源侧未单列（本档是 `[M]` 的收口），判据 = 「多元素 + 若干状态，但无状态机」。

## 2. 三条路由

| 档 | 路由 | diy 落点 |
| --- | --- | --- |
| **Simple** | 源 Path A：**在页规格里就地记录**，不进设计系统 | 单条 `components[]` 记录即可（`complexity: simple`）——`states` 至少 1 条 |
| **Moderate** | 源 Path B 的轻量形态：记录 + **标注待分解** | 单条 `components[]` + 在 `notes` 一句写清「哪一部分将来会独立」（`complexity: moderate`） |
| **Complex** | 源 Path B：**分解教练**——把组件拆成 WHERE / HOW / WHAT 三问，逐问落位 | `complexity: complex` + **拆成多条 `components[]`**（父件 + 子件各占一条记录，各自铸号），父件的 `related` 列出子件 ID |

**源 Path B 的三问 → diy 承载位**（`COMPLEXITY-ROUTER.md:120–305` 的分解工作流）：

| 源问 | 源落点（三文件扇出，属 [P]/C·3） | diy 落点（本技能） |
| --- | --- | --- |
| **WHERE**（出现在哪、多大、什么位置） | `Pages/<n>-<name>.md` | `components[].usage`（何时用 / 何时不用）+ `used_in[]` 引 `SC-<nn>.P<n>` |
| **HOW**（每个状态长什么样） | `Components/<name>.component.md` | `components[].styling` + `states[]` + `variants[]` |
| **WHAT**（怎么动、什么业务规则） | `Features/<name>.feature.md` | `components[].behavior`（交互 / 动画 / 规则） |

**分解的判据（承源）**：先问用户「要不要拆」（源 `<ask>` 二选一）；**用户不拆也可放行**，但要把源给的警示原样带出——「这可能产生一份过大的规格，维护成本会上升」。**绝不替用户拆。**

## 3. 内容放置规则（源 `Content Placement Decision Tree`，:779–820）

源问「这段内容会不会随它出现的位置而变」：

- **会变 → 归页**（源 Page File）：标题、正文、图片、按页变化的数据接口、作用域
- **不变 → 归组件 / 功能**（源 Feature File）：按钮文案、通用报错、通用 tooltip、恒定的数据接口
- **视觉规格不进内容桶**（源 Component File 只放视觉）

**diy 化**：本技能只产组件 → 判据落成一句话写进 `components[].usage.when_to_use` 或 `notes`：
**「这条内容换一页还成立吗？」** 不成立 → 它属页面，别写进组件记录。

## 4. 源侧列的收益（`KEY BENEFITS`，:727–790；作为本路由的存在理由保留）

1. **防规格膨胀**——单文件从 800 行降到「100 + 150 + 200 三份」，各自可读；
2. **交接清晰**——视觉侧拿 Components、实现侧拿 Features、设计侧拿 Pages，三方各取所需；
3. **防原型漏项**——源侧复盘的真实事故：leaderboard 没进组件文件、日历状态没文档化、周视图只画 5 天；
   分解后「组件文件显式列出全部视觉元素、功能文件显式列出全部交互、故事板画出全部状态」。

**diy 侧的第四条（本批补白）**：分解后的子件各占一条 `components[]` 记录，**因此它们也各自铸 ID**——
下游页面规格按 ID 引用子件，不需要知道父件的内部结构。

## 5. 边界

- **不接外部服务**：源该文件内的 Figma 引用（Mode B）随裁定 6 裁掉，本收编版不含。
- **不落三文件扇出**：`Pages/` / `Components/` / `Features/` 目录树是 `[P]` 的产物位，**归 C·3 的 `diy-design`**。
- **[K]/[P] 侧的引用**（`data/object-types/workflow.md` 与 `workflow-sketch.md`）：**C·3 按需回接**，本批只落 `[M]` 一侧。
