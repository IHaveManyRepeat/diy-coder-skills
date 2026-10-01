# Step — WDS 线（第 2–3 步换成本节，第 6 步证伪轮不适用；第 1 / 4 / 5 步纪律照旧，主线四层与判决规则一条不改）

**Read (input):** `{output_dir}/design.yaml`（`project.status: 已定稿`）；目标页的 `states[].signals` 与 `prototype` 结构稿；实现面。
**Write (output):** 审查报告与本轮会话（WDS 线无 YAML 载体）；失败时经 `transition` 走回修边——**不写 `design.yaml`**。

- **目标与零产出**：`pages[].status: 待验收` 的页（词表从 `diy-design` 接——5 值与 9 条合法边，**不另立词表**；`status` 键缺失即 `未开始`，旧稿兼容、不是待审页）；零页可审 → 一行说明后零产出停止——不写 `review` 块、不动状态、不报「通过」。
- **独立复验**：判据 = 该页 `states[].signals`（与浏览器强制门同源）＋ `prototype` 结构稿 ＋ 实现面；**不采信 `diy-dev` 的自述**——逐条自己跑，结论只引自己拿到的证据（分工同 L3：你不手动重验，你跑机械核对）；暴露真缺陷另经规则第 3 条入库。
- **判决与写权**：通过 → 页**保持 `待验收`**，出「可呈用户批准」结论（`待验收 → 已批准` 的触发是**用户批准**——本技能**绝不代用户批准**、不调这条边）；失败 → `python "{project-root}/.claude/skills/diy-design/scripts/design.py" transition --design "{output_dir}/design.yaml" --page <id> --to 结构稿中 --json`（回修边）。状态写入**一律经 `transition`**——不直改 YAML、**不新增 schema 键**；审查结论的落点主线 / WDS 不对称——主线落 `sprint.yaml` 任务条目的既有键（`review.findings[]`），WDS 线**只落审查报告与本轮会话**（无 YAML 载体），按规则第 4 条的 WDS 落点列路由。
