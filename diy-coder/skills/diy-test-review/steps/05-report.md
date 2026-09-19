# Step 5 — 落盘与交付（Report）

Progress: `Preflight → Criteria → Evaluate → Score → [Report]`

**Read (input):** 定稿的 `RV-###` 草稿；`check` 回执。
**Write (output):** `{output_dir}/test-review.yaml` 定稿（`status: final`）；渲染；交付摘要。

## 1. 定稿

1. `recommendations`：每条针对一条真实命中写"改什么、改成什么"（如 `page.route` 换 `interceptNetworkCall`），不写"建议关注测试质量"。表里没有谓词的缺陷写在这里并注明注册表无对应行。
   **排序与上限**：先按影响力排——该意见所在维度的分 `< 70` 记 `HIGH`、否则 `MEDIUM`，`HIGH` 在前（无维度归属的行排最后），**只留前 10 条**。维度分见 `score` 回执；超 10 条 `check` 直接打回。
2. `open_questions`：推不出的判定（惯例语料不足、上下文歧义、要不要给 bonus 的边界情形）落这里，别用 `[ASSUMPTION]` 混过去。
3. 记录改 `status: final`；`project.updated` 改今天；全文档搜一遍 `[ASSUMPTION]`——本产物定稿禁止该字面量。

## 2. 终门

```
python "{project-root}/.claude/skills/diy-test-review/scripts/test_review.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`exit 0` 是唯一放行。它机械核对：schema / 枚举 / 账本自洽（findings 计数 → deductions → 行相加 → score/grade/recommendation → 维度分）/ `row` ∈ 有效 32 行 / `coverage_gaps` 形态与配型 / `walkthrough` 自洽 / `excluded` 理由三值 / `scope` 非空 / 零 `[ASSUMPTION]` / **convention 行的 `class` 与 `convention_baseline` 对表** / **`recommendations` ≤ 10 条** / **`scope.paths` 不含空测试文件**。违规就地修，重跑，不得跳过。

## 3. 渲染

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

静默执行，不进浏览器、不等路径、不阻塞。

## 4. 交付摘要

```
测试评审完成：RV-001
- scope：N 个文件（excluded M 个：unsupported-format x / generated y / out-of-scope z）
- 账本：CRITICAL a / HIGH b / MEDIUM c / LOW d → 扣分 D；bonus B
- 评分：S（grade G）→ recommendation R
- 维度：determinism .. / isolation .. / maintainability .. / performance ..

Must fix（CRITICAL）：
1. C1 tests/x.spec.ts:12 — <一句话：为什么这条用例证明不了任何事>

覆盖缺口（不进评分）：
- no_impl AC-1.1 → 建议 diy-dev；no_test AC-1.2 → 建议 diy-test-design；never_run TC-1.2.1 → 建议 diy-test-author
- walkthrough: full|partial|skipped（非 full 说明缺源与跳过类）

路由：recommendation=Block / Request-Changes → 先修测试代码再复审（修复归 diy-dev / diy-test-author）；Approve-with-Comments → 意见交用户定夺；缺口路由是建议，执行归对应技能。
```

`check` 的回执（含 counts）就是收尾证据；摘要里的数字全部取自回执，不手算。
