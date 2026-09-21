# Step 1 — 意图路由与开场

Progress: `[意图路由与开场] → 构建单循环 → 五透镜分析 → 门禁与评测 → 交付收尾`

**Read (input):** 用户的原始来意（描述 / 路径 / 计划文件）；`diyc.py resolve` 回执；`{output_dir}/build-logs/` 下与本技能相关的日志。
**Write (output):** 判定出的意图与目标技能路径（对话里给出，不落盘）；`mlog init` 建日志；给用户的一句进度播报。

## 定意图

三选一——**Build 造 / Edit 改 / Analyze 评**。用户说清了就用；没说清就问一次，给三个选项（造新的 / 改已有的 / 评已有的），等回话，别猜。判据：

- 给的是一个**新东西的描述**（"我想要一个能……的技能"）→ Build。
- 给的是**既有技能的路径** + 要改什么 → Edit。
- 给的是**既有技能的路径** + 要评什么（"看看它怎么样"）→ Analyze。
- 给的是**计划文件**（`module-plan.yaml`）→ 见下节。

`--headless` / `-H` 出现即置无头态：跳过所有交互提问，缺省值一律落 memlog 的 `assumption` 条目。

## 门禁（三条，全部零产出）

1. **无意图**：既没说造什么、也没有目标技能 → 一行拒绝（点名缺什么）+ **零产出**，停。
2. **输入过薄**（仅 Build）：没有任何真专家知识可扎根（没有 runbook / 事故报告 / 评审意见 / 提交史 / 一次手做的转录）→ **停并问**，不要拿模型的通识起草。硬化优先于生成。
3. **Analyze 的 target 不存在 / 无 `SKILL.md`**：不在本步拦，交给 `prepass` / `check` 拒（回执 `MISSING_FILE`），把违规码转述给用户后停。

## 续接检测

目标技能定了之后，看 `{output_dir}/build-logs/<skill-name>.md` 在不在。在 → **整读一次**重建上一轮的状态，然后继续只经 `mlog` 追加；不在 → 跑一次建日志：

```
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" mlog --dir "{output_dir}/build-logs" init --file <skill-name>.md --subject "<一句话主题>" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

日志是**唯一的过程记忆**（不要再找 `.decision-log.md` 之类）。文件名由调用方显式给，不靠目录反推。

## 放权开场（交互态）

在任何结构化提问之前，请用户把他手上的东西**一次倒完**：目标、参考、例子、半成型的点子、既有技能或产物的路径、规格或简报。倒完补一句软性的"还有吗"。**无头态跳过**；来意已经够动手时也跳过。

## 接计划文件（`module-plan.yaml`）

来意是计划文件时：先要求它 `status: 已定稿`。

- 已定稿 → 按 `build_order` 逐个造，每个技能用 `skills[]` 里的自足 `brief` 当 Build 输入（brief 就是为了"不靠对话上下文直接交棒"而写的）。
- 未定稿 → **停**，一行说明并指向 `diy-bmb-module`（计划器负责定稿；本技能不替它改计划）。
- 计划里 `dropped: true` 的条目跳过；`build_order` 之外的条目不擅自补做。

## 播报与下一步

给用户一句话：意图、目标技能名与落点、本轮打算做什么。

- Build / Edit → 读全并照做 `02-build.md`。
- Analyze → 读全并照做 `03-analyze.md`。
