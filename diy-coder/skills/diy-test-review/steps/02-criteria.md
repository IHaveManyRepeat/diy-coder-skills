# Step 2 — 规则集与惯例基线（Criteria）

Progress: `Preflight → [Criteria] → Evaluate → Score → Report`

**Read (input):** `{skill-root}/criteria.yaml`（技能内静态资产）；`scan` 回执的 `baseline`；**仅当**判读 `bdd_naming` / `assertion_style` 时读回执 `baseline` 点名的采样文件。
**Write (output):** 草稿记录的 `convention_baseline` 区块。

## 1. 规则集加载

`criteria.yaml` 是**唯一权威表**（逐行留档自源 `criteria-registry.md`，35 行；M9 / M10 / L9 标 `disabled: true` 留档——私有库绑定裁剪，**有效 32 行**）：

- `severity` 读表，**不选**：命中的 severity 永远是行值；表里没有的行为只写散文建议（`recommendations`），不给 severity、不扣分。发明 severity 是评审的缺陷，不是测试的发现。
- `basis` 三类门：`必查`（每个文件都查）/ `视情况`（文件确实做该行为才查，读文件定，不看流行度）/ `惯例`（仓库确有此惯例才查）。
- `detect`：`mechanical` 行由 `scan` 直接产出（step 3 只做复核）；`semantic` 行由你判定。
- `dimensions` / `bonus_guard`：引擎的展示维度与 bonus 矛盾复核映射，**不在本步使用**，只解释判定为何如此。

## 2. 惯例基线解读（7 key）

`scan` 的 `baseline` 已在**评审集之外**的既有语料上采样（上限 40 文件，就近优先）。照抄进产物 `convention_baseline`，并分清两类键：

- **5 个机械键**（`priority_markers` / `test_ids` / `network_first` / `data_factories` / `fixtures`）：`{adopted, status}` 由 `scan` 判定，**你不自判、不复算**。阈值固定三行：`sampled < 4 → 未知`；`adopted == 0 → 缺失`；`adopted/sampled ≥ 0.5 → 已确立`，否则 `新现`。
- **2 个判读键**（`bdd_naming` / `assertion_style`）：源文明确无机械信号（没有单一 token 能区分命名风格或断言方言的"采用/未采用"）→ `scan` 只回 `judged_by: llm`。**你读采样文件判读**，照同一组三行阈值定 `status`，把 `{adopted, status}` 补进产物（`adopted` 要能对着采样文件数出来，不许估）。
- `baseline_unavailable`（评审集之外无语料）→ 7 键全 `未知`，所有 convention 行 `PASS (n/a)`；产物与摘要都写明基线不可得。**不得从评审文件自身推断惯例**（循环论证）。

## 3. convention 行的扣分表（照抄，判据只有这一张）

| status | 含义 | 对该文件的效果 |
| --- | --- | --- |
| `已确立` | ≥ 50% 且 corpus ≥ 4 | 按行值 severity 记违规，`note` 引采用计数 |
| `新现` | ≥ 1 且 < 50% | 降一档、floor `LOW`（引擎在 score 施加），`note` 说惯例尚未普及 |
| `缺失` | 0 个文件采用 | **不违规不扣分**，该行不成立、不得成条目 |
| `未知` | corpus < 4，样本不足 | **不违规不扣分**，同上 |

**下一步：读 `steps/03-evaluate.md`。**
