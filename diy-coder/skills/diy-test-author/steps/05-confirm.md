# Step 5 — Confirm（静态确认与交接）

Progress: `Preflight → Scope → Generate → Audit → [Confirm] → Finish`

**Read (input):** 已过审计的文件集；`audit` 回执的 `counts`。
**Write (output):** 无——本步不写任何文件（脚手架在 step 3 已落盘）。确认时若发现形态问题，回 step 3 修后重跑 step 4 的 `audit`。

## 静态确认（不执行）

- 逐文件确认**每个** test 体都带 `skip`（step 4 的 `audit` 已机械判定，此处只做一次人工回读：抽样看形态，**不跑**）。
- 回执 `counts.tests` / `counts.tcs` 与计划对照：生成的用例数 == 范围内 TC 数（多一个少一个都要说清）。
- 交付门就是这两条：**全部 `skip` 且未执行**。跑测试不在本技能范围内——`skip` 的用例跑了也只会得到 `skipped`，产不出红相。

## 交接契约（一句话讲清）

**这些是待激活的测试源**：diy-dev 在实现前先去掉范围内测试的 `skip`，再跑红 → 写实现 → 跑绿——红相证据由那一步产生，不由本技能产生。

## 播报与下一步

Read fully and follow `./06-finish.md`.
