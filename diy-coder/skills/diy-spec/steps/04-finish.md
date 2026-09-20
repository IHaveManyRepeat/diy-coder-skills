# Step 4 — 终门与交付（Finish）

Progress: `输入与定位 → 蒸馏 → 两遍自校验 → [终门与交付]`

**Read (input):** 定稿的记录（含 `verdict`）；引擎 `check` 回执。
**Write (output):** `{output_dir}/spec-kernel.yaml` 定稿（记录 `status: 已定稿`）；渲染；交付摘要；`revisions`（仅改动既有记录时）。

## 定稿

1. 记录 `status` 改 `已定稿`，`project.updated` 刷今天（记录级 `date` 不动——它记的是本条动作的日子）。
2. 清 `[假设]` 标记：未决的推断落 `assumptions[]` 或 `open_questions[]`，不留正文（`--final` 扫全记录）。
3. 本次若改动了既有记录 → 追加一条 `revisions`（`{date, change, reason}`）；同时把**该记录的 CAP 处置**核一遍：退役的留条目标 `retired: true`，绝不删条目。

## 终门

```
python "{project-root}/.claude/skills/diy-spec/scripts/spec_kernel.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

更新既有记录时**必须**附 `--previous "{output_dir}/spec-kernel.yaml.prev"`（step 1 留的旧稿副本）：它比对旧稿 CAP 集合，旧有新无且未标 `retired` → `ID_UNSTABLE`。

`exit 0` 是唯一放行。违规 → 按回执的 `where` 就地修，重跑，直到 exit 0；`ID_UNSTABLE` 说明 CAP 丢了——找回它的条目或明确标 `retired: true`，**绝不重编号**。过了终门再删 `.prev` 副本（未过不得删，它是找回 CAP 的依据）。

## 渲染

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

静默执行，不进浏览器、不等路径、不阻塞。

## 交付摘要

一句话交代能直接决策的信息，不倒 JSON、不堆版面：

- 记录 `SK-###`（slug、新建还是更新）
- 能力几个（其中退役几个）、adopted companions 几个、artifacts 几条
- `verdict` 一句（两遍判决的结果）
- `assumptions[]` / `open_questions[]` 非空则**逐条一行**列出，并邀请用户逐条过——回应它们可以更新源文档（若源是文件）、更新本记录，或两边都更新，由用户选。

## 路由

- 假设 / 未决项被回应 → 更新本记录（`revisions` 追加一条）；源文档的改动归**用户或该文档的持有者**，本技能不改源。
- 同 slug 再次被指向 → 回到 step 1 走更新路径（`cp` 留旧稿 → 就地改 → `check --final --previous`）。
- 契约要被执行 → 交给实现通道（如 `diy-quick-dev` 的小变更通道，或主线故事环）；本技能只出契约，不落实现。

## 播报与下一步

这是最后一个步骤文件——终门 exit 0 后本轮到此结束。结果由 `specs[]` 记录与 `verdict` 承载；不再读任何 `steps/` 文件。
