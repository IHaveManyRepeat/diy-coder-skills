# Step 5 — 判定与交付（The Verdict）

Progress: `Ignition → Press Release → Customer FAQ → Internal FAQ → [Verdict]`

**Read (input):** `{output_dir}/prfaq.yaml` 里前三节的全部内容；累积中的 `distillate`；会话记忆里剩下的东西。
**Write (output):** 判定消息；`prfaq.verdict`、`prfaq.stage: 5`、`project.status: 已定稿` 与 `updated`，同一次写入；完成的 `distillate`；渲染视图；收尾摘要。

## 评估

通读整份 PRFAQ——新闻稿、客户 FAQ、内部 FAQ——给出坦率的判定。

**概念强度**是叙事式评估，不是分数：思考在哪里锋利、在哪里还软？什么挺过了拷问，什么只是勉强没散？

**三类发现**——其中一档成为 `prfaq.verdict.strength`：

- **`已锤炼`** —— 清晰、有说服力、站得住的部分：真能让客户停下滚动的那些发布稿小节，诚实且有说服力的那些 FAQ 答案。
- **`欠火候`** —— 有苗头但没长成：方向有了、深度还不够；这些在进 PRD 之前还得再练。
- **`地基裂缝`** —— 真实风险、未解矛盾或可能掀翻整个概念的缺口；不一定是致命伤，但必须被有意识地处置。

**整体取档（最重一档）：** 逐条发现归入三类；只要有实质 `地基裂缝` → 整体取 `地基裂缝`；否则有 `欠火候` → `欠火候`；否则 `已锤炼`。`地基裂缝` / `欠火候` 条目按下文第 3 点落成 `distillate.open_questions`。

**直接给出判定。** 别软化——这个过程的全部意义就是在投入资源之前把真相摆出来。但每条发现都要建设性地框住：每道裂缝，都说清要补上它得做什么。

## 定稿文档

1. **润色** —— 新闻稿读起来是一篇连贯叙事，FAQ 逻辑顺畅，格式一致。
2. **写判定** —— `prfaq.verdict: {strength: <三档之一>, narrative: <这次评估>}`、`prfaq.stage: 5`、`project.status: 已定稿`，全在同一次写入里。
3. **补完 distillate** —— 总要做，就在同一份文件里。前四个阶段已经交出了各自的下游相关条目；再扫一遍会话记忆，把还缺的捞出来——需求信号、技术约束与平台偏好、范围信号、资源与时间线估计、未决问题。bullet 要密，每条自带足够上下文、能独立给下游 LLM 读；保持第 1 步的五个桶（`problem`、`target_users`、`value_props`、`constraints`、`open_questions`），判定里的 `欠火候` 与 `地基裂缝` 落成可执行的 `open_questions` 条目。
4. **收束 notes** —— 剩下的、属于过程叙事而非下游事实的东西（判定为何落在这档、拷问是怎么走的），成为 `notes` 里的 stage-5 条目：`{stage: 5, content}`。收束前再扫一遍下游残留：另类定位与被否的框法进 `distillate.constraints`，写成 `Not <X>: because <Y>`；影响采纳的竞争情报进 `distillate.constraints`（已定）或 `distillate.open_questions`（仍开放）。`distillate` 保持干净的机器契约；`notes` 承载故事。

## 终门（机械）

跑 `python "{project-root}/.claude/skills/diy-prfaq/scripts/prfaq.py" check --final --json`，实参与激活时同一份：`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"`——`--output-dir` 必填、从不取缺省。`已定稿` 与 `stage: 5` 在门跑之前就写好：它们是门检查的对象，不是门的产物。exit 0 是唯一放行；逐条修完上报的违规再重跑。JSON 回执（含计数）即收口证据；渲染与收尾都等 exit 0。

## 呈现完成

"你为 {project_name} 写的 PRFAQ 走完了拷问。" 然后点名它产出的两样东西：单一源 `{output_dir}/prfaq.yaml`（含 distillate 段）与渲染视图。

**建议下一步：** 把这份 PRFAQ 与它的 distillate 带进 PRD 创作——跑 `diy-prd`，把 `{output_dir}/prfaq.yaml` 指给它。在规划流水线里，PRFAQ 取代 product brief。

## Headless 模式输出

把这段 JSON 作为本次运行的收尾（源工作流另发一份 detail-pack 路径；diy 是单一源，所以 distillate 就活在文档里）：

```json
{"status": "complete",
 "prfaq": "{output_dir}/prfaq.yaml",
 "verdict": "已锤炼|欠火候|地基裂缝",
 "key_risks": ["最要紧的未决项"],
 "open_questions": ["FAQ 里未决的条目"]}
```

失败 / 拒绝形状（键名与 `diy-product-brief` 统一）：

```json
{"status": "blocked",
 "prfaq": "{output_dir}/prfaq.yaml",
 "reason": "<一句话：什么推不出来 / 卡在哪>",
 "route": "<接手技能名 | null>",
 "open_questions": ["..."]}
```

`reason` / `route` **仅在 `blocked` 时出现**，`complete` 时省略。激活期的拒绝（`prfaq.py headless` exit 1 的 `gaps` + 指引）仍走引擎回执，不在这里重复。

## 播报与下一步

本阶段是终局阶段。用户要修订 → 退回对应阶段（`prfaq.stage` 随之后移）；否则流程到此结束。这是最后一个步骤文件——记录的 `distillate` 与渲染视图承载结果，不再读任何 `steps/` 文件。
