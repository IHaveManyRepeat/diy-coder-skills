# 复杂度路由与分解教练

- **源**：`wds-4-ux-design/data/object-types/COMPLEXITY-ROUTER.md`（842 行，独占资产）
- **引用方**：`wds-4/steps-m/step-02-define-component.md:77`（「Reference `../data/object-types/COMPLEXITY-ROUTER.md`」）

## 1. 复杂度判定（源 STEP 2 的指标表；[M] step-02 收成三级）

只分两档（simple / complex）不够——本表分三级（Simple / Moderate / Complex），指标沿用源表：

| 档 | 源指标（命中任一即落该档） |
| --- | --- |
| **Simple** | 单状态（无 hover / active / loading 变体）· 无用户交互（纯展示）· 无数据依赖 · 无业务规则 |
| **Moderate** | 多元素 + 若干状态（2 个）· 有交互但无状态机 · 有数据依赖但不跨组件 |
| **Complex** | 3+ 状态（empty / loading / active / completed / error）· 时间驱动变化（倒计时、定时器、实时）· 多步交互（预约 → 开始 → 完成）· 业务规则（校验、权限、阻断）· 数据同步（改动其他组件）· 状态机（有定义的迁移路径） |

三个标定例逐字保留：**Simple** = 静态文字 / 图片 / 基础按钮；**Complex** = 日历组件 / 预约系统 / 带筛选的搜索 / 多步表单；**Moderate** = 无逐字标定例（本档是 `[M]` 的收口），判据 = 「多元素 + 若干状态，但无状态机」。

## 2. 三条路由

| 档 | 路由 | diy 落点 |
| --- | --- | --- |
| **Simple** | 源 Path A：**在页规格里就地记录**，不进设计系统 | 单条 `components[]` 记录即可（`complexity: simple`）——`states` 至少 1 条 |
| **Moderate** | 源 Path B 的轻量形态：记录 + **标注待分解** | 单条 `components[]` + 在 `notes` 一句写清「哪一部分将来会独立」（`complexity: moderate`） |
| **Complex** | 源 Path B：**分解教练**——把组件拆成 WHERE / HOW / WHAT 三问，逐问落位 | `complexity: complex` + **拆成多条 `components[]`**（父件 + 子件各占一条记录，各自铸号），父件的 `related` 列出子件 ID |

**源 Path B 的三问 → diy 承载位**（`COMPLEXITY-ROUTER.md:120–305` 的分解工作流）：

| 源问 | 源落点（三文件扇出，属 [P]） | diy 落点（本技能） |
| --- | --- | --- |
| **WHERE**（出现在哪、多大、什么位置） | `Pages/<n>-<name>.md` | `components[].usage`（何时用 / 何时不用）+ `used_in[]` 引 `SC-<nn>.P<n>` |
| **HOW**（每个状态长什么样） | `Components/<name>.component.md` | `components[].styling` + `states[]` + `variants[]` |
| **WHAT**（怎么动、什么业务规则） | `Features/<name>.feature.md` | `components[].behavior`（交互 / 动画 / 规则） |

**分解的判据**：先问用户「要不要拆」（二选一）；**用户不拆也可放行**，但要把警示原样带出——「这可能产生一份过大的规格，维护成本会上升」。**绝不替用户拆。**

## 3. 内容放置规则

源问「这段内容会不会随它出现的位置而变」：

- **会变 → 归页**（源 Page File）：标题、正文、图片、按页变化的数据接口、作用域
- **不变 → 归组件 / 功能**（源 Feature File）：按钮文案、通用报错、通用 tooltip、恒定的数据接口
- **视觉规格不进内容桶**（源 Component File 只放视觉）

**diy 化**：本技能只产组件 → 判据落成一句话写进 `components[].usage.when_to_use` 或 `notes`：
**「这条内容换一页还成立吗？」** 不成立 → 它属页面，别写进组件记录。

## 4. 分解的收益（存在理由）

1. **防规格膨胀**——单文件从 800 行降到「100 + 150 + 200 三份」，各自可读；
2. **交接清晰**——视觉侧拿 Components、实现侧拿 Features、设计侧拿 Pages，三方各取所需；
3. **防原型漏项**——复盘的真实事故：leaderboard 没进组件文件、日历状态没文档化、周视图只画 5 天；
   分解后「组件文件显式列出全部视觉元素、功能文件显式列出全部交互、故事板画出全部状态」。


## 5. 边界

- **不接外部服务**：Figma 引用（Mode B）不在本收编版。
- **不落三文件扇出**：`Pages/` / `Components/` / `Features/` 目录树是 `[P]` 的产物位，**归下游设计技能**。
