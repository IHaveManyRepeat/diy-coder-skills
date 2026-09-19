# Step 1 — 文档发现

Progress: `[文档发现] → 需求清点 → 覆盖校验 → UX 对齐 → 史诗质量评审 → 总评与定稿`

**Read (input):** 激活段那次 `collect` 的回执；回执清点到的文档。
**Write (output):** `{output_dir}/readiness.yaml` 里的草稿记录（`id` / `date` / `scope` / `status` / `findings` / `coverage` / `counts`）。

## 先过门（拒绝即零产出）

`collect` 已经跑过门。exit 1 时本轮在开始前就结束：转述回执的一行理由与它的 `gate.route`（diy-prd / diy-epics-stories），然后停下、什么都不写。拒绝永不成为记录；上游文档缺席，也绝不靠改评别的文档绕过去。

## 清点真实文档集

文档清单取自回执的 `docs` 块——不要手工重扫目录：

- `prd`、`epics`、`stories` —— 必须在场，且 epics/stories 的 `project.status: 已定稿`（门的要求）。
- `architecture` —— 可选：缺席以 warning 进回执；带进总评，不阻断。
- `design` —— 可选：缺席是合法状态；第 4 步判定 UX 是否被隐含并要求告警。

记录里的 `scope` = 实际清点到的文档，取 `[prd, architecture, epics, stories, design]` 的子集。

## 重复或游离版本（人的判断）

引擎只认规范文件名；其余都是对话式判读：

- 残留草稿（`*.prev`、`*.bak`、同名产物的带日期副本）、遗留 markdown 孪生（`prd.yaml` 旁边的 `prd.md`）、别的实例目录漏进本目录；
- 分片遗留文档（`prd.yaml` 旁边的 `prd/` 文件夹）——diy 的单一源是那个 YAML 文件。

把在场的东西点明，并先落定哪个版本权威，再开始评估。带着未落定的重复版本往前走是系统性失败（源 step-1 规则）；人定不了的重复版本落成一条带 `route` 的 finding，绝不静默选一个。

## 起草记录

向 `{output_dir}/readiness.yaml` 追加一条记录（文件缺席时新建：`project: {name, created, updated}`——`name` 取 `diy-coder.yaml` 的 `project.name`——外加空的 `checks` 列表与 `revisions: []`）：

```yaml
  - id: IR-001                    # 下一个 = 既有最大值 + 1，三位零填充；永不重编号、永不复用
    date: YYYY-MM-DD              # 今天（本条动作的日子）
    status: 草稿
    scope: [prd, epics, stories]  # 实际清点到的文档
    findings: []
    coverage: {must_frs: 0, covered: 0, gaps: []}   # 照抄回执
    counts: {frs: 0, nfrs: 0, epics: 0, stories: 0, acs: 0, findings_by_severity: {}}
```

计数与覆盖照抄回执逐字——机器锚点绝不凭记忆重打。

## 播报与下一步

读全 `./02-requirement-inventory.md` 并照做。
