# C·15 批保真度报告 —— diy-reverse init 骨架补两键（C·12 欠账清偿）

- 批次：C 阶段第 15 项（小批，清偿 `c12-fidelity.md` §五 W1-R1 欠账）｜ 完成日期：2026-10-02 ｜ 编制：lead
- 施工形态：**agent team（c15-batch）八工位任务列表序贯**——环境无子代理派发工具（与自检阶段登记一致），lead 兼全工位执行与 V 亲验，如实登记
- 任务书：`diy-coder/.analysis/2026-10-02-c15/taskbook-c15.md`（两裁 2026-10-02 用户定案：裁 1 = A 空串、裁 2 = B 链路级；呈核 1 项已裁「steps 扩面随批」；自检 D 表 8 项全采纳）
- 基线：HEAD `aa3b204`（§二十九，**1603 passed / 243 subtests**）→ 收口态 **1608 passed / 243 subtests**（归因闭合：C·15 **+2** 新锚用例；另 **+3** = C·7 未提交工作区改动——`test_design.py` +1 / `test_design_skill.py` +1 / `test_suite_texts.py` +1，逐文件 `def test_` 计数亲测）
- 本批改动：**4 文件**（`reverse.py` +2 键 +3 行注释 ｜ `steps/01-define.md` 两处 ｜ `steps/04-extract-tokens.md` 五处 ｜ `tests/test_diy_reverse.py` +37 行两用例）＋ `.claude` 源镜 3 文件（`sync.sh` 同步）——工作树未提交（待授权）
- 收口链：① 面内 **35 passed**（33 基线 + 2 锚）→ ② 对拍锚**逐字 SAME** → ③ `sync.sh` 49 技能冒烟 + 源镜 md5 **3/3 MATCH** → ④ 全量**停笔串行 374.02s 零红** → ⑤ 本报告 → ⑥ `迁移计划.md` §三十二 → ⑦ registry.yaml 零改动（链不变）

## 一、两裁定落地（§0）

| 裁定 | 落地 | 证据 |
|---|---|---|
| 裁 1 = A 空串 | `skeleton()`（reverse.py:163-164）`"form_factor": ""` / `"modes": ""`，位置 = `frontend_framework` 后、`tokens` 前（`tokens_doc()` 同拓扑） | 实跑骨架 YAML `form_factor: ''` 在场；键级锚断言两键在盘 |
| 裁 2 = B 链路级 | 链路锚用例：init 产物 → `design.py validate`（test_diy_reverse.py:366 同款形态：subprocess + `PYTHONIOENCODING=utf-8` + skipTest 护栏）；主锚 = `ok is False` ∧ 码集合 ⊇ {`FORM_FACTOR_MISSING`, `MODES_MISSING`}，rc=1 辅证 | **RED 阶段事实登记**：链路锚在补键前即绿（缺键≡MISSING 同码）——它是行为锁定锚而非 TDD 红锚，与裁 2 依据自洽；键级锚亲见红（`assertIn("form_factor", got)` 失败）后转绿 |

## 二、对拍锚（§2.2 硬判据，lead 亲跑）

补键前后「init → design validate」violations 各 **8 条**（6×EMPTY_FIELD + FORM_FACTOR_MISSING + MODES_MISSING），**code / where / msg 三字段及顺序逐字 SAME**：

- 前轮 = 开工基线重测（本会话，临时目录）；后轮 = 补键后紧邻轮。两轮间 `design.py` md5 `fc94b1f6…` 零漂移（C·7 窗口活跃，特记）。
- 结论：**键缺失 → 空串零行为漂移**（design.py:747/:754 空串≡缺失同码的直接实证），recon-w2 推论收口。

## 三、steps 文档面（呈核已裁随批；三处执行偏离如实登记）

| 文件 | 处 | 改动 |
|---|---|---|
| 01-define.md | :6 | 「三段空壳」→「五段空壳」+ 列举加两键 |
| | :68 | 「三段置空」→「五段置空」+「**不新增字段**」→「**不新增 schema 外字段**」（D-5 矛盾句）+ 括注两键空串依据 |
| 04-extract-tokens.md | :6 | Write 句「三段」→「五段」+ 列举加两键 |
| | 1.2 节 | 标题「另两项必填」→「**另四项**顶层必填」+ **两键填写时点 bullet**（D-6 时序缺口闭合：时点 = 本步〔step-04〕，值域 = design.py 判据，双模联动句） |
| | :32/:34 | 落盘句与检查点句列举加两键 |
| | 3.2 终门 | 括注「两键必填与值域判据**不在本引擎**，由 3.3 `design.py validate` 核」 |
| | 3.3 交叉核对 | 两键判据归属句（必填 + 值域 + 空串≡缺失同码） |

**执行偏离登记（vs 任务书 §1.2）**：

1. 任务书「三段空壳 → **四段**空壳」系计数笔误——3+2=5，实改「五段」（不留假事实优先于机械照抄）。
2. **3.2 终门句反向修正**：初稿曾将两键列入「--final 核」，即时核查证伪——`reverse.py check --final` **不核两键**（全脚本 grep 仅 skeleton :163-164 含两键）；终门判据改由 3.3 design.py validate 承载，防虚报引擎判据。
3. 04 实改**五处** vs 任务书列三处（+:34 检查点列举句属 B6 复扫面 + 1.2 标题计数句同批矛盾面）。

## 四、B6 复扫两轮（§7 固化道）

- 第一轮（机械旧值扫）：「三段空壳」「三段置空」「`frontend_framework` / `tokens` 旧并列模式」——`skills/ tests/ docs/` 全库**零命中**。
- 第二轮（语义复扫）：diy-reverse 面内「骨架/空壳」泛称句 9 处逐一判无矛盾（SKILL.md:41「既有 schema 的空壳」随 schema 演进自动涵盖，零改动申报维持）；外技能 4 文件（diy-analyze / diy-wds-brief / diy-wds-evolution 等）的「init 骨架」确认为各自引擎产物，语境无关。

## 五、多窗口实况（开工两项重测 + 施工中事件）

- 开工重测①节号：迁移计划.md 最高已落 §二十九、§三十 C·7 预留、§三十一 C·14 占 → §三十二 可用；②对拍锚基线 8 条重跑零漂移。
- **施工中事件**：C·7 窗口于本批全量前落下 §三十 登记段（迁移计划.md 1108→1112 行）；工作区 `design.py` 改动 = C·7 施工（pages[].meta 三键判据），与本批两键判据不相交——对拍锚前后 8 条逐字一致为行为级实证。
- 节号竞争收定：§三十一 = C·13/C·14 竞争中（C·13 taskbook:129 呈核待裁），本批**先收口锁 §三十二**（C·13 taskbook:6/:118 已明文认可「§三十二 已记 C·15」）。

## 六、验收清单对账（任务书 §2 八项）

| # | 验收 | 实况 |
|---|---|---|
| 1 | 面内绿（两锚在场） | ✓ 35 passed（含键级锚 + 链路锚） |
| 2 | 对拍锚逐字 SAME | ✓ §二（8 条，code/where/msg 及顺序） |
| 3 | 既有测试零改动 | ✓ :171 宽松循环未动、:179 键元组未扩（例外通道未启用） |
| 4 | sync 源镜零不匹配 | ✓ 49 技能冒烟 + reverse.py/01-define.md/04-extract-tokens.md 3/3 MATCH |
| 5 | 全量停笔串行零红 | ✓ 1608 passed / 243 subtests / 374.02s（归因闭合见卷首） |
| 6 | viewer 零改动 | ✓ 未触（两键渲染通道 C·12 已全套登记） |
| 7 | 文档面零自相矛盾 | ✓ B6 两轮 + 3.3 判据归属句后全流程终稿可过 validate（两码消解路径在场） |
| 8 | steps 零测试波及 | ✓ test_diy_reverse + test_diy_analyze 面 61 passed（路径硬读型断言零波及） |
