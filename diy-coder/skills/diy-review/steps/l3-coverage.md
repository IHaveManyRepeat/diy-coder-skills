# Step — L3 覆盖审计（Coverage Audit）

**Read (input):** `test-plan.yaml`（已声明的覆盖）；`check --type review` 回执（本步与第 3 步块校验是同一条命令）。
**Write (output):** 台账 findings（点名 TC ID + 「声明 vs 记录」；`layer: 覆盖审计`）。

- **L3 覆盖审计。** 你不手动重验。跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type review --story <S-x> --json`——机械核对四项台账：每个 `test_refs` 的 TC 都有 `evidence` 条目；红线在绿线之前；证据结论与 test-plan 的 TC `status` 一致；绑定本任务的每个 TC 都带非空 `kill_target` 与对 test-plan schema 枚举合法的 `technique`（缺声明或出枚举 = 用例可能是装饰品——区分不了正确代码与它该杀的故障——点名 TC ID 报出）。本步时点 `review` 块尚未写、**其缺席不是违规**：此处回执里的每条违规都是台账 finding（`EVIDENCE_MISSING` / `STATUS_MISMATCH` / 声明类），按本条处置；块结构校验（verdict / layer / route 枚举、通过-失败一致性）发生在第 3 步写块后跑的**同一条命令**上。重开复审时，`test_refs` 里由 diy-augment 追加的后编码用例若无 `evidence`，`EVIDENCE_MISSING` 就是「该周期未重跑它们」的信号 → 挂 diy-dev 补 red/green，**不当豁免**。仍属目读的：TC 步骤是否真断言了 AC 的 then 子句。任何不一致——脚本报的或目读发现的——是一条点名 TC ID、声明与实际记录的 finding（AC-8.2）；回执 `known[]` 里的条目是用户已认可的基线，不是待修违规。
