# Step 6 — 综合成文与定稿（共享收尾步）

Progress: `Scope → 02–05 (dimension) → [Synthesis]`

**Read (input):** `{output_dir}/research.yaml` 里本记录——`topic` / `goals` / `scope` 与目前全部 findings。
**Write (output):** 本记录的 `synthesis`（`executive_summary` / `key_points` / `open_questions`）与 `status: 已定稿`；渲染视图；收尾播报。

## 综合

把该维度各分析步的 findings 整合起来——不是把它们重新列一遍：

- 证据整体支持什么，置信到哪一档。
- 来源在哪里汇聚、在哪里冲突。
- 对照记下的 `goals`（逐条）意味着什么，以及哪些建议类 finding（`技术` / `领域` 维度带 `recommendations` area）经得起推敲。

跨切面断言需要时，跑定向补检索——例如拿 `"{topic} significance importance"` 定框架，或在综合要超出 02–05 覆盖范围时跑市场进入、风险框架类查询。新证据照旧以一条带来源的 `findings[]` 条目落地；收尾期新条目**复用本维度 02–05 步已定义的 `area` 句柄**（句柄表在那些步里，不新造）；找不到贴切句柄的观察不进 `findings[]`，落 `synthesis.open_questions`。综合只引 findings，绝不抛出无来源的事实。

## 写 synthesis

填本记录的 `synthesis`（`--final` 要求三键齐全）：

- `executive_summary` —— 2–3 段：范围、最关键的 findings、以及战略含义。它是产物的总览——源模板的 "Research Overview" 占位角色由它承担。
- `key_points` —— 决策者必须记住的 3–7 条：目标达成情况及其证据、最重要的建议、以及实质性风险。
- `open_questions` —— 研究缺口、局限，以及再做哪些调研能解决。来源局限与低置信区落在这里，绝不抹平；起草期带 `[假设]` 前缀的推断在定稿前必须落到这里。

源技能的三维度长文结构（目录、编号章节、附录）由这条 YAML 记录承接：每一章的内容都是一条带 `area` 与来源的 finding，执行摘要 = `synthesis.executive_summary`，方法学 = `scope`（该字段注释即 scope and methodology）；**检索轨迹本身不落盘**（过程叙事留在对话里）。检索覆盖范围若本身就是局限（只跑 N 条查询 / 只覆盖某区域），按规则 3 写成 `synthesis.open_questions` 的局限条目。绝不把同样的话在别处重写一遍。

## 来源文档与质检

定稿前，以审阅者的姿态审这条记录：

- 每条 finding 至少一个带 `url` + `accessed` 的来源，且 `confidence` 与证据相称（多个权威来源 → `高`；单一或局部覆盖 → `中`；不确定或过时 → `低`）。
- 每条 `critical claim` 带两个独立来源；分歧要看得见，不许平均掉。
- 市场规模 / 版本 / 监管类断言带各自的日期，过时数据要标注。

## 终门

1. 先给本记录写 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物。
2. 跑 `python "{project-root}/.claude/skills/diy-research/scripts/research.py" check --final --json`，带与激活时相同的 `--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两个实参（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑。JSON 回执（含计数）即收口证据。
3. 经 diy-viewer 渲染——静默旁路命令见 SKILL.md（resolved 实例时附 `--instance <name>`）；不新增浏览器交互点、不报阻塞路径、不等待。
4. 收尾：播报本记录的 `topic`、`status` 与回执里的计数（researches / findings / sources / open_questions），并点明这项研究接下来能喂给谁（`diy-product-brief`、`diy-prfaq`、`diy-prd`）。

## 播报与下一步

这是最后一个步骤文件——终门 exit 0 后本轮结束。要研究同主题的另一个维度，就追加新记录（`RS-###`）并从 `steps/01-scope.md` 重新起步（第二条记录串行：本条收尾完才开，见 `./01-scope.md`）；要改本记录，先把它的 `status` 回退 `草稿`，再向 `revisions` 追加 `{date, change, reason}`（ID 不动），改完按上面的终门重新置 `已定稿` 并重跑 `check --final --id RS-xxx`。
