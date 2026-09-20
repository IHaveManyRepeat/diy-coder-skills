# Step 3 — Finalize（决策日志审计 → 润色 → 交付）

Progress: `Discovery → Draft → [Finalize]`

**Read (input):** `{output_dir}/brief.yaml` 全文——brief、`decisions`、`addendum`；对话。
**Write (output):** 定稿的 `brief.yaml`（`project.status` / `updated`）；交付消息；渲染投影（静默旁路）。

## 1. 决策日志审计 + 附录复核

本步收尾时，把 `decisions`（连同 `addendum`）里有分量的内容怎么处置，摊开成一份双方认可的清账。每条落进且只落进三个桶之一，并由用户当面点头：

- 已进简报正文，
- 留在附录（`why_separate` 完好），
- 作为过程噪音搁置。

没有东西静默消失，也没有条目未经复核。然后收尾线头：清掉每处 `[假设]`（用户确认即摘掉前缀，否则降为一行 `open_questions`），并把每条 `open_questions` 了结或显式挂起。

## 2. 润色

对简报文字施三遍成文标准，从最粗的做起，然后对 `addendum` 重复同样三遍：

1. 结构——删减、重组、章节分量（长过 1-2 页的都归附录）；
2. 语气与惯例——术语、口径、合规约束；
3. 文字机械层——语法、清晰度、错别字。

动手前先取 findings：调用 `diy-editorial-review` 评审 `{output_dir}/brief.yaml`（传 `--target {output_dir}/brief.yaml`；两透镜全跑、不中途停下问，评审完它自己走终门）。分工是**产出归它、施加归本技能**——它只出建议、不代改 target，本技能按上面三遍顺序把 findings 施加到 `brief` 与 `addendum`。先润 `brief` 再润 `addendum`，让用户审的是一份定稿，而不是移动靶。findings 里拿不准或需作者拍板的（`QUESTION` 类），落 `open_questions`，不擅自动内容。

**证据落盘。** 成功取回记录后，把它的 `ER-###` 写进 `brief.yaml` 顶层 `review_refs`——只记 ID，不复制 findings 内容。`--final` 拿它做六条校验：`review_refs` 非空、`{output_dir}/editorial-review.yaml` 在场、该 ID 在 `reviews[]` 内、记录 `status: 已定稿`、`target` 归一化后指向本 `brief.yaml`、`lenses` 同时含 结构 与 文风（结构 + 文风是源里两条 append-only 的标准提供者，不可少其一）。`where` / `msg` 指哪修哪，修完重跑。

**证据时效。** 按 findings 施加改动后，该记录仍是本版简报的证据；但本轮若另有实质改动（内容增删改，不只是措辞），重评审一次、换上新的 `ER-###`。时效靠这条纪律判定，不做内容摘要比对（流程会过重，ER schema 也无承载字段）。

**失败与降级。** 派发不可用（环境缺 `diy-editorial-review`）→ 引擎按 `TOOL_MISSING` 降级：六条校验一并转 warning、`--final` 放行，附一行中文诊断——这是**环境问题**，不是产物问题。边界别混：**技能在场而记录缺失或不合格 → 硬拒**（`EVIDENCE_MISSING` / `MISSING_FILE` / `UNKNOWN_ID` / `STATUS_MISMATCH`，exit 1），不静默放行。存量已定稿的 `brief.yaml`（本门收紧前产出）无 `review_refs` 也走硬拒，回执带补跑指引：补评审一次、把新 ID 落 `review_refs`（更新路径下即 `./04-update.md` 对完账回到本步时）。**没有 bypass 旗标**——强制调用是本节的本体，不给回退开关。

## 3. 交付与路由

告诉用户好了：`{output_dir}/brief.yaml` 的本地路径，用用户的语言。点名链上的下一步——`已定稿` 之后由 `diy-prd` 把简报变成需求；其余由 `diy-help` 分派。外部交接不在 diy 范围内：YAML 加 viewer 投影就是交付。

## 4. 终门（机械）

先写 `project.status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑（`--project-root` / `--output-dir` 与激活期同值，`--output-dir` 必填、无缺省）：

```
python "{project-root}/.claude/skills/diy-product-brief/scripts/brief.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

exit 0 是唯一放行；逐条修完上报的违规再重跑。JSON 回执（含计数）即收口证据。渲染与收尾等 exit 0。

## 收尾

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。最后一行给路由，并带上回执里的计数。

## 播报与下一步

终门 exit 0 后，新建路径到此结束。日后的变更信号 → `./04-update.md`；要求批判性复读 → `./05-validate.md`。
