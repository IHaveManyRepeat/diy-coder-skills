# Step 4 — NFR（四域证据审计 + ADR 清单）

Progress: `Preflight → Oracle → Matrix & Gaps → [NFR] → Gate → Finish`

**Read (input)：** `collect` 回执的 `nfr_inputs`（四域 / 阈值载体实测 / `prd.yaml` 的 NFR 条目 / `architecture.yaml` 的 affects 面 / 合规五标准清单 `compliance_standards` / 跨域合成规则 `cross_domain_rules`）；`adr-checklist.yaml`（技能内静态资产，29 行）。
**Write (output)：** 草稿记录的 `nfr`（`domains`——含合规行与跨域行的 `findings` / `overall_risk` / `adr` / `gaps`）。

## 域与状态

四个域固定、不增不减：`security` / `performance` / `reliability` / `maintainability`。每域一个 `status`：

| status | 含义 |
| --- | --- |
| `PASS` | 目标达成，且**有证据**（threshold 有出处、measured 有实测 / 有据可查的运行记录） |
| `CONCERNS` | 部分达成、接近临界，或**缺支撑证据**（无基线 / 无监控 / 无 owner）——不阻断，但需跟进 |
| `FAIL` | 未实现，或存在阻断该维度信心的缺陷 / 漏洞 |
| `N/A` | 该域对本系统不适用（写明理由，进 `findings`） |

**聚合是引擎做的**：`overall_risk` = max(域状态映射：`FAIL→HIGH` / `CONCERNS→MEDIUM` / `PASS→NONE`；`N/A` 不计)。你写域状态，引擎重算总风险并判 `SET_MISMATCH`——别手填 `overall_risk`。

## 阈值纪律：不得猜测（本步的核心）

**阈值唯一合法来源 = 用户在会话里显式给出。** 2026-09-15 实核：`prd.yaml` 的 NFR 条目 / `architecture.yaml` 的决策 / `test-plan.yaml` 三处候选源**都没有结构化阈值载体**——它们能提供意图（「登录要快」），不能提供数字（「P95 < 200ms」）。

- 用户没给数字 → `target: UNKNOWN`，该域**至少 `CONCERNS`**（`UNKNOWN` 阈值域记 `PASS` 会被 `check` 判 `UNKNOWN_THRESHOLD_PASS` 违例）。
- 每条 `thresholds[]` 必须写 `source`，形态只认「用户会话 `<YYYY-MM-DD>`」（可附用户引用的出处字符串作追溯，例如 `用户会话 2026-09-15（用户引用 SLA 文档 §3.2）`）。写「行业惯例」「一般要求」「默认 99.9%」一律 `THRESHOLD_UNSOURCED` 拒收。
- 拿不到证据 → 不猜，写 `gaps: [{what: <缺什么>, why: <为什么要它 / 谁该提供>}]`。缺口是**交付物**，不是失败。

`measured` 是实测或可查记录（跑过的命令、监控面板读数、用户提供的报告）；没测就留空并把该域压到 `CONCERNS`——**没测过不等于达标**。

## 四域各自问什么

- **security**：认证 / 授权（OAuth2 / OIDC、最小权限）、加密（静态 + 传输）、密钥存放（Vault 而非代码）、输入净化（注入面）。**任一 FAIL 不可豁免**（见 step 5）。
- **performance**：延迟目标（P95 / P99）、吞吐、限流；测法与样本量写进 `findings`。
- **reliability**：可用性目标、错误率、容错（熔断 / 重试 / 降级）、MTTR。
- **maintainability**：测试覆盖与结构、重复度、依赖漏洞、结构化日志、错误追踪。

阈值来自用户时逐条落到对应域；用户给的是「非功能要求」而非数字 → 该条进 `gaps`，域状态按上面规则压档。

## ADR 清单走查（29 行，`adr-checklist.yaml`）

逐条问「有没有证据」，不评好坏、不猜答案，三态记账：`有证据` / `缺口` / `未评估`。

- `adr.rows` 固定 **29**（引擎按资产文件行数重算，写别的值 `SET_MISMATCH`）。
- `adr.passed` = 有证据的条数。strong 线 ≥26/29 **只进展示与 `recommendations`**，不进 `gate` 判据——不要把它当分数线。
- 「缺口」与「未评估」的条目：能落到四域的写进对应域 `findings`；其余写 `nfr.gaps`（`what` = 哪条 ADR，`why` = 缺什么证据、谁提供）。

清单是**技能内静态资产**，不读 BMAD 原文、不联网：`{skill-root}/adr-checklist.yaml`。

## 第五个走查维度：合规标准审计（SOC2 / GDPR / HIPAA / PCI-DSS / ISO27001）

四个域之外**再走这一个维度**：五个标准逐个问「本系统有没有这条合规要求、拿得出什么证据」，**一个都不许跳**——不适用就写 `N/A` + 一句理由（源面：「Compliance requirements identified」或明确不适用；别把「没想过」写成 `N/A`）。组织给的行业基线自取（`collect` 回执 `nfr_inputs.compliance_standards` 就是这五个）。

**记账形态**（写进最相关那个域的 `findings` 数组，一个标准一行）：

```
<标准>: <PASS|PARTIAL|FAIL|N/A> — <依据>
<标准>@<域>: <PASS|PARTIAL|FAIL|N/A> — <依据>      # 可选：逐域观察行
```

聚合**必须 FAIL > PARTIAL > PASS**（源聚合口径）：任一逐域观察行 `FAIL` → 该标准 `FAIL`；否则任一 `PARTIAL` → `PARTIAL`；全 `PASS` → `PASS`；全 `N/A` → `N/A`。聚合行与逐域行矛盾 → `COMPLIANCE_AGGREGATE_MISMATCH`；行形态不合（以标准名开头却读不出状态）→ `COMPLIANCE_UNRECORDED`——两者 `check` 当场拦；五标准缺行 / 缺聚合行是 `--final` 义务（同样判 `COMPLIANCE_UNRECORDED`）。

标准 `FAIL` 的处置：相关域 `findings` 写清缺什么，`nfr.gaps` 记证据缺口（`what` / `why`），`gate.recommendations` 给整改路由；该标准观察落在哪个域，那个域的 `status` 至少 `CONCERNS`（域状态 → 门至少 `CONCERNS`，规则树自然传导）。

## 跨域风险合成（两组合成规则）

四域是分开审的，风险却常跨域。逐条走源的两条合成规则（`collect` 回执 `nfr_inputs.cross_domain_rules` 给出机器可读版）：

| 组合 | 触发（域状态） | 源合成结论 |
| --- | --- | --- |
| `reliability×maintainability` | 两域均 `CONCERNS` / `FAIL` | 低覆盖 / 缺观测可能掩盖可靠性回归 |
| `security×reliability` | `security` = `FAIL` 且 `reliability` ≠ `PASS` | 安全缺陷可能演变为可靠性事故 |

**命中即必须落点**：在 `gate.recommendations` 或相关域 `findings` 写一行「`<域>×<域>: <判定与理由>`」——**判定不成立也要写明为什么不成立**（`check --final` 命中而两处都无线 → `CROSS_DOMAIN_UNRECORDED`）。源 `impact` 的 `CRITICAL` 在 diy 三值尺度（`HIGH|MEDIUM|NONE`）压缩为 `HIGH`，写进那一行。

合成结论**只进 `recommendations` / `findings`，不进 `gate` 判据**——它不新开判据、不单独抬档（要抬档就得有判据落点：域状态或软指标，否则 `check` 判 `DECISION_INCONSISTENT`）。

## 回填与下一步

写 `nfr` 四段：`domains`（四域，各带 `thresholds` / `findings`——**合规行与跨域行都落在 `findings`**）、`overall_risk`（按域状态映射如实写，引擎会重算对账）、`adr`、`gaps`。有域 `CONCERNS` 时记住后果：闸门**至少 `CONCERNS`**（step 5 处理）。

读完并执行 `./05-gate.md`。
