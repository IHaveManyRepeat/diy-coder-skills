# Step 3 — 汇报与终门（Report）

Progress: `定范围 → 执行 → [汇报与终门]`

**Read (input):** run 目录的 `execution-summary.json` / `triggers-result.json` / `timing.json` / `grading.json`；终门回执。
**Write (output):** `mlog` 的收尾条目；run 目录内的 `grading.json`（若 quality 刚补完）；会话摘要。

## 聚合

```
python "{project-root}/.claude/skills/diy-eval-runner/scripts/eval_runner.py" aggregate --run-dir <run 目录> [--against <config>] --project-root "{project-root}" --json
```

- 逐 config 出 `mean` / **样本标准差（n-1 贝塞尔校正）** / `min` / `max`；对比出 `delta` 与 `delta_pct`。
- `delta` 的定义写死：**被测侧 `skill` 的均值 − `--against` 基准的均值**；`--against` 缺省 `bare`（基准不在场时退回 run 的另一个非 `skill` config 并 warning）。单 config 的 run（trigger）无 delta 面 → 只出均值与离散度。
- 想只验公式：`aggregate --self-test --json`（固定夹具，不依赖任何 run）。
- **均值是信号不是结论**：方差大时先加 `--runs` 再说「有差别」；一次之差不能当证据。

## 终门

```
python "{project-root}/.claude/skills/diy-eval-runner/scripts/eval_runner.py" check --run-dir <run 目录> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`exit 0` 是唯一放行。它验的是**结构与自洽**，不是「结果好不好」：公共根三件在场；`execution-summary.json` 的计数与实际目录一致（`SET_MISMATCH`）；每个已执行 case 的文件齐（`MISSING_FILE`）；quality 的每个已执行 case 有 `grading.json` 且**每条 expectation 举证非空、score 无部分分、`rubric_feedback` 三键在场**；trigger 的 `detection` 必须是 `tool_use`、触发率与 `triggers/runs` 一致、`pass` 与阈值判定一致。

按回执的 `where` 就地修（缺 `grading.json` 就补派 grader；计数不符就说明手改过 run 目录），重跑至 exit 0。**run 目录追加式、无「定稿态」**——本技能没有 `--final` 旗标，终门只此一条。回执的 `counts.run_dirs` 是累计 run 目录数（只报表不清理；清理归用户决定）。

## 摘要（给用户一份能直接决策的东西）

```
评测完成：<技能名>｜run 目录 <run_dir>
- baseline：skill <均值> vs bare <均值>（delta <±值>）——打不过裸模型就该退休，不是打补丁
- variant：全量 vs 精简版（delta <±值>）——同分即那节是装饰，可裁
- quality：<通过/总数>（逐条失败的 expectation 与证据摘一句）
- trigger：<通过/总数>，失败问句逐条列（该触发没触发 / 不该触发却触发）
降级与警告：<ADAPTER_MISSING / MODE_SKIPPED / AGAINST_FALLBACK / INCOMPLETE_RUN 逐条>
```

**诚实底线**：绿灯只报绿不给结论；靠平凡理由通过的 case 要点出来（弱断言在 `rubric_feedback.weak` 里）；**绝不为了好看放宽阈值或去掉失败的 case**。

## 路由

- baseline 打不过裸模型 → 建议**退休或重定位**，而不是继续加补丁。
- variant 与精简版打平 → 该节是装饰：按 `diy-bmb-builder` 的 Analyze 模式给的 `proposed_smallest` 裁掉，再复跑一次确认。
- quality 未过 → 改技能（不是改 rubric）；若判定 rubric 本身弱，按 `rubric_feedback` 重写 expectation（强/弱分类见 `references/eval-format.md`）。
- trigger 失败 → 改 `description`（分层切分、测试集盲化的闭环见 `references/description-optimization.md`）。
- 想按结果反复改进技能 → **先问用户**（自改进是 opt-in），闭环与轮数上限见 `references/self-improvement.md`。

这是最后一个步骤文件——终门 exit 0 后本轮到此结束；不再读任何 `steps/` 文件。要再跑一次就另起一次 `run`（新 run-id、新 run 目录），既有 run 目录永不删除、覆盖、轮转。
