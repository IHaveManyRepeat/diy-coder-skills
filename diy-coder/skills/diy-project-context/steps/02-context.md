# Step 2 — 语境（扫描事实落 YAML）

Progress: `Scan → [Context] → Rules → Finalize`

**Read (input):** 第 1 步的扫描回执；仅当下面某条条件扫描点明时才读某部件的源文件。
**Write (output):** `{output_dir}/project-context.yaml` 的 `stack` / `structure` / `architecture` / `integration`。

## 读回执，不重扫

本步要的机械事实都已算好：部件、类型、清单、技术栈行、文档、目录树、文件/行数计数。照抄回执。手工重跑扫描是禁止的——第二次推导就是第二个真相。

一次一条字段组，呈现完就走——组内不追问。

## stack

照抄回执的 `stack` 行，逐字：`{part, language, framework, version, notes}`。引擎留空的行（未解析的清单、未知语言）此刻与人一起关掉，用人的原话——空串只在人回答前留着。**人确认后的 part 清单是权威**（SKILL.md 规则 2）：人修正过的 part 以人给的为准，回执里没有的行用人的原话补 `language` / `framework`、`version` 留空、`notes` 注明「人确认（引擎未解析）」。

## structure

- `tree` —— 回执的 `tree` 字符串：标出每个部件的根、入口，以及部件之间的接口路径。标注过的摘录胜过整串：留读者导航需要的。
- `key_dirs` —— 关键目录一条一个：`{path, purpose}`。种自回执的 `tree` 与 `stats`，再补上第 1 步人点名的关注区域。purpose 用大白话，不是文件夹名的转述。

## architecture

每部件一条：`{part, summary, key_points}`。

- `summary` —— 这个部件是什么，一两句。
- `key_points` —— 实现者必须知道的：入口、分层、下面的条件扫描。

**条件扫描** 按部件的 `type` 决定（类型 → 扫描面的判定，折叠在此）：只跑适用的行，结论以要点形式落 `key_points`。

| 部件类型 | 扫描 | 结论落哪 |
| --- | --- | --- |
| 网页, 扩展, 桌面端, 移动端 | API 契约 · 数据模型 · 状态管理 · UI 组件 | `key_points`（端点 / 表 / store / 组件族） |
| 后端, 数据 | API 契约 · 数据模型 | `key_points` |
| 命令行, 库, 基础设施 | 入口 · 公开面 | `key_points` |
| 嵌入式 | 找得到的硬件/引脚接口 | `key_points` |
| 游戏, 桌面端, 移动端, 网页, 扩展 | 资产（格式、大小、在哪） | `key_points` |

档位纪律（第 1 步所选）：**快速** 不读源文件——只列目录与模式并说明这一点；**深入** 读回执 `critical_dirs` 里的目录（该部件类型的关键目录里实际存在的那些；列表为空 → 按目录结构判断并说明），不读别的；**穷尽** 读全部源文件，排除 `.git`、`node_modules`、`dist`、`build`、`coverage`——一次一个子目录，每个结论写完再开下一个，绝不让阅读清单在上下文里堆积。

## integration

只多部件项目才有——单块项目省略该键（引擎接受缺席）。一对耦合一条：`{between: [<partA>, <partB>], contract, notes}`。`contract` 点名机制与形态（REST `/api/v1`、gRPC 服务、队列 topic、共享数据库）。`notes` 一行装数据流与认证路径。绝不为了填满该节发明耦合：不说话的部件对就是没有条目。

## 本步不写什么

开发与运维事实——前置条件、安装/构建/运行/测试命令、环境搭建、部署与 CI、贡献规则——是实现规则，不是扫描事实。它们在第 3 步落成 `工作流` 与 `质量` 类规则，命令与路径逐字保留。

## 播报与下一步

读全 `./03-rules.md` 并照做。
