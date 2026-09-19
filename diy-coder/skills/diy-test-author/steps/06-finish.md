# Step 6 — 终门与路由（Finish）

Progress: `Preflight → Scope → Generate → Audit → Confirm → [Finish]`

**Read (input):** `audit` 回执（计数与 warnings）；本场计划里的文件清单与 TC 映射。
**Write (output):** 会话摘要（对话内，无独立产物）。

## 终门（机械判定，最后的门）

`--files` 带**本次全部**文件：

```
python "{project-root}/.claude/skills/diy-test-author/scripts/author.py" audit --files <本次文件> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

exit 0 是唯一放行；修掉每一条报告的违规并重跑。JSON 回执（含 `counts`）就是收尾证据——**不用**再跑一次别的检查（本技能不设 `check` 别名，终门就是它）。

## 会话摘要（对话内收尾，不建独立产物）

1. **文件清单**：新建的测试文件路径 + 行数，标注它承载的 TC（引用 ID，不抄用例正文）。
2. **TC 映射**：每个 TC → 覆盖文件 → `待办`（脚手架，全部 `skip`、不执行）。
3. **warnings**：`audit` 回执里的降级项、`detect` 的探测降级项、框架或环境问题——逐条列出，不吞。
4. **路由**：**diy-dev**（先去掉 skip 跑红，再实现）；框架缺口 → **diy-test-framework**；覆盖缺口 → **diy-augment**；无 TC 前提的探索式系统级需求 → **diy-e2e-tests**。

## 本步骤之后

- **无渲染步骤**：本技能没有 YAML 产物、也零 YAML 写入（测试代码落项目测试目录），viewer 无类型可渲染——不调用 viewer，不新增「打开浏览器 / 等待路径」交互点。
- 本文件是最后一个步骤文件，run 到此结束。新的范围 / 新 TC 需求 → 回 `./02-scope.md`，不必重跑探测（除非项目清单变了）。
