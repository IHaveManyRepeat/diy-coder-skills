---
name: diy-help
description: Dynamic workflow navigator. Scans diy-output artifacts (existence + status) and recommends the exact next skill, or names the blocking file when something is not 已定稿. Use when the user asks where they are, what to do next, or wants to start/continue the diy-coder workflow.
# ↑ 中文：动态工作流导航——扫 diy-output 产物的存在性与 status，给出精确的下一个技能；有产物没定稿就点名卡住的那份文件。用户问「现在到哪了 / 下一步做什么」，或要开始、继续 diy-coder 工作流时触发。
---

# diy-help — 工作流状态机导航（FR-4.2）

你是一台薄导航仪：位置由确定性脚本算出，你只解读与路由。本技能**从不写产物**——只读。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；本技能零产物，`document_output_language` 不适用。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 实例名取自上一行 `diyc.py resolve` 回执的 `instance` 键；该键为空（本次未传实例）就一律不带 `--instance`，键非空则带同一实例名——绝不自行回落到主线平铺根。

## 工作流

1. 只跑一次，且任何情况下都不改工作目录：

   ```bash
   python "{project-root}/.claude/skills/diy-help/scripts/help.py" --project-root "{project-root}"
   ```

   resolved 实例时附 `--instance <name>`；调用方是别的脚本时才附 `--json`。唯一例外：用户对结果存疑 → 带 `--json` 重跑一次（见规则 2）。
2. 分支判定读 `--json` 回执的键（`blocked` / `next_skill` / `workflow_done`）；无 `--json` 的人读中文行只作转述。
   - `blocked` 在场 → 逐字转述该段并聚焦这里；整个跳过可选提示，绝不软化成一张选项菜单。
   - `next_skill` 在场 → 点名该技能，并建议新开一个上下文窗口。
   - `workflow_done` 为真 → 公告工作流已全部完成。
3. 转述与收尾：按规则 3 的语言与篇幅回复。

## 结构

本技能零产物；它读的是**产物链**与**脚本回执**（`--json`）：

```yaml
# 产物链 = 脚本 CHAIN 的判定顺序；status 一律读节点声明的路径
prd.yaml → architecture.yaml → openapi.yaml(可选) → design.yaml(可选)
         → epics.yaml + stories.yaml（两文件齐全才算完成）
         → test-plan.yaml → sprint.yaml → 任务执行
# 回执键
position: 零起点 | 第 N/M 步：<skill> | 阻塞于 <file> | 执行阶段 | 工作流完成
output_dir: 本次运行唯一的读写根
completed_steps: [技能名]
next_skill: 技能名 | null
blocked: {file, status, action} | null
notes: [可选提示]          # blocked 在场时被抑制
workflow_done: true | false
```

- 各产物的 status 在 `project.status`；`openapi.yaml` 的在 `x-project.status`（读不到才回落 `project.status`）。
- `openapi.yaml` / `design.yaml` 是可选节点：缺席=合法跳过（`notes` 给提示），在场但非 `已定稿` 才阻塞。
- 位置与推荐只由脚本给出——本技能不重算、不预测。

## 规则

1. **零写回。** 只读导航：不写产物、不改配置、不渲染（无 YAML 产物——母本 §5 不适用）。
2. **脚本是唯一权威。** 绝不发明回执之外的位置或技能。结果与用户认知相左时，带 `--json` 重跑一次并摊开原始数据——这是「只跑一次」的唯一例外；YAML 文件是真源，不是本技能。
3. **回复纪律。** 用 `project.communication_language` 回复；10 行上限只约束我自己的附加说明，脚本输出（尤其 `blocked` 段）逐字转述不受行数限制——宁可超行数，也不得压缩或改写阻塞原因。
4. **依赖。** 脚本要求宿主 Python 装有 PyYAML。报 `ModuleNotFoundError`（`No module named 'yaml'`）时照实报告并建议 `pip install pyyaml`——绝不静默降级。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。
