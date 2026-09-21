# Step 4 — 门禁、两版对比与评测

Progress: `意图路由与开场 → 构建单循环 → 五透镜分析 → [门禁与评测] → 交付收尾`

**Read (input):** 造出（或改过）的技能目录；三个 lint 门回执；`diy-eval-runner` 的 run 回执。
**Write (output):** `<技能目录>/evals/cases.json`；`mlog` 条目；给用户的 lint 结果与裁决建议。

## lint gate（三次修不好就停）

```
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" prepass --target "<技能目录>" --set all --project-root "{project-root}" --output-dir "{output_dir}" --json
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" scan --target "<技能目录>" --check all --project-root "{project-root}" --output-dir "{output_dir}" --json
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" check --target "<技能目录>" --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

三个都 `exit 0` 才继续。`where` / `msg` 指哪修哪，修完重跑（**不要跳过、不要只改回执**）。**同一个违规修三次还不好 → 停并上报**：把它记成 `mlog` 的 `gap`，写清卡在哪、你试过什么，然后交给用户——不要进入无休止的自我修补。

三条判据各有侧重：`prepass` 查结构与语言（阶段文件落点、禁用段、残留标记、四段、步骤编号、直白度）；`scan` 查机械形态（绝对路径、越界引用、脚本合规）；`check --final` 查**四项**——结构合规（四段 + `SKILL.md ≤90 行`）/ 母本句式逐字 / 自足性 / frontmatter 六字段。token 计数只作信息面（`prepass --set metrics` 出数），不构成门禁。

**自己是精简的，才有资格教精简**：过门前确认这个技能自己也过得去 leanness 那一关；`SKILL.md` 超 90 行就把最大的自足段落搬到 `steps/` 或 `scripts/`，而不是压缩成要解码的句子。

## 两版对比裁决

结构不是从单次运行里能判出来的——输出看起来一样，无论模型是尽了力还是将就了。拿**最小版**（角色 + 产出 + 消费者 + 一条有血债的规则，约五行）与当前版**在同一个输入上**跑一遍，读判决：

| 看到什么 | 意味着什么 |
| --- | --- |
| 最小版赢 | 那些结构是紧身衣，砍掉 |
| 打平 | 结构是装饰，逐行辩护或杀掉 |
| 最小版更糙，但两轮内能追回来 | 你买到的是省事，不是质量——认了就行 |
| 最小版明显更差且一直差 | 结构挣到了它的位置，暂时留着 |

跑不了两版对比时，逐行按 leanness 三测过一遍即可。分析模式留下的 `proposed_smallest` / `predicted_delta` 正是为这一步准备的输入。

## eval beat（opt-in，调 `diy-eval-runner`，不 fork）

**先产用例**——用例由本技能自己落，运行器不发明用例：

```json
[{"id": "<case-id>", "input": "<真实输入>", "rubric": ["<可判定的期望>"],
  "state_prefix": "<可选的方括号起手式：把技能按到流程中段>", "files": ["<随输入附带的文件>"]}]
```

写进 `<技能目录>/evals/cases.json`。强期望 = 必须出现的事实 / 结构断言 / **否定断言** / frontmatter 检查 / 有界输出块 / 过程纪律；弱期望（只查文件名在不在、纯主观措辞、同义反复）**比没有更糟**，别写。

再调被调方（**评测一律走它，本技能不自造评分逻辑**）：

```
python "{project-root}/.claude/skills/diy-eval-runner/scripts/eval_runner.py" run --skill "<技能目录>" --mode <baseline|variant|quality|trigger> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

**分工：产出归它、施加归本技能**——它出 run 目录与判据结果，你把结论施加回技能（改哪一行、留还是砍），不接受也不代改它的 run 目录。四模式各自结清一件事，逐条向用户说清再让他选：

- `baseline`：打得过裸模型吗——打不过就没有存在的理由。
- `variant`：这一节值不值——结清 leanness 的 `proposed_smallest` 判决。
- `quality`：达得到 rubric 吗。
- `trigger`：描述在该触发的问句上真的触发吗。

**opt-in**：默认只提议、不代跑；用户点头才跑。

**降级（明示，不静默、不入队）**：`diy-eval-runner` 不在场 → 一行 warning + 跳过，不阻断交付；无头态下真实模型调用还受 `runner.py` 白名单约束（`claude` 不在 `DEFAULT_ALLOW` 内）→ 同样降级为 warning + 跳过该模式并说明，调用方需要额外命令族时经 `runner.py --allow` 传入——**本技能不替它扩名单**。

## 播报与下一步

给用户：三个 lint 门的结论（exit 码 + 有无 warning）、两版对比的裁决、eval 的结果或降级原因、memlog 的 `decision` 条目。然后读全并照做 `05-finish.md`。
