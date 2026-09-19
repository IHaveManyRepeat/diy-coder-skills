# Step 5 — 结业摘要与终门（Completion）

Progress: `Init → Assess → Hub → Session → [Completion]`

**Read (input):** `progress.py status` 回执（7 节分数与日期、学员画像、`learner.assessed`、`started_date`）；台账 `{output_dir}/learning-progress.yaml` 的节记录；`templates/completion-summary.md`。
**Write (output):** `{output_dir}/completion-summary.md`（散文，本步骤唯一的 md 落点）；`summary` 区块——只经 `update --summary`。

## 门：7 / 7

回执 `sessions_completed == 7`（含 session 7 的探索主题数达标）才往下走；不满 7 节 → **停下**，报「还差 N 节」并把用户送回 `./03-hub.md`，零写入。这不是错误状态，是门没到。

## 算数（只算一次）

- **平均分**：只对第 1-6 节中**有 `score` 的节**求值取整（session 7 无 quiz，不参与；无分的节跳过，不按 0 计）。
- **总历时**：由 `started_date` 到当日的天数，写「N 天」或「N 周」。
- **各节分数**：逐节取 `score`，session 7 记探索主题数。

这些数字**一律从 `status` 回执取**，不凭记忆、不重算。

## 生成摘要

按 `templates/completion-summary.md` 写 `{output_dir}/completion-summary.md`：课程信息 / 完成的课次 / 掌握的能力 / 学习产物 / 下一步。摘要里的「下一步」指 diy 测试链技能（`diy-test-design` → `diy-test-framework` → `diy-test-author` → `diy-test-review` → `diy-test-gate`，补测用 `diy-augment` / `diy-e2e-tests`）——不出现源平台品牌字样与外部 URL。

## 置位（唯一通道）

```
python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" update --summary --path completion-summary.md --project-root "{project-root}" --output-dir "{output_dir}" --json
```

引擎在这里把三道门一次挡完：7 节未满 → `STATUS_MISMATCH`；路径不解析到 `{output_dir}/completion-summary.md` → `ENUM_INVALID`；摘要文件不在场 → `MISSING_FILE`。撞到拒回就按报告的位置补齐再跑，不要手改 YAML。成功即 `summary.generated: true` + `date` = 当日。

## 终门（机械判定）

```
python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`exit 0` 是唯一放行——它同时证明三件事：7 节全 `已完成`、`summary.generated` 为真、摘要文件在盘上。有违规就**修掉每条并重跑**（回执的 `counts` 就是收尾证据：完成节数 / 完成度）。渲染与收尾都等 `exit 0`。

## 收尾

播报结业结果（平均分 / 总历时 / 摘要路径 / 笔记目录），并说明随时可回任一节复习：重做会覆盖同名笔记、分数以最新一次为准，进度台账照常续用。

## 播报与下一步

读 `./03-hub.md` 并照做（完成态 Hub：可重进任一节，或结束本次运行）。
