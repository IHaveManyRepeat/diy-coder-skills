# Step 3 — 逐文件评估与三向走查（Evaluate）

Progress: `Preflight → Criteria → [Evaluate] → Score → Report`

**Read (input):** 回执 `files` 里的**全部**评审文件；`criteria.yaml` 的 `semantic` 行（判定谓词）；`baseline` 采样文件（仅判读键）。
**Write (output):** `{output_dir}/test-review-findings.json`；草稿记录的 `coverage_gaps` 与 `walkthrough` 区块。

## 1. 机械项复核

`scan` 的 `mechanical` 列表是机械集的**唯一来源**（可扩不可缩）。逐条核实后原样转为 findings（row / file / line / note 照抄，`line: null` 只许出现在文件级行 H5/H6/H7/H8/L4）。发现误报（例如 C1 豁免行）就丢掉该条并在摘要说明；**不许新增表外机械行**。

## 2. 语义项判定（`detect: semantic` 的行）

逐文件读，问一句："这条规则的谓词在这个文件里成立吗？"

- **severity 不填**——引擎按表复算。
- **convention 行必须带 `class`**（`已确立` 或 `新现`，照 step 2 的键值）；`缺失` / `未知` 时该行不成立、**不得成条目**。`class` 不是判断，是**引用**——它与产物 `convention_baseline.keys.<convention_key>.status`（键名取 `criteria.yaml` 行的 `convention_key`）是同一件事的两处写法，`check` 会逐条对表，不符即拒（引用与实际语料独立复测）。
- `视情况` 行先问门开没开（文件是否真的 navigate / 是 Maestro flow / 有时间边界值……）；门关 = `PASS (n/a)`，不是 WARN、不扣分。
- 表里没有谓词的真实缺陷 → 写进 `recommendations` 的散文，不给 severity、不扣分，并说明注册表没有对应行。
- **空 / 极简文件**（`scan` 的 warning 带锚串）：空文件已归 `excluded` 不评分（不得为它编 findings）；**极简文件**（有内容零断言）按 C4 成条目，`note` 用 `No meaningful tests` —— 用例声明得再多，零断言就是一个不可能失败的用例，分数必须反映内容缺失。
- **pact 附加上报**（`scan` 的 warning，均属"注册表无此行"）：单 `it()` 内 >1 个 `addInteraction()`（Rust FFI 会非确定性丢 interaction）须写进 `recommendations` 散文；配置经 `mergeConfig` / `extends` 组合致三条必需设置不可验证时，`scan` 已按 L4 记账（分类名 `pact-config-unverifiable`），`note` 引它并给出两条出路（叶子配置内联 / `// tea:pact-ffi-safe` 标记）。
- 判定要顺着"这条测试能不能失败、失败会不会指错地方"想：被禁用的用例（C1）、恒真断言（C3）、零断言（C4）、自证 mock（C5）、不可达断言（C6）、条件断言（H3）、共享状态（H4）、硬等待（H1）……四条 CRITICAL 之外的语义档同理，只是代价不同。

**四维评估视角**（源四个 worker 的视角清单保留；顺序走查，不派子代理。行↔维度映射见 `criteria.yaml` 的 `dimensions` 字段，维度分由引擎算、你只借用视角不漏判）：

| 视角 | 问什么 | 行 |
| --- | --- | --- |
| determinism 确定性 | 这条用例的结果能不能复现？失败会不会是随机的？ | C1-C4 / C6 / C7 / H1-H3 / H6-H8 / L4 |
| isolation 隔离性 | 用例之间会不会互相污染？任何一条能不能单独跑？ | C5 / H4 / M4 |
| maintainability 可维护性 | 半年后改这里的人能不能看懂、改对、定位失败？ | M2-M5 / M7 / H5 / L1 / L3 / L5-L7 |
| performance 性能 | 这条用例是不是在用时间换确定性、或让失败定位变慢？ | M1 / M6 / H5 |

H9 / M8 / L2 / L8 不归任何维度（源表原样）——撞见就按行判定，别硬塞进视角里。

**findings 载体**（单份覆盖式工作文件；评分后保留留痕，下次评审覆盖）：

```json
{"findings": [{"file": "tests/api.spec.ts", "line": 42, "row": "H1", "class": null, "note": "裸计时器排序步骤"}],
 "bonus": [{"key": "完全隔离", "points": 5, "note": "全文件无共享可变状态"}]}
```

- `note` 与额外键不参与计分；**severity 不在输入面**（写了也不计分，引擎复算）。
- 同一 `(file, line, row)` 只写一次（机械项与语义项撞车时归并为一条）。
- **bonus 六类**（`优秀 BDD` / `完备夹具` / `数据工厂` / `网络优先` / `完全隔离` / `测试 ID 完备`）：review 级判定，须**跨本次全部评审文件**成立才给 5，否则 0，**无部分分**。给 5 而对应规则行有命中 → 引擎判矛盾违例，别写进去。

## 3. 三向走查（必跑）

```
python "{project-root}/.claude/skills/diy-test-review/scripts/test_review.py" walkthrough --project-root "{project-root}" --output-dir "{output_dir}" --json
```

AC 面 = `stories.yaml` 全量 AC（须定稿）；源码面 = 委派 `diyc.py trace`（不重写扫描）；TC 面 = `test-plan.yaml` 的 `ac` 绑定与 `status`（须定稿）。四类缺口照抄进产物 `coverage_gaps`，路由是**建议**：

| kind | 含义 | 建议路由 |
| --- | --- | --- |
| `无实现` | AC 从未出现在 `# trace:` 引用的 AC ID 中（项目全量零 trace 标记时整类跳过） | diy-dev |
| `无测试` | AC 无 TC 绑定 → diy-test-design；有 TC 但全 `待办` → diy-test-author | 见左 |
| `孤儿用例` | TC 的 `ac` 不可解析（委派 `diyc check --type test-plan` 转记） | 用户 |
| `从未运行` | TC `status: 待办`（含红相脚手架产出） | diy-test-author |

`walkthrough.status` 照抄：`全覆盖`（四类全评）/ `部分覆盖`（缺源跳过若干类）/ `已跳过`（三源全缺）；非 `全覆盖` 时 `note` 记缺源与跳过类。**走查不进规则集评分**——它是覆盖缺口，不是测试代码质量违规。

**下一步：读 `steps/04-score.md`。**
