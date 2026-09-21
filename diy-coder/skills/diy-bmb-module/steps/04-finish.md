# Step 4 — 终门与交付（Finish）

Progress: `构思会话 → 落计划 → 校验 → [终门与交付]`

**Read (input):** 通过 step 3 的计划文件；`check --final` 的回执。
**Write (output):** 计划记录的 `status: 已定稿`；渲染调用；交棒摘要。

## 终门

1. 把被定稿的记录改成 `status: 已定稿`（顶层不设 status——定稿态挂记录级）。改前确认零 `[假设]` 字面量：未落定的推断先落定，别带进定稿稿。
2. 跑机械终门：

```
python "{project-root}/.claude/skills/diy-bmb-module/scripts/bmb_module.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

**退出 0 是唯一放行**；逐条修违规、重跑，回执（含 counts）就是收口证据。`--final` 的作用域随 `--id`，缺省 = 全部记录逐条要 `已定稿`。空态（`plans: []` 或 `skills: []`）在 `--final` 下一律拒绝——空计划不是计划。

3. 渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 交棒

计划是给 `diy-bmb-builder` 消费的数据。交棒口径：

- 指向计划文件与 `build_order` 的第一个技能名，提议当场开造（"计划已定稿于 `<path>`，路线图建议先造 `<diy-xxx>`——现在开 `diy-bmb-builder` 吗？我会把计划文件作为上下文传过去"）。
- **交棒前置**：计划须 `status: 已定稿`；`diy-bmb-builder` 会在未定稿时停下并让你先回本技能定稿。
- 本技能**不推进建造**——造物是 `diy-bmb-builder` 的事；用户拒绝交棒也到此为止。

## 摘要

末尾给一段（不落盘成第二个产物）：

- 计划位置 + `MP-###` + slug；
- 技能清单（名字 + 一句话 purpose）；
- `build_order` 与第一个要造的技能；
- 未决问题（`open_questions`）与 warning 计数；
- 一行路由：开造 → `diy-bmb-builder`；想法还要再长 → 本技能重跑（同 slug 就地更新）。

## 播报与下一步

会话到此结束；用户要开造时，指路 `diy-bmb-builder` 并带上计划文件。
