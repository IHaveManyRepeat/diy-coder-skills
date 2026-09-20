# Step 4 — Update（变更信号对齐）

Progress: `Discovery → Draft → Finalize`（更新从本步进入；收口回到 Finalize）

**Read (input):** `{output_dir}/brief.yaml` 全文——brief、`decisions`、`addendum`；它引用的原始输入；变更信号。
**Write (output):** 对好账的 `brief.yaml`；新增与翻转的 `decisions`；追加的 `revisions`。

## 先对账，再打补丁

读简报、附录、决策与原始输入，然后拿 Discovery 的姿态去问变更信号本身——变了什么、为什么是现在、牵动哪个档位。脱离上下文的补丁会变成漂移；信号是被盘问的，不是被服从的。

## 先摊开冲突

提任何改动之前，列出信号牵动的每一条既有决策及其 `rationale`，请用户确认反转。改动前提出的冲突是决策；改动后才发现的同一冲突是漂移。然后一起改，用用户的语言，逐节来。

答复无论正反都落一条 `BD-###`：确认反转 = 旧条翻 `status: 已反转` + 追加替代条（见下）；**拒绝 = 追加一条「信号已评估、决定不改动」的 `BD-###`（`status: 生效`，`rationale` 记用户理由）**——既有条目不翻转、也不写 `revisions`（它没有被改）。

## 快照与校验（机械）

1. `cp {output_dir}/brief.yaml {output_dir}/brief.yaml.prev`
2. 起草对好账的简报。把每条被推翻的决策翻成 `status: 已反转`，替代条按下一个 `BD-###` 追加——永不重编号、永不重用、永不改写旧史。
3. 跑（`--project-root` / `--output-dir` 与激活期同值）：
   `python "{project-root}/.claude/skills/diy-product-brief/scripts/brief.py" check --previous {output_dir}/brief.yaml.prev --project-root "{project-root}" --output-dir "{output_dir}" --json`
   Exit 0 = 没丢决策。**非 0 一律不删 `.prev`**：`ID_UNSTABLE` → 从快照找回被丢记录、补进新稿、重跑到 exit 0 再删；`MISSING_FILE` / `UNPARSABLE_YAML` → 快照不可用、安全网失效，停手告知用户，确认前不得再写。
4. 删掉 `.prev`（第 3 步 exit 0 之后）。刷新 `project.updated`，每条被改动的记录向 `revisions` 追加 `{date, change, reason}`。

## 根本性变更

信号是根本性的——问题、用户或利害档位动了——就别打补丁，改提**新建**：围绕新前提重建的简报是另一份简报。替换旧文件同样过上面的快照；没有任何东西被静默覆盖。

## Headless

不问。反转先落 `decisions`，再动手。推断后意图仍含糊则 halt `blocked`——零写入、一行理由、一条路由。

## 播报与下一步

对好账的草稿可以定稿时，读全 `./03-finalize.md` 并照做。仅当用户要批判性地复读这次变更时，才先读 `./05-validate.md`。
