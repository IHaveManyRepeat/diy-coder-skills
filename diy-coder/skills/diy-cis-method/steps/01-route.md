# Step 1 — 路由与续接（Route）

Progress: `[路由与续接] → 创新策略 / 问题求解 / 设计思维 / 叙事（进入对应分支文件）`

**Read (input):** 激活段 `list` 回执（会话清单，只含六字段）；用户对分支选择、续接菜单、议题询问的回答。
**Write (output):** `{output_dir}/cis-method.yaml` 的新记录骨架（经 `init` 铸造）或既有记录的状态推进；给用户的播报。

六拍：分支选择 → 续接检测 → 门禁 → 铸号 → 载库 → 进入分支。**每一拍的输出都是下一拍的输入**，不得跳拍。

## 一、分支选择（四选一）

问用户要走哪条方法流，**给推荐**（推荐依据 = 用户说的目标 + 手里已有的素材；拿不准就按四个触发语对号）：

```
[1] 创新策略 —— 找颠覆机会、定战略方向、出执行路线图（"lets create an innovation strategy"）
[2] 问题求解 —— 把复杂难题拆到根因、选出方案、规划落地（"guide me through structured problem solving"）
[3] 设计思维 —— 以用户为中心走共情 → 定义 → 构思 → 原型 → 验证（"lets run design thinking"）
[4] 叙事 —— 用故事框架把想法讲成叙事成品（"help me with storytelling"）
```

用户说不清 → **用一句话问清**：「要战略方向 / 要解难题 / 要做人本设计 / 要讲故事？」——回答即映射到上表之一；仍不明确 → 不代选，进「三、门禁」按拒答处置。

选定后 `method` 逐字取 `创新策略` / `问题求解` / `设计思维` / `叙事`（**四处同词**：库判别列 / 产物 `method` 值 / `--method` 取值 / 分支文件名后缀——本步与后续所有命令一律用同一套词）。

| 选定 | 分支文件 | 步数 | 能量检查点 |
| --- | --- | ---: | --- |
| 创新策略 | `./02-innovation.md` | 9 | 第 3 / 5 / 8 步 |
| 问题求解 | `./03-problem.md` | 9 | 第 5 / 8 步 |
| 设计思维 | `./04-design.md` | 7 | 第 3 / 5 / 7 步 |
| 叙事 | `./05-story.md` | 10 | 无（源侧为零） |

## 二、续接检测

激活段已跑 `list`——回执只给 `id` / `method` / `topic` / `date` / `status` / `current_step` 六字段，**到此为止，不许读正文**（列出名不读内容，选中目标才加载）。

- 回执 `sessions` 为空 → 直接进「三、门禁」。
- 有记录 → 播报最近一条（`id` / `topic` / `date` / `status` / `current_step`，`method` 一并说清），给菜单 **[1] 继续 / [2] 新建 / [3] 看全部**，**HALT 等选择**。
  - `[3] 看全部` → 列全部记录（仍只六字段）→ 问「继续哪一条（给 `id`）还是新建」。
  - `[2] 新建` → 进「三、门禁」。
  - `[1] 继续` → 按 `id` 加载那一条（此时才读内容），**分支由该记录的 `method` 决定**（不再问「一、分支选择」），读对应分支文件、按 `current_step` 复位到该步。

续接的复位表（`current_step` 是唯一续接锚点）：

| 该记录的 `method` | `current_step` 域 | 去向 |
| --- | --- | --- |
| 创新策略 | 1-9 | `./02-innovation.md` 的第 `current_step` 步 |
| 问题求解 | 1-9 | `./03-problem.md` 的第 `current_step` 步（第 9 步可选） |
| 设计思维 | 1-7 | `./04-design.md` 的第 `current_step` 步 |
| 叙事 | 1-10 | `./05-story.md` 的第 `current_step` 步 |

`status: 已完成` 的记录 → **只读回看**：呈出 `deliverable` / `open_questions` 摘要即结束，**不再写入**；还想再走一遍 → 走「新建」铸下一条 `CM-###`。续接时不重铸 `id`、不动 `date`。

## 三、门禁（零产出退出）

新会话必须先有议题：**① 走哪条分支（「一」已选）？② 这次要解决什么议题？**

- 议题缺席 → 由会话询问收集（一次问清：议题是什么、想要什么产出）；拒答 → 一行说明并停止，**不写任何文件**。
- 「无议题也无素材」→ 同样拒绝，建议先想清楚要解决什么（**不代拟议题**，可路由 `diy-prfaq` 点火）。
- 议题为空串 → 不调 `init`（引擎会判 `EMPTY_FIELD`）；先补齐再铸号。
- 可选素材：`project-context.yaml` 等既有产物在场时**只读**取相关段，以引用式提及（`path:<relative>`），禁复制内容。
- 指向既有 `CM-###` → 回「二、续接检测」按 `status` 路由。

## 四、铸号（init）

复述确认（分支 + 议题各一句）→ 用户点头后调引擎铸骨架：

```
python "{project-root}/.claude/skills/diy-cis-method/scripts/cis_method.py" init --method "创新策略" --topic "<议题>" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`--method` 的值换成用户选定的那一个（逐字取 `创新策略` / `问题求解` / `设计思维` / `叙事`；非法值引擎判 `ENUM_INVALID`）。**路径旗标不得省**——`--project-root` 与 `--output-dir` 都要给（引擎不自解析实例、不私读 `diy-coder.yaml`）。

回执的 `id` 就是本条会话的 `CM-###`（此后一切写入都用它定位，永不重编号）；骨架落 `status: 草稿` / `current_step: 1`。

## 五、载库（不凭记忆列方法）

```
python "{project-root}/.claude/skills/diy-cis-method/scripts/cis_method.py" methods --method "<M>" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- 默认只回**该分支工作流实际引用的类**（创新策略 25 / 问题求解 30 / 设计思维 15 / 叙事 25——叙事分支按类呈现全部 25 条）。
- `--all` 列该 `method` 的全部条目（**不跨分支**）——库含源侧未接入工作流的条目；`--category "<中文类名>"` 在结果集上按类过滤（类名须是该分支的合法类，否则 `ENUM_INVALID`）；`--random N` 从默认结果集抽 N 条（`N` 超出 → 全给 + warning）。
- 分支文件里点名的方法一律**逐字用库里的 `name` / `category`**；凭记忆列方法会被终门判 `ENUM_INVALID`。

## 六、进入分支

一句话播报（新建：`CM-###` 已铸 + 分支 + 议题；续接：回到哪一步 + 既有进度），然后读全并照做对应分支文件：

- 创新策略 → `./02-innovation.md`
- 问题求解 → `./03-problem.md`
- 设计思维 → `./04-design.md`
- 叙事 → `./05-story.md`
