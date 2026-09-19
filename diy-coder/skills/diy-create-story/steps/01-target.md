# Step 1 — Target（目标故事）

Progress: `[Target] → Artifacts → Code Survey → Compose → Finish`

**Read (input):** 激活时那次 `collect` 的回执；它落定的那条故事。
**Write (output):** `{output_dir}/story-context.yaml` 里的草稿记录（`id` / `story` / `status` / `date` / `epic` / `ac_refs` / `tc_refs` / `decisions` / `files: []`）。

## 落定故事

按序级联——命中即停：

1. **用户点名了**（`create story S-3`、`3-2`、一个故事标题）→ 取其 ID。
2. **没人点名** → 读 `{output_dir}/sprint.yaml` 的 `tasks[]`，取文件序里第一条 `status` 非 `已完成` 的任务，跳过 `已阻塞`。每个任务只读 `story` 与 `status`——该文件其余一概不读。
3. **两条都不成立**（无 sprint.yaml，任务全 `已完成` 或 `已阻塞`）→ 问用户，给出尚未 `已完成` 的故事 ID。

解析不到的故事 ID 会让 `collect` 以 exit 1 返回，并附 `suggestions` 列表——**那是菜单，不是决定**：与用户确认后再重跑。绝不发明故事，绝不静默换目标。

## 门禁优先（零产出拒绝）

`collect` 跑门禁。exit 1 时本次运行在开始前就结束：转述回执的一行理由与其 `gate.route`（diy-epics-stories）或 `suggestions` 列表，然后停下、什么都不写。拒绝永不变成记录；上游缺席，绝不靠「换一条故事来打包」绕过。

## 跑开场

```
python "{project-root}/.claude/skills/diy-create-story/scripts/story_context.py" collect --story <S-x> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

回执是本次会话的证据基座：`acs`（该故事的 AC——**完整 AC 对象**，子字段 `id` / `given` / `when` / `then` / `refs` / `design_ref`）、`epic`（该故事的 epic）、`tcs`（绑定这些 AC 的用例）、`prior`（前序故事的 sprint 任务）、`decisions`（架构决策，摘要级）、`git`（最近 5 次提交）、`warnings`。机器锚点一律从回执复制——绝不凭记忆重打。

## 起草记录

往 `{output_dir}/story-context.yaml` 追加一条记录（文件缺席时创建：`project: {name, created, updated}`——`name` 取 `diy-coder.yaml` 的 `project.name`——加空 `contexts` 列表与 `revisions: []`）：

```yaml
  - id: SC-001                  # 下一个 = 既有最大 + 1，三位零填充；永不重编号，永不复用
    story: S-3                  # 落定的故事
    status: 草稿
    date: YYYY-MM-DD            # 本条动作的日子
    epic: E-1                   # 取自回执
    ac_refs: [AC-3.1]           # 该故事的 AC ID，从回执复制
    tc_refs: [TC-3.1.1]         # 回执 tcs 的 ID
    decisions: []
    files: []
    risks: []
    verify: []
    open_questions: []
```

`ac_refs` / `tc_refs` 取自回执；`design_ref` 在第 2 步、当 AC 带它时补上。

空块是信号，不是待糊上的空白：`tcs: []` 意味着没有测试绑定本故事的 AC——sprint 的 TDD 门会扣住该任务，直到 diy-test-design 覆盖它们。这一事实在第 4 步点名（`open_questions` / `risks`），绝不丢掉。

## 播报与下一步

读 `./02-artifacts.md` 并照做。
