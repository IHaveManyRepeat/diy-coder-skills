# Step 3 — Generate（按 TC 生成测试代码）

Progress: `Preflight → Scope → [Generate] → Audit → Confirm → Finish`

**Read (input):** 本场计划里的每个 TC（`title` / `steps` / `technique` / `kill_target` / `type` / `priority`）；该 story 的 AC（`stories.yaml`，按 ID 定位）；`detect` 回执的 `test_dirs` / `existing_patterns` / `fixtures`。
**Write (output):** 目标项目测试目录下的测试代码文件（**新建**）——**本次交付的主要产物**。

## 1. 按 TC 的 `type` 分派

| type | 形态 | 纪律 |
| --- | --- | --- |
| `unit` | 纯逻辑：函数/类的输入 → 输出断言 | 不依赖外部进程与网络；边界值取 min-1/min/min+1 |
| `integration` | 跨模块/产物：真实依赖参与（文件、子进程、DB） | 用夹具建真实前置，不 mock 掉被测接缝 |
| `e2e` | 端到端旅程：由 runner 或操作者驱动 | 关键快乐路径 + 1–2 条异常路径；语义定位（`getByRole` / `getByLabel` / `getByText`），禁 CSS / XPath；network-first（拦截声明写在导航之前）；禁 `waitForTimeout` / `sleep`，用事件或状态等待 |

同一行为**不跨层级重复覆盖**：TC 的 `type` 已由 diy-test-design 定好，照做——author 不重新分层。

## 2. 每个用例的骨架

1. **锚注释**（上方一行）：`TC: TC-x.y.z`，C 族写 `// TC:`——与 diy-dev 的 `# trace:` 形态区分，是 diy-dev 定位待激活测试、`audit` 核对 TC 范围的唯一凭据。
2. **断言期望行为**：oracle 从 AC 与 TC 的 `steps` 推导，写清「预期结果」。**禁占位断言**（`expect(true)` / `assert True` 一类）——失败也分不出对错的断言是装饰品。
3. **单断言原子**：一个用例一条断言，多断言拆用例。
4. **`kill_target` 可回读**：用例打的是 TC 声明的那个故障假设；打不中说明用例没对准，回去改用例而不是加断言。
5. **数据走工厂**：禁硬编码业务数据（邮箱 / 口令 / 账号等字面量），用 `detect` 命中的既有夹具或新建工厂生成。
6. **用例名带优先级标签**：`[P0]`–`[P3]` 取自锚定 TC 的 `priority`（`'[P0] 边界值被拦截'`）——标签跟随 TC，不符即改标签；名字同时说清被测行为与期望，禁 `test1` / `example` 一类占位名。py 的 `def` 名带不了方括号，标签落 `def` 行尾注释或上方注释 / 文档字符串。
7. **Given-When-Then 三行结构注释**（写进用例体内）：`// Given …` / `// When …` / `// Then …`（py 用 `#`）——一屏看懂前置 / 动作 / 期望（源把 GWT 列在三层共用的硬纪律上）。
8. **确定性隔离**：禁跨用例共享状态（顶层 `let` / `var`、函数内 `global`）、禁顺序依赖（`test.describe.configure({ mode: 'serial' })` / `@pytest.mark.dependency` 一类）、用例体内禁随机与时钟源（`Math.random()` / `Date.now()` / `random.*` / `datetime.now()`）——数据走工厂（固定种子）、时钟靠注入，同输入必须同结果。
9. **测试逻辑不包 try-catch**：失败就让它失败；只有清理动作（`delete` / `cleanup` / `close` 一类）可包 `try`。
10. **禁调试语句**：`console.log` / `print` / `debugger` 不进测试代码（写进注释不判）。

## 3. 红相形态

test 体**全部 `skip`**（`skip` = 待实现标记，不是跳过不管）＋ 实现指引注释（点名要实现的位置与命令，供 diy-dev 照做）；**不执行**。断言仍要写——红相脚手架的价值就在"实现前先把期望说清"。

## 4. 落位与命名

沿用 `test_dirs` 与 `existing_patterns`：目录、文件后缀、命名风格照项目既有约定，**不新增目录结构、不换框架**。夹具/工厂落在既有 `fixtures` 命中目录（没有则按项目约定新建）；**夹具自建的数据必须自带 teardown 清理**——JS 在 `await use(data)` 之后删除、py 在 `yield` 之后删除（源「auto-cleanup (delete created data)」，`audit` 判 `FIXTURE_NO_TEARDOWN`；纯生成器的工厂没有 setup/teardown 相位，不受牵连）。**单文件行数不超上限**（`audit` 会判 `FILE_TOO_LONG`），超了拆文件。

## 5. 写盘边界

只写目标项目内的测试文件（+ 既有 `fixtures` 目录内的新工厂）；`{output_dir}` 下本步零写入。越界写盘属保留确认类（交互式问用户；无头经 `diyc.py defer-add` 入队不阻塞）。

## Next

Read fully and follow `./04-audit.md`.
