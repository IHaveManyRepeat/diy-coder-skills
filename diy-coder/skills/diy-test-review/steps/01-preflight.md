# Step 1 — 前置与文件发现（Preflight）

Progress: `[Preflight] → Criteria → Evaluate → Score → Report`

**Read (input):** `{project-root}/diy-coder.yaml`；本步骤文件；`scan` 回执。
**Write (output):** `{output_dir}/test-review.yaml` 的 `RV-###` 草稿（`status: 草稿`）。

## 1. 确认 scope

- 用户给了路径/目录/glob → 原样作为 `--paths`（可重复）。
- 用户只说"审一下测试" → 问一次范围（单文件 / 目录 / 全仓），不自行发明评审集。
- 只读的上下文（story / PRD / 变更源码）**不进评审集**：它只能加发现（如用例与其 AC 矛盾），不能豁免、不能降 severity、不能改分。要引用就写进 finding 的 `note`。

## 2. 跑 scan（发现 + 机械面 + 惯例语料）

```
python "{project-root}/.claude/skills/diy-test-review/scripts/test_review.py" scan --paths <P> [--paths <P>]... --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `exit 1` = **拒绝**（scope 内无测试文件）：转述一行理由 + 路由（`--paths` 指到测试文件/目录，或先跑 diy-test-author 产出测试代码），**零产出停止**。匹配不到任何规则得到的 100 不是 100。
- `exit 0`：回执即本步的全部机械事实——`files` / `excluded` / `mechanical` / `baseline`。

## 3. excluded 判定（三值，无第四种）

`scan` 已按三值分类，逐条核对理由是否成立（产物里照抄，不新增理由）：

- `格式不支持` — registry 没有谓词的格式（`.feature` / `.robot` / `.http`）：**不评分**，不是"通过"。
- `自动生成` — 带生成标记的文件（`@generated` / `DO NOT EDIT` 等）。
- `超出范围` — 路径不存在、不是测试文件，或**空测试文件**（剥掉注释后没有任何内容，`scan` 的 warning 写 `No tests found`）。

空文件是"匹配不到任何规则"的极端情形：它证明不了任何事，计入评审集就是让 `files_reviewed` 替它撒谎（"100 不是 100"）。**全部为空的 scope 走无测试文件的拒绝路径**（exit 1，零产出）。

任何"读者会以为它在评审集里"的文件都必须出现在 `excluded` 里——漏列等于报告替你说谎（"diff 里没有别的"）。同一个 path 不得同时出现在 `files` 与 `excluded`。

## 4. 起草记录

在 `{output_dir}/test-review.yaml` 追加一条 `RV-###` 记录（ID 续号，稳定不重用；文件不存在则按 Schema 建 `project` + `reviews` + `revisions`）。此步先落：`id` / `date` / `status: 草稿` / `scope`（`paths` / `files_reviewed` / `excluded`）。其余区块留给后续步骤填。

**下一步：读 `steps/02-criteria.md`。**
