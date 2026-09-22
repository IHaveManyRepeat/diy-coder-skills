# Step 6 — 交付摘要、下轮计划与收尾（Deploy & Close）

Progress: `[1 预交付清单与交付摘要 → 2 可选 PR 与下轮计划 → 3 质检、定稿与收尾]`

**Read (input):** 本产物 `rounds[EV-<nn>]` 的六相段（`analysis` / `scope` / `design` / `implement` / `test`）；`data/kaizen-principles.md` 的「何时暂停」；用户对「要不要开 PR」的回答。
**Write (output):** `rounds[EV-<nn>].delivery`（交付摘要 + 监控指引）+ `rounds[EV-<nn>].status: 已交付` + `project.status: 已定稿` + `revisions` 的收尾条目。

你是**收尾与交付的主持人**。源侧这一步叫 Deploy（[P]，5 步），diy 侧**只迁它的增量纪律内核**——理由与改法见第 1 步抬头。

## 第 1 步 —— 预交付清单与交付摘要（源 P1 + P3 + P4 的增量纪律内核）

**先说清为什么**：为什么交付物是一份**摘要**而不是一堆链接——下一轮分析要读的是「上一轮改了什么、预期什么、现在该盯什么」，这三件事必须在同一处能被一次读全。用你自己的话讲。

〔**源侧处置（[P] 的改迁落点，任务书 W3 卡 p1）**〕源 [P] 的 5 步里，**第 4 步「Notify Team」整段是「WDS Designer → BMad Developer」的人工通告信**（`steps-p/step-02-hand-off.md:75–126` 是一份完整的邮件模板：收件人称谓、目标、当前问题、预期影响、工件清单、验收判据、时间表、署名）。**diy 侧无 BMad 开发这一角色**，整段机迁即产生一封没有收件人的信。**diy 处置 = 只迁它的「增量纪律内核」**：通告信里真正承重的是 ① **工件链必须逐环引用**（analysis → scenario → spec → test → PR 一环不少）与 ② **监控指引**（上线后盯什么、盯多久）——这两条落进本步的交付摘要 `artifacts` 与 `monitoring` 两键；**信件的形态（称呼 / 署名 / 双向往来）整块裁**，登记为「形态裁撤、纪律保留」。

**预交付清单（源 [P] step-01 的五项勾选，逐条核）**：

- [ ] 全部 `acceptance_criteria[]` 通过（溯 `test.criteria[].verdict`）
- [ ] 分支干净：无未提交改动（非 git 项目 → 记 `none` 并说明）
- [ ] 提交信息成条理且写清对应哪条判据
- [ ] 没有夹带无关改动（对照 `scope.pages_affected[]`）
- [ ] 文档已更新（若适用）

**交付摘要（源 [P] step-03 的 7 段 + DD 骨架的承重键，落 `delivery`）**：

```yaml
delivery:
  summary: <这次改了什么、为什么——一段话>
  artifacts:                                  # 工件链逐环引用（源 P4 的增量纪律内核）
    analysis: rounds[EV-<nn>].analysis
    scope: rounds[EV-<nn>].scope
    design: rounds[EV-<nn>].design
    implement: rounds[EV-<nn>].implement
    test: rounds[EV-<nn>].test
    pr: <PR 链接 | none>
  impact: <按成功判据预期的改善>
  monitoring:                                 # 源 P4 的监控指引 + `monitoring-guide.md` 的内核
    metrics: [<盯哪几个数字>]
    period: <盯多久>
    watch_for: [<什么现象算没成——源 Failure Modes 的收口>]
  effort: <实际花了多久 / 相对估时的偏差>
  notes: <给下一轮的一句话>
```

**引用不复述**：`artifacts` 只写 `rounds[EV-<nn>].<相>` 的**指针**，不复制内容（源 DD 骨架把 14 段抄了三遍，是它的冗余源）。

〔**源侧处置（孤岛 data 的落点）**〕源 `data/monitoring-guide.md`（156 行，**零入边**）与 `data/kaizen-iteration-guide.md`（167 行，**仅被前者引用**）是一对**孤立件**——它们自称 `# Step 07: Monitor Impact` 与 `# Step 08: Iterate`，是菜单化改版后遗留的全局 8 步流程尾段（`workflow.md:75–83` 的 REFERENCE 表**没列**它们）。**diy 处置 = 内核收编、文件裁**：测量周期 / 指标 / 定性反馈 / 影响报告四件 → `monitoring` 四键（本步）；「Kaizen 永不停」与「何时暂停」→ `data/kaizen-principles.md` 的收尾两节；`data/monitoring-templates.md`（388 行，3 模板）同因**裁**（模板形态改由 YAML 键承载）。

**产出键**：`rounds[EV-<nn>].delivery` 的 `summary` / `artifacts` / `impact` / `monitoring` / `effort`。

**落盘**：`rounds[EV-<nn>].delivery` 整段 + `rounds[EV-<nn>].status: 已交付` + `project.updated`。

**检查点（六拍）**：① 生成 → ② 落盘（`delivery` 段 + 状态推进）→ ③ 分隔 → ④ 呈出预交付清单与交付摘要 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 可选 PR 与下轮计划`。

## 第 2 步 —— 可选 PR 与下轮计划（源 P2 + P5）

**先说清为什么**：为什么 PR 在这一步是「可选」——单人项目里 `gh pr create` 是一封发给自己、没人合并的信；它只有在**真有人接**的时候才有价值。用你自己的话讲。

**PR 是选项，不是步骤**（源 [P] step-02 的命令保留、触发条件改由用户定）：

- **问一句**：「这轮改动要开 PR 吗？（有人接这个仓库 / 想留一段可评审的记录 → 开；自己一个人的项目 → 跳过）」
- **要开**：`gh pr create --title "[改进]: <一句话>" --body "<按交付摘要的七键展开>"`——PR 体**引用**摘要键，不另写一份。
- **不开**：`delivery.pr: none`，在会话里一行说明「本轮无 PR」，**不再追问**。
- **本项目不是 git 仓库** → 本步整段跳过。

〔**源侧处置**〕源 [P] step-02 的 PR 是**必做步**，且假定有 `gh` 与远端。diy 侧改**可选**（裁定 6 的「零外部服务」射程：`gh` 是对外服务调用，须由用户显式点头），并把 PR 体从「5 段重写」改为「引用交付摘要」。

**下轮计划（源 [P] step-05 的三件）**：

1. **归档本轮**——一句「EV-<nn> 已交付」进 `delivery.summary` 落定（不另建归档目录）
2. **回看剩余目标**——读 `rounds[EV-<nn>].analysis.targets_considered[]` 与 `kaizen_priority.candidates[]`（本轮测试期新记的也在此），**逐条念 score**
3. **建议下一目标或新一轮分析**——二选一，由用户点头（**不代选**）

**Kaizen 不停**（源 `data/kaizen-iteration-guide.md` 的内核 + `kaizen-principles.md` 的「何时暂停」三问）：下轮照常；**暂停的三种情形**从 `data/kaizen-principles.md` 取照（重大战略转向 / 团队容量 / 测量期）——**但暂停不是结束，是等一个数**。

**产出键**：`delivery.pr` / `delivery.notes` / `delivery.next`（下一目标或「待新一轮分析」）。

**落盘**：`delivery.pr` / `delivery.notes` / `delivery.next`（下一目标或「待新一轮分析」）+ `project.updated`。

**检查点（六拍）**：① 生成 → ② 落盘（`delivery.pr` / `.next`）→ ③ 分隔 → ④ 呈出下轮建议（含剩余目标的 score）→ ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 质检、定稿与收尾`。

## 第 3 步 —— 质检、定稿与收尾

**先说清为什么**：为什么定稿前还要过一遍表——本产物是**多轮累积**的，前几轮的键会被这一轮的手改顺带碰坏；一次机械全扫比来回人眼找便宜得多。用你自己的话讲。

**收尾五拍**：

1. **完整性闸**：逐轮数一遍六相段非空（缺的当场回补，**不跳过**）；`kaizen_priority` 的候选 score 与三因子重算一致。
2. **定稿落盘 + 终门（机械，`exit 0` 是唯一放行）**：先落 `project.status: 已定稿` + 本轮 `status: 已交付` + `project.updated` 刷今天，再跑：
   ```
   python "{project-root}/.claude/skills/diy-wds-evolution/scripts/wds_evolution.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
   ```
   违规按回执 `where` 就地修、重跑，**不得跳过**。终门机械核对的关键几项：`project.status: 已定稿` · 每轮 `status: 已交付` · 六相段齐备 · `test.scope: 本轮增量`（裁定 10）· 判据全部 `通过` · `score` 重算一致 · `EV-<nn>` 序号连续 · 零 `[假设]`。
3. **渲染（静默旁路）**：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。**不新开交互点、不等查看**。
4. **交接摘要（会话内呈出、不落盘）**：① 本轮目标与根因各一句；② 改动清单（文件数 + 分支）；③ 判据 X/Y 通过；④ 交付摘要的 `monitoring` 三键（盯什么、盯多久、什么算没成）；⑤ 下一目标与它的 score。
5. **路由与收尾**：一句话给下轮入口——「下一轮从 `steps/01-analyze.md` 起（本产物已在，续接检测会认出 `EV-<nn>`）」；未决项写进 `revisions`（`change` 点名键名、`reason` 写为什么还没定），**不用 `[假设]` 标记**。

**产出键**：`project.status: 已定稿` + 本轮 `status: 已交付` + `revisions` 收尾条目（终门 exit 0 是放行凭据）。

**落盘**：`project.status: 已定稿` / 本轮 `status: 已交付` / `project.updated` / `revisions` 收尾条目。

**检查点（六拍）**：① 生成 → ② 落盘（定稿 + 终门 exit 0）→ ③ 分隔 → ④ 呈出交接摘要 → ⑤ 出四选项 → ⑥ 等响应。

本文件到此结束——终门 exit 0 后本轮收尾，**不再读任何 `steps/` 文件**。下一轮从 `01-analyze.md` 重新开始。
