# Step 5 — 收口呈核（Close）

Progress: `冻结与编排判定 → 三机制派发 → 合并去重分级 → 处置与复扫 → [收口呈核]`

**Read (input):** D 表终态；处置后目标；片 A 的 `spec-scan.yaml` 记录。
**Write (output):** 定稿主产物 `{output_dir}/selfcheck.yaml`（`status` 草稿→已定稿、`anchor` 终值）。

## 终门

spec-scan 终态以 02 派发处初跑为准；本门＝selfcheck 自建终门：

```
python "{project-root}/.claude/skills/diy-selfcheck/scripts/selfcheck.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`exit 0` 唯一放行。本门＝selfcheck 六义务：`b_review` 必出 / 引用核对必报总数 / `disposals[]` 对账 `findings[]` 全覆盖 / `rescans` 两轮在场 / 全字段零 `[假设]` / `ss_ref` 可解析；片 A 机器面的 spec-scan 终态以 02 派发处初跑为准。

## 主产物定稿

区块对写：

1. **`anchor`**：所扫版本锚（处置前 md5 + commit → 处置后 md5 + commit）+ 执行形态（并行分片 / 单执行者，分片数；降级形态的诚实登记）。
2. **`target` ＋ `findings[]`**：判定结果与 Step 3 合并写面（分级 + 处置落点合并视图）。
3. **`disposals[]`**：逐条处置记录，无空行。
4. **`b_review`——对机制本身的评价**：哪个机制好用 / 哪个跑偏 / 缺什么 / 有无新教训值得固化进本技能。**B 部分必出**——只出 A 是普通审查，出 B 才算 dogfood。

## 解冻与呈核

- 解冻判据：终门 exit 0 + `disposals[]` 无空行 + 复扫第二轮零命中，锚核对对象＝`anchor` 字段。仍存未处置阻断 → 不解冻，回 Step 4 再循环。
- 呈核给用户：阻断清零情况 / 驳回条目及理由 / 观察项去向 / **待用户裁的项**（列「我定不了的」——目标 / 取舍 / 风险偏好类；有判据可推的技术细节不占用户决策带宽）。
- 解冻即开工准入：主产物 `{output_dir}/selfcheck.yaml` = 开工证据，随批归档。

## 播报与下一步

这是最后一个步骤文件——呈核完毕本轮结束。主产物与分片产物留在 `{output_dir}`，不再读任何 `steps/` 文件。
