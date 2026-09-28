# Step — 收尾与交棒（状态写回 + 渲染 + 路由）

Progress: `[1 状态写回] → [2 渲染（静默旁路）] → [3 交棒摘要] → 下一扇门`

**Read (input):** `{output_dir}/design.yaml` 该页 `status` 现值；本轮的浏览器门结论（会话内）；`--reason` 文案（仅 `→ 已移除` 时）；`{output_dir}/stories.yaml` 的 `AC[].design_ref`（悬空检查，只读）。
**Write (output):** `design.yaml` 的 `pages[].status`（**只经 `design.py transition`**，不手改）；渲染调用（静默旁路）；会话内的交棒摘要。**不写 `design.yaml` 的其他键。**

## 第 1 步 —— 状态写回（经引擎，不手改）

```bash
python "{project-root}/.claude/skills/diy-design/scripts/design.py" transition \
  --design "{output_dir}/design.yaml" --page <页 id> --to 待验收 --json
```

- **门不过不许写**：浏览器门未逐条过 → 不写 `待验收`（写了就是假事实）；回 `./wds-self-verify.md`。
- 回执读法（全家族统一形状，单行 JSON）：`ok` · `from` → `to` · `counts` · `next_hint`；`violations[].code` 里 **`GATE_FAILED`** = 页级门未满足（四态缺一 / 结构稿缺失，msg 点名缺什么）、**`ILLEGAL_TRANSITION`** = 边不合法（9 条合法边由引擎判，报错会教合法出口）、`UNKNOWN_ID` = 页 ID 不在 `pages[]`。`transition` 重写前落 `.prev` 快照，写回是原子替换。
- 用户确认废弃（**实现期**页级废弃；设计期砍页归 `diy-design`，同一条边两阶段显式分工——见主文件规则 7）→ `--to 已移除 --reason "<为什么>"`（**`--reason` 必填**，写进 `removed_reason`）；回执 `warnings[]` 给 `stories.yaml` 里 `AC[].design_ref == <页 id>` 的悬空 AC 清单 → 路由 `diy-epics-stories`（写权在它，本技能只读）。
- **`待验收 → 已批准` 不由本技能写**：那是用户批准（`diy-review` 出「可呈用户批准」结论，也不代批）。

## 第 2 步 —— 渲染（静默旁路）

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 第 3 步 —— 交棒摘要

呈三行（会话内，不落盘）：① 页 ID + 实现路径 + 新状态；② 门与 `audit` 的回执摘要（逐条 pass 数 / `one-off-*` 零）；③ 未决项（跳过的门 / 悬空 AC / 待用户裁的规格改动）。

→ 交 **`diy-review` 的 WDS 路径**（报路径；审查时点由用户定）：审查目标 = `pages[].status: 待验收` 的页，判据同本门、**独立复验不采信本技能自述**；失败走回修边（`待验收 → 结构稿中`）。

## 下一扇门

该场景全部页过审并获批后 → 读 `./wds-accept.md` 跑场景级全量验收。本文件到此结束，不再回头。
