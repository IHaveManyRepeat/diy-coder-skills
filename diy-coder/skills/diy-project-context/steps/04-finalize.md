# Step 4 — 定稿（复核·终门·交付）

Progress: `Scan → Context → Rules → [Finalize]`

**Read (input):** 整份 `{output_dir}/project-context.yaml`——这是唯一通读它的步骤。
**Write (output):** 定稿的文件；渲染视图；收尾摘要。

## 复核

像它的消费者那样读这份文件——一个明天就要照着办事、却不记得这场对话的代理。

- **完整性。** `scan.parts` 里每个部件都有 `stack` 行与 `architecture` 条目；每条规则都有 `rule` / `why` / `where`；第 1 步人点名的每个部件都在场。该有却没有的节是此刻要补的缺口——源工作流那句 `_(To be generated)_` 标记在这里没有对应物：缺口是补掉，不是标出来。`[假设]` 值与用户落定后去掉前缀。
- **精简。** 砍转述、砍显然的忠告、砍重复的规则；共享见证的规则合并；命令与路径保持逐字，周围的叙述收紧。密度就是特性。
- **准确。** 每条断言都能追到一个文件、一条命令或用户自己的话。过时的规则（挪走的目录、变了的命令）是改掉，不是留着。

摆出复核结果与计数，还有待办就停在终门之前等用户。

## 重写比对（Rewrite check）

**重扫** / **深挖**——重写既有文件的这两种模式——且仅当第 1 步建过 `.prev` 副本时：

```
python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" check --previous {output_dir}/project-context.yaml.prev --json --project-root "{project-root}" --output-dir "{output_dir}"
```

exit 0 意味着没有丢任何 `PC-###` 规则。`ID_UNSTABLE` 逐条点名丢失的规则：要么恢复它，要么带一条说明删除理由的 `revisions` 条目重新加回——静默消失正是这道门要抓的。通过后才删 `.prev` 文件。

## 终门

跑，实参同激活：

```
python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" check --final --json --project-root "{project-root}" --output-dir "{output_dir}"
```

exit 0 是唯一放行——逐条修完上报的违规再重跑。回执的 `violations` / `warnings` / `counts` 即收口证据：不留 `[假设]`、规则非空且 `rule` / `why` / `where` 齐全、`stack` 非空、`scan.parts` 非空。只有在 exit 0 之后：渲染文件、结束本轮。

## 交付与路由

按 SKILL.md 工作流里的静默旁路命令渲染（resolved 实例时附 `--instance <name>`）——只写命令，不新增浏览器交互点、不等待路径。然后收尾一行摘要：路径、模式，以及 `check --final` 回执的 `counts`（`parts` / `rules` / `deep_dives`）；并一行点名路由（交付面与取值键如下）：

- 接下来做棕地功能或 PRD → **diy-prd**，它把本文件当棕地输入读——`{output_dir}/project-context.yaml` 的 `rules[]`（取值键 `rule` / `why` / `where`）、`stack[]`、`architecture[]`、`integration[]`（本文件就是旧文档集里叫 master index 的那个检索入口）；
- 改系统的形态 → **diy-architecture**，同样读这份文件的 `architecture[]` / `integration[]`；
- 还要穷尽记录另一个区域 → 回 `./05-deep-dive.md`。

## 退出

终门 exit 0 后本轮在此结束。再来一次深挖从 `./05-deep-dive.md` 重入；否则不再读任何 `steps/` 文件。

## 播报与下一步

本步是本轮最后一个步骤文件：交付后停止，不点名下一个步骤。**深挖** 续做时读全 `./05-deep-dive.md` 并照做。
