# Step 1 — 定位与切分（Collect）

Progress: `[定位与切分] → 预演执行 → 穷举 → 交叉验证 → 落盘与交付`

**Read (input):** 目标路径（激活段定下的）；引擎 `collect` 的回执。
**Write (output):** `{output_dir}/spec-scan.yaml` 的草稿记录（`id` / `date` / `target` / `units`）；给用户的进度播报。

## 跑引擎

```
python "{project-root}/.claude/skills/diy-spec-scan/scripts/spec_scan.py" collect --target "<目标路径>" --project-root "{project-root}" --output-dir "{output_dir}" --json
```

回执给出：目标文件清单（相对路径 + 行数）、每个文件按 `## ` 二级标题切出的**单元名**、总计。

`ok: false` → 把违规码与消息转述给用户，零产出停止（这是拒绝路径，不是记录）。

## 定目标类型

`target.kind` 四选一：任务书 | 技能 | 规格 | 文档（引擎不给，照三阶判据链判，不开放现场裁量）：

1. **用户明示 kind → 照录**。激活段或对话中用户点名，直接采用。
2. **规则表机械判**。体系内产物查对照表定归（下表，查到即归、不代判）；体系外用结构判兜底——`SKILL.md`+`steps/` → 技能；名字含 prd/epic/story/架构 → 规格；带分工施工指令 → 任务书；无执行结构（无可预演 duties）→ 文档。
3. **模糊档 → 先问一次**。前两阶走完仍模糊（表外产物、结构信号互相打架），AI 不代判，停下来问用户。

**体系产物→类型对照表**（封闭世界，产物真名以代码为准）：

| 类型 | 体系产物 |
| --- | --- |
| 规格 | prd / brief / prfaq / epics / stories / architecture / openapi / design / test-plan / spec / story-context / change-proposal / project-context；WDS 四产物 trigger / scenarios / system / brief。prfaq / story-context / change-proposal / project-context 从紧归规格 |
| 技能 | SKILL.md / steps / 模板与教学资产 |
| 任务书 | taskbook* |
| 文档 | sprint / review / mutation-report / selfcheck / spec-scan / investigation / research / retrospective / checkpoint / editorial-review / readiness / WDS assets 清单 / evolution |

## 调整单元粒度

引擎按二级标题切单元，这是**起点不是终点**。两条调整纪律：

1. **合并过碎的单元** —— 短于 15 行的连续单元可并成一个（连续的标题行、一两句话的小节等）。单元的意义是"一段可独立预演的执行指令"，不是标题计数。
2. **拆分过大的单元** —— 单单元超过约 150 行时按三级标题再切，否则预演时会滑过细节。

调整后的单元清单必须**覆盖全部正文**：每个文件的所有行都要落进某个单元，或被显式标为"非规格正文"（目录、参考文献、附录索引）。覆盖是唯一的防漏扫凭证。

## 落草稿记录

创建 `{output_dir}/spec-scan.yaml`（文件不存在时建：`project: {name, created, updated}`——`created`/`updated` 留空，建文件后跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" stamp --type spec-scan --json` 盖秒级章、每次写回产物后再跑一次；`name` 取自 `diy-coder.yaml` 的 `project.name`——加顶层 `schema: 2` 版本戳、空的 `scans: []` 与 `revisions: []`），追加一条：

```yaml
  - id: SS-001            # 下一个 = 已有序号最大值 + 1，三位零填充；不重编不重用
    date: YYYY-MM-DD        # 本次扫描的日子，不随 project.updated 变
    status: 草稿
    target: {kind: <判定值>, path: <相对路径>, files: N, lines: N}
    units:
      - {unit: <单元名>, path: <相对路径>, lines: N, scanned: false}
    findings: []
    summary: {total: 0, blocker: 0, major: 0, minor: 0, units_total: N, units_scanned: 0}
    open_questions: []
```

`units` 先全部写 `scanned: false`，预演在场时 step 2 每扫完一个改成 `true`（纯文档路由由 step 3 接管改标）——这是覆盖凭证，不是装饰。

## 播报与下一步

给用户一句话：目标是什么、切出多少个单元、总共多少行、下一步去向（纯文档 → 穷举，其余 → 预演）。

`kind` 判为 `文档` → 读全并照做 `./03-exhaustive.md`（纯文档路由：跳过 02 预演，`scanned` 由 03 接管）；其余照旧 → 读全并照做 `./02-dry-run.md`。文档轻扫口径（03 照此执行）：不整篇预演，只扫两类——①规范性语句（「须／禁止／唯一／优先／才算」等 AI 会照着行动的句子）逐句查两读；②指涉可解析性（引用 ID／文件／术语落盘是否存在、唯一）。风险轴＝「谁以什么方式消费它」：机械消费靠引擎断言，语义消费靠扫＋写作纪律。与 diy-editorial-review 的 `--reader-type 人类|LLM` 单篇深审互补、不互代。
纠错通道：用户自然语言明示改判 → HALT 重走本步重判 `kind`，`revisions` 留痕（非初判即终判）。
