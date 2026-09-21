# Step 1 — 分诊与铸骨架（Intake）

Progress: `[1 分诊] → 2 客户画像 → 3 路由与铸骨架 → ./02-alignment.md`

**Read (input):** 激活段 `list` 回执（`name` / `status` / `stage` / `project_type` / `updated` 五字段）；用户对项目类型、复杂度、档位、客户画像各问的回答；用户手上已有的材料（有则只读取用）。
**Write (output):** `{output_dir}/wds-brief.yaml` 的顶层骨架（经 `init` 铸造）——`project` + `intake` + `client_profile` + `brief` 四段空位 + `alignment` + `signoff` + `revisions`；给用户的播报。

你是**项目分诊的主持人**（源 wds-0-project-setup 的 Phase 0 身份）。三步走完：分诊问答 → 客户画像 → 铸骨架。**分诊结论是整条 WDS 链路由的根**——项目类型决定走 Phase 1 还是 Phase 8，复杂度与档位决定后续哪些段可跳过。

**本段纪律**（源 setup 的两条硬约束）：① **不代拟、不默认**——每个配置项都要问过用户，不得假设答案（源 `FORBIDDEN to skip configuration questions or assume answers`）；② **分诊在最前**——「带着存量代码开跑 Phase 1」是源侧点名的头号错误，项目类型未定就不得进简报。

## 第 1 步 —— 分诊：项目类型 / 复杂度 / 项目名 / 既有材料 / 档位

**先说清为什么**：讲清「为什么先分诊」——源侧口径是 **Phase 1–7 = 从零建新的，Phase 8 = 改已有的**，走错路要重来的不是一步而是一条链。用你自己的话讲。

逐项问（一次问清、逐项确认；**不问就不许写**）：

- **项目类型**（源 step-01）：这是**新建**（greenfield，从零搭）还是**存量**（brownfield，改已有的）？说不清 → 先聊「你现在手上有什么」，再判。
- **项目名**：这个项目叫什么？（进 `project.name` 的对话名；机器锚点 `name` 键不动）
- **产品复杂度**（源 step-02 第 2 问）：`simple` 单页营销站 / `standard` 多页内容站 / `complex` 复杂功能站 / `complex+mobile` 带移动端——决定后续哪些段与阶段开关。
- **既有材料**（源 step-02 第 6 问）：手上有没有现成材料（旧站、品牌手册、竞品分析）？有 → 只读取用、引用式提及（`path:<relative>`），禁复制内容；无 → 记 `existing_materials.has_materials: false`。
- **简报档位**（源 step-02 第 7 问）：`complete` 完整战略文档 / `simplified` 简版（只记「现状 + 要改什么」）。**存量项目推荐 simplified**；新建项目源侧一律 complete。
- **战略深度**（源 step-02 第 8 问，**仅新建且非 simple 时问**）：`full` 走完整触发图 / `simplified` 战略背景并进简报 / `skip` 跳过——本技能只记档位，下游 `diy-wds-trigger` 按它决定是否整段走。

〔**技术栈与组件库两问已裁**（裁定 14 P3）：diy 侧由 `architecture.yaml` / `design.yaml` 覆盖，本技能只留**复杂度**这一档驱动后续开关。**用户主动提及时**记进 `brief.platform.platform_requirements.tech_stack`，不主动问。〕

**落盘**：`intake.project_type` / `intake.complexity` / `intake.brief_level` / `intake.strategic_analysis` 与 `intake.existing_materials`（骨架由本文件第 3 步的 `init` 一次铸成，本步只在会话内收齐答案）。

**检查点（六拍）**：① 生成 → ② 落盘（本步答案进 `intake`，随第 3 步 `init` 一次写入）→ ③ 分隔 → ④ 呈出分诊表 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面、多视角）｜ `[y]` YOLO → 跳过后续检查点，连续推进到本文件结束（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 客户画像四域与协作档位`。

## 第 2 步 —— 客户画像四域与协作档位

**先说清为什么**：讲清「为什么要画客户，而不是直接画产品」——源侧口径：这一步问的是**跟我们打交道的人**（组织、人、他们内部被什么推着走），不是他们的产品、不是他们的用户。用你自己的话讲。

**四域**（源 step-01a 的四块 + 源 setup 的协作档位；**一次一个话题，从对话里自然捞，别当清单逐个盘问**）：

1. **组织** → `client_profile.organization`：类型（初创 / 成长期 / 成熟 SME / 大企业 / NGO / 公共部门 / 内部团队）、规模（大致人数）、行业与处境、技术成熟度（做过数字产品吗、有内部技术团队吗）、设计成熟度（跟设计师合作过吗、顺不顺）。
2. **关键人** → `client_profile.key_people`：谁下单（姓名 / 角色 / **能不能自己拍板还是要往上签**）、有没有推动者（champion，未必与下单人同一人）、技术对接人、其他有意见或审批权的人（董事会 / 投资人 / 别的部门）、**决策文化**（一人快定 / 共识 / 层级 / 委员会）。
3. **内部驱动** → `client_profile.internal_drivers`：**什么事触发了这个项目**（换帅 / 丢客户 / 投资人施压 / 竞品动作 / 忍了很久的痛点到了临界点）、**对他们而言成功长什么样**（政治上和个人上的——推动者拿到功劳 / 董事会拿到创新证据 / 团队终于有拿得出手的东西）、有没有**因内部原因而非发布原因**的硬期限。
4. **协作方式** → `client_profile.collaboration`：沟通偏好与响应速度、时间线文化（快迭代 / 结构化里程碑 / 审批慢）、既有外部合作经验（跟外部团队合作过吗、好与不好在哪）、再加源 setup 第 9 问的**干系人风险档位**（个人爱好 / 小生意 / 部门级 / 企业级高赌注——**C/D 档要追问干系人与政治敏感点**）与**参与度 / 我方角色 / 建议呈现方式**三问。

**已答过的不要重问**：第 1 步或激活段自然聊出来的信息，确认后直接代入。

**落盘**：`client_profile` 四域（逐一给键；确实不知道的**标 `—` 留空**，不猜——`check --final` 只要求四域在场与内容非空，不要求填满每一格）。

**检查点（六拍）**：① 生成 → ② 落盘 `client_profile` 四域 → ③ 分隔 → ④ 呈出画像摘要 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` / `[c]` / `[p]` / `[y]` 同上步。

读全并照做本文件 `## 第 3 步 —— 路由、门禁与铸骨架（init）`。

## 第 3 步 —— 路由、门禁与铸骨架（init）

**先说清为什么**：讲清「为什么在这里分叉」——需要别人点头的和自己能定的，后面要走的路不一样。用你自己的话讲。

### 3.1 路由（源 step-01 第 3 问 + alignment 01b）

问一句：**「开工前需要别人点头吗？」**

- **需要**（有客户 / 有供应商 / 要向上批）→ 走对齐与签核：下一步读 `./02-alignment.md`。
- **不需要**（自己就能定）→ 跳过 02 / 03 两个文件，直接把 `alignment.status` 落 `不需要`、`signoff.type` 落 `不签核`，然后读 `./04-core.md`。
- 拿不准 → 按源 01b 的判据再问一层：**谁要签字？签的是什么？** 有具体签字人就走对齐。

### 3.2 门禁（零产出退出）

- 项目类型**为空 / 拒答** → 一行说明并**零产出停止**（不写任何文件）；可路由 `diy-prfaq` 点火。
- 用户说「先随便建个空的」→ 拒绝：分诊是入口技能的唯一门禁，空类型会让整链路由失效。

### 3.3 铸骨架（`init`）

复述确认（项目类型 + 复杂度 + 档位各一句）→ 用户点头后调引擎：

```
python "{project-root}/.claude/skills/diy-wds-brief/scripts/wds_brief.py" init --project-type "<greenfield|brownfield>" [--complexity <simple|standard|complex|complex+mobile>] [--brief-level <complete|simplified>] [--strategic-analysis <full|simplified|skip>] --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `--project-type` **必填**：空值 → `EMPTY_FIELD`、非法值 → `ENUM_INVALID`（两者都零产出）。
- 骨架落 `project.status: 草稿` / `intake.stage: 分诊`；`project.name` / `created` 由 `init` 铸造后**不再由你改**。
- **已有产物 → 不覆盖**：同值重跑只刷 `project.updated` 并给一行 warning；`--project-type` 与产物不符 → `SET_MISMATCH` 且零写入（要改判先与用户确认，再往 `revisions` 记一条 `change`）。
- 路径旗标不得省（引擎不自解析实例、不私读 `diy-coder.yaml`）。

**检查点（六拍）**：① 生成 → ② 落盘（`init` 铸骨架；`intake.stage` 留在 `分诊`，等 02 起再推进）→ ③ 分隔 → ④ 呈出回执与骨架摘要 → ⑤ 出四选项 → ⑥ 等响应。

**收尾与路由**：
- 走了对齐 → `intake.stage: 对齐`，读 `./02-alignment.md`。
- 不走对齐 → 在 `alignment` / `signoff` 两段落「不需要」判定后，`intake.stage: 核心`，读 `./04-core.md`。

本文件到此结束，不再回头。
