# Step 4 — 落盘与交付（Report）

Progress: `定位与切分 → 预演执行 → 交叉验证 → [落盘与交付]`

**Read (input):** 定稿的 findings；引擎 `check` 回执。
**Write (output):** `{output_dir}/spec-scan.yaml` 定稿（`status: 已定稿`）；渲染；交付摘要。

## 定稿

1. `open_questions` 收尾：无法定级的、需要用户拍板方向的，写进这里（≤5 条）。
2. 记录改 `status: 已定稿`，`project.updated` 改今天（记录级 `date` 不动——它记的是本次扫描的日子）。
3. `findings` 的**非 `quote` 字段**禁止 `[假设]` 字面量（存疑走 `open_questions`，不用假设标记）；**`quote` 豁免**——引文逐字照抄，被扫规格自带该标记时不改写；非 `quote` 字段确需提及该标记时写全角 ［假设］。终门只扫 `findings` 字段，其余部分不在扫描面内。

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
- findings 共 K 条：阻断 X / 建议 Y / 观察 Z

Blocker（必须裁定）：
1. SS-001-03 <类型> <path:line> — <一句话：卡在哪 / 会猜成什么>

其余按类型分布：<类型> ×N ……

建议：`阻断` 裁定后改规格；`建议` / `观察` 可批量过一遍。
```

每条 `阻断` 必须带"会猜成什么"——用户靠这一句就能拍板，不必回去读原文。

## 路由

- 用户裁定完 → 规格修改由用户或对应负责人执行（本技能不改规格）。
- 裁定完成 → 规格由用户 / 对应负责人修订；修订后同一目标可**重扫一次**（新建 `SS-002` 记录）——比对 blocker 是否清零，即本轮整改的收尾凭证。
- 想复查另一个目标 → 同样从 step 1 开始（铸下一条 `SS-0nn` 记录）。

## 播报与下一步

这是最后一个步骤文件——终门 exit 0 后本轮到此结束。结果由 `summary` 计数、`findings` 与 `open_questions` 承载；不再读任何 `steps/` 文件。
