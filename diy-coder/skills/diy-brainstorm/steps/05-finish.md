# Step 5 — 收尾：终门、渲染与交付（Finish）

Progress: `会话设置与续接 → 技术选取 → 教练执行 → 组织 → [收尾]`

**Read (input):** 定稿的记录（`themes` / `priorities` / `actions` 已齐）；引擎 `check` 回执。
**Write (output):** 记录的 `status: 已完成` + `current_step: 5`；渲染；给用户的交付摘要。

## 一、定稿前自清

1. 未决项落位：拿不准的、要用户日后拍板的，写进 `open_questions`（**不用 `[假设]` 标记**——定稿前必须清零）。
2. 收尾态硬要求复核（终门会查）：`themes` 非空、`actions` 非空、`priorities.top` 非空。
3. 记录改 `status: 已完成`、`current_step: 5`；`project.updated` 刷今天（记录的 `date` 不动——它记的是会话建立的日子）。

## 二、终门（机械）

```
python "{project-root}/.claude/skills/diy-brainstorm/scripts/brainstorm.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`exit 0` 是唯一放行。违规 → 按回执的 `where` 就地修，重跑，直到 exit 0。不得跳过。回执的 `counts`（`sessions` / `ideas`）就是收尾证据。

## 三、渲染

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

静默执行，不进浏览器、不等路径、不阻塞。

## 四、交付摘要

给用户一份能直接决策的摘要：

```
会话完成：<议题>（BS-###）
- 走过 N 个技术：<技术名列表>
- 想法 M 条 → 主题 K 个
- Top 优先级：<no 列表>；快速见效：<no 列表>；突破：<no 列表>
- 行动计划 L 条：<一句话，每条>
- 未决问题：<open_questions 逐条，无则写「无」>
```

## 五、路由

- 想继续发散 → **新开会话**（回 `./01-session.md`，铸下一条 `BS-###`）；已完成的记录只读回看，不再写入。
- 要让某条想法变成规格 / 需求 → `diy-prfaq` 点火或 `diy-prd` 立需求。
- 要对某个想法做深挖增强 → `diy-elicit`（零写面，结果交回本会话或对应产物持有者落盘）。
- 本次会话的产物是 `/diy-viewer` 渲染出的 `brainstorm.yaml` 视图。

## 播报与下一步

这是最后一个步骤文件——终门 exit 0 后本轮到此结束。会话结论由 `themes` / `priorities` / `actions` / `open_questions` 承载；不再读任何 `steps/` 文件。
