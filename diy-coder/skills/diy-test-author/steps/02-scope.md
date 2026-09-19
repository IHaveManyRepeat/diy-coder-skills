# Step 2 — Scope（范围选择）

Progress: `Preflight → [Scope] → Generate → Audit → Confirm → Finish`

**Read (input):** `{output_dir}/test-plan.yaml` 的 `test_cases[]`（按 `ac` / `status` 定位）。
**Write (output):** 本场执行计划（TC 列表 → 目标文件）——只存在于对话与摘要，不落独立产物。

## 1. 范围选择（四种入口，用户显式指定的优先）

| 入口 | 形态 | 取值约束 |
| --- | --- | --- |
| story | `S-x` | 该 story 全部 AC 绑定的 TC |
| type | `unit` / `integration` / `e2e` | TC 的 `type` 字段 |
| priority | `P0` / `P1` / `P2` | TC 的 `priority` 字段 |
| 显式列表 | `TC-x.y.z,...` | 逐个校验存在 |

## 2. 范围与 `status` 的交集（机械）

**只取 `status: pending`** 的 TC——红相脚手架只覆盖「测试还没落地」的用例：

- `fail` 是**已激活**的测试：它已经有可运行的测试代码了，拿脚手架去覆盖等于把已有断言冲掉。
- `pass` 已收口，没有可做的。

筛选后范围内**无可做 TC**（全 `pass` / 空）→ 一行报告「范围内无待处理 TC」+ 零产出停止；绝不静默空跑、绝不新建 TC（追加 TC 归 diy-augment / diy-e2e-tests）。

## 3. 已有脚手架消重（幂等）

生成前先扫既有测试文件的 TC 锚（`TC: TC-x.y.z`）：**已有同 TC 锚的用例 → 跳过，不重复生成**，并在摘要里点名。锚是唯一的消重凭据——重复生成会落下内容相同的第二份文件，而 `audit` 判不出它（同锚跨文件不违例）。

## 4. 输出

一屏计划，逐 TC 一行：`TC-x.y.z → 目标文件（新建 / 已有锚跳过）`。给用户一句进度播报后直接进 step 3；范围本身是用户已给的输入，不再重复确认（缺输入时问一次）。

## Next

Read fully and follow `./03-generate.md`.
