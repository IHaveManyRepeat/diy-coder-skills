# Step 4 — 账本计算（Score）

Progress: `Preflight → Criteria → Evaluate → [Score] → Report`

**Read (input):** `{output_dir}/test-review-findings.json`；`score` 回执。
**Write (output):** 草稿记录的 `findings` / `score` / `dimensions` 区块（**照抄回执，不手写数字**）。

## 1. 跑 score（纯函数，只算不写）

```
python "{project-root}/.claude/skills/diy-test-review/scripts/test_review.py" score --findings "{output_dir}/test-review-findings.json" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

管线（全在引擎里，你只看结果）：severity 复算（按 `criteria.yaml` 行值 + convention 行按 `class` 降档）→ 按 `file:location:row` 去重（文件级行以 `file` 取代行号，去重在计分之前）→ deductions / bonus → score / grade / recommendation → 维度分。

口径（不得漂移）：`deductions = CRITICAL*10 + HIGH*5 + MEDIUM*2 + LOW*1`；bonus 六类各 0 或 5、上限 30；`score = clamp(100 - deductions + bonus, 0, 100)`；A≥90 / B≥80 / C≥70 / D≥60 / F<60。

- `exit 1` = findings 载体有问题（row 越界 / 用了 disabled 行 / convention 行缺 `class` 或用了 `absent`·`unknown` / 行号形态错 / bonus 数值域 / bonus 与命中矛盾）——**回 step 3 改判定，不改引擎**。
- `ok: false` 的回执里每条 violation 都点名了 `where`，逐一处置后重跑，直到 exit 0。

## 2. 落回产物

把回执的 `deductions` / `bonus` / `score` / `grade` / `recommendation` / `dimensions` / `counts` 照抄进草稿记录：

- `findings` 区块逐条写 `{row, severity, file, line, note, basis, class}`——`severity` 与 `basis` 取自 `criteria.yaml` 的对应行，`class` 仅 convention 行写（照抄 step 2 的键值），`line` 为 null 只限文件级行。
- **`score` 五键与 `dimensions` 一律由引擎产出**；手写数字会被 `check` 的账本自洽判据打回。

## 3. 展示

给用户一行硬事实，不给修饰：`score/grade/recommendation`，四档计数（CRITICAL / HIGH / MEDIUM / LOW），维度分四值。recommendation 是**算出来的**，不是判断出来的——`Block`（有用例不可能失败）不等于"再商量"，它意味着先修再谈。

**下一步：读 `steps/05-report.md`。**
