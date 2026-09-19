---
name: diy-research
description: 'Conduct market, technical, and domain research with current web data and verified sources into one research.yaml. Use when the user says they need market research. Use when the user says they would like to do or produce a technical research report. Use when the user says wants to do domain research for a topic or industry.'
# ↑ 中文：做市场 / 技术 / 领域三维度联网调研——检索现势数据、每条断言带已核来源，收进单一源 research.yaml。用户说要做市场调研、要出一份技术调研报告，或要对某主题/行业做领域研究时触发。
phase: 1-analysis
precededBy: []
followedBy: []
required: false
line: mainline
outputs: research.yaml
---

# diy-research — 联网调研三维度（市场 / 技术 / 领域，YAML 单一源）

你是调研引导者，配一位专家搭档：你出研究方法与联网检索能力，用户出领域知识与研究方向。一条研究记录 = 一个主题的一个维度；同一份文件里可以有多条记录。产物是**一个 YAML 文件**——绝不产 markdown 副本、绝不另写一份文档。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（topic、scope、claim、synthesis）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 目标文件：`{output_dir}/research.yaml`。在场 → **Update**，缺席 → **Create**。记录 ID 铸为既有最大 `RS-###` + 1、三位零填充；永不重编号、永不复用。追加新记录 = 文件追加（不触发 `.prev`）；改写既有记录的字段 = 记录级重写（规则 5 的触发条件）。
3. 改写既有记录前，先把该记录 `status` 回退 `草稿`；改完按规则 6 重新置 `已定稿` 并重跑终门（`check --final --id RS-xxx`）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。`{output_dir}/research.yaml` 只在铸下一个 `RS-###`、按 `id:` 行改一条记录、或判 Create/Update 时才打开；校验判词取引擎的 JSON 回执，绝不重读规则。本 schema 不定义 `detail` 字段——没有可跳过的内容。
5. 读 `steps/01-scope.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只载一个 `steps/` 文件——绝不预载某维度的四个分析步；前置给全（front-load）——一步的输出整块给出，不挤牙膏、不在步中追问；每条 finding 在对应检索一落地时就写进 YAML，绝不攒到末尾批量写；`[C]` 门禁处停下等用户答复，非 `C` 答复按 `steps/01-scope.md` 的 `[Modify]` 惯例处理——收齐意见、更新记录与相关 finding、重新展示**同一门禁**（不当作继续、也不卡死）；产物叙述用 `document_output_language` 写、对话讲 `communication_language`。

1. `steps/01-scope.md` — 主题、目标、范围、维度确认；此步不做任何检索；建草稿记录。
2. 按记录的 `dimension` 路由，依次读该维度的四个分析步：
   - 市场 → `steps/market/02-customer-behavior.md` → `03-pain-points.md` → `04-decisions.md` → `05-competitive.md`
   - 技术 → `steps/technical/02-stack.md` → `03-integration.md` → `04-architecture.md` → `05-implementation.md`
   - 领域 → `steps/domain/02-industry.md` → `03-competitive-landscape.md` → `04-regulatory.md` → `05-trends.md`
3. `steps/06-synthesis.md` — 综合成文、终门、渲染、收尾。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/research.yaml` —— 唯一源头，集合形态（顶层形状对齐 `bug-log.yaml`）：

```yaml
project: {name, created, updated}   # 日期口径：格式 YYYY-MM-DD；created 建文件时设、此后不改；updated 每次写回刷今天
researches:
  - id: RS-001                  # RS-###：顺序递增、稳定，永不重编号、永不复用
    dimension: 市场|技术|领域
    topic: <string>             # 用户自己的原话
    goals: [<string>]           # 研究目标，第 1 步记下
    scope: <string>             # 范围与方法学
    date: YYYY-MM-DD            # 本条动作的日子（建这条记录那天），不随 updated 变
    status: 草稿|已定稿          # 只有本记录过了终门才写已定稿
    findings:                   # 平铺列表；每条断言都带来源
      - {area: <本维度分析步句柄表里取，如 customer-behavior / regulatory>, claim, sources: [{title, url, accessed}], confidence: 高|中|低}
    synthesis: {executive_summary, key_points: [<string>], open_questions: [<string>]}
distillate: {problem, target_users, value_props: [<string>], constraints: [<string>], open_questions: [<string>]}
                                # 交出面（B1）：跨全部 researches[] 记录的汇总裁面——本技能只声明交这五个字段，
                                # 不重定义摄取规则；字段级映射的唯一出处 = diy-prd 的输入清单
                                # problem = 研究问题；value_props = 已验证的机会点；constraints = 证据支持的边界与限制
revisions: []                   # {date, change, reason} —— 改既有记录时追加
```

## 规则

1. **硬前提。** 必须能联网检索——不可用即中止并告知用户：不研究、不写、不建记录。单条查询零结果 → 换检索词重试一次；该 `area` 仍空则**不写条目**（不得拿弱证据凑数，见规则 3），缺口留到第 6 步落 `synthesis.open_questions`。`Searches` 段落是最小集：每个 `area` 至少一条查询；某 `area` 无对应查询时，为该 `area` 追加一条锚定查询（`"{topic} <area>"`）后照常检索，不得拿别的 `area` 的证据顶替。
2. 写范围：只写 `{output_dir}/research.yaml`——记录与其 `revisions`。绝不碰上游产物（`prd.yaml`、`sprint.yaml`、`stories.yaml`）或源码：调研只供它们参考，绝不编辑它们。
3. 引用纪律：每条断言至少一个来源（`title` + http(s) `url` + `accessed` 日期）加一个 `confidence` 档位。冲突的来源要摆出来，不许平均掉；无出处的说法不进 `findings[]`——若它影响结论，收尾时作为缺口落 `synthesis.open_questions`，不静默丢弃。研究缺口与局限一律记 `open_questions`，绝不抹平。
   `critical claim` ＝ 若为假就要改方向或改设计的 claim，点名五类：市场规模/增速、监管与合规义务、竞争格局与份额、协议/标准与版本事实、成本与定价；其余 claim 单源 + `confidence` 标注即可。
4. ID 纪律：`RS-###` 一经铸定，稳定、永不重用。新主题或新维度 = 追加新记录（文件追加）；改写既有记录 = 改字段并向 `revisions` 追加 `{date, change, reason}`——先按激活第 3 步把该记录 `status` 回退 `草稿`，改完重新定稿并重跑终门（ID 不动、记录不搬）。
5. 重写安全：触发条件 = **既有 `RS-###` 记录的字段被改写**（含随之追加 `revisions` 条目）；**新增记录不触发** `.prev` / `check --previous`。改写前 `cp {output_dir}/research.yaml {output_dir}/research.yaml.prev`；写完跑 `python "{project-root}/.claude/skills/diy-research/scripts/research.py" check --previous {output_dir}/research.yaml.prev --json`（exit 0 = 无记录丢失）。**非 0 一律不删 `.prev`**：`ID_UNSTABLE` → 从快照找回被丢记录、补进新稿、重跑到 exit 0 再删；`MISSING_FILE` / `UNPARSABLE_YAML` → 快照不可用、安全网失效，停手告知用户，确认前不得再写。
6. 终门（机械）：先写记录级 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-research/scripts/research.py" check --final --json`，`--project-root "{project-root}"` 与 `--output-dir "{output_dir}"` 两个实参同激活（`--output-dir` 必填、绝不缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾都等 exit 0。
7. 假设标记（C7 三条约定）：`[假设]` 前缀只写在**值**上，不新增独立键。`--final` 前必须清零——交互态经用户确认后删前缀；**headless 态一律转成 `synthesis.open_questions` 里的一条，不删不猜**。终门扫的字段集 = 记录的全部字符串（引擎递归全扫，键与值都算；一处命中即 `ASSUMPTION_PRESENT`）。
8. 渲染按工作流里的静默旁路句执行——只写命令；不新增浏览器交互点、不报阻塞路径、不等待。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
