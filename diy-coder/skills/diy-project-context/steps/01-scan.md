# Step 1 — 扫描（模式与档位）

Progress: `[Scan] → Context → Rules → Finalize`（`深挖` 模式下 `Scan → Deep-Dive → Finalize`）

**Read (input):** `{output_dir}/project-context.yaml` 的 `scan` 块（存在时；只用于判模式）；引擎的扫描回执。
**Write (output):** `{output_dir}/project-context.yaml` 里的草稿记录（`project` + `scan`）。

## 定模式

目标文件说了算。`{output_dir}/project-context.yaml` 缺席时就没什么可续的——这是一次 **全量** 扫描。

在场时，只读它的 `scan` 块，先把记录下来的东西摆出来（mode / level / date / parts）——该块就是续跑状态；没有 `project-scan-report.json`，将来也不会有：

```
我发现 {scan.date} 的项目上下文——模式 {scan.mode}、档位 {scan.level}、{n} 个部件：{parts}。

1. **重扫** 整个项目 —— 以该日期为增量窗口起点，更新每个部件的变化
2. **深挖** 单个区域 —— 对单一区域逐文件穷尽记录
3. Cancel —— 文件原样保留
```

HALT——等选择。**Cancel** 以零写入结束本轮，收尾一行说明。**深挖** 置 `mode: 深挖`、`level: 穷尽`，然后跑下面的扫描并直接进 `./05-deep-dive.md`（不走第 2 步）——它编辑既有文件：`project` + `scan` 是它唯一写的两节，其余每节原样前滚。**重扫** 置 `mode: 重扫`。这两种模式都要重写既有文件，所以任一种在写之前先跑：

```
cp {output_dir}/project-context.yaml {output_dir}/project-context.yaml.prev
```

`.prev` 留到第 4 步的终门——它是「没有丢过 `PC-###`」的证据。

## 定扫描档位

只对 **全量** / **重扫** 用。给三档——它们改的是引擎读多少，不是记什么：

1. **快速**（缺省）——模式分析：清单、目录结构、配置文件。不读源文件。
2. **深入**——加每部件的源文件计数（读面 = 回执的 `critical_dirs`：该部件类型的关键目录里**实际存在**的那些）。
3. **穷尽**——再加代码行数；读源文件，受内置文件数与字节上限约束。

## 跑扫描

```
python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" scan --project-root "{project-root}" --output-dir "{output_dir}" --level {快速|深入|穷尽} --json
```

引擎是确定性的、只读的：什么都不写。一切取回执——`repository_type`、`parts`、`stack`、`docs_found`、`tree`、`critical_dirs`、`stats`、`warnings`、`counts`——绝不手工重推部件、类型或版本。非零退出即拒绝：转述它的一行理由，零写入停下。

`MANIFEST_UNPARSED` warning 不是失败——那是引擎拒绝猜测。逐条收齐：它们就是下面要问人的问题。

## 确认分类

摆出探测结果，请人裁定：

```
我这样分类了这个项目：

- 仓库类型：{repository_type}（单体 / 多部件 / 单仓多包）
- {part.name}（{part.path}）— {part.type}
  技术栈：{stack row} / 清单：{part.manifests}

这样对吗？[y/n/edit]
```

HALT——等回答。人修正时，部件的清单与类型逐字照收；清单未解析时，问语言与框架是什么并记人的原话。部件与类型绝不发明——没落定的那个保持 `未知`，直到人把它关掉。**人确认后的清单是权威**（SKILL.md 规则 2）：未被修正的值照抄回执，人修正过的 part 以人给的为准——`scan.parts` 与 `stack[].part`（以及 `architecture[].part` / `integration[].between`）逐一对齐该清单；回执里没有的行用人的原话补 `language` / `framework`、`version` 留空、`notes` 注明「人确认（引擎未解析）」。

## 既有文档与关注区域

转述 `docs_found`（各带 `kind`），并问：还有别的重要文档或要重点关注的区域吗？他们的回答不新增字段——第 2 步落成 `structure.key_dirs` 条目（path + purpose），是流程而非地点时第 3 步落成 `工作流` 类规则。

## 开草稿

写 `{output_dir}/project-context.yaml`（缺席时新建），机器锚点照抄回执——绝不重打：

```yaml
project: {name: <diy-coder.yaml project.name>, created: <today>, updated: <today>}
scan:
  mode: 全量|重扫|深挖
  level: 快速|深入|穷尽
  date: YYYY-MM-DD                     # 本次写 scan 块的日子：三种模式一律写今天（不是首扫日）
  parts: [{name, type, path}, ...]     # 人确认后的清单（stack / architecture / integration 的归属已对齐它）
stack: []          # 第 2 步填
structure: {}
architecture: []
rules: []
revisions: []
```

日期口径：格式一律 `YYYY-MM-DD`；`project.created` 建文件时设、此后不改写；`project.updated` 每次写回刷今天；`scan.date` 是**本次写 `scan` 块的日子**——全量 / 重扫 / 深挖一律写今天，不是首扫日（它同时就是下一次续跑播报的增量窗口起点）。`deep_dives[].date` 记那一次深潜的日子，与 `scan.date` 不必相同。定义源在 SKILL.md，本步只落笔。

**重扫** 或 **深挖** 时，既有各节先整块前滚、就地编辑——`revisions` 记录改了什么。上面的骨架是**新建文件**的形态：拿它覆盖既有文件会连同 `stack` / `structure` / `architecture` / `rules` 与全部人工确认的 `PC-###` 一起丢掉。

## 播报与下一步

读全 `./02-context.md` 并照做。**深挖** 模式改读 `./05-deep-dive.md`；它跑完回到定稿步。
