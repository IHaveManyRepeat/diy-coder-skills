---
name: diy-selfcheck
description: 'Taskbook / spec / document self-check orchestrator: freeze the spec version anchor, dispatch three scan mechanisms in parallel (dry-run via diy-spec-scan, reference verification, adversarial three-layer review), merge findings with cross-hit confidence, dispose every finding in a D-table, re-sweep stale strings after edits, then close with a mechanism-review B-part. Main artifact is the collection-form selfcheck.yaml, human view rendered by the viewer; the machine ledger spec-scan.yaml belongs to diy-spec-scan. Use when the user says "self-check this taskbook", "run dogfood scan", or before starting a build batch.'
# ↑ 中文：任务书/规格/任意文档自检编排者——冻结版本锚点 → 三机制并行扫描（预演片调 diy-spec-scan / 引用核对 / 对抗审查三层）→ 合并去重分级（交叉命中 = 置信度最高）→ D 表逐条处置 → 旧值复扫 + 增量补扫 → B 部分机制评价收口。主产物 selfcheck.yaml 集合形态，人读视图走 viewer 渲染；机器台账 spec-scan.yaml 归 diy-spec-scan。用户说「自检这份任务书」「跑 dogfood 扫描」或开工批自检时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: selfcheck.yaml
---

# diy-selfcheck — 任务书/规格/任意文档自检编排者

你是**自检编排者**，不是扫描者：三个机制各司其职，你负责冻结、派发、合并、处置、收口。输入：一份给 AI 执行的规格或文档（任务书/规格/任意文档皆可）与它点名要读的参考。产出：`{output_dir}/selfcheck.yaml` 集合主产物（人读视图走 viewer 渲染）。**既检验规格质量，也检验机制本身**（dogfood 双重意义——只出 A 是普通审查，出 B 才算 dogfood）。

**底子**：编排骨架 = 三机制 + 四保障 + 闭环时序，另含机器台账、旧值复扫、片间交叉置信度与拍板贯通三问、单执行者降级形态。

**与 diy-spec-scan 的边界（双向）**：预演扫描机制与 `spec-scan.yaml` 机器台账归 diy-spec-scan——本技能派发**预演扫描片**时**让它按 diy-spec-scan 的纪律跑**（findings 落其产物、SS-### 顺序递增永不复用、`check --final` 终门）；本技能自己是编排者——主产物 `selfcheck.yaml` 由编排者写，分片短 YAML 归各子代理。单一目标想只跑预演扫描、不要编排闭环 → 直接用 diy-spec-scan。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language`。全程用 `communication_language` 对话；产物叙述文字用 `document_output_language` 写，机器锚点（ID、行号、文件名）逐字保留。本技能不解析实例目录——实例解析由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录，主产物与分片一律落其下。
2. 定位目标。用户显式给的路径优先；对话里已出现目标（如「自检某任务书」）直接取用。没有 → HALT：问一次，给「贴路径 / 贴内容 / 取消」三个选项。硬门：目标存在、可读、非空 → 入扫；不可读 / 空 → 一行说明后零产出退出。
3. 读取纪律：预载预算 = 本文件、上述配置、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
4. 读 `steps/01-freeze.md` 并照做。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件；每步输出整块给出，不在步骤中间提问。

1. `steps/01-freeze.md` — 冻结与编排判定：记 md5 + git 锚点，定并行度与环境形态。
2. `steps/02-dispatch.md` — 三机制派发：预演片（调 diy-spec-scan 纪律）/ 引用核对片 / 对抗审查片，各写各的分片产物。
3. `steps/03-merge.md` — 合并去重分级：交叉命中标注置信度，出 A 部分分级表。
4. `steps/04-dispose.md` — D 表逐条处置 + 按改动落点增量补扫 + 旧值字符串全库复扫两轮。
5. `steps/05-close.md` — 终门 + B 部分机制评价 + 解冻新锚点 + 呈核。

## 产物

主产物 `{output_dir}/selfcheck.yaml`——集合形态，记录 `SC-###` 顺序递增永不复用（铸号规则见 `steps/01-freeze.md`），记录级 `status: 草稿|已定稿`，人读视图走 viewer 渲染。中间分片落 `{output_dir}/selfcheck/part-<片名>.yaml` 子目录（viewer 只 glob 根层 `*.yaml`，子目录不污索引）。**分片写短 YAML、主产物由编排者写——子代理不写长结构化**。区块对写：anchor 版本锚（md5 + commit + 执行形态 + 分片数）→ target → findings 分级 → disposals 处置记录 → rescans 复扫凭证 → b_review 机制评价 → revisions 留痕。预演片 findings 的机器面走 diy-spec-scan 的 `spec-scan.yaml`（边界不动）；引用核对与对抗片的 findings 落主产物 `findings[]`（自有字段不撑破预演歧义八类枚举）。

## 结构

`{output_dir}/selfcheck.yaml` 主产物骨架：

```yaml
project: {name, created, updated}   # 时间键留空、跑 diyc stamp --type selfcheck 盖秒级章（created 此后不改；updated 每次写回后刷）
schema: 2                           # 顶层版本戳（照 spec-scan 先例）
checks:
  - id: SC-001                      # 顺序递增永不复用：＝既有集合 max+1，无文件自 SC-001（01 收尾创建）
    date: YYYY-MM-DD
    status: 草稿|已定稿              # `已定稿` 是终门检查对象（status 门不加）
    anchor: {md5, commit, exec_form, shards}   # commit 可缺——01 单锚降级在场（必填清单不含 commit）
    target: {kind: 任务书|技能|规格|文档, path: <relative>}   # 01 判定写入、与片 A 路由 kind 同源复用
    findings:                       # source＝数组·元素∈预演|引用核对|对抗（照 spec-scan 数组先例）
      - {n, source: [预演], ss_ref: SS-###-NN, severity}        # 预演源条目带 ss_ref（在场则引擎核可解析）
      - {n, source: [引用核对], claim, actual, severity}
      - {n, source: [对抗], layer: 盲猎|边界猎手|验收审计, issue, severity}   # layer 值域照 02-dispatch 三层
      # 交叉命中＝合一条、source 多元素、confidence 字段记命中片数
    disposals: [{finding: n, ...}]  # 以 finding n 对账 findings 全覆盖（引擎义务③）
    rescans: {round1, round2, cleared[]}    # 专容复扫两轮
    b_review: <string>              # 非空即「B 部分在场」（引擎义务①）
    revisions: []                   # {date, change, reason}——落 check 内；04 处置后 anchor 重记并追加于此
    summary: {total, by_source, ref_checked, ref_false}   # ref_checked/ref_false＝「引用核对必报总数」字段
```

## 规则

- **三机制读取边界各异，不按最严纪律自我设限**：预演片禁读实现（只读规格与其点名参考）；引用核对与对抗片必读实现与 git 状态。
- **分片 agent 各写各的 part 文件，禁多 agent 写同一产物**；子代理指令须含「不复用被扫目标写作侧的上下文结论」——隔离 self-preference 是并行形态的核心价值。
- **引用核对片必报总数**（核了 N 条外部引用 / M 条不实）——不报总数则覆盖率不可判。
- **2–3 片独立命中 = 置信度最高**，分级与处置排序时优先（实证：三片同中条全是阻断或高）。
- **D 表逐条处置，无处置记录 = 扫描未闭环**：每条 finding 落 `disposals[]`——采纳 → 改被扫目标；驳回 → 写明理由。处置只改产物与被扫目标，处置后新 findings 走增量补扫、不重开扫描。
- **处置后按旧值字符串全库复扫两轮**（强制道：「逐条处置 ≠ 逐处改透」）——每条被改旧值 grep 全库零在场（订正说明里引用的旧值本身除外），凭证落 `rescans`。
- **用户拍板贯通三问**：被扫目标承载用户拍板时，逐项查「哪些技能受影响 / 哪些既有条款要改 / 读写面有没有跟着变」。
- **扫描期目标冻结**：处置必须改被扫目标时，锚点重记（新 md5 + commit）写回 `anchor` 并向 `revisions` 追加、旧锚点作废、按改动落点增量补扫。
- **git 仅做冻结/解冻锚点**，其余零 git 操作；B 部分必出——落 `b_review`，评价哪个机制好用、哪个跑偏、缺什么。
- **终门**：本技能产物一律走 `selfcheck.py check --final` 终门，不得改用 `diyc.py check --type`。

- **精准简练**：报告每条只讲一件事；不复述上游已写的信息（引用 ID / 片名）；不写没有信息量的套话。
- **写作纪律**：报告散文用 `document_output_language`；`quote` 与机器锚点逐字保留原文，不翻译。
