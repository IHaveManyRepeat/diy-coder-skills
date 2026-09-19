# Step 1 — 建进度与分流（Init / Resume）

Progress: `[Init] → Assess → Hub → Session → Completion`

**Read (input):** `progress.py status` 的回执（进度是否在场、`entry_step`）；进度缺席时读技能内 `curriculum.yaml` 的节清单（回答「学什么」的问句）。
**Write (output):** `{output_dir}/learning-progress.yaml`（只经 `init`；损坏件经 `init --recover`）与 `{output_dir}/notes/` 目录（`init` 同时建）。

## 先探明再动手

跑 `status`（只读），它是本技能唯一入口的判定输入：

```
python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" status --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- 回执 `ok: true` → 已有进度。**禁止 `init`**（会撞 `ALREADY_EXISTS`），直接按回执的 `entry_step` 分流：
  `steps/01-init.md` / `steps/02-assess.md` / `steps/03-hub.md` / `steps/05-completion.md`。
- 回执 `MISSING_FILE` + `entry_step: steps/01-init.md` → 新学员，走下面的建进度。
- 回执 `UNPARSABLE_YAML` / `EMPTY_FIELD` + `entry_step: steps/01-init.md` → 进度文件**损坏**（**不是**新学员），走下面的损坏恢复。

进度文件已存在 → 强制走 resume（源「不得跳过检查」纪律保留）：**不得跳过 `status` 直接开会话**，也不得为了「重来一遍」覆盖进度——断点即学习历史。

## 损坏恢复（唯一出路）

`status` 回执报 `UNPARSABLE_YAML`（或 `EMPTY_FIELD`：顶层不是映射 / 缺 `sessions` 列表）→ 进度文件已不可用。此时**每条命令都读不动它**（`update` / `check` 同样拒），而单一写通道纪律禁止手改 YAML——出路只有引擎的恢复通道：

```
python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" init --recover --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- 引擎先把原文件**逐字节备份**成 `learning-progress.yaml.corrupt-<时间戳>.bak`，再重建 7 节骨架；回执 `recovered.backup` 就是备份路径，**必须播报给用户**。
- 代价说清楚：笔记 md（`notes/session-<NN>.md`）原样留在盘上，**只有台账断点清零**（旧分数与完成日期不回填）——这是「重来一遍」，不是「修好了」。
- 纪律：`--recover` **只在损坏时用**。文件可用时带上它照样被拒（`ALREADY_EXISTS`）；**不许** `rm` 文件，也**不许**手改 YAML。
- 恢复完就是一份全新进度，照常往下走（新学员路径）。

## 建进度（仅新学员）

```
python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" init --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`--role` 可省；也可以带上用户当场说出的角色（`QA|开发|组长|负责人` 四值之一）。两条口径：

- 省略 `--role` → `learner.role: null`，合法——角色归 step 2 的画像采集。
- **`learner.assessed` 恒为 null**（无论是否给 `--role`）：画像采集走 step 2 的 `update --learner`，`init` 不得置位。

`init` 同时建 `{output_dir}/notes/` 目录——笔记 md 的落点，**你不自建目录**。回执里的 `counts` 就是「7 节 / 0 节完成 / 0%」。

## 播报

一句话给用户：7 节课程已就绪、当前完成度、下一步先花两分钟做画像采集（决定后面每节按什么角色讲）。

## 播报与下一步

按 `status` 回执的 `entry_step` 走：

- `steps/01-init.md`（刚 `init` 完）→ 读 `./02-assess.md`。
- `steps/02-assess.md` → 读 `./02-assess.md`。
- `steps/03-hub.md` → 读 `./03-hub.md`。
- `steps/05-completion.md` → 读 `./05-completion.md`。
