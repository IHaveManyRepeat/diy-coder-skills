# Step — 全量验收（[T] Acceptance Testing，场景级）

Progress: `[1 备料与起环境] → [2 四类判据逐条跑] → [3 记录问题与分流] → [4 报告与结论] → 路由`

**Read (input):** `{output_dir}/design.yaml` **该场景全部页**（各页 `states[].signals` / `prototype` / `implementation`）；本轮增量清单（哪些页、哪些单元是本轮新增）；项目可跑的命令（构建 / 开发服务器 / 测试）；用户在本文件各步的回答。
**Write (output):** 会话内的验收报告（逐页逐条 actual vs expected + `verdict`）与问题清单 + 分流结论。**不写 `design.yaml`**——状态迁移一律经 `transition`（`./wds-finalize.md`）。

**范围（B7b 裁定 10）**：**全量验收归本技能**——`diy-wds-evolution` 的 `[T]` 只验本轮增量（一轮一条改进）；本节验**该场景全部页 × 全部态**。判据四类同族（与 `diy-wds-evolution` 的 `test.criteria` 的 `kind` 词表一致），**不另铸词表**。

## 第 1 步 —— 备料与起环境（源 `steps-t/step-01-prepare.md`）

1. **判据清单**：逐页把 `states[].signals` 抄成可核对判据（一页一块，标 `SC-<nn>.P<n>`）。
2. **环境**：起开发服务器 / 构建产物 + 浏览器——**环境口径同 §2.6 门**（Playwright；不可用按裁定 21 停下上报，不静默降级）。
3. **回归面**：列出本轮改动影响到的既有页与共享件（token / 组件 / 路由）。

## 第 2 步 —— 逐条执行（源 `steps-t/step-02-execute.md`）

| 类 | 判什么 | 判据来源 |
| --- | --- | --- |
| `HP` | 阳光路径逐条走通、态按序切换 | 该页 `states[].signals` 的常态与交互项 |
| `REG` | 本轮改动未破坏既有页 | 改动前基线 + 既有页裸跑 |
| `EC` | 边界与异常（空态 / 错误 / 追加态） | `states[]` 的异常态 + `open_questions` 的已解决项 |
| `A11Y` | 键盘可达、触控目标 ≥44px、语义 HTML、对比度 | `design.py check` 回执的 `violations[].code`（`contrast` / `color-only-signal` / `semantic-html` / `a11y-touch-target` / `a11y-keyboard`） |

每条一行 `{criterion, how, expected, actual, verdict}`——`verdict` 只有 `通过` / `未通过`：**不写「大致符合预期」**（那样下一轮无从分辨是哪条起了作用）。

## 第 3 步 —— 记录问题与分流（源 `steps-t/step-03-document-issues.md`）

每条：现象 / 判据 ID / 复现步骤 / 归属。四路分流：

| 分流 | 去向 |
| --- | --- |
| **规格缺陷**（判据本身不成立） | 路由 `diy-design`（`states[].signals` 改由它写，经 `transition` 回修边） |
| **实现缺陷** | 回 `./wds-implement.md` 修完 → 重走浏览器门 → 重跑本节 |
| **缺页 / 偏题**（页面树就不对） | 路由 `diy-wds-scenarios` |
| **小修** | 就地修，不扩面（源 `NEVER refactor surrounding code`） |

## 第 4 步 —— 报告与结论（源 `steps-t/step-04` / `step-05`）

报告六行内：页数 / 判据条数 / 通过数 / 未通过数 / 分流去向 / 下一步。未通过 → 迭代回第 2 步；全过 → 出**「可呈用户批准」**的结论并呈报用户。

**不代用户批准**：`待验收 → 已批准` 是用户动作（经 `transition`），本步骤与 `diy-review` 都只出结论。

## 裁撤登记（源侧台账）

`data/testing-guide.md` / `test-result-templates.md` / `issue-templates.md` 三份模板与「问题票据」落盘面**裁**——判据真源是 `design.yaml`、报告落会话；diy 侧不建 `test-reports/` 散件（单一源纪律）。源侧 `## Progress` 设计日志章节（全流水线缺陷，5 技能 11 处）**裁**：进度真源 = `pages[].status`。

## 收尾与路由

全过且用户获批 → 该场景收口，转向下一场景 / 下一页（回 `./wds-implement.md`）。本文件到此结束，不再回头。
