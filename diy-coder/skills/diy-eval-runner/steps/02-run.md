# Step 2 — 执行（Run）

Progress: `定范围 → [执行] → 汇报与终门`

**Read (input):** step 1 的摘要；用例文件 / 问句文件；`references/eval-format.md`（case 与强/弱 expectation）、`references/grader.md`（quality 才读）、`references/platform-adapter.md`（隔离契约与触发判定）。
**Write (output):** run 目录（引擎一次写全）；quality 的 `grading.json`（grader 写）；`mlog` 的 `decision` / `event` 条目。

## 起 run

```
python "{project-root}/.claude/skills/diy-eval-runner/scripts/eval_runner.py" run --skill <技能目录> [--evals <F>] --mode <M> [--mode <M>]... [--runs N] [--invocation <命令…> | --adapter <F>] [--variant-path <P>] [--queries <F>] --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `--mode` 可重复（一次 run 可同时要 baseline 与 quality）；不给即 `quality`。
- 引擎建 run 目录并写公共根三件（`run.json` / `execution-summary.json` / `.memlog.md`）、逐 case stage 与执行、即时落 `timing.json`（完成瞬间写盘，后崩不丢测量）。
- 记住回执里的 `run_dir`——后续每一步都用它，别用时间戳臆造。
- **发现同 label 的未完成 run 只提示不续跑**（`INCOMPLETE_RUN` warning）：本批不做 `--resume`、不自动合并、不覆盖既有目录。

## 清场环境契约（引擎实现，你只需知道它为何可信）

每个 case 在**清场工作目录**里跑：子进程环境**从零构建、绝不继承**——只有 `PATH` + 全新的空 `HOME`（`<case>/.home`）+ 指向其中的 `CLAUDE_CONFIG_DIR` + adapter 的 `auth_env` 变量（**仅当宿主非空才传**：传空串会毁掉运行时自己的凭据回落）+ `env_passthrough` 键。无容器、无终端模拟、无凭据文件暂存。故结果反映的是**技能在干净环境里的行为**，不是宿主 shell 的记忆与配置。

## quality：派只读 grader

quality 模式引擎只负责把 case 跑完；评分由你**逐 case 派一个只读 grader 子代理**（契约见 `references/grader.md`），传它：

`case_id` / `input`（含已前置的 `state_prefix`）/ `rubric` 列表 / `transcript_path`（`<case 目录>/transcript.jsonl`）/ `artifacts_dir`（`<case 目录>/cwd/`）/ `grading_path`（`<case 目录>/grading.json`）。

三纪律（**不许打折**）：

1. **不给部分分**——每条 expectation 只有过 / 不过。
2. **举证责任在通过方**——无证据不得判过；证据不确定即判不过。判过要引证（引一行、点名一个文件、指一个事件序号）。
3. **反向批评 rubric**——标出「错输出也会通过」的弱断言，点名 rubric 漏掉的重要结果；写进 `grading.json` 的 `rubric_feedback`。

grader 只读 run 目录、只写 `grading.json`；子代理出错 → 该 case 记 `grading_error`，**绝不代入默认判决**。引擎的终门会按「每条 expectation 都有非空 `evidence`」复核——写满证据才放行。

## 两条降级路径（都不崩、都不静默、都不入队）

- `invocation` 解析为空 → 只 stage，结果记 `skipped`（回执带 `ADAPTER_MISSING` warning）。补上 invocation 再跑。
- invocation 命令不在 PATH（无头下即 `runner.py` 白名单未覆盖该命令族）→ 跳过该 mode 并明示（回执带 `MODE_SKIPPED` warning，`execution-summary.json` 记 `skipped_modes`）。**不入队**——确认是当场决策，队列语义是「用户稍后自行执行」；要真跑请调用方经 `runner.py --allow` 传入该命令族。

## trigger：只认 `tool_use`

引擎给每条问句 stage 一个唯一名（`<技能名>-trig-<uuid8>`）的合成技能，逐问句跑 `--runs` 次算触发率。**触发判定只看 `tool_use`**：点名合成技能的技能调用工具，或读取落在合成技能目录内的文件。init 事件与文本提及**一律不算**——init 会列出每个被发现的技能名，算进去触发率就永远 100%。

触发是概率事件：建议 `--runs 3`（否则一条问句跑一次就是个硬币）。判据 = 该触发的问句触发率 ≥ 阈值、不该触发的低于阈值；阈值缺省 `0.5`。

## 记 run memlog

决策与方向变化随发生随记（**只追加**）：

```
python "{project-root}/.claude/skills/diy-eval-runner/scripts/eval_runner.py" mlog --dir <run 目录> append --file .memlog.md --type decision --text "<一句话>" --project-root "{project-root}" --output-dir "{output_dir}"
```

`--type` ∈ `decision` / `direction` / `assumption` / `gap` / `note` / `event`；每次操作恒发一行 ack `{ok, file, n, appended}`。全部跑完（或降级结束）走 `set-complete`。

做完读并照做 `./03-report.md`。
