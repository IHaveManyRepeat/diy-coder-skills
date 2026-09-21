# adapter 缝与隔离契约

运行时相关的一切都在这一道缝后面：技能怎么被调起来、认证从哪来、transcript 长什么样。其余部分（脚本、case 形态、grader、四模式）都写在这道缝之上，保持运行时无关。**任何地方都不硬编码模型名**——模型只是运行时需要时由 adapter 转发的值，绝不是本技能维护的一份清单。

## adapter 配置

一个 adapter 是一份 JSON，键如下（全部可省略，省略即取括号里的默认）：

| 键 | 含义 |
|---|---|
| `invocation` | 一次非交互运行的 argv 模板。`{prompt}`（别名 `{query}`）换成合成后的输入，`{cwd}` 换成该 case 的清场目录。diy 侧由调用方经 `--invocation` 给（**没有默认串**——默认一个具体 CLI 正是被裁掉的东西）。 |
| `auth_env` | 运行时读取凭据的那一个环境变量名。**仅当宿主上非空才转发**——转发空串会覆盖运行时自己的凭据回落、反而弄坏认证。 |
| `transcript` | `{"format": "stdout-jsonl"}`（默认，stdout 即 JSONL transcript）或 `{"format": "file", "path": "transcript.jsonl"}`（运行时在 cwd 里写文件）。 |
| `skill_dir` | 清场目录下运行时发现技能的目录（默认 `.claude/skills`）。被测技能与 trigger 的合成技能都 stage 在这里。 |
| `load_signal` | trigger 专用：哪些工具调用算「技能被加载」。默认 `{"skill_tool": "Skill", "read_tool": "Read"}`。 |
| `env_passthrough` | 额外要转发进 run 的宿主环境变量名（默认空）。 |

**发现顺序**：`--adapter <F>` > 用例/问句文件旁的 `adapter.json`。都没有 → 逐键取默认；若连 `invocation` 也没有 → **只 stage、结果记 `skipped`**（不崩、不静默）。

## 调用与隔离

引擎把模板填上输入（`state_prefix` 已前置）与清场目录，从该目录运行命令、等它结束。调用前 stage 进该目录：被测技能落 `<cwd>/<skill_dir>/<技能名>/`，以及该 case 的夹具。

子进程环境**从零构建、绝不继承**，宿主 shell 配置、记忆与令牌都无法污染结果。它里面恰好只有：

- `PATH`；
- 一个全新的空 `HOME`，位于 `<case>/.home`；
- 指向该 HOME 内的 `CLAUDE_CONFIG_DIR`；
- `auth_env` 指名的那个变量——**仅当宿主上非空**；
- adapter 声明的 `env_passthrough` 键（宿主上存在的那些）。

没有容器、没有终端模拟、没有凭据文件暂存。baseline 用同一输入发同一命令两遍（一遍 stage 技能、一遍什么都不 stage），裸模型地板因此是在完全相同的条件下量出来的；variant 则一边 stage 全量、一边 stage `--variant-path`。

## transcript 形态

transcript 告诉引擎 token 用量在哪、告诉 grader 怎么读工具调用与最终消息。脚本按行读 JSON 事件：`assistant` 事件带 `message.content[]`（`tool_use` 项有 `name` 与 `input`；usage 块带 token 计数），`result` 事件的 usage 块是总量权威值。事件形状不同的运行时需要自己的记账分支——那个分支属于这道缝，不属于任何模式或 grader。

## 触发判定：「技能被加载了吗」

trigger 不量产物，只量描述有没有让技能起火。引擎给每条问句 stage 一个**唯一名**的合成技能（`<技能名>-trig-<uuid8>`，唯一后缀把它与同名真技能区分开），把问句经 adapter 发出去，再扫 transcript 找加载。**只有 `tool_use` 事件算加载**：

- 一次 `skill_tool` 调用，其输入点名了合成技能；或
- 一次 `read_tool` 调用，其 `file_path` 落在合成技能目录内（它的 SKILL.md）。

**整篇 transcript 子串匹配一律拒绝**：运行时的 init 事件会把每个被发现的技能名列出来，子串匹配的触发率永远是 100%，与描述写什么无关。`load_signal` 写成 `{"type": "string"}` 时引擎直接抛错拒跑。

## 降级路径（diy 侧现状）

- `invocation` 解析为空 → 只 stage：case 目录、prompt、夹具、清场 HOME 都在场，`timing.json` 记 `skipped`；人或有配置的运行时可以接着补完。回执带 `ADAPTER_MISSING` warning。
- invocation 命令不在 PATH —— 无头下即 `runner.py` 的默认命令白名单未覆盖该命令族（`claude` 不在默认白名单内）——→ 跳过该 mode 并明示（`MODE_SKIPPED` warning，`execution-summary.json` 记 `skipped_modes`）。**不入队**：确认是当场决策，队列语义是「用户稍后自行执行」。要真跑，让调用方经 `runner.py --allow` 传入该命令族，或换一个在白名单内的 invocation。

## 接一个新运行时

写一份声明上表的 adapter 文件即可；要用 trigger 模式就补 `skill_dir` 与 `load_signal`。**别在别处加模型清单或供应商分支**——超出这些键的值属于 adapter，不属于脚本或提示词。
