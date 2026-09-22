# 文案成稿骨架（五模型框架）

> **出处**：源 `wds-6-asset-generation/templates/content-output.template.md`（349 行，`[C]` 活动唯一被引用的模板，`steps-c/step-06:91`）。**改造点**：① **Alpha Feedback 段裁**（源 :339–:343 的「工作坊反馈」是 alpha 语境，见 `data/content-creation-workshop-guide.md:256–:277` 的 alpha 声明）；② **Workshop Metadata 收窄**（源要求的 Duration / Participants / Agent 名在 diy 侧无对应物——保留一条 `date` 与 `produced_by`）；③ **双语段裁**（源含双语字段，diy 侧语言由 `document_output_language` 决定，不做双语对照）。
> **用法**：`steps/07-content.md` 第 7 步把六段（`content_purpose` / `trigger_map_context` / `awareness_strategy` / `action_filter` / `empowerment_frame` / `structural_order`）+ 终稿渲染成本文件，落 `{output_dir}/assets/content/<条目名>.md`。
> **占位符约定**：`{…}` 一律从 `wds-assets.yaml` 的 `items[].content` 取，**填完不留占位符**（引擎把产物里的未解析 `{…}` 令牌判 `TOKEN_UNRESOLVED`）。机器锚点（ID / 枚举值）逐字保留。

---

# 文案成稿 — {内容段名}

**页 / 场景：** {页名（ID 可写，不进对外文案）}
**日期：** {date}
**方法：** 五模型框架（Content Purpose · Trigger Map · Customer Awareness · Action Mapping · Badass Users · Golden Circle）

---

## 一、战略地基（Trigger Map）

```
business_goal: {BG-<n>} {目标一句话}
persona: {TG-<n>} {人物名}
driving_forces:
  positive: {DF-<n>.<m>+} {盼什么}
  negative: {DF-<n>.<m>-} {怕什么}
customer_awareness:
  start: {起始认知层级}
  end: {目标认知层级}
```

## 二、内容策略（Content Strategy）

```
awareness_strategy:
  start_level / end_level: {层级}
  start_characteristics: [{知道什么}, {不知道什么}, {感觉如何}]
  end_characteristics:   [{会知道什么}, {会明白什么}, {会感觉如何}]
  language_guidelines:
    use:   [{能用的词}]
    avoid: [{要避开的词}]
    tone:  {语气}
  information_priorities:
    essential: [{非有不可}]
    helpful:   [{有更好}]
    avoid:     [{现阶段添乱}]
  emotional_journey: {start} → {bridge} → {end}
```

## 三、行动筛选（Action Mapping）

```
action_filter:
  required_action: {读者读完能做的那个动作}
  success_test:    {怎么算做到}
  business_impact:
    action:  {动作}
    outcome: {结果}
    goal:    {推动哪个业务目标}
  motivation:
    positive: {做了得到什么}
    negative: {不做失去什么}
  essential_information: [{必须有}]
  cut_list:              [{删掉}]
  obstacles: [{他卡的}, {你怎么拆}]
```

## 四、赋能框（Badass Users）

```
empowerment_frame:
  current: {现在的他}
  badass:  {用上之后他成为什么样的人}
  aha_moment: {那个「原来可以这样」的瞬间}
  capability_reframe: [{feature}, {reframed——你能做到什么}]
  cognitive_load: [{哪里太重}, {怎么简化}]
```

## 五、结构序（Golden Circle）

```
structural_order:
  section_why:  [{问题}, {确认}, {愿望}]
  section_how:  [{方法}, {差异}, {转化}]
  section_what: [{命名}, {证言}, {行动}, {除险}]
  flow_validation: {三节串读：每节是否把读者推向下一节}
```

## 六、终稿（Final Content）

### 选中的版本

{终稿全文——按 WHY → HOW → WHAT 的顺序，用第二节定下的语言指南写}

### 版本与选择理由

| 版本 | 差异轴 | 牺牲了什么 | 适合什么场景 |
| --- | --- | --- | --- |
| A | 愿望向 | | |
| B | 恐惧向 | | |
| C | 平衡 / 认知位移 | | |

**选择理由：** {为什么选它 / 合了哪两版 / 就地改了什么}

### 战略可追溯性（逐条对表）

- [ ] `essential_information` 逐条在场：{逐条打勾}
- [ ] `cut_list` 逐条不在场：{逐条打勾}
- [ ] 认知旅程位移成立：读完他到了 {层级}

---

**产出元信息：** `date: {date}` ｜ `produced_by: diy-wds-assets / AS-07` ｜ 条目 ID `{AS-07.<m>}`
**源方法出处：** Content Purpose（自有）· Trigger Map（`wds-trigger.yaml`）· Customer Awareness Cycle · Action Mapping（Cathy Moore）· Badass Users（Kathy Sierra）· Golden Circle（Simon Sinek）
**Alpha 声明：** 本框架源侧标注「未经实战验证、时长为估、可能增删步骤」（`data/content-creation-workshop-guide.md:256–:277`）——**本迁移如实登记，不当成熟能力**。
