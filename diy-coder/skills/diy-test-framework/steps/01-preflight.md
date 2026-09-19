# Step 1 — 前置校验（探测 + 门禁）

**Read (input):** `detect` 回执（`stack` / `existing` / `conflicts` / `suggested` / `templates` / `git` / `context`）；`{output_dir}/test-framework.yaml`——只在 Update 时按 `id:` 定位既有记录（不整份读）。
**Write (output):** 会话内的选型基线与前置结论；本步不写任何文件（记录 `草稿` 在 step 3 之前不落盘）。

## 1. 机械探测

```
python "{project-root}/.claude/skills/diy-test-framework/scripts/test_framework.py" detect --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `stack.type` ∈ `前端|后端|全栈|移动端`（移动端优先判定）；`stack.languages` / `stack.package_manager` / `stack.manifests` 是事实，**禁手推**。
- `existing.framework` / `existing.ci` = 项目既有基建；`conflicts` = 需要用户裁决的替换类冲突。
- `suggested` = 选型建议（框架 / 平台 / profile）；**建议不是结论**——step 2 由用户确认。
- `templates.framework_supported` / `templates.ci_supported` 为 false（当前 = 移动端面）→ **HALT**：一行报告「哪个栈、为什么无模板覆盖」+ 在回报/摘要登记，本技能零产出（禁 LLM 手写脚手架）。
- `git.repository` / `git.remote`：仓库事实（`ci` 模式的门禁之一，见 §3）。
- `context.docs` / `context.auth`：架构文档与 auth 线索（命中才列）。**逐份读进本次基线**——记下认证方式与对外 API 面，供 step 2 写 `framework.reason`、定 `BASE_URL` / `API_URL` / secrets 清单；读不出结论的落 `open_questions`，**别猜**。

## 2. 模式判定

- 用户要建框架/脚手架 → `框架`；要建 CI/流水线/质量门 → `CI`；两者都要 → `两者`。
- 说不清 → 停下问一次（给这三个选项），不猜。

## 3. 门禁

- **公共门**：`detect` exit 0（清单表命中）。exit 1 → 一行拒绝（缺项目清单）+ 路由「补 `package.json` / `pyproject.toml` 等清单后重入」，**零产出**。
- **冲突门**：`conflicts` 非空 → 停下把冲突摆给用户（源「已有冲突框架」HALT 保留，替换 = 内容决策）：
  - 用户确认替换 → 由用户在项目侧移除或改名旧文件后**重入**（旧路径此后记 `action: 新建`）；
  - 用户不改 → 冲突文件不写、不删、不覆盖，其余文件照常推进（摘要记明）。
- **CI 模式附加门**（仅 `mode=CI`；`mode=两者` 是同一会话内先 框架 段后 CI 段，不设前置门）：
  - **仓库门**：`git.repository` 为 false → **HALT**：一行报告「CI/CD 需要 git 仓库（源：Git repository required）」+ 路由「`git init` 后重入」，零产出。`git.remote` 缺失只记摘要一行（推送与平台侧触发由用户自办）。
  - **就绪凭据**：**满足任一条即过**——① 台账任一 `setups[]` 含 `kind ∈ {脚手架, 配置}` 的 `files[]` 条目且这些文件当前在场；② `existing.framework` 非空。两条皆不满足 → HALT + 一行报告 + 路由本技能 `框架` 模式（源「先跑 framework」保留）。

## 4. 记录草稿
按 Update/Create 分列：Update → 本次 `TF-###` = 既有最大序号 + 1（**稳定不重用**）；Create → `TF-001`。ID 由本会话铸造，引擎只校验格式与唯一性。

## 播报与下一步

读 `./02-select.md` 并照做。
