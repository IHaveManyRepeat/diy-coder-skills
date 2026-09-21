# Step 1 — 定范围（Scope）

Progress: `[定范围] → 执行 → 汇报与终门`

**Read (input):** 用户给的技能路径与模式；该技能的 `SKILL.md`（只为确认存在）；用例文件（形态自检）；adapter（若有）。
**Write (output):** 对话里的运行摘要（skill / cases / modes / runs / output_dir / adapter）；`mlog` 的一条 `decision`。

## 定位 target

用户显式给的路径优先；对话里已出现的技能名（"评测一下 diy-elicit"）按安装面 `{project-root}/.claude/skills/<名>/` 与套件源 `diy-coder/skills/<名>/` 两处找。两处都没有、或目录里没有 `SKILL.md` → **一行拒绝**（点名缺什么）+ 零产出 + 停：`run` 会在门禁处回 `MISSING_FILE`。

## 发现用例文件

发现链照引擎，**找不到就停**——运行器不发明用例：

```
--evals <F>  >  <技能目录>/evals/cases.json  >  {project-root}/evals/<技能名>/cases.json  >  {project-root}/evals/cases.json
```

- 找到 → 读一眼形状：`{"id", "input", "rubric": [...], "state_prefix"?, "files"?}`（trigger 用 `--queries`，形态 `{"query", "should_trigger"}`）。形状不对 → 引擎回 `UNPARSABLE_JSON` / `EMPTY_FIELD`，据此报一行并停。
- 找不到 → 一行说明「该技能没有用例」，并指路：用例归 **`diy-bmb-builder` 的 eval beat**（造技能时就地落 `<技能>/evals/cases.json`）或用户手写；**本技能不代写**。

## 解析 adapter

顺序：`--invocation <命令…>`（命令模板，优先）> `--adapter <F>` > 用例文件旁的 `adapter.json`。三处都没有不是错——逐键取默认，只是**没有 invocation 就只 stage、结果记 `skipped`**（引擎会明示，不静默）。

- `invocation` 里不写模型名：`{prompt}`（别名 `{query}`）换成问句/输入，`{cwd}` 换成清场目录。
- `load_signal` 只收具名工具（`{"skill_tool": "Skill", "read_tool": "Read"}`）；**子串式（`{"type": "string"}`）引擎直接拒跑**——那会让触发率恒为 100%。
- 无头下 `claude` 不在 `runner.py` 的默认命令白名单内：真跑会走降级路径（见 step 2）。要真跑就给调用方传 `runner.py --allow`，或换一个在白名单内的 invocation。

## 确认运行摘要（不给确认就不跑）

```
评测对象：<技能名>（<技能目录>）
用例：<N> 条（<用例文件路径>）｜模式：<baseline / variant / quality / trigger>
重复：--runs <N>｜adapter：<none / 路径>
产物：{output_dir}/eval-runs/<时间戳>-<label>/
```

- **交互态**：把摘要摆给用户，问一次「就这样跑？」——变体模式要确认 `--variant-path` 指的是哪个精简版；trigger 要确认问句集。
- **无头**：跳过确认，取最保守的默认（`--runs 1`）直接跑，摘要进收尾行。
- 摘要定了往 run memlog 记一条（step 2 起 run 目录后补），此处先在对话里给出。

做完读并照做 `./02-run.md`。
