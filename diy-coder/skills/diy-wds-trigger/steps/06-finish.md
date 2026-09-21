# Step 6 — 质检、定稿与交接（Quality Gate & Handover）

Progress: `[1 质检（13 维去重后 + 源 steps-v 五维）] → 2 定稿、交接与收尾`

**Read (input):** `./05-documents.md` 的放行（`effect_map` 全段齐、`stage: 成品`）；本产物的全部段；`wds-brief.yaml`（复验上游门禁）。
**Write (output):** `project.status: 已定稿` + `stage: 收尾`；`revisions` 的收尾条目；给用户的交接摘要与路由。

你是**收尾与质检的主持人**（源 Saga 线的收尾段）。**第 1 步是本技能的终门前置**——质检查表过完才准定稿。

## 第 1 步 —— 质检（源 07g 的 13 维去重后 + 源 steps-v 五维）

**源侧处置先读（两处，均为裁定 15 的落地）**：

① 源侧另有一条**独立的 validate 子流程**（`workflow-validate.md` + `steps-v/` 五步，668 行），产出 `validation-report.md`。**diy 侧裁独立子流程与报告产物**——终门 = `check --final`，复检 = 重跑 `check`；**另立 md 报告 = 双实现**。五维校验的内容**全部保留在下面的「五、链式校验」组**。

② 源侧 13 维质检**双写**（`step-07g` 的 13 维与 `data/quality-checklist.md` 的 13 维）且已出现项名与阈值漂移，还有若干不可机械判定的项（「Markdown 渲染正确」等）。**diy 去重口径**：`13 维 → 五组`（文件结构 / Markdown 格式 / 交叉链接三面在单 YAML 产物上不存在，并入或被取代；Key Insights 一节并入业务目标与特征影响组；其余按主题并组），**逐项可核对**——能落到键上的写键名，源侧的空话项一律不保留。

**逐项核对（48 项，机械过一遍；不合格的回对应步骤文件修，修完重跑本组）**：

**一、成品与图（源 07g 维 1 / 2 / 7 / 13 去重）**
- [ ] `{output_dir}/wds-trigger.yaml` 在场且可解析
- [ ] `project` 四键齐备（name / created / updated / status）
- [ ] `project.status: 已定稿` 与 `stage: 收尾` 同档
- [ ] 六个主体段全在场（business_goals / personas / driver_patterns / priority / feature_impact / effect_map）
- [ ] `revisions` 是在场列表
- [ ] `effect_map.diagram` 非空且含 `flowchart LR`
- [ ] 图内全部节点以 `<br/>` 起、以 `<br/><br/>` 收
- [ ] 图内无 HTML 标签（粗体 / 斜体）
- [ ] 图内节点 ID 形态正确（`BG<i>` / `TG<i>` / `DF<i>` / `PLATFORM`）
- [ ] 平台节点恰一个
- [ ] `class_defs` 四条逐字齐（源 08g）
- [ ] `diagram` 与 `nodes` / `connections` 一致（改结构先改键、再重生成图）

**二、跨段一致与语言（源 07g 维 3 / 4 / 5 / 11 去重）**
- [ ] 愿景在 `business_goals[0].statement` 与 `wds-brief.yaml` 的 `brief.core.vision` 逐字符相同
- [ ] 人物名在 `personas[]` / `priority` / `driver_patterns` 三处拼写一致
- [ ] 数字（人物数 / 目标数 / 分数）跨段一致
- [ ] 优先级顺序在 `business_goals[]` / `personas[]` / `priority` 三处不矛盾
- [ ] 驱动因素 ID 引用全部可解析（无悬空 ID）
- [ ] 文案为正向赋能口径（「造就能人」而非「转化用户」）
- [ ] 每条内容具体可核——无套话、无空泛建议、无「希望它好用」这类空话
- [ ] 零 `[假设]` 标记残留

**三、人物与驱动因素（源 07g 维 6 / 12 去重）**
- [ ] 人物 2–4 条（裁定 6）
- [ ] 各人物代表不同用户类型，互不重叠
- [ ] 每条人物十键齐（id / name / role / priority / summary / context / goals / frustrations / current_behavior / driving_forces）
- [ ] 恰一条 `priority: 主`
- [ ] 主人物带 `transformation.before` / `after`
- [ ] 人物名为叙述型且取头韵名（源 saga principle）
- [ ] 每人正向驱动 3–5 条
- [ ] 每人负向驱动 3–5 条
- [ ] 每条正向带 `promise`、每条负向带 `answer`
- [ ] 驱动因素具体到使用语境（非泛泛人生目标），且负向栏真的在场

**四、业务目标与特征影响（源 07g 维 8 / 9 / 10 去重）**
- [ ] 首条为愿景（`BG-1` / `kind: 愿景`）
- [ ] 目标 3–5 条且各含 statement / metric / target / timeline
- [ ] 目标可量（SMART 四要素齐：数字 + 时点 + 可达 + 与愿景相关）
- [ ] `driver_patterns` 三键在场，`shared` / `unique` 非空
- [ ] 焦点声明在场且 `must` 非空
- [ ] 特征每条含 name / scores / score / decision / rationale
- [ ] 评分与评分表重算一致（主人物 高5/中3/低1；其他 高3/中1/低0）
- [ ] 分档与 Must-Have 判据一致，且主人物命中「高」的特征未被判「可选」

**五、链式校验（源 steps-v 五维：目标群覆盖 / 优先级一致性 / 人物一致性 / 特征影响对齐 / 跨段连贯）**
- [ ] 目标群覆盖：每条人物都有正负两栏
- [ ] 目标群覆盖：每条驱动因素都有 Promise / Answer，无缺项
- [ ] 优先级一致性：恰一条 `主`，分布合理（不是全判主）
- [ ] 优先级一致性：每条排序都带 `why`
- [ ] 人物一致性：人物名 / 优先级在成品视图与既有记录之间一致
- [ ] 人物一致性：各人物的驱动因素之间无无理由重复
- [ ] 特征影响对齐：每条特征都对着全部人物打了分
- [ ] 特征影响对齐：高分特征服务主人物，无主人物关键特征被判「可选」
- [ ] 跨段连贯：术语一致，因果链（业务目标 → 人物 → 驱动因素 → 特征）不破
- [ ] 跨段连贯：Effect Map 与记录一致（节点数 / TG-DF 配对 / 连接数 = 目标数 + 2×人物数）

**48 项过完** → 进第 2 步第 2 条跑终门 `check --final`。**质检不通过就回对应步骤文件修，不得带病定稿。**

**检查点（六拍）**：① 生成 → ② 落盘（修正项就地改）→ ③ 分隔 → ④ 呈出质检结果（每组几项过 / 几项改过）→ ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 定稿、交接与收尾`。

## 第 2 步 —— 定稿、交接与收尾（源 step-09a–09f）

**源侧处置先读（三处，均为源侧缺陷的 diy 收口）**：

① **生成环（源侧实测）**：源 `09a:44,60` 指令「回到 `07a` 重新生成全部文档」，而 `07a→…→08h→09a` 正好回到自身——一旦执行即成环，且 `07a`–`07g` 一次运行跑两遍。diy **不设这一步的重新生成**：成品在 `05-documents.md` 已落定，本步只做**最后核对**。

② **设计日志（源 step-09e）**：源侧要求把进度与关键决策追加进 `{output_folder}/_progress/00-design-log.md`——diy 侧**不建散 md**（D3 已裁定拆解）：**进度 = `stage` + `project.updated`；决策 = `revisions`**。

③ **Freya 激活路径（源 step-09f:67）**：源侧指令 `Load: getting-started/agent-activation/wds-freya-ux.md`——**该路径不存在**（且 agent 线已裁）。diy 侧**不指幽灵路径**：交接 = 本技能自己的收尾路由。

**收尾五拍**：

1. **完整性闸（源 09a）**：六个主体段逐个数一遍非空（缺的当场回补，**不跳过**）；上一节的 48 项已过。
2. **定稿落盘 + 终门（机械，`exit 0` 是唯一放行）**：先落 `project.status: 已定稿` + `stage: 收尾` + `project.updated` 刷今天，再跑：
   ```
   python "{project-root}/.claude/skills/diy-wds-trigger/scripts/wds_trigger.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
   ```
   违规按回执 `where` 就地修、重跑，**不得跳过**。定稿时会**复验上游门禁**（`wds-brief.yaml` 仍在场且 `project.status: 已定稿`）——上游被回退就停在这里。随身体检 `metrics`（人物群 2–4 / 每人 3–5 正 + 3–5 负 / 连接数）随时可跑，越界只给 warning。
3. **渲染（静默旁路）**：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。**不新开交互点、不等查看**。
4. **交接摘要（源 09d，会话内呈出、不落盘）**：给下游 `diy-wds-scenarios` 的一页——① **主群与转型**（人物名 + role + before → after）；② **必办 / 须办**（主群的 Top 3 正向驱动与 Top 3 负向驱动，**逐条念 ID**）；③ **特征优先级**（必须 / 应该 / 可选各几条、前 3 条是谁）；④ **焦点声明**（`top_group` + `must`）；⑤ **图的读法**（左→右、上→下即优先级、✅ 想要 / ❌ 怕）。
5. **路由与收尾**：一句话给「触发图已定稿，可进入场景（`diy-wds-scenarios`）」；未决项写进 `revisions`（`change` 点名段名 / 键名，`reason` 写为什么还没定），**不用 `[假设]` 标记**。**WDS 线是自己的短链**（brief → trigger → scenarios），diy 主线的 `diy-design` / `diy-dev` 在 C·3 之前不接这条线。

**落盘**：`project.status: 已定稿` / `stage: 收尾` / `project.updated` / `revisions` 收尾条目。

**检查点（六拍）**：① 生成 → ② 落盘（定稿 + 终门 exit 0）→ ③ 分隔 → ④ 呈出交接摘要 → ⑤ 出四选项 → ⑥ 等响应。

本文件到此结束——终门 exit 0 后本轮收尾，**不再读任何 `steps/` 文件**。
