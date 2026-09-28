# Step — [M] 管理设计系统（Manage Design System）· 归位与引用口径

Progress: `[1 组件身份归位] → [2 三档成熟度] → [3 token 引用口径] → [4 对象级清单引用] → 收尾路由`

**Read (input):** `{output_dir}/design.yaml` 的 `tokens`（唯一风格源）；`{output_dir}/wds-design-system.yaml`（若在场：`components[]` / `token_refs[]` / `used_in[]`，**只读**）；`{output_dir}/prototypes/*.html` 与 `src`（组件实际出现的两处）；`data/object-types/<类型>.md`（对象级清单）。
**Write (output):** 无独立产物——本活动**只对本技能的两个写面**动手：`design.yaml` 的 `tokens` / `direction`，与结构稿里的 token 引用写法。

你是**设计总监**。**本活动的主体归 `diy-wds-system`**（B7b 已建）——组件库、令牌命名空间、跨页用法审计、复杂度路由**都在它那边**，本文件**只声明边界与引用口径**，不重写它已有的内容（单一源）。

〔**归位声明（裁定 12 / 裁定 2 / 裁定 10）**〕源 wds-4 `[M]`（`workflow-design-system.md` 60 行 + `steps-m/` 3 文件 374 行 = 434 行）在 diy 侧**不整块并入本技能**：

| 源侧内容 | diy 落点 |
| --- | --- |
| 组件定义产物 `D-Design-System/**`（源 `step-02:85`，四个互斥落点命名，普查 D13） | **收敛进 `design.yaml` + `src`**：组件身份 = 结构稿里的标记 + `src` 的框架代码（该 hub 文件 `D-Design-System/00-design-system.md` **由 `wds-0-project-setup` 的骨架模板创建**——跨技能复核结论，普查 D10 定性已订正为**误判**；diy 的产物模型是 `design.yaml` 单一源，**本就不设该文件**，与源侧有无创建方无关） |
| 组件库 / 令牌命名空间 / 用法一致性审计 / 复杂度路由 | **`diy-wds-system`**（`components[]` · `data/token-vocabulary.yaml` · `data/complexity-router.md`） |
| 对象级模板五件 | `data/object-types/`（见第 4 步） |

## 第 1 步 —— 组件身份归位

**本技能不铸组件、不建组件目录树**。判据：一个元素是不是「组件」，**看它有没有第二次出现**——那要跨页扫，是 `diy-wds-system` 的活（它的 `components[].used_in[]` 引 `SC-<nn>.P<n>`）。本技能在写规格时**只报候选**（`[K]` 第 3 步、`[D]` 第 1 步各有一处报告点），处置权在 `diy-wds-system`。

## 第 2 步 —— 三档成熟度（源侧最有价值的一条判据，直译）

源 `DESIGN-LOOP-GUIDE.md:159-167` 与 `workflow-design-system.md:18-31` 的三档语义**保留为纪律**，落点归 `diy-wds-system`：

1. **首用 = 一次性**（`First use = one-off`）——第一次出现时**留在页内**，不抽；
2. **二次 = 真模式**（`The second time the same pattern appears (same states, same behavior), it's a real pattern. Extract it to the design system.`）——同样的态、同样的行为，才抽；
3. **三次 = 进 Patterns**——同一模式的第三次出现才做具名化。

**源侧「间距首次出现即抽」不保留**（`diy-wds-system` 规则 5 已裁）：间距的**值**解析自 `design.yaml.tokens.spacing.scale`（唯一源），「何时抽间距」这个问题不复存在。

**复杂度路由的互斥声明**：组件级复杂度判据（3+ 状态 / 时变 / 多步交互 / 业务规则 / 数据同步 / 状态机）**由 `diy-wds-system` 持有**（源 `COMPLEXITY-ROUTER.md:30-37`，收编为 `data/complexity-router.md`）；本技能只在 `./scenario-bridge.md` 第 2 步用它的**页面树版本**（同一判据的两个尺度，各持一侧，**不重复持有**）。

## 第 3 步 —— token 引用口径（本技能唯一的实质写面）

token 的**单一源是 `design.yaml.tokens`**。本技能的两条义务：

1. **写规格时**：新增色值/字号/间距先登记进 `tokens.*` 再引用（`./p-specify.md` 的两条硬约束）；
2. **跑审计时**：`design.py audit --src` 是 token 单一源闸——每条 `one-off-color` / `one-off-font-size` 都是此处要修的基线缺陷，**不留到 `diy-dev` / `diy-review` L4(c)**。

**继承外部 UI 系统**（源 `design-example-shadcn.md` 的「只写 delta」范式）：把库默认当契约时走 `token_scope`（路径列表，`audit` 跳过）或把默认值显式登记进 `tokens.color`——**两条出口二选一**，不得两边都不做（那会让 `audit` 把第三方库默认色值全判 `one-off-color`，普查 §6 #4）。

## 第 4 步 —— 对象级清单引用

对象级规格清单五件（`data/object-types/button.md` · `heading-text.md` · `text-input.md` · `image.md` · `link.md`）是**参考层**：本活动与 `./p-specify.md` 第 3 步各引用一次，供「某类对象该问哪些规格项」时查。

**不产独立产物、不铸三级 ID**（对象级载体 = `src` 框架代码 + `states[].signals`）；源五件的 Figma 字段与 `OBJECT ID` 段已在改写时删除（裁定 4 硬要求，见这五件的文件头声明）。

## 收尾与路由

无独立落盘 → 直接读 `./h-delivery.md`（进框架实现段）。

**裁撤登记**：源 `steps-m/step-01` 的「盘点 `D-Design-System/` 找缺口」（`step-01:47` `🚫 FORBIDDEN to skip gap analysis`）**裁**——它盘点的那棵树在 diy 侧不存在（组件身份已收敛）；该判据的等价物是 `diy-wds-system` 的重复检测与 `used_in[]` 空值检查。源 `step-01:37` 的「盘点步禁改」（`🚫 FORBIDDEN to make changes to the design system in this step`）**保留为原则**并已由归位声明承接：本技能**任何一步都不改组件库**。

本文件到此结束，不再回头。
