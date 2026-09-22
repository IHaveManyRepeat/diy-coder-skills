# Step 7 — 文案（C，五模型框架）

Progress: `[1 定目的] → [2 载触发图] → [3 认知策略] → [4 行动筛选] → [5 赋能框] → [6 结构序] → [7 成稿]`

**Read (input):** `{output_dir}/wds-scenarios.yaml` 的 `scenarios[].pages[]`（每页要承载的信息）；`{output_dir}/wds-trigger.yaml`（**战略地基**：`business_goals[]` / `personas[]` 及其驱动因素 / `priority`）；`{output_dir}/wds-brief.yaml` 的 `brief.content`（品牌人格 / 语气 / 语言 / SEO 关键词）——**触发图缺则回落简报并标注缺口**（源侧 `steps-c/step-01` 的原口径）；`templates/content-output.template.md`（成稿骨架）。
**Write (output):** `wds-assets.yaml` 的 `activities[AS-07]`；`{output_dir}/assets/content/` 与 `prompts/`。

你是**文案生产的主持人**（源 `steps-c/` **七步**，本技能唯一非图形的活动）。文案是本技能里**战略含量最高**的一段——它不靠灵感，靠**五个模型**把「说什么」推出来。**本活动不读风格库**（源侧口径）：语气与结构由模型与简报定。

**本段纪律**：① **六段 YAML 全落**（`content_purpose` / `trigger_map_context` / `awareness_strategy` / `action_filter` / `empowerment_frame` / `structural_order`），一段不落才算走完；② **不可机械**：文案质量只能人判——引擎核的是**六段在场与键齐**，不是「写得好不好」；③ **源侧标 Alpha**（`data/content-creation-workshop-guide.md:256–:277`：框架未经实战、时长为估）——**登记为未验证能力，不得当成熟件宣传**。

## 第 1 步 —— 定目的（源 `steps-c/step-00`）

**先问清**：「这段内容要达成什么？」**五问全答，答不全不许往下**：① 内容是什么？② 要达成什么？③ 读者是谁、他现在处在什么状态？④ 怎么算成功？⑤ 哪几个模型为主（primary / secondary / tertiary）？

**「好目的」的判据**（源侧给的好/坏对照）：能写出**成功判据**的才是好目的——「提升品牌认知」不是好目的，「让第一次来的人 30 秒内明白我们是做什么的」才是。

**产出键**：`items[].content.content_purpose`（内容类型 / 目的陈述 / 受众 `who-state-context` / 成功判据 / 模型优先级 / `review_question` 六键齐）。

**检查点（六拍）**：① 生成目的块 → ② 落盘 `content.content_purpose` + `AS-07.status: 进行中` + `stage: 文案` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 载触发图`。

## 第 2 步 —— 载触发图（源 `steps-c/step-01`）

**先问清**：「这段内容挂在哪条业务目标、哪个人物、哪几条驱动因素上？」——**锚必须点名 ID**（`BG-<n>` / `TG-<n>` / `DF-<n>.<m>+|-`），不复制上游内容。

**读三样**：① 业务目标（这条内容服务的那个）；② 人物（是谁在读）与**正负驱动因素**（盼什么 / 怕什么——负向驱动决定你要拆掉哪个顾虑）；③ **认知旅程**（`START → END`：他从哪个认知层级进来、你要把他送到哪一级）。

**缺触发图时**（源侧原口径的回落）：读 `wds-brief.yaml` 的 `brief.core` + `brief.content` 作替代，并在 `revisions` **记一条 gap**（写清回落了、缺的是哪一层信息）。

**产出键**：`items[].content.trigger_map_context`（业务目标 / 人设 / 正负驱动因素 / 认知 `START`→`END`）。

**检查点（六拍）**：① 生成触图上下文块（引用 ID）→ ② 落盘 `content.trigger_map_context` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 认知策略`。

## 第 3 步 —— 认知策略（源 `steps-c/step-02`）

**先问清**：「他现在能听懂什么话？要听到什么才肯往下走？」

**五个认知层级**（源侧原口径，逐级有名有特征）：`Unaware`（不知道有问题）→ `Problem`（知道有问题、不知道有解）→ `Solution`（知道有解、不知道有你这个）→ `Product`（知道你了、在比价）→ `Most Aware`（就等一个理由）。

**逐项定死四件**（源侧口径）：
- **起止层级与特征**：`START` 那一级的「知道什么 / 不知道什么 / 感觉如何」各写一句；
- **语言指南**：`use`（能用的词）/ `avoid`（要避开的词）/ `tone`（语气）；
- **信息优先级**：`essential`（非有不可）/ `helpful`（有更好）/ `avoid`（现阶段只会添乱）；
- **情绪旅程**：`start` → `bridge` → `end`（从哪里起、靠什么过渡、到哪里落）。

**产出键**：`items[].content.awareness_strategy`（起止层级与特征 / 语言指南三键 / 信息优先级三键 / 情绪旅程三键）。

**检查点（六拍）**：① 生成认知策略块 → ② 落盘 `content.awareness_strategy` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 4 步 —— 行动筛选`。

## 第 4 步 —— 行动筛选（源 `steps-c/step-03`，Cathy Moore Action Mapping）

**先问清**：「读完这段，他**能做什么**？」——**答案必须是一个动作**（点、填、约、买），不是「更了解我们」。

**三件**（源侧口径）：
1. **必需动作 + 判据**：动作是什么、怎么算做到；
2. **业务影响逻辑**：`Action → Outcome → Goal` 三段链（这个动作带来什么结果、结果推动哪个业务目标）；
3. **用户动机正负**：做了能得到什么 / 不做会失去什么。

**筛选出两张清单**（这是本步的实质动作）：`essential_information`（为完成该动作**必须有**的信息）与 `cut_list`（**删掉**的信息——源侧口径：好内容的一半是删）。再加**障碍-对策对**（他卡在哪 → 你怎么拆）。

**产出键**：`items[].content.action_filter`（必需动作与判据 / 业务影响三段 / 动机正负 / `essential_information` / `cut_list` / 障碍-对策对）。

**检查点（六拍）**：① 生成行动筛选块 → ② 落盘 `content.action_filter` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 5 步 —— 赋能框`。

## 第 5 步 —— 赋能框（源 `steps-c/step-04`，Kathy Sierra Badass Users）

**先问清**：「读完这段，他会觉得自己**变强了**，还是只是被告知了一个功能？」

**四件**（源侧口径）：
1. **`current` vs `badass`**：现在的他是什么样 / 用上之后他成为什么样的人（写**人**，不写功能）；
2. **`aha` moment**：那个「原来可以这样」的瞬间是什么（一句能让人点头的话）；
3. **能力化改写**：`feature → reframed`——逐条把「我们有 X 功能」改写成「你能做到 Y」（**这是本步的核心动作**，逐条不留）；
4. **认知负荷**：哪里太重 → 怎么简化；**技能优先于工具**（先讲他能做到什么，再讲靠什么做到）。

**产出键**：`items[].content.empowerment_frame`（current vs badass / `aha` / 能力化改写表 / 认知负荷问题-简化）。

**检查点（六拍）**：① 生成赋能框 → ② 落盘 `content.empowerment_frame` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 6 步 —— 结构序`。

## 第 6 步 —— 结构序（源 `steps-c/step-05`，Simon Sinek Golden Circle）

**先问清**：「先讲为什么，还是先讲是什么？」——**源侧口径：WHY → HOW → WHAT**（先让人情绪上认同，再讲道理，再落到行动）。

**三节各有内容元素的有序表**（源侧原口径的排序规则，逐条落地）：
- **`section_why`**：问题 → 确认 → 愿望（先点出他的处境，再确认我们懂，再给愿望）；
- **`section_how`**：方法 → 差异 → 转化（怎么做 / 与别人哪里不同 / 他能得到什么变化）；
- **`section_what`**：命名 → 证言 → 行动 → 除险（这是什么 / 谁说过好 / 现在能做什么 / 做完的风险怎么消）。

**`flow_validation`**：把三节串起来读一遍，确认**每一节都把读者往下一节推**（推不动的节标出来重排）。

**产出键**：`items[].content.structural_order`（三节的有序内容元素表 + 节内排序规则 + `flow_validation`）。

**检查点（六拍）**：① 生成结构序 → ② 落盘 `content.structural_order` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 7 步 —— 成稿`。

## 第 7 步 —— 成稿（源 `steps-c/step-06`）

**先问清**：「要几版给你挑？」——**默认三版**（源侧三轴：`A` 愿望向 / `B` 恐惧向 / `C` 平衡或认知位移）。

**三版逐版给理由**（不是给三个差不多的版本让人挑顺眼的）：每版写明它压的是哪一轴、牺牲了什么、适合什么场景。

**选 / 合 / 调**：用户选一版、或把两版的段拼起来、或就地改。改完做**两项校验**：
- [ ] **完备性**——`essential_information` 逐条在场、`cut_list` 逐条不在场；
- [ ] **认知旅程**——从 `START` 到 `END` 的位移真的发生了（读一遍，自己回答「读完他到了哪一级」）。

**落成稿**：按 `templates/content-output.template.md` 的骨架把**六段 + 终稿 + 战略可追溯性**落成一份文件，放 `{output_dir}/assets/content/`；`items[].prompt` 写**这份文案的写作简报**（供日后重写或批量同族文案时复用），`items[].assets[]` 登记产出的 `.md` 路径。

**产出键**：`items[].content.final`（`versions[]` 三版原文 + `chosen` + 选择理由 + 完备性与认知旅程校验结论）+ `items[].prompt` + `items[].assets[]` + `activities[AS-07].status: 已评审`。

**收尾动作**：更新活动级 `status` 到 `已评审`；一句话说明文案是页面稿的上游料（第 2 步的就绪度评估会回读这批）；**Alpha 声明**：本活动的框架源侧标注为「未经实战验证」（`data/content-creation-workshop-guide.md:256–:277`），**本迁移如实登记，不当成熟能力**；本文件到此结束——读 `steps/08-presentation.md` 继续，或回活动菜单。

**检查点（六拍）**：① 生成三版 + 校验结论 → ② 落盘 `content.final` / `assets` / 活动 `status` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。
