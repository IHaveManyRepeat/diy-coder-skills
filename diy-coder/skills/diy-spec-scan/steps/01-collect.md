# Step 1 — 定位与切分（Collect）

Progress: `[Collect] → Dry Run → Cross Check → Report`

**读入：** 目标路径（On Activation 定下的）；引擎 `collect` 的回执。
**写出：** `{output_dir}/spec-scan.yaml` 的草稿记录（`id` / `date` / `target` / `units`）；给用户的进度播报。

## 跑引擎

```
python "{project-root}/.claude/skills/diy-spec-scan/scripts/spec_scan.py" collect --target "<目标路径>" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

回执给出：目标文件清单（相对路径 + 行数）、每个文件按 `## ` 二级标题切出的**单元名**、总计。

`ok: false` → 把违规码与消息转述给用户，零产出停止（这是拒绝路径，不是记录）。

## 定目标类型

`target.kind` 由你判定（引擎不给），三选一：

- `taskbook` — 任务书 / 施工指令（含角色分工、分节规格）
- `skill` — 技能规格（`SKILL.md` + `steps/`）
- `spec` — 其他给 AI 执行的规格文本

## 调整单元粒度

引擎按二级标题切单元，这是**起点不是终点**。两条调整纪律：

1. **合并过碎的单元** —— 短于 15 行的连续单元可并成一个（连续的标题行、一两句话的小节等）。单元的意义是"一段可独立预演的执行指令"，不是标题计数。
2. **拆分过大的单元** —— 单单元超过约 150 行时按三级标题再切，否则预演时会滑过细节。

调整后的单元清单必须**覆盖全部正文**：每个文件的所有行都要落进某个单元，或被显式标为"非规格正文"（目录、参考文献、附录索引）。覆盖是唯一的防漏扫凭证。

## 落草稿记录

创建 `{output_dir}/spec-scan.yaml`（文件不存在时建：`project: {name, created, updated}`——`name` 取自 `diy-coder.yaml` 的 `project.name`——加空的 `scans: []` 与 `revisions: []`），追加一条：

```yaml
  - id: SS-001            # 下一个 = 已有序号最大值 + 1，三位零填充；不重编不重用
    date: YYYY-MM-DD
    status: 草稿
    target: {kind: <判定值>, path: <相对路径>, files: N, lines: N}
    units:
      - {unit: <单元名>, path: <相对路径>, lines: N, scanned: false}
    findings: []
    summary: {total: 0, blocker: 0, major: 0, minor: 0, units_total: N, units_scanned: 0}
    open_questions: []
```

`units` 先全部写 `scanned: false`，step 2 每扫完一个改成 `true`——这是覆盖凭证，不是装饰。

## 播报与下一步

给用户一句话：目标是什么、切出多少个单元、总共多少行、下一步开始预演。

读完并执行 `./02-dry-run.md`。
