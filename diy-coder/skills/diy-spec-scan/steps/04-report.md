# Step 4 — 落盘与交付（Report）

Progress: `Collect → Dry Run → Cross Check → [Report]`

**读入：** 定稿的 findings；引擎 `check` 回执。
**写出：** `{output_dir}/spec-scan.yaml` 定稿（`status: final`）；渲染；交付摘要。

## 定稿

1. `open_questions` 收尾：无法定级的、需要用户拍板方向的，写进这里（≤5 条）。
2. 记录改 `status: final`，`project.updated` 改今天。
3. 全文档搜一遍 `[ASSUMPTION]`——本产物禁止该字面量（存疑走 `open_questions`，不用假设标记）。

## 终门

```
python "{project-root}/.claude/skills/diy-spec-scan/scripts/spec_scan.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`exit 0` 是唯一放行。违规 → 按回执的 `where` 就地修，重跑，直到 exit 0。不得跳过。

## 渲染

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

静默执行，不进浏览器、不等路径、不阻塞。

## 交付摘要

给用户一份能直接决策的摘要：

```
扫描完成：<目标名>
- 单元 N 个全部扫完（M 行）
- findings 共 K 条：blocker X / major Y / minor Z

Blocker（必须裁定）：
1. SS-001-03 <类型> <path:line> — <一句话：卡在哪 / 会猜成什么>

其余按类型分布：<类型> ×N ……

建议：blocker 裁定后改规格；major/minor 可批量过一遍。
```

每条 blocker 必须带"会猜成什么"——用户靠这一句就能拍板，不必回去读原文。

## 路由

- 用户裁定完 → 规格修改由用户或对应负责人执行（本技能不改规格）。
- 扫的是迁移任务书且裁定完成 → 可进入建设批次。
- 想复查另一个目标 → 重新从 step 1 开始（新建 `SS-002` 记录）。
