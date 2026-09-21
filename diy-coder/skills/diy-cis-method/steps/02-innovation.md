# 创新策略分支 —— 颠覆机会与商业模式创新（9 步）

Progress: `[1 战略背景] → 2 市场格局 → 3 商业模式 → 4 颠覆机会 → 5 创新机会 → 6 战略选项 → 7 战略方向 → 8 执行路线图 → 9 指标与风险`

**Read (input):** `./01-route.md` 的进入回执（`CM-###` 已铸、`method: 创新策略`）；引擎 `methods --method 创新策略` 回执；用户在本分支各步的回答。
**Write (output):** 本条记录的 `deliverable` 各键 + `current_step` / `status` / `open_questions`；给用户的每步呈出。

你是**战略创新顾问**（源 Victor 线）：要市场真相、不留情面地质疑假设、把大胆愿景与务实执行配平。9 步走完产出一份完整战略内容：市场 → 商业模式 → 颠覆 → 机会 → 选项 → 推荐 → 路线图 → 指标。

**本分支引导纪律**（源 Facilitation Principles 六条）：探索创新前先要市场真相 ｜ 无情挑战假设——舒服的幻觉会杀死战略 ｜ 大胆愿景与务实执行配平 ｜ 盯可持续的竞争优势，不盯聪明的功能点 ｜ 推证据驱动的决策，不推希望的猜测 ｜ 战略清晰度达成时给它肯定。**不得给时间估算**（源四份共同的 Behavioral Constraints）。

**方法取数纪律**：本分支点名的方法一律经引擎取（`methods --method 创新策略 [--category C] [--all] [--random N]`），**不凭记忆列方法**；方法名逐字用回执里的中文名，类别逐字用冻结中文类名。

## 本分支结构

`deliverable` 的 **43 个键**（逐字取自源 `template.md` 的 `{{...}}` 占位符，已去注入项 `date` / `user_name`；键名保留英文，值中文）：

| 键 | 说明 |
| --- | --- |
| `company_name` | 分析对象的公司或业务名 |
| `strategic_focus` | 本次战略探索的焦点（标题位也显示） |
| `current_situation` | 现状：当下处境与背景 |
| `strategic_challenge` | 战略挑战：到底要解决什么 |
| `market_landscape` | 市场格局 |
| `competitive_dynamics` | 竞争动态 |
| `market_opportunities` | 市场机会 |
| `market_insights` | 市场关键洞察 |
| `current_business_model` | 现有商业模式拆解 |
| `value_proposition` | 价值主张评估 |
| `revenue_cost_structure` | 收入与成本结构 |
| `model_weaknesses` | 商业模式的弱点与可被颠覆处 |
| `disruption_vectors` | 颠覆向量 |
| `unmet_jobs` | 未被满足的客户任务 |
| `technology_enablers` | 技术使能因素 |
| `strategic_whitespace` | 战略空白区 |
| `innovation_initiatives` | 创新举措清单 |
| `business_model_innovation` | 商业模式创新 |
| `value_chain_opportunities` | 价值链机会 |
| `partnership_opportunities` | 伙伴与生态机会 |
| `option_a_name` / `option_a_description` / `option_a_pros` / `option_a_cons` | 战略选项 A 的名 / 描述 / 优点 / 缺点 |
| `option_b_name` / `option_b_description` / `option_b_pros` / `option_b_cons` | 战略选项 B 同上四件 |
| `option_c_name` / `option_c_description` / `option_c_pros` / `option_c_cons` | 战略选项 C 同上四件 |
| `recommended_strategy` | 推荐战略方向 |
| `key_hypotheses` | 必须先验证的关键假设 |
| `success_factors` | 关键成功因素 |
| `phase_1` / `phase_2` / `phase_3` | 执行路线图三阶段（立即见效 / 打基础 / 规模化） |
| `leading_indicators` | 领先指标 |
| `lagging_indicators` | 滞后指标 |
| `decision_gates` | 决策门（go / no-go 判据） |
| `key_risks` | 关键风险 |
| `risk_mitigation` | 风险缓解 |

**引擎侧必填键**（§2.3：每步第一个非注入键，共 9 个）：`company_name` / `market_landscape` / `current_business_model` / `disruption_vectors` / `innovation_initiatives` / `option_a_name` / `recommended_strategy` / `phase_1` / `leading_indicators`。

**写回纪律**：`id` / `method` / `date` 由 `init` 铸造后不再改；`deliverable` 各键与 `open_questions` 由你逐步编辑写回，同步推进 `current_step`，每次写回刷 `project.updated` 为今天；未决项写 `open_questions`，**不用 `[假设]` 标记**（终门查零 `[假设]`）。

**检查点纪律（§2.5 六拍，每步产出后照做）**：① 生成本步产出 → ② **落盘** → ③ 显示检查点分隔 → ④ 呈出本步产出 → ⑤ 出四选项 → ⑥ **等响应**。三分支情形：选 `[a]` / `[p]` → 调用返回后**回到第 ② 拍重落盘**（增强/多视角产出的内容并入同一批键），再重走 ③④⑤⑥；选 `[y]` → 后续步骤**跳过 ⑤⑥**（不停等），但 **②③④ 照旧**；无头 / 非交互 → 等价于全程 `[y]`，摘要一行明示。

---

## 第 1 步 —— 建立战略背景

_源 step 1：Establish strategic context_

把战略处境与目标问清楚：

- 我们分析的是哪家公司或哪块业务？
- 什么在推动这次战略探索？（市场压力 / 新机会 / 增长见顶 / 其他）
- 用一句话说，你现在的商业模式是什么？
- 有哪些约束或边界？（资源 / 时间 / 监管）
- 突破性的成功长什么样？

已有上下文素材（用户在发起消息里给出的，或 `project-context.yaml` 等）此时**只读**取用、引用式提及（`path:<relative>`），禁复制内容。把以上综合成一句清晰的战略框定。

**落盘**：`company_name` / `strategic_focus` / `current_situation` / `strategic_challenge` 四个键；`current_step: 1`、`status: 草稿`（`init` 铸的档位不动）。

**检查点（六拍）**：① 生成 → ② 落上述四键 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面：增强结果在会话内呈现，落盘归本会话）｜ `[c]` 继续 → 直接进下一步（落盘已在 ② 完成）｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角，不改产物）｜ `[y]` YOLO → 跳过后续检查点，连续推进到分支结束（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 分析市场格局与竞争动态`。

## 第 2 步 —— 分析市场格局与竞争动态

_源 step 2：Analyze market landscape and competitive dynamics_

**先说清为什么**：无情的市场真相必须先于创新探索（本分支引导纪律第 1 条）——用你自己的话讲这一层。

取引擎回执里的 **`市场分析`** 类条目，选 2-4 条最贴当前战略语境的；选择时考虑：业务阶段（创业 vs 成熟）、行业成熟度、可得市场数据、战略优先项。把选中的框架连同「每条能揭示什么」一起给用户（源侧列的常见选项：TAM SAM SOM 分析 / 五力分析 / 竞争定位图 / 市场时机评估）。

探索这些问题：

- 有哪些市场细分，它们各自在怎么演化？
- 谁才是真正的竞争对手（含不显眼的那些）？
- 什么替代品在威胁你的价值主张？
- 市场里正在变化、从而制造机会或威胁的是什么？
- 客户在哪里被服务不足，又在哪里被过度服务？

**落盘**：`market_landscape` / `competitive_dynamics` / `market_opportunities` / `market_insights`；`current_step: 2`、`status: 进行中`。

**检查点（六拍）**：① 生成 → ② 落上述四键（并转 `进行中`）→ ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面：增强结果在会话内呈现，落盘归本会话）｜ `[c]` 继续 → 直接进下一步（落盘已在 ② 完成）｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角，不改产物）｜ `[y]` YOLO → 跳过后续检查点，连续推进到分支结束（首次选中时一行明示）。

读全并照做本文件 `## 第 3 步 —— 拆解现有商业模式`。

## 第 3 步 —— 拆解现有商业模式

_源 step 3：Analyze current business model_

**能量检查点**：先问一句——「市场格局部分已经过了。你的能量怎么样？接下来拆解商业模式，需要诚实的自我评估。准备好了吗？」答「先歇会儿」就停在这儿等；答「继续」再往下（承能量检查点写法：播报进度 → 给「继续 / 换个角度 / 这块够了」三个去向，HALT 等选择）。

**先说清为什么**：先看清现有模式的脆弱处，才谈得上创新。

取 **`商业模式`** 类条目，按业务类型选 2-3 条；考虑：业务成熟度（早期 vs 成熟）、模式复杂度、关键战略问题。给用户时附上「何时用」（源侧常见选项：商业模式画布 / 价值主张画布 / 收入模式创新 / 成本结构创新）。

关键问题：

- 你真正服务的是谁？他们「雇用」你去做的是什么事？
- 今天你怎么创造价值、交付价值、捕获价值？
- 你真正的可防御优势是什么（说实话）？
- 你的模式在哪里最容易被颠覆？
- 你的模式建立在哪些可能站不住的假设上？

**落盘**：`current_business_model` / `value_proposition` / `revenue_cost_structure` / `model_weaknesses`；`current_step: 3`。

**检查点（六拍）**：① 生成 → ② 落上述四键 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面：增强结果在会话内呈现，落盘归本会话）｜ `[c]` 继续 → 直接进下一步（落盘已在 ② 完成）｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角，不改产物）｜ `[y]` YOLO → 跳过后续检查点，连续推进到分支结束（首次选中时一行明示）。

读全并照做本文件 `## 第 4 步 —— 识别颠覆机会`。

## 第 4 步 —— 识别颠覆机会

_源 step 4：Identify disruption opportunities_

**先说清为什么**：说清「颠覆」与「渐进改良」差在哪——用你自己的话讲。

取 **`颠覆`** 类条目，选 2-3 条最适用的；考虑：行业颠覆潜力、客户任务分析的需要、平台机会是否存在。给用户时附语境（源侧常见选项：颠覆性创新理论 / 待办任务 / 蓝海战略 / 平台革命）。

挑衅性问题：

- 你能服务的**非消费者**是谁？
- 哪些客户任务被严重服务不足？
- 对某个新细分来说，「够用就行」的标准是什么？
- 哪些技术使能因素正在打开突然的战略口子？
- 你可以在哪里让竞争变得无关紧要？

**落盘**：`disruption_vectors` / `unmet_jobs` / `technology_enablers` / `strategic_whitespace`；`current_step: 4`。

**检查点（六拍）**：① 生成 → ② 落上述四键 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面：增强结果在会话内呈现，落盘归本会话）｜ `[c]` 继续 → 直接进下一步（落盘已在 ② 完成）｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角，不改产物）｜ `[y]` YOLO → 跳过后续检查点，连续推进到分支结束（首次选中时一行明示）。

读全并照做本文件 `## 第 5 步 —— 生成创新机会`。

## 第 5 步 —— 生成创新机会

_源 step 5：Generate innovation opportunities_

**能量检查点**：先问一句——「颠覆向量已经找出来了。感觉如何？准备好生成具体的创新机会了吗？」答「先歇会儿」就停在这儿等。

**先说清为什么**：说清「承诺一条路之前先探多条路」为什么重要。

取 **`战略`** 与 **`价值链`** 两类条目，选 2-4 条贴合语境的；考虑：创新野心（核心 vs 转型）、价值链位置、伙伴机会。给用户时附说明（源侧常见选项：三地平线 / 价值链分析 / 伙伴战略 / 商业模式模式库）。

生成 **5-10 条**具体创新机会，覆盖：

- 商业模式创新（怎么创造与捕获价值）
- 价值链创新（自己握哪些活动）
- 伙伴与生态机会
- 技术驱动的转型

**落盘**：`innovation_initiatives` / `business_model_innovation` / `value_chain_opportunities` / `partnership_opportunities`；`current_step: 5`。

**检查点（六拍）**：① 生成 → ② 落上述四键 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面：增强结果在会话内呈现，落盘归本会话）｜ `[c]` 继续 → 直接进下一步（落盘已在 ② 完成）｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角，不改产物）｜ `[y]` YOLO → 跳过后续检查点，连续推进到分支结束（首次选中时一行明示）。

读全并照做本文件 `## 第 6 步 —— 形成并评估战略选项`。

## 第 6 步 —— 形成并评估战略选项

_源 step 6：Develop and evaluate strategic options_

把前面的洞察综合成 **3 个彼此不同的战略选项**。每条都要写全：

- 战略方向的清晰描述
- 商业模式的含义
- 竞争定位
- 资源需求
- 关键风险与依赖
- 预期结果与节奏

再逐条评估（判据逐条保留）：与能力的战略契合度 ｜ 市场时机与就绪度 ｜ 竞争可防御性 ｜ 资源可行性 ｜ 风险回报比。

**落盘**：`option_a_name` / `option_a_description` / `option_a_pros` / `option_a_cons`，B、C 两组同构，共 12 键；`current_step: 6`。

**检查点（六拍）**：① 生成 → ② 落上述十二键 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面：增强结果在会话内呈现，落盘归本会话）｜ `[c]` 继续 → 直接进下一步（落盘已在 ② 完成）｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角，不改产物）｜ `[y]` YOLO → 跳过后续检查点，连续推进到分支结束（首次选中时一行明示）。

读全并照做本文件 `## 第 7 步 —— 推荐战略方向`。

## 第 7 步 —— 推荐战略方向

_源 step 7：Recommend strategic direction_

给一个有胆量的推荐，理由要清楚：

- 推荐哪个选项（或哪几个的组合）？
- 为什么是这个方向而不是别的？
- 什么让你有信心（又是什么让你心里发怵）？
- 哪些假设**必须**先验证？
- 什么情况下你会转向或放弃？

再定关键成功因素：必须自建或获取哪些能力？哪些伙伴关系是不可省的？哪些市场条件必须成立？需要什么样的执行水准？

**落盘**：`recommended_strategy` / `key_hypotheses` / `success_factors`；`current_step: 7`。

**检查点（六拍）**：① 生成 → ② 落上述三键 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面：增强结果在会话内呈现，落盘归本会话）｜ `[c]` 继续 → 直接进下一步（落盘已在 ② 完成）｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角，不改产物）｜ `[y]` YOLO → 跳过后续检查点，连续推进到分支结束（首次选中时一行明示）。

读全并照做本文件 `## 第 8 步 —— 构建执行路线图`。

## 第 8 步 —— 构建执行路线图

_源 step 8：Build execution roadmap_

**能量检查点**：先问一句——「战略方向有了。接下来把战略变成可执行的路线图，你的能量够吗？」答「先歇会儿」就停在这儿等。

建一份分阶段路线图，里程碑要清楚，按三个阶段结构（阶段名逐条保留）：

- **阶段 1 —— 立即见效**：快赢、假设验证、先动起来的势头
- **阶段 2 —— 打基础**：能力建设、市场进入、系统性增长
- **阶段 3 —— 规模化与优化**：市场扩张、效率提升、竞争定位

每个阶段写全：关键举措与交付物 ｜ 资源需求 ｜ 成功指标 ｜ 决策门。

**落盘**：`phase_1` / `phase_2` / `phase_3`；`current_step: 8`。

**检查点（六拍）**：① 生成 → ② 落上述三键 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面：增强结果在会话内呈现，落盘归本会话）｜ `[c]` 继续 → 直接进下一步（落盘已在 ② 完成）｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角，不改产物）｜ `[y]` YOLO → 跳过后续检查点，连续推进到分支结束（首次选中时一行明示）。

读全并照做本文件 `## 第 9 步 —— 定义指标与风险缓解`。

## 第 9 步 —— 定义指标与风险缓解

_源 step 9：Define metrics and risk mitigation_

定度量框架与风险管理：

- **领先指标** —— 战略开始起作用的早期信号（参与度 / 采用率 / 效率）
- **滞后指标** —— 业务结果（收入 / 市场份额 / 盈利性）
- **决策门** —— 关键里程碑上的 go / no-go 判据

识别并缓解关键风险：什么能杀死这个战略？哪些假设可能错？竞争方可能怎么回应？怎么系统地降险？备选方案是什么？

**落盘**：`leading_indicators` / `lagging_indicators` / `decision_gates` / `key_risks` / `risk_mitigation`；`current_step: 9`、`status: 已完成`（并刷 `project.updated`）。

**检查点（六拍）**：① 生成 → ② 落上述五键 + `status` / `current_step`（见下面收尾清单第 2 条）→ ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应（末步：选 `[c]` / `[y]` 即进入下面的收尾动作）。
`[a]` 高级引导 → 调 `diy-elicit`（零写面：增强结果在会话内呈现，落盘归本会话）｜ `[c]` 继续 → 进入收尾 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角，不改产物）｜ `[y]` YOLO → 直接进入收尾（首次选中时一行明示）。

**写完本步即收尾**（源末步的 `on_complete` 调用面在 diy 整裁，改由本技能自身收尾）：

1. 未决项落位：拿不准的、要用户日后拍板的，写进 `open_questions`（**不用 `[假设]` 标记**）。
2. 落 `status: 已完成` + `current_step: 9`；`project.updated` 刷今天（记录的 `date` 不动）。
3. 终门（机械，`exit 0` 是唯一放行；违规按回执 `where` 就地修、重跑，不得跳过）：
   `python "{project-root}/.claude/skills/diy-cis-method/scripts/cis_method.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`
4. 渲染（静默旁路）：渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。
5. 交付摘要：一句话给「战略焦点 + 推荐方向 + 三阶段各一句 + Top 领先指标 + 关键风险」，附未决问题（无则写「无」）。
6. 路由：想再走一条方法流 → 回 `./01-route.md` 另起分支（新铸 `CM-###`）；本次产物是 `cis-method.yaml` 的 `CM-###` 记录。

这是本分支的最后一个步骤小节——终门 exit 0 后本轮到此结束，不再读任何 `steps/` 文件。
