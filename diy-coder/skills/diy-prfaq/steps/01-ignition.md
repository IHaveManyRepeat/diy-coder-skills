# Step 1 — 点火（Ignition）

Progress: `[Ignition] → Press Release → Customer FAQ → Internal FAQ → Verdict`

**Read (input):** 激活期拿到的 `headless` 回执（headless 模式）；恢复续跑时的 `prfaq.stage` 锚点；用户带来的一切——一个想法、笔记、产品意图，或文档路径。
**Write (output):** 点火消息；草稿 `{output_dir}/prfaq.yaml`（`project` 块、`prfaq.stage: 1`、`prfaq.concept_type`、`prfaq.essentials`、空的各阶段容器、`distillate` 骨架、`revisions: []`）。

## 先定调，再把方法落地

开场要冷——这不是温和的试探式寒暄。把它框成一场挑战：用户即将在动手之前，先为「已完成的产品」写发布稿，以此压力测试自己的想法。走完这一程说明概念已就绪；在这里失败则省下白费的力气。直给，且有劲。

然后用三句话把方法落地：Amazon 的 Working Backwards——先写成品发布稿，再回答最刁钻的客户与利益相关方问题。要点是在投入资源之前逼出清晰度。

## 客户优先的强制

用户从哪里起手，决定你往哪里推：

- **开口就是解法**（"我想做 X"）→ 拉回客户的问题。别让他跳过痛。
- **开口就是技术**（"我想用 AI / 区块链 / 等等"）→ 挑战得更狠。技术是"怎么做"，不是"为什么"——逼他讲清人的问题。剥掉热词，问他还有没有人在乎。
- **开口就是客户问题** → 往具体里挖：他们今天怎么凑合、试过什么、为什么还没被解决。

用户卡住时，基于他已分享的内容给具体建议——替他起草一个可以反驳的假设，而不是把同一个问题问得更凶。

## 概念类型判定

对话早期判定属于哪一类，存进 `prfaq.concept_type`：

| 用户在做的 | `concept_type` | 第 3-4 阶段的框 |
| --- | --- | --- |
| 商业产品 | `商业` | 默认商业框 |
| 内部工具 | `内部` | 利益相关方价值、采纳路径、维护 |
| 开源项目 | `开源` | 采纳策略、贡献者、可持续性 |
| 社区 / 非营利 | `社区` | 利益相关方价值、参与、可持续性 |

非商业概念没有"单位经济"或"前 100 个客户"——第 3、4 阶段改用利益相关方价值、采纳路径与可持续性来框。

## 四要素

第 1 阶段在你对这四件事清楚到能写出发布稿标题时结束。在对话里把它们捕获下来，然后写进 `prfaq.essentials`：

- **客户 / 用户是谁？**——具体的人群，不是"所有人"。
- **他们的问题是什么？**——具体可感，不是抽象。
- **这为什么对他们重要？**——客户侧利害与后果。
- **解法的初始概念是什么？**——粗糙的也行。

够不够具体是你的判断；在场与非空是引擎的（`headless` 门，以及每一次 `check`）。

**快车道：** 用户在开场消息里（或经结构化输入）给齐四要素 → 确认收到、复述你的理解、建文档，直接进第 2 阶段。括注界定范围：extended discovery ＝ 逐轮追问；**语境采集不在被跳过之列**——两路并行子代理照跑（降级路径见本节末），"研究接地气"是硬承诺。

**优雅改道：** 2-3 轮之后用户仍讲不出客户或问题，不要硬逼。说明这个想法需要先做一轮专门的头脑风暴探索——调用 `diy-brainstorm`，就此停下。建在空地上的 PRFAQ 只会产出一份空洞的发布稿；诚实退出也是赢。

## 语境采集

1. **先问输入。** 问用户手头有没有既有文档、研究、头脑风暴素材或其他可喂给 PRFAQ 的源。收集路径交给子代理——用户给的文件你自己不读，那是产物分析器的活。
2. **在一条消息里扇出两个子代理（并行）。** 各自收到产品意图摘要（客户、问题、解法方向、领域）。

   **产物分析器** —— *过程：* 扫描 `{output_dir}` 与 `{project-root}/docs`（存在时并列 `{project-root}/documentation`），按文件名模式找可能相关的文档：brainstorming/ideation、research/analysis/findings、context/overview/background、brief/summary，以及任何看起来相关的 markdown、文本或结构化文档；分片文档（一个文件夹带 `index.md` 加若干部分）→ 先读 index，再只读相关部分；超大文档（估计 >50 页）→ 先看目录、执行摘要与各节标题，只读与意图直接相关的节，并记下哪些节是略读、哪些是通读；所有读取在一条消息里发出，不要一条一条来；不相关的文档忽略。*抽取：* 与意图相关的洞见、市场与竞争信息、用户研究或画像、技术上下文与约束、**被采纳与被否决**的想法（被否决的防止再提议）、指标与数据点。*只返回这个 JSON*，不写任何前言，1500 token 以内，每节最多 5 条 bullet：
   ```json
   {"documents_found": [{"path": "...", "relevance": "一句话相关性"}],
    "key_insights": ["自足的 bullet"],
    "user_market_context": ["..."],
    "technical_context": ["..."],
    "ideas_and_decisions": [{"idea": "...", "status": "accepted|rejected|open",
                             "rationale": "简短理由"}],
    "raw_detail_worth_preserving": ["细节、数据点、引语"]}
   ```

   **网络研究员** —— *过程：* 从意图里识别检索角度——直接竞品、同一痛点的邻近解法、市场规模与趋势、制造机会或风险的行业新闻、用户对现有解法的情绪；跑 3-5 次定向检索（重质不重量），形如 `"[问题领域] solutions comparison"`、`"[竞品] alternatives"`、`"[行业] market trends [当前年份]"`、`"[目标用户类型] pain points [领域]"`；综合出信号，不要罗列链接。*只返回这个 JSON*，1000 token 以内，每节最多 5 条 bullet：
   ```json
   {"competitive_landscape": [{"name": "...", "approach": "...", "gaps": "..."}],
    "market_context": ["..."],
    "user_sentiment": ["..."],
    "timing_and_opportunity": ["..."],
    "risks_and_considerations": ["..."]}
   ```

3. **优雅降级：** 子代理不可用 → 内联扫描最相关的 1-2 份文档，并直接跑定向检索。绝不阻塞流程。
4. **合并发现** 与用户已分享的内容；起草开始前，把任何让假设更丰富或受挑战的意外发现摆出来。

## 建草稿文档

写 `{output_dir}/prfaq.yaml`——后续每个阶段都更新的单一源：

```yaml
project: {name: <diy-coder.yaml 的 project.name>, status: 草稿, created: <today>, updated: <today>}
prfaq:
  stage: 1
  concept_type: <detected>
  essentials: {customer: ..., problem: ..., stakes: ..., solution: ...}
  press_release: {}
  customer_faq: []
  internal_faq: []
  verdict: {}
distillate: {problem: ..., target_users: [<string>], value_props: [], constraints: [], open_questions: []}
notes: []
revisions: []
```

## 教练笔记捕获 → `notes` + distillate

两个去处、两件事——分开。**`notes` 是过程叙事**（源工作流 `<!-- coaching-notes-stage-1 -->` 块的 diy 形态，必须在上下文压缩后活下来）；**`distillate` 是机器契约**，由下游 `diy-prd` 消费，所以保持干净摘要、不带过程评论。

本阶段向 `notes` 追加一条：

```yaml
notes:
  - stage: 1
    content: <概念类型及其理由；你挑战过的假设；方向判定背后的教练过程；子代理的发现过程；无处安放的用户上下文>
```

然后把下游相关的条目路由进五个桶（后续每个阶段都用同一套切分）：

- `distillate.problem` —— 被磨锐后的问题，以及它暗含的需求信号。
- `distillate.target_users` —— 它服务谁：画像、市场、采纳人群。
- `distillate.value_props` —— 站住的东西：差异点、经得起追问的主张。
- `distillate.constraints` —— 技术上下文、平台偏好、范围信号（in / out / maybe）、资源与时间线估计、硬限制、**任何因某个理由被否决、下游不得再提议的东西——写成约束 `Not <X>: because <Y>`**（这条就是拦住 PRD 重提被砍选项的机制），以及已定且影响采纳的竞争情报。
- `distillate.open_questions` —— 未知项、未决项（含仍开放的竞争情报），以及后续判定里的「欠火候」/「地基裂缝」条目落成的可执行项。

否决是约束，不是故事：*为什么*与*是什么*同行，条目才能对下游读者自足。围绕它的教练过程——试过什么、探索过又搁置什么、备选感觉如何——留在 `notes`。

### 子代理字段去向（两模式同规）

两个子代理的返回字段各有落点，交互态与 headless 态**同一套规则**，不因模式而变：

- `documents_found` → `distillate.constraints` 一条溯源 bullet（本次实际用到的源文档；diy 没有 frontmatter `inputs` 字段，这条轨迹必须活下来，下游才能追溯某条主张的来源）。
- `key_insights` / `market_context` / `timing_and_opportunity` / `competitive_landscape` → 按内容归 `distillate.problem` / `value_props` / `constraints`；还没落定的 → `distillate.open_questions`。
- `user_market_context` / `user_sentiment` → `distillate.target_users`；成不了结论的观察 → `distillate.open_questions`。
- `risks_and_considerations` → `distillate.open_questions`（未决风险）或 `distillate.constraints`（已裁定的限制）。
- `technical_context` → `distillate.constraints`。
- `ideas_and_decisions` → 按 `status` 分流：`accepted` → `distillate.value_props`；`rejected` → `distillate.constraints` 的 `Not <X>: because <Y>`；`open` → `distillate.open_questions`。
- `raw_detail_worth_preserving` → `notes` 的 stage-1 `content`（原文细节、数据点、引语）；其中属下游事实的，另按上面各条入 `distillate`。

## Headless 模式

门在激活期已经过了。本步非交互跑：跳过定调与强制两节（它们要人在场），对调用方给的材料扇出两个子代理，建草稿文档，并以子代理小结给 `distillate` 播种。除四项必需之外，调用方给什么就收什么：竞争上下文、技术约束、团队/组织上下文、目标市场、既有研究。

实际用到的源文档（产物分析器的 `documents_found`）按上一节「子代理字段去向」落盘——两模式同规，本步不再另立义务。

然后直接进第 2 阶段，无交互跑完第 2-5 阶段；在那里，每条低置信答案带 `[假设]` 前缀，供人事后复核。

## 播报与下一步

对客户、问题与解法清楚到能写发布稿标题（或 headless 模式已走到建文档）→ 完整读 `./02-press-release.md` 并照做。
