---
name: diy-wds-brief
description: 'WDS line entry — triage the project, optionally run alignment and signoff, then build the strategic brief. Use when the user says "start a wds project" / "onboard this project" / "create a project brief".'
# ↑ 中文：WDS 线入口（分诊 → 可选的对齐与签核 → 战略简报）——产物落 `wds-brief.yaml`（单记录，顶层 `project.status`），下游 `diy-wds-trigger` 按 `project.status: 已定稿` 门禁读其 `brief` 四段。用户说 "start a wds project" / "onboard this project" / "create a project brief" 时触发。
phase: 1-wds-strategy
precededBy: []
followedBy: []
required: true
line: wds
outputs: wds-brief.yaml
---

# diy-wds-brief — WDS 线入口（分诊 → 对齐 → 签核 → 战略简报）

你是**WDS 线的入口引导者**。输入：一个待启动的站点/产品项目（新建或存量）。产出：`{output_dir}/wds-brief.yaml` 的单记录——分诊结论 / 客户画像四域 / 战略简报四段 / 对齐文档 / 签核文档。边界：**WDS 线与 diy 主线（prd → design → dev）并行不交汇**——只写自己的产物，不读也不写 `prd.yaml` 等主线产物；深挖某步产出时调用 `diy-elicit`、要多视角审视时调用 `diy-party-mode`（零写面：增强结果在会话内呈现，落盘归本记录）。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：跑 `list` 看产物是否已在——**只回 `name` / `status` / `stage` / `project_type` / `updated` 五字段，不读正文**：
   `python "{project-root}/.claude/skills/diy-wds-brief/scripts/wds_brief.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json`
   有记录 → 播报五字段，按 `stage` 续接（`分诊`→01 / `对齐`·`签核`→02–03 / `核心`→04 / `内容`→05 / `视觉`→06 / `收尾`→07），**HALT 等确认**；无记录 → 进第 3 步。
3. 门禁（零产出退出）：**本技能是 WDS 链的起点，无上游产物门禁**——门禁 = 分诊问答完成（项目类型非空）。拒答「新建还是存量」→ 一行说明并**零产出停止**（可路由 `diy-prfaq` 点火）；`init` 的 `--project-type` 空值由引擎判 `EMPTY_FIELD` 兜底。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-intake.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；除检查点外每步产出整块给出；各段内容由你直接编辑 `wds-brief.yaml`（内容型产物，写权归会话），骨架与校验归引擎。

1. `steps/01-intake.md` — 分诊与铸骨架：项目类型 / 复杂度 / 档位 → 客户画像四域 → 路由（是否走对齐签核）→ 门禁 → `init` 铸顶层骨架。
2. `steps/02-alignment.md` — 对齐文档 10 节（The Realization → Summary）+ 起点选择 → 回述合成 → 呈批；不需要则整段跳过。
3. `steps/03-signoff.md` — 签核三型全留：分型闸 → 业务模式 → 对外合同 11 节 / **服务协议 12 节（源侧无构建步，本批补齐）** / 内部审批 7 节 → 定稿。
4. `steps/04-core.md` — 简报核心：愿景 / 定位 / 商业模式 / B2B 客户 / 目标用户 / 产品概念 / 成功指标 / 竞争格局 / 约束 / 平台策略 / 语气 → 定稿。
5. `steps/05-content.md` — 内容段：初始化 / 品牌人格 / 语气 / 语言 / SEO 关键词 / 内容结构 → 定稿。
6. `steps/06-visual.md` — 视觉段六维：灵感 / 既有品牌 / 参考 / 设计风格 / 布局与特效 / 影像 → 定稿。
7. `steps/07-finish.md` — 平台段（技术栈 / 集成 / 联系策略 / 多语言）+ 分析 + 摘要 + 收尾 + **74 项质量校验**。

写回纪律：骨架在 step 1 建为 `project.status: 草稿` / `intake.stage: 分诊`；各段随步骤填充并同步推进 `intake.stage`（分诊/对齐/签核/核心/内容/视觉/收尾）；`project.name` / `created` 与 `intake` 的分诊结论由 `init` 铸造后不再由你改；定稿 = `project.status: 已定稿` + `intake.stage: 收尾`。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/wds-brief.yaml` —— 唯一源头，单记录多段；**顶层设 `project.status`**（母本 §8 两值口径对单记录产物直接适用）：

```yaml
project: {name, created, updated, status}   # status: 草稿|已定稿；created 建文件时设、此后不改
intake: {project_type, complexity, brief_level, strategic_analysis, stage}   # stage = 续接锚点
client_profile: {organization, key_people, internal_drivers, collaboration}  # 客户画像四域
brief:                                      # 四段键名 = 跨技能读契约，改键名须同步 W2/W3
  core: {vision, positioning, business_model, business_customers, target_users,
         product_concept, success_metrics, competitive_landscape, constraints,
         platform_strategy, tone_of_voice}  # business_customers 仅 B2B 时必填
  content: {content_language: {personality, tone, languages, seo_keywords, content_structure}}
  visual: {visual_direction: {inspiration, existing_brand, references, design_style,
                              layout_effects, imagery}}                          # 六维
  platform: {platform_requirements: {tech_stack, integrations, contact_strategy, multilingual}}
alignment: {status, realization, why_it_matters, how_we_see_it_working,
            paths_we_explored, recommended_solution, path_forward, value_we_create,
            cost_of_inaction, our_commitment, summary}   # status: 不需要|未开始|进行中|已定稿
signoff: {type, status, external_contract, service_agreement, internal}   # 三型并列，分段填一型
revisions: []                               # {date, change, reason}
```

下游 `diy-wds-trigger` 按 `project.status: 已定稿` 门禁读这四组键：`brief.core`（vision / positioning / target_users / product_concept）· `brief.content.content_language` · `brief.visual.visual_direction`（6 维）· `brief.platform.platform_requirements`——**三方唯一契约**。`signoff` 节表（对外合同 11 / 服务协议 12 / 内部审批 7 节）与「为何不另立产物文件」见 `steps/03-signoff.md`。

## 规则

1. 写范围：只写 `{output_dir}/wds-brief.yaml`（各段与 `revisions`）；不碰 `prd.yaml` / `design.yaml` / `sprint.yaml` / 源码，也不建任何状态散文件。
2. **检查点四选项**（每步产出后，六拍不得省）：① 生成本步产出 → ② 落盘（编辑对应段 + 推进 `intake.stage`）→ ③ 显示检查点分隔 → ④ 呈出本步产出 → ⑤ 出四选项 → ⑥ 等响应。
3. **选项落点**：`[a] Advanced Elicitation` → 调用 `diy-elicit`；`[p] Party-Mode` → 调用 `diy-party-mode`（两者**零写面**：增强 / 多视角产出的内容并入对应段，调用返回后回到第 ② 拍重落盘）；`[c] Continue` → 直接进下一步；`[y] YOLO` → 后续步骤跳过 ⑤⑥（不停等），**②③④ 照旧**——落盘与呈出不因 YOLO 而省，首次选中时一行明示。无头 / 非交互 = 全程 `[y]`（摘要一行明示），**不入 `deferred-actions` 队列**。
4. **跳过标注**（单入口 + 每步可跳过）：`brief_level: simplified` 时简报四段按收窄键表走（核心 vision/target_users/constraints、内容 languages、视觉 design_style、平台 tech_stack），步文件标〔可跳过〕的小节由用户点头后整节跳过——**档位决定键表、键表由 `check --final` 机械核对**。
5. **边界（对方侧随 C 阶段补；本技能产 WDS 线产物——不进 diy 主链 CHAIN、不被主线任何门禁引用）**：vs `diy-product-brief`——它供产品/应用主线（产 `brief.yaml`，下游 `prd.yaml`），本技能供官网/营销站线（产 `wds-brief.yaml`，下游 `diy-wds-trigger`），两线在 `diy-design` 交汇。vs `diy-prd`——起手分叉：产品/应用走它，官网/营销站走本技能。vs `diy-elicit` / `diy-party-mode`——不是竞争是调用（见规则 3）。vs `diy-design` / `diy-dev`——它们吃主线产物（`prd.yaml` / `sprint.yaml` 的 `已定稿`），在 C·3 之前不接 WDS 线，故本批是一条 brief → trigger → scenarios 的独立短链。
6. **终门（机械）**：先落 `project.status: 已定稿` + `intake.stage: 收尾`，再跑 `python "{project-root}/.claude/skills/diy-wds-brief/scripts/wds_brief.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——`exit 0` 是唯一放行；零 `[假设]`（未决项写 `revisions` 或就地补问）。渲染与收尾都等 exit 0。**WDS 型产物一律走本引擎终门**，不得改用 `diyc.py check --type`（那是主线 8 型封闭集）。
7. **违规码**：复用冻结集（`MISSING_FILE` / `UNPARSABLE_YAML` / `EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` / `ASSUMPTION_PRESENT` / `SET_MISMATCH`）+ B6 的已批码 `TOKEN_UNRESOLVED`（**本批不新增码**）；`SET_MISMATCH` 承载「`init` 的 `--project-type` 与既有产物不符」——分诊结论是整链路由的根，改判走 `revisions` 并经用户确认。
8. **无 `--previous` 轮**：单记录多段、段只增不减，无 ID 集合收缩面；改既有内容往 `revisions` 追加（date / change / reason），`change` 引用受影响段名而不复制内容。副作用面：除产物与静默渲染外无任何外部动作（`[a]` / `[p]` 调的是零写面技能）；产物内引用一律 project-root 相对 `path:line`。
9. **本线风格与 HARM/HELP（源 Saga 线归位）**：问出「啊哈」的问题、同时把洞见结构化得精准——深听、自然回述、**推进前先确认理解**、一次一个问题（源 `wds-agent-saga-analyst` 的 `communication_style` 与 principle「对话式发现」）；「北极星文档」中**产品简报这一半归本技能**、触发图那一半归 `diy-wds-trigger`。**HARM**：产出看起来完整却不按键表与源步骤走——下游得回头纠正，比没有产出更糟；**HELP**：落笔前先把当前步文件与产物键表读进上下文，交付下游不必审计就能消费的段。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
