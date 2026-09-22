---
name: diy-wds-system
description: 'Design system stage — grow a component library and its token namespace out of actual page usage: create with duplicate detection, import an existing system, preview/browse as a local HTML catalog, edit components in place, then audit cross-page usage consistency. Token names are derived from design.yaml.tokens (never restated). Use when the user says "build the design system" / "add a component" / "check component usage".'
# ↑ 中文：设计系统段（WDS 线设计段 + `wds-4` 的 `[M]` 活动合并）——产物落 `wds-design-system.yaml`（顶层 `project.status`），逐组件写 `components[]` 记录（ID `[prefix]-[NNN]`，26 前缀 / 6 分类），另存 `tokens`（**派生自 `design.yaml.tokens`**，引用不复述）/ `categories` / `prefixes`。五活动：C 建库（含重复检测）/ I 导入 / V+B 合一（预览与浏览 + catalog 生成链）/ E 就地编辑（**已去 Figma 通道**）/ 收尾（用法一致性校验 + 终门）。门禁 = 读 `wds-scenarios.yaml` 且 `project.status: 已定稿`；缺失 → 零产出停止并路由 `diy-wds-scenarios`。默认开启（`--mode on`）。用户说 "build the design system" / "add a component" / "check component usage" 时触发。
phase: 2-wds-design
precededBy: [diy-wds-scenarios]
followedBy: []
required: false
line: wds
outputs: wds-design-system.yaml
---

# diy-wds-system — 设计系统段（组件库 + 令牌，token 派生自 `design.yaml`）

你是**设计系统架构师**。输入：一份已定稿的场景集（页面清单）。产出：`{output_dir}/wds-design-system.yaml`——从**实际页面使用**里长出来的组件库（重复检测、复杂度路由、跨页用法审计）+ 一份 `{output_dir}/wds-design-system-catalog.html` 浏览应用。边界：**token 的单一源是 `design.yaml.tokens`**（本产物只引用不复述，裁定 5）；**本产物是两线共用的设计系统单一源**——WDS 线读 `wds-scenarios.yaml` 的页面 ID，主线侧在 C·3 由 `diy-design` 消费同一批 ID；深挖某条判断时调用 `diy-elicit`、要多视角审视时调用 `diy-party-mode`（零写面：增强结果在会话内呈现，落盘归本记录）。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：跑 `list` 看有没有已在做的组件库——**只回 `id` / `name` / `category` / `prefix` / `complexity` / `status` 六字段，不读正文**；有记录 → 播报六字段并问「接着做哪个活动（C / I / V / E）」，**HALT 等选择**；无记录 → 进第 3 步走 `[C]` 建库。
   `python "{project-root}/.claude/skills/diy-wds-system/scripts/wds_system.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json`
3. 门禁（零产出退出）：读 `{output_dir}/wds-scenarios.yaml`——**缺失 → 一行说明并零产出停止，路由 `diy-wds-scenarios`**；其 `project.status: 已定稿` 不成立 → 同样零产出停止（`init` 会把两者机械兜住：`MISSING_FILE` / `STATUS_MISMATCH`）。门禁过 → 读 `scenarios[].pages[].id`（组件 `used_in[]` 的合法值域）。`design.yaml` **可选读**：在场 → token 走派生；缺席 → 降级为独立定义并记 warning（不阻断）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-create.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；除检查点外每步产出整块给出；`components[]` 由你直接编辑 `wds-design-system.yaml`（内容型产物，写权归会话），骨架、铸号与校验归引擎。源侧是**菜单驱动**（用户挑活动），diy 侧保留这个形态：`[C] 建库` 是默认起点，其余四活动按用户意图进入。

1. `steps/01-create.md` — 盘点与建库（**用户关卡 1** + `init` 铸骨架）→ 候选扫描与四维比对 → 相似度聚合 → 机会与风险打分 → 决策呈批与执行（**用户关卡 2**）→ 组件落库与复杂度路由。
2. `steps/02-import.md` — 识别来源（URL / File / Code 三源，**Figma 源已裁**）→ 提取令牌 → 提取组件 → 写入本产物 → 校验导入。
3. `steps/03-view.md` — 载数据与选件 → 生成浏览应用（**V 精选预览 + B 四视图合一**，静态 HTML）→ 交互复核与反馈路由 → 生成 catalog。
4. `steps/04-edit.md` — 选组件 → 就地编辑定义 → 逐键 diff 与审批 → 同步校验（源 Figma 通道已裁，见规则 8）。
5. `steps/05-finish.md` — 用法一致性校验（`[M]` 版）→ 缺口处置与回写 → 定稿与终门 → 渲染与交接。

写回纪律：骨架由第 1 步的 `init` 铸为 `project.status: 草稿` 并铸首条记录 `[prefix]-001`；此后每条新组件按同前缀计数 +1 铸号（不重编不复用）；定稿 = `project.status: 已定稿` + 全部记录十五键齐备 + 零 `[假设]`。`project.name` / `created` 与已铸的 `id` 由 `init` 铸造后**不再由你改**。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/wds-design-system.yaml` —— 唯一源头；顶层设 `project.status`（母本 §8 两值口径）：

```yaml
project: {name, created, updated, status}   # status: 草稿|已定稿；created 建文件时设、此后不改
design_system_mode: on|off                  # 裁定 17 的唯一开关键，默认 on（一行关闭）
tokens:                                     # 裁定 5：派生自 design.yaml.tokens，引用不复述
  source: {file: design.yaml, path: tokens, mode: 派生|独立}
  namespaces: {color: [...], spacing: [...], typography: [...]}   # 只存名与指向，不存值
categories: [Interactive, Form, Layout, Content, Feedback, Navigation]   # 6 类（冻结）
prefixes: [{type, prefix, category}]        # 26 条（冻结；机械取数源 step-08b:68-95）
components:
  - id: btn-001                             # `[prefix]-[NNN]`，逐前缀独立计数、三位补零
    name / prefix / category / complexity / status: 在用|已废弃
    variants[] / states[{name, signals[]}] / styling{visual_properties, layout, library_component}
    behavior{interactions[], animations[], rules[]} / accessibility{aria, keyboard[], screen_reader}
    usage{when_to_use, when_not_to_use[], best_practices[]} / used_in[]   # 引 SC-<nn>.P<n>
    token_refs[]                            # `命名空间.名`（color./spacing./typography.），值回 design.yaml 取
    related[] / version{created, updated, changes} / notes
revisions: []                               # {date, change, reason}
```

**只产这两件**：本 YAML + `{output_dir}/wds-design-system-catalog.html`（可重生成的浏览应用）。**不建 `D-Design-System/` 目录树、不建 `components/*.md`、不建 `figma-mappings.md` / `component-library-config.md` / `catalog.template.html` 的副本**（那四个文件形态随裁定 2 / 裁定 6 处置：组件进 `components[]`、库映射进 `styling.library_component`、Figma 映射裁）。

## 规则

1. **写范围**：只写 `{output_dir}/wds-design-system.yaml` 与 `{output_dir}/wds-design-system-catalog.html`；不碰 `design.yaml`（**token 单一源在它那边，本技能只读**）、不碰 `wds-scenarios.yaml`（页面规格写权归 C·3 的 `diy-design`）、不碰 `prd.yaml` / 源码，也不建任何散文件与目录树。**零 git 写操作**（源 `step-08e:585-596` 的自动提交已裁）。
2. **检查点四选项**（每步产出后，六拍不得省）：① 生成本步产出 → ② 落盘（编辑对应键/记录）→ ③ 显示检查点分隔 → ④ 呈出本步产出 → ⑤ 出四选项 → ⑥ 等响应。
3. **选项落点**：`[a] Advanced Elicitation` → 调用 `diy-elicit`；`[p] Party-Mode` → 调用 `diy-party-mode`（两者**零写面**：增强 / 多视角产出的内容并入对应记录，调用返回后回到第 ② 拍重落盘）；`[c] Continue` → 直接进下一步；`[y] YOLO` → 后续步骤跳过 ⑤⑥（不停等），**②③④ 照旧**。无头 / 非交互 = 全程 `[y]`（摘要一行明示），**不入 `deferred-actions` 队列**。
4. **两个用户关卡不得省**：`01-create.md` 第 1 步的建库呈批（用户关卡 1）与第 5 步的决策呈批（用户关卡 2）——**没拿到明确点头不许往下走**；`05-finish.md` 的定稿同样要点头。
5. **默认开启 + 唯一提取阈值（裁定 17）**：`design_system_mode` 缺省 `on`（计划 §四 :232 的反转口径），显式关闭 = 一行写 `off`。**「第二次使用才提取」是唯一渐进阈值**——源侧「间距首次即提取」**不保留**（KISS）：间距名已改为**派生自 `design.yaml.tokens.spacing`**，不再由本活动产生，「何时提取间距」这个问题不复存在。
6. **token 派生（裁定 5）**：`tokens.namespaces` 只存**名**与指向，值一律回 `design.yaml.tokens` 取。**四套并存的源词汇表（9 元 `space-3xs…3xl` / 7 元裸名 / 8 元含 `flex` / Tailwind 数值阶）已归一为一套 `space-*`（10 个）**，归一依据与逐条映射见 `data/token-vocabulary.yaml`。
7. **重复检测的边界**：四维（Visual / Functional / Behavioral / Contextual）→ 百分比 → 等级 → 推荐这一**聚合段可机械，交引擎** `similarity` 子命令算（权重 30/30/25/15，High/Medium/Low = 1.0/0.6/0.2，L1–L6 六级）；**输入段（规格 + 候选 → 四维等级）不可机械**——源侧只有散文示例、无字段级规则，故由你逐维判定 + 用户确认。**不得假装全自动**。
8. **V 与 B 合一 + catalog 链保留（裁定 4）**：`03-view.md` 把源的 View（精选预览）与 Browse（四视图）合成**一个静态 HTML 应用**（四视图能力一条不少）；源的 localhost 服务与四路由**裁**（平台耦合）。**Figma 通道整块裁**（裁定 6 连带）：`04-edit.md` 是**本地编辑 + 逐键 diff + 审批 + 引擎校验**，**本技能全程零外部服务**。
9. **ID 体系**：组件 `[prefix]-[NNN]`（**26 条前缀**：`btn inp crd mdl drp chk rad tgl tab acc alt bdg avt icn img lnk txt hdg lst tbl frm cnt grd flx div spc`；**6 分类**见 `data/component-prefixes.yaml` / `data/component-categories.yaml`）；**逐前缀独立计数、三位补零、顺序递增、不重编不复用**；页面引用一律 `SC-<nn>.P<n>`（引 ID 不复制内容）。
10. **用法一致性校验归本技能（取 `[M]` 版）**：源的跨页审计有 `steps-m/step-03` 与 `steps-v/step-09` 两个入口，本批取 `[M]` 版落 `05-finish.md`（`wds-7` 本体无此能力，计划「页面规格引用其 token」需要它闭环；`diy-design` 的 `[V]` 段在 C·3）。同族的**复杂度路由**（源 `COMPLEXITY-ROUTER.md` 842 行）**亦归本技能**，收编为 `data/complexity-router.md`（`[K]`/`[P]` 侧引用在 C·3 按需回接）。
11. **终门（机械）**：先落 `project.status: 已定稿`，再跑 `python "{project-root}/.claude/skills/diy-wds-system/scripts/wds_system.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——`exit 0` 是唯一放行；零 `[假设]`（未决项写 `revisions` 或就地补问）。渲染与收尾都等 exit 0。**WDS 型产物一律走本引擎终门**，不得改用 `diyc.py check --type`（那是主线 8 型封闭集）。
12. **违规码**：复用冻结集（`MISSING_FILE` / `UNPARSABLE_YAML` / `DUPLICATE_ID` / `UNKNOWN_ID` / `EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` / `SET_MISMATCH` / `ASSUMPTION_PRESENT`）+ B6 的已批码 `TOKEN_UNRESOLVED`（**本批不新增码**；两处**语义复用**已在引擎 docstring 登记：`SET_MISMATCH` 承载编号跳号 / 分类与前缀表不符 / 既有产物不覆盖，`TOKEN_UNRESOLVED` 承载 token 引用解析不到与派生漂移）。
13. **无 `--previous` 轮（裁定 19）**：`components[]` 只增不减（废弃走 `status: 已废弃`，不删记录），无 ID 集合收缩面；改既有记录往 `revisions` 追加（date / change / reason，`change` 点名 `[prefix]-[NNN]` 而不复制内容）。副作用面：除两个产物与静默渲染外无任何外部动作。
14. **边界（对方侧随 C 阶段 / C·3 补）**：vs `diy-design`——**同一 token 位的两半**：`design.yaml.tokens` 是唯一风格源（含 `design.py audit` 的 `one-off-*` 闸），本产物**引用不复述**；本技能要改 token 值须回 `diy-design`。vs `diy-wds-scenarios`——它是硬门禁上游（页面 ID 的来源，只读）。vs `diy-wds-assets`——它**可选读**本产物的 `tokens` 段做令牌一致性校验（缺则降级）。vs `diy-elicit` / `diy-party-mode`——不是竞争是调用（见规则 3）。
15. **本线风格与 HARM/HELP（源 Freya 线归位，逐条带字段来源）**：**规格必须完整**（源 `customize.toml:32`「Specifications must be logical and complete — if you can't explain it, it's not ready」→ 组件十五键必填 + 终门）；**设计系统从实际使用中长出**（源 `:34`「Design systems grow organically from actual usage, not upfront planning」→ 裁定 17 的「二次使用才提取」）；**先原型后生产**（源 `:33`「Prototypes validate before production」→ `03-view.md` 的本地预览应用）。**HARM**：库看起来很齐，但组件的 `used_in[]` 全是空的（组件是凭空造的，不是从页面里长出来的，下游一接就发现对不上）；**HELP**：每加一条组件前先跑一遍候选扫描与四维比对，交付一份「每个组件都说得清它在哪一页、引了哪些令牌」的记录。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
