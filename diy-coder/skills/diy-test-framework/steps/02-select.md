# Step 2 — 选型与 substitutions 取值表

**Read (input):** step 1 的 `detect` 回执；`{output_dir}/test-plan.yaml` 的 `static_checks[]`（**按 `order` 定位**取 阻断 层 `tool`，不整份读）。
**Write (output):** 会话内的选型结论 + substitutions 取值表（两张 plan 共用；step 3/4 落进 plan）。

## 1. 框架选型（源 step-02 规则）

- `前端` / `全栈` → 默认 **Playwright**（大仓库 / 多浏览器 / API+UI / CI 并行要快）；小团队 DX 或组件测试重心 → **Cypress**（profile `browser-cypress`）。
- `后端` → 按语言：node `vitest`、python `pytest`、java `JUnit 5`、go `go test`、dotnet `xUnit`、ruby `RSpec`、rust `cargo test`、php `PHPUnit`。
- `移动端` → 模板面不支持（step 1 已 HALT）：Maestro + 单元层的选型只作为报告结论，不生成文件。
- `existing.framework` 与建议不同 → 先问用户（替换属内容决策；无头不替用户默认）。

## 2. 平台选型
`existing.ci` 命中 → 建议沿用；否则在五平台（`github-actions` / `gitlab-ci` / `jenkins` / `azure-devops` / `harness`）里问用户选一个；用户明确不建 CI → `platform: none`（台账照记，check 给 warning）。

## 3. substitutions 取值表（模板头 `# placeholders:` 是唯一权威）

- `RUNTIME_SETUP_CMD`：运行时准备**单行**命令（如 `nvm install 22 && nvm use 22`、`python -m pip install --upgrade pip`）。
- `INSTALL_CMD` / `LINT_CMD` / `TEST_CMD` / `BROWSER_INSTALL`：与项目包管理器一致的命令。
- **阻断 层命令是硬约束**：`static_checks[]` 中 `gate: 阻断` 的 `tool` 整串 → 逐字进 `LINT_CMD`（check 按「空白归一化 + 独立命令形态」在 CI 文件里找它；写成 `lint:fix` 一类会判 `CI_MISALIGNED`）。多条 阻断 条目按 `order` 升序用 `&&` 串成一条命令（`&` 属匹配边界，故逐条仍可独立命中）。**按 `order` 引用，禁把命令内容抄进台账**。
- `P0_GATE` / `P1_GATE`：固定 `100%`（质量门口径拉满；源 P1≥95% 已作废）。
- 版本与文档类：`NODE_VERSION` / `PYTHON_VERSION` / `JAVA_VERSION` / `RUBY_VERSION` / `DOTNET_SDK_VERSION` / `FRAMEWORK_NAME` / `TEST_DIR` / `BASE_URL` / `API_URL`。
- 语言特定：`TEST_PACKAGE`（java）/ `PACKAGE_NAME`（go）/ `CRATE_NAME`（rust）/ `TEST_PROJECT_NAME`（dotnet）。
- 取值给不出（lint 工具未定、地址未定）→ 停下问用户，**别编**；一个值填空会让 `scaffold` 整条拒绝（`EMPTY_FIELD`）。
- `static_checks` 缺席或为空 → 无对齐对象：`LINT_CMD` 按项目既有 lint 取，并在摘要记明「无 static_checks，CI 对齐未生效」。

### 3.1 缓存 / 产物 / 通知（`ci` 面必填；模板头为准）

| 占位符 | 口径 | 取值（示例） |
| --- | --- | --- |
| `CACHE_PATH` | 依赖缓存路径 | node `~/.npm`；python `~/.cache/pip`；java `~/.m2/repository`；go `~/go/pkg/mod`；dotnet `~/.nuget/packages`；ruby `vendor/bundle`；rust `~/.cargo/registry`；php `~/.composer/cache` |
| `CACHE_KEY` | 缓存键，**必须含锁文件哈希** | GHA `deps-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}`；Harness `cache-{{ checksum "package-lock.json" }}` |
| `CACHE_RESTORE_KEYS` | 回退键前缀（仅 GHA / Azure 有此概念） | 把键去掉哈希段：`deps-${{ runner.os }}-` |
| `CACHE_LOCKFILE` | 锁文件路径（**仅 GitLab**，喂 `cache:key.files`） | `package-lock.json` / `poetry.lock` / `go.sum` / `Gemfile.lock` / `Cargo.lock` |
| `BROWSER_CACHE_PATH` 等 | 浏览器缓存的同名三件套（浏览器面） | `~/.cache/ms-playwright`；Harness 的路径须落在 `/harness` 下 |
| `REPORT_PATH` | 失败产物的报告目录（浏览器面） | playwright `playwright-report/`；cypress `cypress/` |
| `NOTIFY_SECRET` | 失败通知的秘密**名**（不是值） | `SLACK_WEBHOOK_URL`（缺省） |
| `CI_PLATFORM` / `CI_FILE` / `CI_PLATFORM_SECRETS_UI` | 文档面：平台名 / 流水线文件 / 秘密配置入口 | GHA `Repository Settings → Secrets and variables → Actions`；GitLab `Project Settings → CI/CD → Variables`；Jenkins `Manage Jenkins → Credentials`；Azure `Pipelines → Library → Variable groups`；Harness `Project Setup → Secrets` |

- 缓存键只认锁文件（不写时间戳、不写分支）：锁文件变才换键——键写法直接决定命中率。
- **Jenkins 无声明式缓存原语**：`CACHE_PATH` / `CACHE_KEY` 落在模板注释里（约定口径），不写进 `sh` 步骤。

## 4. 报给用户
一行选型：框架 + 平台 + profile + 理由；用户确认后才进 step 3。

## 播报与下一步

读 `./03-scaffold.md` 并照做。
