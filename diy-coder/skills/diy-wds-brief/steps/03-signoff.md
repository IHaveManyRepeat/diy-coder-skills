# Step 3 — 对齐之后的签核（Signoff）

Progress: `[1 分型闸] → 2 业务模式 → 3 对外合同 11 节 → 4 服务协议 12 节 → 5 内部审批 7 节 → 6 定稿落盘`

**Read (input):** `./02-alignment.md` 的放行（`alignment.status: 已定稿`）；用户对分型、业务模式、各节内容的回答；对齐文档十节（合同的多处正文从它取，不重问）。
**Write (output):** `signoff` 段（`type` / `status` + 被选中的那一型 `sections` / `pricing_model` / `finalized`）；`intake.stage: 签核`；给用户的逐节呈出与定稿呈批。

你是**签核文档的起草人**。输入：一份已被干系人接受的对齐文档 + 一个商业关系。产出：`signoff` 段里的**一型**——对外合同 / 服务协议 / 内部审批，或明确「不签核」。

**用户拍板口径（裁定 13）**：**三型全留**——对外合同、服务协议、内部审批都迁，不砍分支。**源侧两处已知缺陷在本文件一并修掉**（裁定 5「断链——可修」类）：① `service-agreement` **源侧无构建步**（05a–05l 只按合同模板建节，`service-agreement.md` 仅在 05l 收尾处被提一句）→ 本文件第 4 步**补齐 12 节构建步**；② `05f Availability` 在源合同模板里**没有对应节** → 本文件把它**补成第 6 节**并标清适用条件。

## 第 1 步 —— 分型闸（源 04a）

**先说清为什么**：讲清「为什么签核是有分支的」——咨询方对客户、创始人对方、公司内部立项，三种关系的文书不是同一种东西。用你自己的话讲。

对齐文档被接受之后，**问清是哪一种关系**（源 04a 的四选，逐条解释）：

1. **对外合同** —— 你是顾问/承接方，**客户**已经认可了对齐文档。
2. **服务协议** —— 你是创始人/业主，**供应商**已经认可了对齐文档。
3. **内部审批** —— 这是**公司内部项目**，干系人已经认可。〔源侧补充：公司已有自己的审批格式，可以贴上来我按它调〕
4. **不签核** —— 现在不需要正式文书。

**用户选「不签核」也是合法结果**（源明示不得逼签）：一行说明「对齐文档随时可以拿去分享，日后要签再回来」→ 落 `signoff.type: 不签核` / `status: 未开始` / 三段留空 → `intake.stage: 核心` → 直接读 `./04-core.md`，**本文件到此结束**。

**落盘**：`signoff.type`（四值之一）+ `signoff.status: 构建中`。

**检查点（六拍）**：① 生成 → ② 落 `type` + `status: 构建中` → ③ 分隔 → ④ 呈出分型结论 → ⑤ 出四选项 → ⑥ 等响应。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 业务模式`。

## 第 2 步 —— 业务模式（源 04b；仅对外合同 / 服务协议）

**先说清为什么**：讲清「为什么钱怎么付决定了合同长什么样」——付款方式一变，付款条款、不超上限、可用性三节的写法全变。用你自己的话讲。

四选一（**不得替用户选**，逐条给适用场景与例子）：

| 选择 | 适合 | 连带影响 |
| --- | --- | --- |
| **固定价** | 范围与交付清楚的项目 | 不超上限**必填**；建议预付 |
| **计时** | 范围不确定、需求会变 | 不超上限**可选** |
| **长期聘用** | 需要长期可用性与稳定投入 | **触发第 3 步的第 6 节（可用性）**；不超上限**不适用** |
| **混合** | 多种工作类型并存 | 多套付款结构并存，逐项写清 |

**落盘**：`signoff.<型>.pricing_model`（四值之一；`type: 内部审批` 时**不填此键**）。确认一句：「你选的是【某型】，这对合同的影响是……」。

**检查点（六拍）**：① 生成 → ② 落 `pricing_model` → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 对外合同构建（11 节）`。

## 第 3 步 —— 对外合同构建（源 05a–05k：11 节）

逐节构建（**一次一节**，每节问完 → 落盘 → 检查点 → 下一节）。**能对齐文档里取到的，一律取而不重问**（引用节名，不复制原文）：

| # | `sections` 键 | 源节名 | 引导问句 / 内容 |
| ---: | --- | --- | --- |
| 1 | `project_overview` | Project Overview | 从 `alignment.realization` + `alignment.recommended_solution` 取；补双方主体、日期、合同语言、适用法律地 |
| 2 | `business_model` | Business Model | 第 2 步选的模式 + 付款结构说明 + 关键条款一句话 |
| 3 | `scope_of_work` | Scope of Work | 从 `alignment.path_forward` 取；**显式三段**：交付物清单 / 含什么（In Scope）/ **不含什么（Out of Scope）**——防范围蔓延 |
| 4 | `payment_terms` | Payment Terms | 总额 / 付款结构 / 付款日程 / 方式（转账、支票…）/ 到期日 / 逾期条款 / 付款条件（是否先付） |
| 5 | `timeline` | Timeline | 何时干、关键里程碑、交付日期 |
| 6 | `availability` | Availability（源 05f） | **条件节：仅 `pricing_model: 长期聘用` 时必填**——其余模式（固定价 / 计时 / 混合）**整节可缺省**（引擎接受缺省，不判违规）；键若已在场则照常校验（留空报 `EMPTY_FIELD`）。内容：营业时段 / 响应时间 / 会议可用性 / 紧急请求是否加价。**★ 源侧缺陷修复**：源 05f 写的这一节在源合同模板里**没有对应节**——本批补为第 6 节；本条条件即源 05f 原文「Only applies to retainer model - skip for other models」 |
| 7 | `confidentiality` | Confidentiality | 双向保密：保密范围 / 例外（已公开、独立研发、法律要求）/ 期限（几年） |
| 8 | `not_to_exceed` | Not to Exceed | **按模式条件**：固定价必填上限 / 计时可选 / 长期聘用不适用。含变更单（Change Order）机制——超范围工作须先签变更单 |
| 9 | `work_initiation` | Work Initiation | 何时可开工（合同签毕 / 特定日期 / 收到首款 / 书面通知 / 其他）+ 防「未授权开工」 |
| 10 | `terms_and_conditions` | Terms & Conditions | 变更与修改 / 知识产权归属 / 终止（提前几天书面通知、已完工作照付）/ 争议解决方式与地点 / 适用法律与管辖 / 合同语言与优先文本 |
| 11 | `approval` | Approval | 双方签署位：客户方（签名 / 姓名 / 日期）+ 承接方（签名 / 姓名 / 日期） |

**源模板有三节没有对应构建步**（Why It Matters / Expected Outcomes / Risks and Considerations，模板 §6–§8）——**本批不另设构建步**：这三节的内容就是对齐文档的 `why_it_matters` / `value_we_create` / `cost_of_inaction`，组装成稿时**直接引用、不复制**（单一源；viewer 渲染时由 `alignment` 段供给）。

**落盘**：`signoff.external_contract.sections.<键>` 逐节写；`pricing_model` 已在第 2 步落位。

**检查点（六拍）**：每节一次——① 生成 → ② 落该节键 → ③ 分隔 → ④ 呈出该节 → ⑤ 出四选项 → ⑥ 等响应。四选项同第 1 步；`[y]` 只跳过 ⑤⑥，**逐节落盘照旧**。

读全并照做本文件 `## 第 4 步 —— 服务协议构建（12 节）`。

## 第 4 步 —— 服务协议构建（源侧无构建步 → 本批补齐）

**★ 源侧缺陷修复**：源 `wds-0-alignment-signoff` 的 05* 十二步只按**合同**模板建节，`service-agreement.template.md`（277 行 / 12 节）**从未被任何步骤加载**——用户在 04a 选了「服务协议」，走完 05a–05l 拿到的仍是一份项目合同。**本批补一条独立构建步**：同一批引导问句，节名与侧重按服务协议模板走。

逐节构建（**一次一节**，节表固定 12 节）：`project_overview`（同合同第 1 节）→ `scope_of_services`（服务范围与交付物；比合同的「工作范围」更偏**持续服务**而非一次性交付）→ `our_commitment`（我们的承诺）→ `timeline` → `why_it_matters`（从 `alignment.why_it_matters` 取）→ `expected_outcomes`（从 `alignment.value_we_create` 取）→ `service_terms`（**服务协议独有节**：付款条款 + 交付物验收 + 知识产权）→ `risks_and_considerations`（从 `alignment.cost_of_inaction` + `our_commitment` 取）→ `confidentiality` → `not_to_exceed`（条件同合同第 8 节）→ `terms_and_conditions` → `approval`。

**落盘**：`signoff.service_agreement.sections.<键>` 逐节写；`pricing_model` 同第 2 步。

**检查点（六拍）**：每节一次，同第 3 步的六拍与四选项。

读全并照做本文件 `## 第 5 步 —— 内部审批构建（7 节）`。

## 第 5 步 —— 内部审批构建（源 06a）

**口径**（源明示）：**这是内部文书，不得写成对外合同**——焦点是目标、权责、审批，不是详细的工时与范围。用户已有公司格式 → 请其贴上来按格式调。

逐节构建（7 节）：`project_overview`（实情 + 推荐方案，同第 3 步第 1 节）→ `goals_and_metrics`（想干成什么 / 成功指标 / 怎么量 / 关键 KPI）→ `budget_and_resources`（预算总额 / 若有分项 / 需要什么资源 / 不超上限上限）→ `ownership`（项目负责人 / 流程负责人 / 关键干系人 / 谁能拍板）→ `approval_and_signoff`（谁要批 / 审批阶段 / 签署流程 / 审批时限）→ `timeline_and_milestones`（关键里程碑 / 交付日期 / 硬期限）→ `optional_sections`（风险与考量〔可选〕/ 保密〔可选〕/ 路径概览〔可选〕）。

**落盘**：`signoff.internal.sections.<键>` 逐节写（**不填 `pricing_model`**）。

**检查点（六拍）**：每节一次，同第 3 步的六拍与四选项。

读全并照做本文件 `## 第 6 步 —— 定稿落盘`。

## 第 6 步 —— 定稿落盘（源 05l + 06b）

1. **整份回顾**：逐节念一遍给用户听（源侧的最后一个质量闸：「有没有要改的？」），改完再问一次。
2. **落定稿标记**：`signoff.<被选中的型>.finalized: true` + `signoff.status: 已定稿`。
3. **推进**：`intake.stage: 核心`。
4. **说明后续**：双方签署后本段才算真签下（本技能只负责**起草与定稿**，不代签、不代发）；签完 → 进简报核心段。

**检查点（六拍）**：① 生成 → ② 落 `finalized` + `status: 已定稿` → ③ 分隔 → ④ 呈出定稿摘要 → ⑤ 出四选项 → ⑥ 等响应。

**收尾与路由**：读 `./04-core.md`。

## 关于 `signoff` 段的三个设计问答（回报必答项）

**① 段结构**——三型**并列**（不是单型 `{type, …}`），`type` 标明哪一型被填：

```yaml
signoff:
  type: 不签核|对外合同|服务协议|内部审批     # 分型闸结果
  status: 未开始|构建中|已定稿                 # 段级状态
  external_contract:                          # 仅 type: 对外合同 时填
    pricing_model: 固定价|计时|长期聘用|混合
    sections: {project_overview, business_model, scope_of_work, payment_terms,
               timeline, availability, confidentiality, not_to_exceed,
               work_initiation, terms_and_conditions, approval}     # 11 节
    finalized: true
  service_agreement:                          # 仅 type: 服务协议 时填（节名按服务协议模板）
    pricing_model: …                          # 12 节：… scope_of_services … service_terms …
    sections: {…}
    finalized: true
  internal:                                   # 仅 type: 内部审批 时填（无 pricing_model）
    sections: {project_overview, goals_and_metrics, budget_and_resources, ownership,
               approval_and_signoff, timeline_and_milestones, optional_sections}   # 7 节
    finalized: true
```

三型并列表述的代价只是一个 `type` 判别键；收益是**空段可见**（用户能看到「另两型是有位置的，我没填」），且 `check` 能机械核对「`type` 与已填段一致」。

**② 为何不另立产物文件**——三条，按硬度排序：

1. **同一份对齐结论只该有一个源头**。三型文书都是从同一份 `alignment` 长出来的（合同第 1 节取 `realization` + `recommended_solution`，服务协议取 `why_it_matters`，内部审批取 `value_we_create`）。另立文件 = 同一事实两处落盘，正是本批要修的源侧病（源侧 contract.md / service-agreement.md / signoff.md / pitch.md 四份并立，且输出根有 6 套——census-1 §4）。**单一产物 = 单一源**。
2. **每阶段一个 YAML 是本线的既定形态**（裁定 2）。三个 WDS 技能各一个 YAML，`diyc.py resolve` 的 `output_dir` 是唯一读写根；本合同段只占 `wds-brief.yaml` 的一个子段，不新增路径、不新增 `outputs` 声明。
3. **签核段天然只有一型**。一次分型闸只有一个赢家——三段并列但**只填一段**，它不构成「多条记录」，不需要独立文件的承载量。真到文档体量成为问题时（比如合同真的长到几百行），升格动作是「`sections` 值改写成 `path:line` 引用 + 另出 md」，**那时再改也不返工**——因为键名与节表已经冻结。

**③ viewer 标签需求**——`wds-brief` 类型**不在** `viewer.py` 的 `DOC_LABELS`（32 条）内（`迁移计划.md:203` 已登记为 3 条确定缺口之一）。本段的具体需求：

- **文档标签**：`wds-brief` → 「WDS 战略简报」（页标题与索引卡片，缺口 2 的通用降级只会回落英文 stem）。
- **键标签**：`signoff` / `external_contract` / `service_agreement` / `internal` / `pricing_model` / `finalized` 需进 `KEY_LABELS`；`intake.stage` / `signoff.type` / `alignment.status` 的三个中文枚举值需进 `VALUE_LABELS`。
- **枚举着色的一个硬需求**：`signoff.type` / `alignment.status` / `intake.stage` 的值全是中文，但**键名不在 `ENUM_KEYS`** 内（现表只有 `status` / `type` 等裸名）——**不报 `unmapped enum`，也不着色**。若要让它们着色，须把 `signoff.type` 这类复合键名加进 `ENUM_KEYS` 或让 `VALUE_LABELS` 兜底。**本批只登记需求、不改 viewer**（`viewer.py` 属禁改面，改动排 C）。
