# Step 4 — Audit（纪律审计，不过即修）

Progress: `Preflight → Scope → Generate → [Audit] → Confirm → Finish`

**Read (input):** **本次**生成的文件集（一个不漏）；`audit` 回执。
**Write (output):** 无——`audit` 只读；不过即改代码后重跑（改的是 step 3 的文件）。

## 命令（`--files` 只带本次文件集）

```
python "{project-root}/.claude/skills/diy-test-author/scripts/author.py" audit --files <本次文件> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- **禁「全测试目录」缺省**：历史文件不进场——`--files` 是本次会话生成的文件集。
- **不设 `check` 终门别名**：终门就是 `audit --files <本次文件集>` exit 0（本技能没有第二套机械判定，别名会让「终门跑哪个」变成猜谜）。

## 判定面（exit 0 唯一放行）

三项一起判，任一处 exit 1 都要修：

1. **上游门禁**：`test-plan.yaml` 在场且 `已定稿`；每个 TC 锚可解析到既有 TC；锚定 TC 的 `technique` / `kill_target` 非空、`status` 为 `待办`——上游带病时这里先拦下，不靠"上游应该没问题"。
2. **规则集**：占位断言 / CSS 与 XPath 定位 / 硬编码业务数据 / 无断言 / 多断言 / `waitForTimeout` 与 `sleep` / `isVisible()` 条件流 / page object 类 / 文件行数超限 / 用例名（优先级标签与可读性）/ Given-When-Then / 顺序依赖与共享状态 / 用例体内的随机与时钟源 / try-catch 包测试逻辑 / 调试语句 / 夹具 teardown 清理。
3. **红相形态**：每个 test 体含 `skip` + 每个用例带 TC 锚（本次新生成文件，无遗留豁免）。

## 修法对照（不猜词义）

| 违规码 | 修法 |
| --- | --- |
| `PLACEHOLDER_ASSERTION` | 换成对准 `kill_target` 的期望行为断言 |
| `MISSING_ASSERTION` / `NOT_ATOMIC` | 补断言，或按行为拆成多条原子用例 |
| `BRITTLE_SELECTOR` | 换 `getByRole` / `getByLabel` / `getByText` 语义定位 |
| `HARDCODED_DATA` | 换工厂 / faker 生成；字面量留在工厂配置里 |
| `HARD_WAIT` / `CONDITIONAL_FLOW` | 换事件或状态等待；可见性分支换成断言 |
| `PAGE_OBJECT` | 拉平为直接用例（选择器与断言写在用例里） |
| `SKIP_MISSING` | 给该 test 体补 `skip`（红相脚手架必须全部 skip） |
| `ANCHOR_MISSING` / `UNKNOWN_ID` | 补/改 TC 锚；锚必须指向既有 TC |
| `STATUS_MISMATCH` / `EMPTY_FIELD` | 上游问题：TC 不在 `待办`、或字段缺失——不在这里修上游，回 step 2 改范围或路由 diy-test-design |
| `PRIORITY_TAG_MISSING` / `PRIORITY_TAG_MISMATCH` | 用例名补/改 `[P0]`–`[P3]` 标签，取值抄锚定 TC 的 `priority` |
| `NAME_UNDESCRIPTIVE` | 用例名换成「行为 + 期望」（`[P0] 边界值被拦截`），删 `test1` / `example` 一类占位名 |
| `GWT_MISSING` | 用例体内补 `Given` / `When` / `Then` 三行结构注释（py 用 `#`） |
| `ORDER_DEPENDENCY` / `SHARED_STATE` | 去掉 `serial` 与跨用例可变状态；每条用例自建前置、任意顺序可跑 |
| `NONDETERMINISTIC_SOURCE` | 随机 / 时钟移进工厂或注入（固定种子），用例体只消费；同输入同结果 |
| `TRY_CATCH_TEST_LOGIC` | 拆掉 try-catch 让断言失败即失败；只有清理动作留在 `try` 里 |
| `DEBUG_STATEMENT` | 删 `console.log` / `print` / `debugger`；要留证据就写进断言 |
| `FIXTURE_NO_TEARDOWN` | 在 `await use(data)` / `yield` 之后补删除自建数据 |
| `FILE_TOO_LONG` | 按层级/故事拆文件 |

回执的 `warnings` 若有内容，逐条写进 step 6 的摘要。

## 播报与下一步

Read fully and follow `./05-confirm.md`.
