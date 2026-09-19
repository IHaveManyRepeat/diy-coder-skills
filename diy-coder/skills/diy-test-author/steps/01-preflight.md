# Step 1 — Preflight（探测与门禁）

Progress: `[Preflight] → Scope → Generate → Audit → Confirm → Finish`

**Read (input):** `author.py detect` 的回执；`{output_dir}/test-plan.yaml`（按 story / TC ID 定位读，不全文重推）。
**Write (output):** 无——本步只做只读探测与门禁判定；测试代码在 step 3 才落盘，拒绝路径零产出。

## 门禁（三查，任一不过 → 一行拒绝 + 零产出 + 路由）

1. **上游产物**：`{output_dir}/test-plan.yaml` 在场且 `project.status: final`。不满足 → 一行点名（文件名 / 当前状态），路由 **diy-test-design**。TC 由它写，author 不初始化、不补写。
2. **范围内 TC 在场**：本次要做的 TC 能在 `test_cases[]` 里按 ID 定位到。范围为空或全部非 `pending` → 一行报告「范围内无待处理 TC」+ 零产出，**不静默空跑**（范围判定在 step 2，此处只确认目标存在）。
3. **框架就绪**：`detect` 回执的 `framework` 非 null。

## 探测命令

```
python "{project-root}/.claude/skills/diy-test-author/scripts/author.py" detect --project-root "{project-root}" --output-dir "{output_dir}" --json
```

回执字段（决定 step 3 的落位与形态）：

- `framework` — `{name, detected_from}`，或 `null`（无框架）。
- `project_type` — `node` / `python` / `rust` / `go` / `java` / `ruby` / `php` / `unknown`。
- `test_dirs` / `existing_patterns` — 既有测试目录与测试文件（生成时沿用其命名与落位，**不引入第二套框架**）。
- `fixtures` — 既有 fixtures / 工厂目录与文件（工厂生成时优先复用，不重造）。
- `suggested` — 无框架时的建议（**仅供参考**）。
- `warnings` — 清单存在但不可解析等降级项，读作事实、写进摘要，不吞。

`framework: null` → 一行拒绝 + 路由 **diy-test-framework**（脚手架与依赖安装是它的职责）。本技能**不装框架、不改清单、不建脚手架**。

## 读与写的边界

- 只读：`{output_dir}` 下的 `test-plan.yaml` / `sprint.yaml` / `stories.yaml`（按 ID 定位），以及目标项目的测试目录与实现源码。
- 引用纪律：跨文档信息一律引用 ID（`S-x` / `AC-x.y` / `TC-x.y.z` / `FR-x.y` / `D-x`），**禁止复制内容**——测试代码与摘要里引用 TC ID，不把用例正文抄进注释。
- 写盘边界：**只写**目标项目内本次声明的测试文件；`{output_dir}` 下零写入（本技能无 YAML 写面）。目标项目与 `{output_dir}` 之外的写盘属保留确认类：交互式调用停下问用户；无头/循环调用经 `diyc.py defer-add` 入队 `{output_dir}/deferred-actions.yaml`（`reason: out-of-bounds`）后照常推进，不阻塞。

## Next

Read fully and follow `./02-scope.md`.
