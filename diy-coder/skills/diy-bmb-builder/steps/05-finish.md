# Step 5 — 交付与收尾

Progress: `意图路由与开场 → 构建单循环 → 五透镜分析 → 门禁与评测 → [交付与收尾]`

**Read (input):** 定稿的技能目录；`check --final` 回执；memlog 全文（审计用）。
**Write (output):** `mlog set-complete`；给用户的交付摘要与分发说明（对话里给出，不落盘）。

## 收尾 memlog

```
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" mlog --dir "{output_dir}/build-logs" set-complete --file <skill-name>.md --project-root "{project-root}" --output-dir "{output_dir}" --json
```

**审计**：把 memlog 整读一遍，逐条确认用户的想法被按他的意思处理了——每条 meaningful 的条目要么已被产物吸收、要么被显式搁置为过程噪音。有对不上的，当场说清，别闷在日志里。

## 交付摘要

给用户一份能直接决策的摘要：

```
<技能名> — <Build|Edit|Analyze> 完成
- 落点：<技能目录>（安装面 / 套件源）
- 文件：SKILL.md（N 行）+ steps/ X 个 + scripts/ Y 个
- 终门：check --final exit 0（四段 / ≤90 行 / 母本逐字 / 自足 / 六字段）
- 评测：<跑了哪种模式 + 结论 | 未跑（opt-in）| 降级原因>
- 日志：{output_dir}/build-logs/<skill-name>.md
```

Analyze 意图的摘要换成：grade、verdict、severity 计数、最值钱的主题、报告路径（`<被分析技能>/.analysis/<时段>/skill-analysis-report.html`）——报告已由脚本渲染落盘，**不打开浏览器、不等用户来看**。

## 分发说明

技能目录是**自足的**（NFR-4）：`SKILL.md` + `steps/` + `scripts/` 自带全部内容，运行期只依赖目标机上已装的 diy-coder 套件（`diyc.py` / `viewer.py` 那些套件级工具，以及 `{project-root}` 令牌路径）。

**分发 = 拷贝目录**：把这个目录拷到任何已经装好 diy-coder 套件的项目 `.claude/skills/` 下即生效，不需要打包格式、不需要安装脚本、不需要再跑一次同步。反过来说：目标机上没有 diy-coder 套件时，本技能造出来的技能会缺它调用的套件级工具——这是要提前讲清的前提。

**要让它进套件本体**（随 git 分发、被 `install.py` 带上）：交互态确认后重跑一次 `scaffold --to-source`（或直接把目录移进 `{project-root}/diy-coder/skills/`，技能名须带 `diy-` 前缀），随后由套件维护者做集成同步——**本技能不跑 `install.py`**。

## 路由

- 还想改同一个技能 → 回到 step 1（Edit 意图；续接检测会读回同一份日志）。
- 报告里还有没结清的 finding → 按用户选择：就地改（Edit）或路由到 `diy-eval-runner` 的 variant 模式取判决。
- 造下一个技能 → 同样从 step 1 开始；有 `module-plan.yaml` 就按 `build_order` 接着做。

## 播报与下一步

这是最后一个步骤文件——`mlog set-complete` 打完、摘要给出后本轮结束。结果由技能目录、memlog 与分析报告承载；不再读任何 `steps/` 文件。
