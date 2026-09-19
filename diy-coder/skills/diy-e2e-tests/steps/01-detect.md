# Step 1 — 框架探测与前置门禁

Progress: `[探测] → 目标 → 生成 API → 生成 E2E → 记录`

**Read (input):** `detect` 回执；`{output_dir}/test-plan.yaml` 与 `{output_dir}/stories.yaml` 的在场情况。
**Write (output):** 无——本步只做只读探测与门禁，不建任何产物。

## 硬门——上游产物优先

探测之前，先确认两个文件都在 `{output_dir}` 下：

- `test-plan.yaml` —— 追加目标。缺席 → 用例既无 AC 可绑，也无处落地。
- `stories.yaml` —— 每条追加用例的 `ac` 都要解析回它。

缺任一件 → 一行说明后停下：点名缺失的文件、说明追加目标未就绪、把用户路由到 **diy-test-design**（用例设计）——零写入，此检之外零探测。绝不新建空的 `test-plan.yaml`：本技能只追加，从不初始化。

## 探测框架

```
python "{project-root}/.claude/skills/diy-e2e-tests/scripts/e2e.py" detect --project-root "{project-root}" --output-dir "{output_dir}" --json
```

引擎按与语言无关的顺序读项目清单（`package.json` → `pyproject.toml` / `requirements*.txt` → `Cargo.toml` / `go.mod` / `pom.xml` / `build.gradle*` / `Gemfile` / `composer.json`），回报：

- `framework` —— `{name, detected_from}`；无声明时为 `null`。
- `project_type` —— `node` / `python` / `rust` / `go` / `java` / `ruby` / `php` / `unknown`。
- `test_dirs` —— 既有测试目录；`existing_patterns` —— 既有测试文件路径（要模仿的模式来源）。
- `suggested` —— `framework` 为 `null` 时推荐的框架。
- `warnings` —— 在场却解析不了的清单降级到这里；探测继续（绝不崩、绝不猜）。

**项目已有什么就用什么。** `framework` 有值时，采用它的 runner、文件命名与目录布局（取自 `test_dirs` / `existing_patterns`）——不引入第二套框架。

## 无框架 → 用户定夺

`framework: null` 是决策点，不是死路。把 `suggested` 摆出来（以 `project_type` 为理由），请用户确认或另点一个框架。**绝不安装任何东西**——不发包管理器命令、不改清单；安装是用户的决定，在本技能之外做。

用户的答复记进收尾摘要；只有确认之后才继续。拒绝即干净收场——目标特性清单与用例文件就此不产出。

## 交接

交接四项，各一行：确认后的框架、runner 命令、测试目录、文件命名模式——它们驱动第 3、4 步。

runner 命令取值顺序：① 项目自己的脚本（`package.json` 的 `scripts.test` / `Makefile` 的 `test` 目标 / 对应语言清单里的同名脚本）> ② framework 惯例命令（`pytest` / `npx playwright test` / `go test ./...`）> ③ 都取不到 → 交接行明写「按惯例推导」并记下命令原文（第 4 步的 runner 不可用分支据此上报）。

## 播报与下一步

读全 `./02-targets.md` 并照做。
