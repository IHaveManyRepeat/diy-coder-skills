# Step 3 — framework 面脚手架（模板渲染 + 手改通道 + 命令执行）

**Read (input):** step 2 的取值表；`detect` 回执的 `stack`；技能内 `templates/framework/` 的**路径清单**（目录树即可，模板内容由引擎读）。
**Write (output):** `{output_dir}/scaffold-plan.json`（framework 面，会话临时文件）+ 项目内新文件 + 台账 `files[]` / `checks[]` 条目。

## 1. 写 plan

落 `{output_dir}/scaffold-plan.json`（**非产物**：不进 schema、不渲染、check 不校验在场；04 步覆写同一路径）：

```json
{"setup": "TF-001", "part": "framework",
 "substitutions": {"<模板头声明的占位符名>": "<取值>"},
 "files": [{"template": "framework/<profile>/<x>.tpl", "path": "<项目内相对路径>", "kind": "scaffold|config|script"}]}
```

- 模板目录 = stack/框架 profile（`browser-playwright` / `browser-cypress` / `backend-<语言>`）+ `shared/`（`tests-readme.md` / `env.example` / `nvmrc` / `python-version` / `scripts/` / `support-readme` / `gitkeep`）。
- 常见落点：框架 config（`playwright.config.ts` / `cypress.config.ts` / `pytest.ini` / `vitest.config.mts` …）、示例测试、`{{TEST_DIR}}/README.md`、`.env.example`、版本文件。
- **语言版本文件**（按语言取一个；Go 的版本在 `go.mod` 里，不另建）：`.nvmrc` / `.python-version` / `.java-version` / `global.json` / `.ruby-version`。
- **助手脚本**（`kind: script`，三个都下）：`scripts/ci-local.sh`（本地复现 CI）、`scripts/burn-in.sh`（抖动检测）、`scripts/test-changed.sh`（改动选测，要 `TEST_GLOB` / `BASE_BRANCH`）——模板在 `shared/scripts/`，产物第一行是 shebang。
- **`support/` 目录布局**（浏览器面）：`{{TEST_DIR}}/support/README.md` + 暂空子目录各一个 `.gitkeep`（`shared/gitkeep.tpl` 可多次落点，path 各写各的）——空目录只有这一条产生通道。**cypress 面另落 `{{TEST_DIR}}/support/e2e.ts`**（模板 `framework/browser-cypress/support-e2e.ts.tpl`）——那是 `cypress.config.ts` 的 `supportFile` 指向的文件，**不落则渲染出的配置指向一个不存在的文件**。
- `path` 一律**相对 + 正斜杠 + 无 `.` `..` 段**，同一路径不得重复；取值须覆盖所选模板声明的全部占位符。

## 2. 调用引擎（一次）

```
python "{project-root}/.claude/skills/diy-test-framework/scripts/test_framework.py" scaffold --plan "{output_dir}/scaffold-plan.json" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- exit 0 → `written` / `skipped` 是事实（`skipped` = 内容逐字节等价，**幂等重入**的常态，不是错误）。
- exit 1 + `FILE_CONFLICT` → 目标是既有文件且内容不同：**停下交给用户裁决**（移除/改名旧文件后重入，或把该 path 移出 plan）；回执 `rollback.removed` 是本次已撤销的写入——**别原样重试**。
- exit 1 + `ENUM_INVALID` / `MISSING_FILE` / `EMPTY_FIELD` → 修 plan（path 形态、模板名、取值）后重跑；此时**零写入**，项目无残留。

## 3. 既有配置文件 → LLM 手改通道

`package.json` 的 `scripts` / `devDependencies`、既有的 `build.gradle` 测试块一类文件**不在模板渲染面**（引擎只新写、不 merge）：由你按项目现状手改，最小改动、不做格式化重排，并把每个文件记进台账 `files[]`（`action: update`）。

## 4. 执行回执命令（自动化档）

`pending_commands` 逐条执行（无头/循环调用一致，不需确认）；结果记台账 `checks[]`：`{command, result: pass|fail, note}`。
- `result: fail` → `note` **必填**：环境面（安装报错 / 工具缺失）写清原因并继续；**产物面失败不在此步处置**（归 step 5 冒烟自检）。
- 装工具 / 配 secrets 一类人工处置项 → 会话摘要逐条列（AI 做不了的事）。

## 5. 台账字段（本步填）
`stack`（抄 detect 回执）/ `framework`（选型 + `reason`）/ `unit_layer`（mobile / fullstack 必填）/ `files[]` / `checks[]`。

## Next

读 `./04-pipeline.md` 并照做。
