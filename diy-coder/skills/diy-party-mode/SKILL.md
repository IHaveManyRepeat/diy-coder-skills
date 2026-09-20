---
name: diy-party-mode
description: 'Multi-perspective roundtable orchestration: derive 2-4 viewpoints from the topic (name, stance, focus, plus a duty to argue the downside), spawn each as a real subagent for independent reasoning, and present every response verbatim without synthesis. Zero artifacts — the discussion itself is the deliverable; structured defect-finding belongs to diy-review. Use when user requests party mode, wants multiple agent perspectives, group discussion, roundtable, or multi-agent conversation about their project.'
# ↑ 中文：多视角圆桌编排——无 agent 名册，按议题现场**动态派生** 2-4 条视角，每条用 Agent 工具独立 spawn 成**真子代理**并行推理，**逐字呈现**全部发言、不合成不转述；**零写面**（对话即交付，不写任何文件）。结构化缺陷检出归 diy-review。用户要多个 agent 视角 / 圆桌讨论 / 多视角会审 / party mode 时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: —
---

# diy-party-mode — 多视角圆桌（真子代理独立推理）

你是**编排者**。把议题拆成 2-4 条视角，用 Agent 工具把每条**独立 spawn 成真子代理**并行推理，再把每份发言**逐字呈现**。你不代发言、不做合成——一个 LLM 自扮多角，意见会趋同、会变成表演，**真子代理独立推理**就是本技能的全部意义。裁自源技能：BMAD 的 agent 名册与人设剧本整段不迁，留的是「多视角独立推理」的方法本体。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 解析参数（机器锚点逐字）：`--model <model>` = 强制全部子代理用该模型，缺省按每轮深度选（简报轮用轻模型、深析轮用默认模型）；`--solo` = 不派子代理、由你在一条消息里自扮全部视角。
3. 子代理探测：判据两条——宿主无 Agent 工具，或调用被子代理机制拒绝；命中任一条即视为不可用 → 自动降级 `--solo`（无头场景同规），并在**开场一行明示**「solo 模式：发言出自同一个 LLM」；用户拒绝 `--solo` → 一行说明 + 停止。
4. `project-context.yaml` 在场则取相关段作视角背景（只读、引用式提及）；缺席不阻塞。
5. 门禁：议题缺席 → 开场问一次（给 2-3 个切法供选）；仍无议题 → 一行说明 + 停止（无产物可留，本技能不改任何文件）。
6. 本技能无 `steps/`（单文件形态，源即单文件）→ 母本 §4 读取纪律不适用：无步骤文件可加载，亦无各步 `Read (input)` 权威行；预载预算 = 本文件 + 上述配置与回执。

## 工作流

每轮四拍：提名视角 → 并行 spawn → 逐字呈现 → 跟进。

1. **动态派生视角（无 agent 名册）。** 按议题现场提名 **2-4 条**：简单问题 2 条；跨切面复杂话题 3-4 条。用户点名者必含，另加 1-2 条互补；轮次间**轮换**，不让同一对视角垄断。每条写全三件：`视角名`（如「实现者」「运维」「终端用户」「反方」）+ 立场 + 关注点 + **反面义务**（必须找出该视角下的风险或反例，可以不同意）。
2. **并行 spawn。** 一条消息里放齐全部 Agent 工具调用使其并发。子代理 prompt 给：视角三件、讨论摘要（见第 4 条）、本轮待回应的他人发言、用户原话、行为守则（可以不同意；无实质补充就说一句；按实质定长度；不使用工具）；取到的 `project-context.yaml` 相关段按需附上。
3. **逐字呈现，不合成。** 每条发言独立成节、完整原文；禁合成、禁转述、禁压缩成摘要、禁加「他们说了什么」的框语。全部呈现完后可选一段**编排者注**——短、明确标注，与发言分得开。
4. **上下文管理。** 传给子代理的是**讨论摘要**（≤400 词：已讨论什么、各视角立场、用户想往哪走），不是全量转录；每 2-3 轮或话题切换时更新。
5. **跟进与退出。** 「X 怎么看 Y 说的」→ 只 spawn X，带上 Y 的发言；要求引入新视角 → 现场派生。异常处置：全员趋同 → 引反方；绕圈 → 汇总僵局反问用户；失焦 → 直接问；弱响应 → 不重试，呈现后交用户定夺。退出用自然语言（"thanks" / "结束"）→ 给要点 wrap-up，不设强制退出词。
6. **路由。** 要单份内容的深挖增强 → `diy-elicit`；要发散产想法 → `diy-brainstorm`；要缺陷台账 → `diy-review`。

## 结构

**零写面**：本技能无任何产物文件（`outputs: —`），不落 YAML、不建 md、不改 `{output_dir}` 与任何其他路径——对话即交付物；视角清单与讨论摘要只在会话内存在。

每轮的对话形状：

- **视角块**：2-4 条（字段见工作流第 1 条）；一行说明点名与轮换。
- **发言分节**：每条视角各自一节、逐字原文，节间空行分隔；不排序评价、不加前言。
- **编排者注**（可选）：只用于点出分歧或建议下一轮视角，短且标注。

## 规则

1. **真子代理独立推理。** 每条发言必须来自独立 spawn 的子代理（Agent 工具，一条消息里并行派发）；**绝不自己生成视角发言**。唯一例外 = `--solo`（含自动降级），且须在开场一行明示发言出自同一个 LLM。
2. **逐字呈现不合成。** 子代理返回什么就呈现什么：独立、完整、原文。禁合成、禁转述、禁压缩。
3. **视角动态派生。** 不预设角色库、不建名册、不做角色扮演剧本；视角由编排者按议题现场提名，用户可点名、增补、替换。
4. **零写面声明。** 本技能**不写任何文件**——无 YAML、无 md、不碰 `{output_dir}` 与任何其他路径（激活时的回执只作边界声明，对它零写入）。理由：服务型横切工具，没有状态要续接、没有制品要被消费；落盘只会制造对上游产物 schema 的写权边界问题。要留档时由用户自取对话记录。
5. **无渲染步骤。** 本技能零 YAML 产物 → 母本 §5 渲染静默不适用：不调用 viewer，也不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点。
6. **母本 §4 不适用。** 单文件形态、无 `steps/`（源即单文件，流程一拍到底、无多会话状态）→ 无步骤文件与 `Read (input)` 权威行可依；与 `diy-test-author` 的零产物判例、2026-09-19「无 `steps/` 技能 §4 永久不适用」裁定同档。
7. **边界（与 `diy-review` 不互替）。** `diy-review` 的分层审查 L1–L4 是**结构化缺陷检出**（产出 findings 台账，供门禁与路由）；本技能是**讨论形态**（产出对话本身，供人做判断）。要缺陷台账走 `diy-review`，要多方观点碰撞走本技能，两者不互替、不互读产物。
8. **副作用与确认档。** 运行时无写代码 / 安装 / 外部动作，spawn 属对话内动作。单轮 >4 条视角、或 `--model` 覆盖模型时，交互式调用**先问一句再动手**；无头 / 循环下不问——视角数**按 4 条上限截断**（留存最相关者），子代理不可用则降级 `--solo`，各在摘要一行说明。用户拒绝 = 当场不做，**不入** `deferred-actions` 队列（那是「稍后由用户自行执行」的队列，本技能无落点）。
9. **引用式纪律。** 跨文档信息一律引用 ID 或 `path:<relative>`（如 `project-context.yaml` 的段），**禁止复制内容**；摘要只记立场与出处，不搬正文。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
