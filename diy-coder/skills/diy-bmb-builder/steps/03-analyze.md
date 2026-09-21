# Step 3 — 五透镜质量分析

Progress: `意图路由与开场 → 构建单循环 → [五透镜分析] → 门禁与评测 → 交付收尾`

**Read (input):** 被分析技能目录（`SKILL.md` + 步骤文件 + 脚本 + `scripts/`）；引擎 `prepass` / `scan` 回执。
**Write (output):** `<被分析技能>/.analysis/<YYYY-MM-DD-HHmm>/` 下十二件；`lens-<名>.json` ×5 与 `findings.json`；`mlog` 一条 event。

## 运行目录

每次分析独占 `<被分析技能>/.analysis/<YYYY-MM-DD-HHmm>/`——**落在被分析技能旁边**（报告跟着被分析对象走；只新建，不改该技能的任何既有文件）。先建目录，再跑预扫。

## 第一步：确定性预扫（先跑，别让透镜自己去数）

```
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" prepass --target "<技能目录>" --set metrics --out "<运行目录>/prepass-prompt-metrics.json" --project-root "{project-root}" --output-dir "{output_dir}" --json
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" prepass --target "<技能目录>" --set integrity --out "<运行目录>/prepass-workflow-integrity.json" --project-root "{project-root}" --output-dir "{output_dir}" --json
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" scan --target "<技能目录>" --check path-standards --out "<运行目录>/scan-path-standards.json" --project-root "{project-root}" --output-dir "{output_dir}" --json
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" scan --target "<技能目录>" --check scripts --out "<运行目录>/scan-scripts.json" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

四件 JSON 由引擎写落，**不要手工誊抄**。`prepass` / `scan` 的 exit 1 表示**它查出了结构问题**——那是本轮的输入事实，不是中止信号：把它们带进合成层（该修就修、该作为 finding 就作为 finding），分析照跑。

## 第二步：五透镜并行

每个透镜拿到预扫 JSON 与技能路径，**回传固定形状的 JSON**（不写文件、不各自出报告——合成归你）：

```json
{"lens": "<透镜名>", "verdict": "<一句话>",
 "findings": [{"id": "<透镜名>-<n>", "severity": "critical|high|medium|low",
               "title": "<短标题>", "location": "<file:区域>",
               "evidence": "<观察到什么>", "recommendation": "<怎么改>"}]}
```

`id` 在本透镜内顺序编号（合并不丢可追溯性）。**没发现就给空 `findings` + 一句"本透镜通过"**——为显得细致去凑条数，比不报更糟。

| 透镜 | 它判什么 |
| --- | --- |
| leanness 精简 | **每一行是否打得过"它不存在"的版本**。① 核心测：称职模型不被告知也会做 → 是摩擦；② 两版对比测：说不出这一段比"五行同义最小版"在哪个具体维度上更好 → 是仪式；③ 产出 vs 处方测：编号顺序若只是装饰，换成一句目标句（真顺序才留）。另外把 ALL-CAPS 的 ALWAYS/NEVER 与堆叠 MUST 记成黄旗——用"防的是哪种失败"重写它。 |
| architecture 架构 | 结构面：frontmatter 与命名；文件拓扑（薄主文件 + 厚子文件是否切得值、有没有跨目录套娃）；渐进披露（引用的文件都在、被切出的文件能独立站住）；模式声明是否真的各通一条路；**一致性**：前面段产出的东西后面段真的消费、概述里立的规矩执行指令真的在执行。 |
| determinism 确定性 | 智能放置边界，两侧都算漏。**智能泄漏**：脚本用正则/子串去判"内容是什么意思"（分界符可以切，含义不能猜）。**确定性泄漏**：提示词在做有唯一正确答案的事（计数、按 schema 校验、比对两份文件、查字段在不在、格式化）——这就是脚本机会，改法是把这段推进原生 Python，并上**预扫 JSON 模式**（脚本读原始文件、吐紧凑 JSON）。含义、语气、歧义判断留在提示词里，那不是漏。 |
| customization 配置面经济性 | 三件事：① 技能是否**私造了第二个配置机制**（`diy-coder.yaml` 是唯一配置源；自造 settings / 开关 / 私有配置段一律违规）；② 是否违反 `SKILL.md ≤90 行` 这一**固定阈值**；③ 是否把本该硬编码的固定值做成了可配置——默认要写成一条纪律，只有稀有分叉才值得开一个覆盖位。 |
| enhancement 增强 | 缺哪个**具名模式**、哪个模式被**过度套用**。走一遍不同的人：新手、知道自己要什么的专家、走错门的人、输入合法但意外的人、敌对环境里依赖挂掉的人、**无头调用者**（每个交互点问一句：一个参数能不能替掉这个提问？）。多轮的构建类技能**必须有工作态策略**（日志 / 结构化中间物 / 两者 / 都不要——四选一，不是默认都要）；反过来，一次性或纯对话技能上挂日志是过度套用，删它并说明丢了什么（多半什么也没丢）。 |

边界别串道：**结构**归 architecture、**逐行的值不值**归 leanness、**脚本身提示词身**归 determinism、**配置面**归 customization、**缺/多模式**归 enhancement。

## 第三步：父上下文内合成（不派子代理）

把五份返回合成**一个 findings 列表**（保留每条 `id`、`lens`、`severity`）。你是唯一持有全部 finding 的人，所以合成由你写，不外包。`leanness` 在"两版对比"类 finding 上另带 `proposed_smallest` 与 `predicted_delta`（其余透镜、其余 finding 不带这两个键）——那两条正是可以路由到 `diy-eval-runner` 的 variant 模式去取"砍掉还是留着"判决的。

写进 `findings.json`（**schema_version 2**，与既有 12 份实物同形）：

```json
{"schema_version": 2, "subject": "<技能目录>", "generated": "<YYYY-MM-DD>",
 "verdict": "<一句话总评>", "grade": "<excellent|good|fair|poor>",
 "summary": "<2–3 句：最强的强项 + 最值钱的改进机会>",
 "themes": [{"title": "<根因名>", "root_cause": "<发生了什么、为什么要紧>",
             "finding_ids": ["leanness-1"], "action": "<对这一簇的一条修法>"}],
 "strengths": ["<必须保住的强项>"],
 "recommendations": [{"rank": 1, "action": "<做什么>", "resolves": ["leanness-1"]}],
 "findings": ["<每条透镜 finding 原样保留>"]}
```

规则：`grade` 小写，`excellent` = 无 critical/high 且 medium 少、`good` = 有 high 或若干 medium、`fair` = 多条 high、`poor` = 有 critical；**severity 计数由脚本从 `findings` 派生**（不写 counts 字段）；`themes` 按**共同根因**聚 3–5 个（问一句"修好 X 能同时解掉几条"，不按文件聚），`action` 是对整簇的一条连贯修法；`recommendations` 按杠杆排序，rank 1 = 花最小力气解掉最多条。全过就是一份真报告：`findings` 空、grade 如实、verdict 说透镜全过。`evidence` 与 `recommendation` 各一句到两句——它们在报告里是折叠行，不是文档。

## 第四步：脚本渲染（禁手写 HTML）

```
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" render --dir "<运行目录>" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

产出 `skill-analysis-report.md` + `skill-analysis-report.html`（自包含、无外部资源）。脚本拒绝渲染时改 `findings.json` 重跑，**绝不手改 HTML**。渲染是静默旁路：只写调用命令，不打开浏览器、不报路径等待查看、不阻塞（md 是同一份数据的归档件）。

**落盘义务：十二件全落**——`findings.json` + `lens-<名>.json` ×5 + `prepass-prompt-metrics.json` + `prepass-workflow-integrity.json` + `scan-path-standards.json` + `scan-scripts.json` + `skill-analysis-report.md` + `skill-analysis-report.html`。少落一件就失去与既有 12 份报告的可比性。

## 记录与播报

```
python "{project-root}/.claude/skills/diy-bmb-builder/scripts/bmb_builder.py" mlog --dir "{output_dir}/build-logs" append --file <skill-name>.md --type event --text "analyze: grade <x>，critical <c>/high <h>/medium <m>/low <l>，报告落 .analysis/<时段>/" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

给用户：grade、一句话 verdict、severity 计数、最值钱的两三条主题要点。然后读全并照做 `05-finish.md`。
