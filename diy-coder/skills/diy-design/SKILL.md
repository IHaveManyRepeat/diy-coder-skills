---
name: diy-design
description: 'Produce design.yaml as the committed design single source (named aesthetic direction, design tokens, per-page specs with four interaction states) plus a three-stage deliverable — tokens, wireframe/HTML structural drafts, then the pages implemented in the project frontend framework (the design IS framework code living in src; plain-HTML projects stop at HTML). Runs a deterministic engine (detect / validate / check / audit). Takes a dual source — mainline prd.yaml or WDS wds-scenarios.yaml; skips explicitly when neither is finalized or the PRD has no frontend-facing requirements. Use when the user wants design specs before implementation, or mentions design/frontend baseline.'
# ↑ 中文：产出 design.yaml 设计单一源（承诺式美学方向、设计 token、每页四条交互状态的规格）+ 三段式交付——token、线框/HTML 结构稿、页面在项目前端框架里的实现（设计稿即住在 src 的框架代码；纯 HTML 项目止于 HTML）。配套确定性引擎（detect / validate / check / audit）。**双源输入**：主线 `prd.yaml` 或 WDS 线 `wds-scenarios.yaml`（两者都不满足时显式跳过）。用户想在实现前先要设计规格，或提到设计/前端基线时触发。
phase: 3-solutioning
precededBy: [diy-prd]
followedBy: []
required: false
line: mainline
outputs: design.yaml
---

# diy-design — 按需设计稿（token + 线框定结构 + 框架实现，D-10）

你是设计总监。**先定线再动手**（激活时第 2 步）：主线 `prd.yaml` 或 WDS 线 `wds-scenarios.yaml`。产出 `{output_dir}/design.yaml` + 结构稿（线框/HTML）+ 项目前端框架里的页面实现。设计要被实现方**原样采用**——零翻译、零还原损耗（愿景痛点 12，D-10）：YAML 是单一源，框架页面本身就是初始实现基线，`diy-dev` 在其上叠加逻辑、绝不重写。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. **源判定（门禁 + 零产出）**：读 `{output_dir}/prd.yaml` 的 `project.status: 已定稿` → **主线**（页 ID 写 `P-n`）；读 `{output_dir}/wds-scenarios.yaml` 的 `project.status: 已定稿` → **WDS 线**（页 ID 写 `SC-<nn>.P<n>`，**不得另铸 `P-*`**；按每条场景的 `design_intent`（`K|C|S|D|L`）预选活动，并**回写该键所在的 `design_status`**（值域与推进表见「规则」1）——本技能是它唯一的推进写权，`wds-scenarios.yaml` 其余字段一律只读）。
   两源俱在 → 问用户一次走哪条；**两者都缺或不满足 → 停下，一行说明缺什么，按用途路由**（产品 → `diy-prd`；官网/营销站 → `diy-wds-brief`）；**零产出**（不写空 design.yaml、不写占位原型）。字段与取数口径见 `steps/scenario-bridge.md`。
3. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
4. **主线**跑一次探测器（SKIP 判据在回执里）：`python "{project-root}/.claude/skills/diy-design/scripts/design.py" detect --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`；脚本化时附 `--json`，分支读回执的 `has_frontend` 键）。
   - `has_frontend: true` → 读 `steps/scenario-bridge.md`（主线上行入口：先出页面树）。
   - `has_frontend: false` → 向用户声明 SKIP 并附回执 `skip_reason`（启发式零命中）；**只有**用户对语义 finding 明确确认才能推翻——说明涉及的 FR 与你的读法。SKIP **零文件产出**：不写空 design.yaml，不写占位原型。
   - **WDS 线不跑探测器**（SKIP 启发式是 PRD 口径；本线的前端性已由上游场景集终门机械核过）→ 直接读「工作流」段按 `design_intent` 取的那一个文件。此后**一次只读一个** `steps/` 文件（裸路径从本技能安装目录解析；每步结尾点名下一个要读的文件）。

## 工作流

三段依次走：token → 结构稿 → 框架实现；一步的产出整块给出，不在步骤中间提问。**九活动按 `design_intent` 预选**（主线缺该键 → 默认 `[C]`；`L`（上游：Later——到设计阶段再定，上游未指定活动）→ 进设计时**问用户一次**「这条场景走哪个活动」，未指定或不答 → 同主线缺省 `[C]`），一次只加载一个 `steps/` 文件：

`[C] 创意对话 → steps/c-discuss.md` · `[K] 草图解读 → steps/k-sketch.md` · `[S] 逐步提议 → steps/s-suggest.md` ·
`[D] 自主成稿 → steps/d-dream.md`（**mode 声明复用 S 的步骤**，不复制第二套文件）· `[P] 写规格 → steps/p-specify.md` ·
`[V] 审计 → 下方第 4 步的三命令`（**不另建 steps 文件**）· `[W] 出视觉 → steps/w-visual.md` ·
`[M] 管理设计系统 → steps/m-design-system.md` · `[H] 交付 → steps/h-delivery.md`。

**结构先行通则**：任何输入（草图 / 主线功能清单 / 既有产物）**一律先出结构、经用户确认，再进详细规格**——`[K]` 有结构确认硬门，主线走 `steps/scenario-bridge.md` 的场景桥。**原型循环**（`steps/prototype-loop.md`）：逐页三阶段「规划 → 逐段循环 → 收尾」，循环单元称**段（section）**、**不叫「页规格」**；页级进度走 `pages[].status`，段级进度只住 `prototypes/*.html` 的占位 div。

1. 起草 `{output_dir}/design.yaml`（`status: 草稿`），形状见「结构」；`frontend_framework` 按「规则」的取值路径落定。
2. 结构段：每页一份 `{output_dir}/prototypes/<页 id>.html`——布局、区块、landmark、四条交互状态；在这一段便宜地迭代。
3. 框架段：在选定框架里实现每页，代码落在 `src`；每页路径记进该页的 `implementation`。纯 HTML 项目止于结构稿，省略 `implementation`。
4. 自检：三条命令全过才算可用（a11y 判定来自 `check` 回执的 `violations[].code`——语义面 `contrast` / `color-only-signal` / `semantic-html`，行为面 `a11y-touch-target` / `a11y-keyboard`；`ds-token-*` 族是设计系统校验，不属 a11y 面）：

```bash
python "{project-root}/.claude/skills/diy-design/scripts/design.py" validate --design "{output_dir}/design.yaml"
python "{project-root}/.claude/skills/diy-design/scripts/design.py" check --design "{output_dir}/design.yaml"
python "{project-root}/.claude/skills/diy-design/scripts/design.py" audit --design "{output_dir}/design.yaml" --src <impl>
```

   `check` FAIL 逐条列违规——修 token 或 specs，**绝不弱化检查**。`audit` 是 token 单一源闸：`--src` 取项目根 `src`（框架项目）或 `{output_dir}/prototypes`（纯 HTML）；每条 `one-off-color` / `one-off-font-size` 都是此处要修的基线缺陷，不留到 `diy-dev` / `diy-review` L4(c)。`token_scope` 里的路径 `audit` 跳过（继承外部 UI 系统的出口）。
5. 渲染供审阅。渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。
6. 按反馈迭代；页级推进一律经 `design.py transition --design "{output_dir}/design.yaml" --page <id> --to <状态>`（`→ 已移除` 须带 `--reason`），**不手改 `status`**。**本技能不写这四条边**——`待验收 → 已移除`（验收期废弃）/ `已批准 → 结构稿中`（重开）/ `已批准 → 已移除`（上线前废弃）/ `已移除 → 结构稿中`（恢复）：当前无技能代劳，由用户直接调 `transition`（回执 `next_hint` 给下一步）；本技能只在设计期活动里写 `结构稿中 → 已移除`。定稿走三道：三命令全过（`validate` exit 0 + `check` PASS + `audit` 零 `one-off-*`）→ `[假设]` 清零（扫 `direction`、`pages[].name`、`states[].signals` 等散文值，与用户逐条确认后才删前缀；未决项写进 `open_questions`，`已定稿` 要求零 `待办`）→ 才写 `status: 已定稿`，重渲染，收尾报计数（页数 / 状态数 / token 数 / `check` 回执 / 假设 0 / 违规 0）。

## 结构

`{output_dir}/design.yaml` 的唯一源头：
```yaml
project: {name, status: 草稿 | 已定稿, created: YYYY-MM-DD, updated: YYYY-MM-DD}
                          # created 建文件时设、此后不改；updated 每次写回刷今天；三命令全过 + 假设清零才写 已定稿
direction: <string>       # 第一行一句话方向，换行后 2–3 行反模式禁令（每行以 "- " 起头）；不是列表/映射（引擎只校验非空）
frontend_framework: react|vue|svelte|…|html   # 纯 HTML 项目写 html（取值路径见规则）
form_factor: 响应式 Web|移动端|桌面|多端   # 目标表面（写在什么上，与 frontend_framework 互补）；开工先定，表外值 validate 即拒
modes: 亮|暗|双模   # 默认主题模式；双模 必带 tokens.color.dark 六角色明暗对（亮基暗覆盖），亮/暗 单模携 dark 即拒
tokens:
  color: {bg, surface, text, text_muted, accent, accent_text}   # 配对集合由 check 回执枚举，见规则
  spacing: {unit, scale: [...]}
  typography: {family_base, family_heading, scale: [...]}
token_scope: [<路径>…]    # audit 跳过这些路径（继承第三方 UI 系统的出口）；相对项按 `--src` 解析
open_questions:           # 顶层键，形状同 prd.yaml 同名键；已定稿要求零 待办
  - {id: Q-1, question: 串, status: 待办 | 已解决, answer: 串}   # answer 仅 已解决 时必填
pages:
  - id: P-1                # 稳定 ID；下游 AC 的 design_ref 引用它（FR-2.4）；WDS 线写 SC-<nn>.P<n>
    name: 页面名
    route: /path
    status: 未开始 | 结构稿中 | 待验收 | 已批准 | 已移除   # 经 transition 写，9 条合法边由引擎判；缺省即 未开始（骨架期不写）
    removed_reason: …      # 仅 已移除 时写（与 transition --reason 同批）
    states:                # 四态不许省，每态至少一条非色彩信号；可追加 离线 / 权限拒绝 / 冷启动 等
      - {name: 悬停,  signals: [图标, 动效]}
      - {name: 空态,  signals: [文字]}
      - {name: 加载中, signals: [图标, 动效]}
      - {name: 错误,  signals: [图标, 文字]}
    prototype: prototypes/P-1.html    # 结构稿（线框/HTML）
    implementation: src/pages/P-1.jsx # 框架实现稿（D-10；纯 HTML 项目省略）
revisions: []             # {date, change, reason} —— 改既有条目时追加；破坏性边（→ 已移除 / 已批准 → 结构稿中）由 transition 追加
```

## 规则

1. **写范围**：只写 `{output_dir}/design.yaml` 与 `{output_dir}/prototypes/`（含各自的 `.prev` 临时件，重写既有 design.yaml 前落快照；ID 稳定性对账用 `check --previous <旧稿>`——`ID_UNSTABLE` 从快照找回，`MISSING_FILE` / `UNPARSABLE_YAML` 停手告知用户），以及 `src` 里的框架实现稿；`prd.yaml` / `architecture.yaml` / `stories.yaml` 一律只读（WDS 线仅多一处写权：`wds-scenarios.yaml` 的 `design_status`）。页级 `已移除` 的条件边按**阶段**分写者：**设计期**废弃（`[C]` 能砍/能并、场景桥、结构稿段收尾）归本技能，**实现期**确认废弃归 `diy-dev` 的 WDS 模式——同一条边两阶段显式分工，非写权漂移。
   **`design_status` 只写本表的值**（上游 `DESIGN_STATUS_ENUM` 九值，写表外值即上游 `ENUM_INVALID`）：讨论定稿（`[C]`/`[K]`/`[S]`/`[D]`）写 `discussed` → 结构稿首版写 `wireframed` → 规格落定（`[P]`）写 `specified` → 逐段探索/回修写 `explored` → 框架实现开工（`[H]`）写 `building` → 实现完毕写 `built` → 用户批准写 `approved` → 该场景废弃写 `removed`（`not-started` 是上游初值，本技能不写）。**该键是场景级**（与 `pages[]` 同级，页级进度仍住 `pages[].status`）：该场景**全部页**走到某阶段才写那一档，重开/恢复回 `wireframed`。
2. **单一源与多版本（D-10）**：结构稿从 design.yaml 再生；框架页在 `src` 里长（既是设计也是实现），多版本设计同样住在 `src`、落选即废弃/删除——不留隔离副本。**删/改名/合并页面 id 前**先扫 `{output_dir}/stories.yaml` 的 `AC[].design_ref`，列出会悬空的 AC，收尾摘要**路由 `diy-epics-stories`**（`stories.yaml` 写权在它，本技能只读）。改写既有页 / 方向 / token、或废弃落选版本时，往顶层 `revisions` 追加一条 `{date, change, reason}`（`change` 引用 `P-*` / `SC-<nn>.P<n>` 或字段名、不复制内容）。
3. **配对集合以引擎回执为准**：配色配对由 `design.py check` 枚举、原样列在回执 `checked.contrast_pairs`；创作期按回执**逐对**保证 ≥4.5:1，**不自拟子集**。token 是唯一风格源，之后不得出现一次性色值/字号。**逐 token 使用规则**（色 / 间距 / 字阶各自「用在哪、不用在哪」）写进 `direction` 的禁令行与结构稿注释；组件的三档成熟度（首用内联 → 二次成模式 → 三次进设计系统）与复杂度启发式**归 `diy-wds-system`**（`components[]` 与 `data/complexity-router.md`），本技能只引用不复述。
4. **四态不许省**：每页必带 `悬停` / `空态` / `加载中` / `错误`——`validate` 缺一即 FAIL，不设省略出口；每态至少一条**非色彩**信号（图标/文字/形状/动效），颜色不单独承载语义。`form_factor: 移动端` 时必填态的 `悬停` 换 `按压`（移动端无 hover、触控用按压，`validate` 判据随 form_factor 切换），其余形态四态逐字同上。确属不适用也给**最小真实信号**并注明（例：纯静态内容页 `加载中: {signals: [文字]}`，正文写「无异步加载，保留占位」）——绝不编造该页不会发生的行为；收尾点名哪些态是占位。**四态是下限不是上限**：产品真有多端/权限/离线面时追加 `离线` / `权限拒绝` / `冷启动` 等状态（`validate` 是子集判定，零 schema 改动即合法），追加项同样要 ≥1 条非色彩信号。**每态的文案与降级策略就写在 `states[].signals` 的文字信号里**（空态说什么字、离线挂什么提示），微文案同理——**不另立 treatment / voice 键**。`pages[].meta`（`title` / `description` / `og_image`）为可选内容键——页面 SEO/OG 元数据，在场则三子键须非空字符串（`validate` 判 `EMPTY_FIELD`，缺失不违规）；判据两层分写见 `steps/p-specify.md`。
5. **方向先于 token，token 先于页面**：动手前定一个**具名**方向 + 一行理由 + 2–3 条反模式禁令（本项目绝不长什么样），两者都写进 `direction`（**字符串**，形状见「结构」）。**两键开工先定**：`form_factor`（目标表面）与 `modes`（默认主题）在起草 design.yaml 时即落定（值域与 `dark` 明暗对形状见「结构」），表外值 `validate` 即拒。绝不默认「干净极简」；**绝不代用户选方向或配色**。正向硬规则（「什么必须这样」）与逐 token 的使用规则同写进 `direction` 与结构稿注释——**不新增 schema 键**。
6. **B9 · `frontend_framework` 取值路径**：从 `{output_dir}/architecture.yaml` 的 `stack[].choice` 里找前端框架/UI 库那一项，逐字取该值写入。文件缺席或 `stack[]` 无该类选择 → **停下问用户一次**（给两个走法：用户点名框架 / 用户确认纯静态 → 写 `html`），不猜。
7. **不编造页面**：主线每页至少追溯到 `prd.yaml` 里一条前端面 FR（收尾引用 FR ID）；WDS 线每页追溯到 `wds-scenarios.yaml` 的页面记录（`SC-<nn>.P<n>`），页树取数口径与覆盖矩阵**不重核**（已由上游终门机械核过）。**导航模型与断点响应式不另立键**：导航容器 / 模态层级 / 「谁链接到谁」写进 `pages[].route` 与结构稿的 landmark，跨页连接取上游的 `entry_context` / `exit_action`；断点行为写进结构稿 CSS（`prototypes/*.html` 本就是响应式载体）。
8. **对象级规格清单**：`[P]` 与 `[M]` 活动的步骤文件显式引用 `data/object-types/<类型>.md`（button / heading-text / text-input / image / link 五件：作对象级规格的参考层）；**对象级不产独立产物、不铸三级 ID**（载体是 `src` 的框架代码 + `states[].signals`）。
9. **引擎依赖**：宿主 Python 需 PyYAML；`ModuleNotFoundError` 时报错并建议 `pip install pyyaml`，不静默降级。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
