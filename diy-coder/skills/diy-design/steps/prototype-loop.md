# Step — 原型循环（Prototype Loop）· 三阶段

Progress: `[0 术语与真源] → [1 规划] → [2 逐段循环 4a→4b→4c→4d→(4e|4f)→4g] → [3 收尾] → 路由`

**Read (input):** `{output_dir}/design.yaml` 该页 `pages[]`（规格是唯一真源：`states[].signals` 是呈测判据，`prototype` 是稿的落点）；`{output_dir}/prototypes/<页 id>.html` 现值与其中**剩余段的占位 div**；`{output_dir}/wds-scenarios.yaml` 该页 `entry_context` / `exit_action`（WDS 线）；用户在本文件各步的回答。
**Write (output):** `{output_dir}/prototypes/<页 id>.html`（逐段实现，剩余段留占位 div）；`design.yaml` 的 `pages[].status`（**经 `design.py transition`，不手改**）与 `revisions`（段的改进记录）；`design_status` 推进（WDS 线，场景级键，值域见主文件规则 1）：**该场景全部页首版结构稿落盘**写 `wireframed`（第 1 步收尾），**逐段循环与回修**写 `explored`（每段落盘后）。

你是**设计总监**。这一段把页面规格变成**可点的结构稿**：**三阶段 —— 规划 → 逐段循环 → 收尾**。

## 术语与真源（裁定 17，必读）

- **循环单元叫「段（section）」**，**不叫「页规格」**。〔**术语陷阱修正**〕源侧 `迁移计划.md:210` 写 wds-5[P]「建页规格」，实测它建的是 **story 文件**（`stories/[View].[N]-[section].md`），**不是页面规格**——后者是 wds-4 `[P] Specify` 的产物（在本活动里**只读**）。diy 侧命名据此区分：`[P] Specify` 保留「页面规格」原义；本活动是**原型循环**，单元叫**段**。
- **批准粒度是「段」不是「页」**（源 `workflow-prototyping.md:52` `ALWAYS get approval before next section`）——每段单独过门，页级批准只在收尾出现一次。
- **段级进度不进 YAML**：真源是 `prototypes/*.html` 里的**占位 div**（源侧 `4c:90-92` 的自描述机制，直译保留）。**页级**进度写 `pages[].status`（5 值：`未开始` → `结构稿中` → `待验收` → `已批准` / `已移除`）。**不另立 `loop` 键**（任务书 §2.3 已删键：段级轮次/问题/改进的**文字记录**走既有 `revisions[]`）。

## 第 1 步 —— 规划（一次性）

源侧步 1–3（`1-prototype-setup.md` 140 / `2-scenario-analysis.md` 130 / `3-logical-view-breakdown.md` 128）**压成三步，且设备/保真度/语言/演示数据那套 4 问对话裁**（源 `1-prototype-setup.md:64-71` 的台词在 `PROTOTYPE-INITIATION-DIALOG.md` 409 行——diy 无演示数据与环境搭建面）：

1. **对规格**：读该页规格，列出「要建什么」的清单（区块 + 每区块的态）；
2. **分段**：把该页切成若干**段**（源侧口径每视图 4–8 段），每段一段话：建什么、判据是什么；
3. **定序与落稿**：建 `prototypes/<页 id>.html` 的首版（**只建首段 + 其余段的占位 div**），并把该页 `pages[].status` 经 `transition` 推到 `结构稿中`（WDS 线：该场景**全部页**首版落盘后，把场景级 `design_status` 推到 `wireframed`）。

**判据来源**：每段的验收判据取自 `design.yaml` 该页的 `states[].signals`（**规格是唯一真源**，源侧在 story 文件里的判据在 diy 侧回到 `design.yaml`）。

## 第 2 步 —— 逐段循环（4a → 4b → 4c → 4d → 4e / 4f → 4g）

源侧中循环十一步里的 4a–4g（合计 858 行）**压成下面五拍**，**每段跑一遍**：

### 4a 公告与取上下文
呈出「这一段要建什么」+ 需求摘要（一段一句）。**不落盘**（源侧同）。

### 4b 段需求定稿
〔**源侧裁撤**〕源 `4b-create-story-file.md` 要建 `stories/[View].[N]-[section].md`——**diy 侧不建第二份源**：段的范围与判据**就在对话里呈出并由用户确认**，文字记录落 `revisions`（`change` 点名页 ID 与段名，不复制内容）。理由：段级信息的三个真源已在场——页规格（`design.yaml`）、故事与 AC（`stories.yaml`，写权在 `diy-epics-stories`）、段实现状态（占位 div）。源侧 story 模板的通用部分归 `[D]`/`[F]` 活动的别批处置。

用户二选一（源 `4b:74-75` 直译）：`review`（先看段需求）或 `implement`（直接做）。

### 4c 逐段实现
线性代码生成（源 `4c:13` `Linear code generation is the task`，不在这步插问答）：

1. 写这一段；**剩余段保留/新增占位 div**（源 `4c:90-92`）；
2. **交付前自检六项**（**改写**：承源 `4c:96-102` 同一拍「呈测前自检」的**精神**，判据按 diy 面重写——源六项为 `All Object IDs from story file are present` / `Tailwind classes match story file` / `JavaScript functions implemented` / `Console logging added` / `Code is clean and readable` / `No syntax errors`，因裁定 7（Object ID 不铸）、无 Tailwind 面、无 console 面、不建 story 文件而**无一项可直接对应**）：语义 HTML 三条（`h1` 唯一 / `img alt` / `input` label）+ 四态在场且每态有非色彩信号 + 色与字号全走 token 变量 + 无裸色值 + landmark 结构完整 + 剩余段占位 div 在场；
3. 不合规就当场改，**不带着已知缺陷进呈测**。

### 4d 呈测（**浏览器强制门**，冻结契约）
**门的判据** = `design.yaml` 该页的 `states[].signals`；**验手段** = Playwright（MCP 或脚本化）；**强制语义** = 未过**不得呈给用户**。

- **改既有功能时先捕基线**，实现后比对，确认只发生预期改动；
- **呈用户的是定性四项**：Flow 感觉 / 视觉层级 / 清晰度 / 一致性（源 `4d:78-82`）；
- **验手段的形态差**：MCP 形态下 `file://` 被浏览器策略拦截（实测 `Access to "file:" protocol is blocked`）——结构稿 HTML 须先起本地静态服务（如 `python -m http.server`）再验；脚本化 Playwright 可直接读文件。别把这条拦截误判成「环境不可用」。
- **环境不可用**（探测不到 Playwright）：**停下如实上报**（说明探测方式与结论），**把选择权交用户**——① 安装/启用后重跑，或 ② 用户明确同意本次跳过。**不得静默降级**（不问就跳过 = 违规）；**不得无条件硬停**（用户已同意仍拒绝 = 僵局）；**跳过须在回报与呈报中留名**（哪一页 / 谁的授权 / 补验计划；**不另立产物键**）。
- 责任分割（源 `INLINE-TESTING-GUIDE.md:16-23`）：**可测量项归 agent，定性判断归人**——门过之后才呈人。
- 本节是冻结契约（§2.6）的执行面；同一条门在 `diy-dev` WDS 模式（实现侧）与 `diy-review` 的 WDS 路径上**同一套判据**，两端互引，不各说一套。

### 4e / 4f 反馈三分支（源 `4d:85-88` 的唯一显式转移边）
用户回三种之一：

| 分支 | 处置 |
| --- | --- |
| **批准** | 进 4g |
| **问题**（`Issue`） | 报根因 → 修 → **重跑 4d 门** → 重回呈测；往 `revisions` 追加一条（`change` 记段名与修什么，`reason` 记根因）。源 `4e:90` `This may loop multiple times until issue is resolved` 直译：**允许自环，不换页状态** |
| **改进**（`Improvement`） | 问一句「**要不要回写进规格**」（源 `4f:77-80`）：要 → 改 `design.yaml` 的对应键再改稿（**规格先于稿**）；不要 → 只改稿。改完重跑 4d，重回呈测 |

〔**源侧缺陷修复**〕源 `4g:69` 要求写「section status」，而 `templates/work-file-template.yaml:125-158` 的 `sections[]` **没有 `status` 键**（普查 V6 幻影字段）——diy 侧段状态**一律由 HTML 占位 div 自描述**，不写任何 YAML 段状态。

### 4g 段批准与下一段
播报进度（总段数 / 已完成 / 剩余）→ 问是否继续（源 `4g:79-84`）：继续 → 回 4a 做下一段；全完 → 第 3 步。等待期间用户可打 `pause`（源 `4g:80` 的暂停语义，直译）：**暂停是会话事实不是设计事实**——**不写状态字段**（diy 侧无「已阻塞」值，裁定 6）。

## 第 3 步 —— 收尾

1. **逐态集成测**（源 `5-finalization.md:61-71` 直译）：该页四个态连跑一遍，按同一套判据核对；
2. **页级批准 = 会话门（不推进 `pages[].status`）**：用户点头 = 设计侧的验收对话，确认「这一页可交下游」——页**停在 `结构稿中`**；`结构稿中 → 待验收` 的写者是 **`diy-dev` 的 WDS 模式**（实现 + 浏览器门过了才写，见 `diy-dev` 规则 7 与 `steps/wds-finalize.md` 第 1 步），**本活动绝不写 `待验收`**；用户在验收里提问题/改进 → 本活动按反馈继续改稿（页仍 `结构稿中`）；`待验收 → 结构稿中`（按审查 findings 回修）由 **`diy-review` 触发**，写权不在本活动；废弃 → `--to 已移除 --reason <文案>`（**`--reason` 必填**；设计期废弃写权归本活动，实现期确认废弃归 `diy-dev` 的 WDS 模式——同边两阶段显式分工）；
3. **更新 `pages[].prototype`** 指向成品稿；有用户改动则落 `revisions`；
4. **三选一**（源 `5:86-89` 直译）：再建一页 / 换一个场景 / 精修本页。

**WDS 线附带（`approved`·纯 HTML 项目写点）**：该 `SC-<nn>` **全部页**交付完毕（框架项目：`design_status` 已 `built`，写点在 `./h-delivery.md` 第 2 步；纯 HTML：结构稿全部经本步会话门）且**用户明确批准该场景设计**后，把场景级 `design_status` 推到 `approved`（人裁，不代批；与页级 `pages[].status: 已批准` 是两回事）。框架项目的本档写点在 `./h-delivery.md` 第 3 步——**二者二择一，不重复写**。

## 检查点与路由

**检查点**（每段 4g 后）：① 生成 ② 落盘稿与 `revisions`（WDS 线：+ 场景级 `design_status: explored`）③ 分隔 ④ 呈出进度 ⑤ 给选项 ⑥ 等响应。

**收尾与路由**：该页结构稿完成 → 读 `./h-delivery.md` 进框架实现段，或回 `./s-suggest.md` 做下一页。

**裁撤登记（源侧缺陷台账）**：源 `1-prototype-setup.md` 落盘的目录树 `[Scenario]-Prototype/` + `data/demo-data.json` + `PROTOTYPE-ROADMAP.md`（含 V3/V4/V7 三套状态词表与计数器）**全裁**——diy 单一源下无演示数据面、无 roadmap 散 md；源 `work-file-template.yaml` 的 `work/*.yaml` 段清单（含 V6 幻影 `status`）**裁**，「段」的契约改由 `design.yaml` 规格 + 占位 div 承载。

本文件到此结束，不再回头。
