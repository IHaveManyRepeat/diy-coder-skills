---
name: diy-test-gate
description: 'Quality gate merging coverage traceability with NFR evidence audit — join stories ACs × test-plan TCs × sprint evidence ledger into a matrix, walk the five blind-spot heuristics, audit the four NFR domains plus the five compliance standards (SOC2 / GDPR / HIPAA / PCI-DSS / ISO27001) without guessing thresholds, flag stale evidence (>7 days) and cross-level duplicate coverage, then decide PASS / CONCERNS / FAIL on hard and soft criteria. Report-only on upstream artifacts. Use when the user says "lets create traceability matrix", "I want to analyze test coverage", "audit NFR evidence", "audit NFRs", "audit compliance requirements", or "evaluate non-functional requirements".'
# ↑ 中文：质量门——把 stories 的 AC × test-plan 的 TC × sprint 证据台账 join 成追溯矩阵，走 5 类盲区启发式，审计 NFR 四域 + 合规五标准（SOC2 / GDPR / HIPAA / PCI-DSS / ISO27001，阈值不猜），标记陈旧证据（>7 天）与跨层重复覆盖，最后按硬/软判据裁 PASS / CONCERNS / FAIL。对上游产物只读。用户说 "lets create traceability matrix" / "audit NFR evidence" / "evaluate non-functional requirements" 等时触发。
phase: 4-implementation
precededBy: [diy-augment]
followedBy: []
required: false
line: mainline
outputs: test-gate.yaml
---

# diy-test-gate — 质量门：覆盖追溯 + NFR 证据审计（YAML 单一源）

你是**质量门的裁决者**。输入 `stories.yaml`（AC 主源）+ `test-plan.yaml`（TC 与 status）+ `sprint.yaml`（证据台账）+ `prd.yaml`（priority 推导源）+ `mutation-report.yaml`（变异得分，可选）；输出 `{output_dir}/test-gate.yaml` 的 `TG-###` 门记录。覆盖与 NFR 进**同一门**：NFR 不另立档，只作判据输入。上游零写入——缺口给路由，不给补丁。**分工：** 覆盖**数字**由 `gate.py collect` 机械产出，你不得手算；oracle 语义、矩阵复核、盲区判定、NFR 证据裁定、豁免裁定由你做。豁免只能人写：引擎永不自动生成 waiver（`diy-augment` 产出的等价变异体也须经用户裁定才进 `waivers`）。
## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 跑确定性采集（门禁 + 矩阵 join + 软指标 + NFR / mutation 证据面，全只读）：
   `python "{project-root}/.claude/skills/diy-test-gate/scripts/gate.py" collect --project-root "{project-root}" --output-dir "{output_dir}" [--story S-x] --json`
   exit 1 是拒绝且零产出：转述一行理由与 `gate.route`（`diy-epics-stories` / `diy-test-design` / `diy-prd`），然后停止——拒绝永不成为一条门记录。`diyc` 子进程的 violations 是上游实况，进 `gate.blockers`，不是失败。
3. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
   读 `steps/01-preflight.md` 并照做（`steps/*.md` 裸路径从本技能安装目录解析），每步结尾点名下一份要读的文件。
## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不预载或批量加载六份；整块给出该步输出，不在步骤中间提问；产物散文用 `document_output_language` 写，对话用 `communication_language`。记录在 step 1 建为 `草稿`，各步填充同一条记录，step 6 定稿；ID 由你铸造（`TG-###` 三位零填充、稳定不重用不重编号）。

1. `steps/01-preflight.md` — 门禁复核 + story 定位 + 落草稿记录（矩阵 / 统计取自 `collect` 回执，禁手抄）。
2. `steps/02-oracle.md` — oracle 解析：AC 主源（`stories.yaml`）+ 降级链；解析不出 → HALT + 路由 `diy-epics-stories`，不落产物。
3. `steps/03-matrix-gaps.md` — 矩阵语义复核 + 缺口分析 + 证据时效处置（`EVIDENCE_STALE`，>7 天）+ 重复覆盖判定（`coverage.duplicates`）+ 5 类盲区启发式走查（脚本给候选，你给判定）。
4. `steps/04-nfr.md` — NFR 四域证据审计：阈值**禁猜**（唯一合法来源 = 用户会话，其余 UNKNOWN + gap）；ADR 清单（技能内 `adr-checklist.yaml`，29 行）走查；第五个走查维度 = 合规五标准（SOC2 / GDPR / HIPAA / PCI-DSS / ISO27001，聚合 FAIL > PARTIAL > PASS）；跨域风险合成（`可靠性×可维护性` / `安全×可靠性`）。
5. `steps/05-gate.md` — 单一门决策：规则树 + overlay + 豁免（用户交互点，仅人工授权写入）。
6. `steps/06-finish.md` — 定稿 + `check --final` 终门 + 渲染 + 摘要（决策 / 覆盖 / blocker / 路由：FAIL → `diy-correct-course` 或回 `diy-dev`）。

终门（机械判定）：先写 `status: 已定稿`，再跑 `python "{project-root}/.claude/skills/diy-test-gate/scripts/gate.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——exit 0 是唯一放行；修掉每一条报告的违规并重跑；JSON 回执（含计数）就是收尾证据。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。
## 结构

`{output_dir}/test-gate.yaml` — 单一源，集合形态（顶层形状对齐 `bug-log.yaml`）：

```yaml
project: {name, created, updated}
gates:
  - {id: TG-001, date: YYYY-MM-DD, status: 草稿|已定稿, scope: story, story: S-x}   # TG-### 稳定不重用；scope 唯一合法值（epic / release 为 v2 推迟项）
    oracle: {source: stories|合成, confidence: 高|中|低, items: N, inferred: [<string>], unresolved: [<string>]}   # inferred = 合成推断条目清单；source=合成 时必填
    coverage:
      items:                  # 矩阵行（oracle item → 覆盖判定）；tests = 已验证 TC（判定表口径见 steps/03）
        - {ref: AC-x.y, story: S-x, priority: P0|P1|P2, coverage: FULL|PARTIAL|NONE|UNIT-ONLY|INTEGRATION-ONLY, tests: [TC-x.y.z]}
      totals: {covered: N, total: N, pct: N}       # covered = FULL|UNIT-ONLY|INTEGRATION-ONLY 计数，PARTIAL / NONE 不计
      by_level: {单元: N, 集成: N, 端到端: N}  # 已验证 TC 按 type 计数
      heuristics: [<string>]  # 盲区命中（5 类）
    nfr:
      domains:
        - {name: 安全|性能|可靠性|可维护性, status: PASS|CONCERNS|FAIL|N/A, thresholds: [{name, target, measured, source}], findings: [<string>]}   # 四域固定；source 唯一合法 = 「用户会话 <date>」；findings 兼载两类走查行：合规 `<标准>[@<域>]: PASS|PARTIAL|FAIL|N/A — <依据>`（五标准齐全，聚合 FAIL > PARTIAL > PASS，`check --final` 判 COMPLIANCE_UNRECORDED / COMPLIANCE_AGGREGATE_MISMATCH）与跨域 `<域>×<域>: <判定>`（命中未写判 CROSS_DOMAIN_UNRECORDED）
      overall_risk: HIGH|MEDIUM|NONE   # 展示字段（不进 decision）= max(域状态映射：FAIL→HIGH / CONCERNS→MEDIUM / PASS→NONE；N/A 不计)
      adr: {rows: 29, passed: N}       # 清单 = 技能内 adr-checklist.yaml；strong 线（≥26/29）只进 recommendations
      gaps: [{what: <string>, why: <string>}]   # 证据缺口（替代「猜阈值」）
    gate:
      decision: PASS|CONCERNS|FAIL     # 无法评估不设档——走 HALT，不落门产物
      hard_criteria:                   # 一票否决：任一 失败 → 整门 FAIL；变异得分 过渡期记 n/a
        - {name: P0 覆盖|总覆盖|P1 覆盖, target: '100%', actual: '<x>%'|n/a, result: 通过|失败|n/a}   # 任务书 §4 三行分列：n/a 仅适用 P0 覆盖 空档（P1 覆盖 空档取 100%）
        - {name: 变异得分, target: '>=90%', actual: '<x>%'|n/a, result: 通过|失败|n/a}   # 多 run 聚合 = 全部 run 的 score 最小值；报告缺席时 actual 记 n/a
        - {name: 非功能致命|P0 未覆盖, target: 0, actual: N, result: 通过|失败}       # 非功能致命 = FAIL 域数 − 已豁免域数
      soft_criteria:                   # 任一 失败 → 降为 CONCERNS（不影响 FAIL 判定）；estimated 项须附 algorithm
        - {name: 业务规则覆盖|边界覆盖|P0 深度完整|ID 链可解析, target: '100%', actual: '<x>%', result: 通过|失败}
        - {name: 负向场景覆盖, target: '>=90%', actual: '<x>%', result: 通过|失败}
        - {name: 有效用例比, target: '>=95%', actual: '<x>%', result: 通过|失败}
      blockers: [{ref: <ID|string>, kind: 覆盖|非功能需求|启发式, why: <string>}]
      waivers: [{ref, approved_by, date, reason, expires, monitoring, fix_owner, fix_target}]   # 8 键固定；仅人工写入；安全域 FAIL 不可豁免
      basis: <string>                  # 决策依据一句话
      recommendations: [<string>]   # 重复覆盖候选（coverage.duplicates）与跨域合成行的落点；`EVIDENCE_STALE` 证据的处置也写这里
    open_questions: [<string>]
revisions: []                          # {date, change, reason} — 改既有记录时追加
```
## 规则

1. **写权边界与副作用：** 只写 `{output_dir}/test-gate.yaml`（记录 + `revisions`）。`stories.yaml` / `test-plan.yaml` / `sprint.yaml` / `prd.yaml` / `mutation-report.yaml` / 源码零写入——它们分别归 `diy-epics-stories` / `diy-test-design` / `diy-sprint` / `diy-prd` / `diy-augment`；缺口写 `gate.blockers` + `recommendations` 并给路由（`diy-dev` / `diy-correct-course`）。本技能不安装依赖、不改用户级配置、不跑 git、不开 GUI，故无待确认队列条目。
2. **引用式纪律：** 跨文档一律引用 ID（`S-x` / `AC-x.y` / `TC-x.y.z` / `FR-x.y` / `DA-0xx`），**禁复制内容**；矩阵行只带 ID 与判定，AC 正文不进产物。
3. **门决策自洽：** 任一 `hard_criteria` 失败 → 必须 `FAIL`；有 `soft_criteria` 失败 或任一 NFR 域 `CONCERNS` 或 overlay 命中（`oracle.source: 合成` 且 `confidence ≠ 高`）→ 至少 `CONCERNS`；全部 `通过` 且无域 CONCERNS 且无 overlay → 才可 `PASS`。`check` 会重算并与 `decision` 对账，自造档位必被拒。
4. **阈值不得猜测：** 未知阈值标 `UNKNOWN`（→ 该域 `CONCERNS`，该域不得 PASS）；`thresholds[].source` 只认「用户会话 `<date>`」，其余来源 `check` 拒收。证据不足写 `nfr.gaps`，不写猜测值。
5. **豁免只由人开：** `waivers` 8 键齐备且由用户裁定后才写入；未获裁定的缺口一律计 blocker。`安全` 域 FAIL 不可豁免。
6. **升级纪律：** 记录只追加，不重编号不重用；改既有记录往 `revisions` 追加 `{date, change, reason}`。**无 `--previous` 轮**——本技能从不整份重写既有文档（`gates[]` 按 `TG-###` 追加，无 ID 集合收缩面）。
7. **收尾路由：** `PASS` → 主线继续（`diy-review` / 发布准备）；`CONCERNS` → 列出 `recommendations` 与到期豁免；`FAIL` → 建议 `diy-correct-course`，或把缺口回 `diy-dev` 修复后重跑本门。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
