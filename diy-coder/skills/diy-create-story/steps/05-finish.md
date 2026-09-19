# Step 5 — Finish（定稿、交付、路由）

Progress: `Target → Artifacts → Code Survey → Compose → [Finish]`

**Read (input):** 已定稿的记录；`collect` 回执。
**Write (output):** 记录上的 `status: 已定稿`；交付消息。

## 终门（机械判定）

先写 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑：

```
python "{project-root}/.claude/skills/diy-create-story/scripts/story_context.py" check --final --json --project-root "{project-root}" --output-dir "{output_dir}"
```

exit 0 是唯一放行。修完每条报告的违规再重跑；JSON 回执（含计数）即收口证据；**门非 0 → 先把 `status` 回退 `草稿`**（Rules 8），修完重走本步——离开本次运行前文档不得停在未过门的 `已定稿`。说人话，这条杠是：每个 `story` / `ac_refs` / `tc_refs` / `decisions` 引用都解析得到，每个 `更新` 文件都存在且带 `current_state` 与 `preserve`，`files` 与 `verify` 非空，零 `[假设]` 残留，未决问题没有悬空的。靠盼望挪动的 `status` 就是 `STATUS_MISMATCH` 点名的东西。

然后用激活时那条命令重新渲染，并用回执里的计数收尾。

## 交付

一条消息：记录 ID 与其路径、它覆盖的故事与 epic、`files` 计数及其中哪些是 `更新`、TC 引用、适用的决策、未决问题及各自如何关上。点名整包刻意**不**含什么——AC 正文的副本、转述的决策、提交信息——这样没人会去找一份不存在的副本，也没人把上下文包当成上游的替代品。

## 路由

- **主线下一步：diy-dev。** 它读故事的 AC、TC 步骤与源码；上下文包告诉它去哪看、什么不能碰坏、完成将怎么被验证。交付面：`{output_dir}/story-context.yaml` 的 `contexts[]` 里 `story: S-x` 那一条，取值键 `ac_refs` / `tc_refs` / `decisions` / `files` / `verify` / `risks` / `prior_story`。
- **`tc_refs` 为空** → 直说：sprint 的 TDD 门会扣住该任务，直到 diy-test-design 覆盖这些 AC。路由是 diy-test-design，覆盖后再重跑本技能把这些新用例接进来。
- **无上游的故事**（未知 ID、stories.yaml 未 `已定稿`）到不了这一步——门在第 1 步就拒绝了，什么都没写。

## 写范围（最后一句）

本技能恰好写了一个文件：`{output_dir}/story-context.yaml`。没有上游文档被碰，没有任务状态被移动，没有源码文件被编辑。为同一故事重跑会原位更新那条记录并追加 `revisions`——绝不为同一故事铸第二个 `SC-###`。

**这是最后一步——没有下一个要读的文件。** 主线下一技能是 diy-dev。
