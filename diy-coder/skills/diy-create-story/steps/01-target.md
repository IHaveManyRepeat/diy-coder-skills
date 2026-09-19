# Step 1 — Target（目标故事）

Progress: `[Target] → Artifacts → Code Survey → Compose → Finish`

**Read (input):** the `collect` receipt from On Activation; the story it resolved.
**Write (output):** the draft record in `{output_dir}/story-context.yaml` (`id` / `story` / `status` / `date` / `epic` / `ac_refs` / `tc_refs` / `decisions` / `files: []`).

## Settle the story

Cascade in order — stop at the first hit:

1. **The user named one** (`create story S-3`, `3-2`, a story title) → take its ID.
2. **Nobody named one** → read `{output_dir}/sprint.yaml` `tasks[]` and take the first task whose `status` is not `已完成`, in file order, skipping `已阻塞`. Read only `story` and `status` from each task — nothing else from that file.
3. **Neither works** (no sprint.yaml, all tasks 已完成 or 已阻塞) → ask the human, offering the story IDs not yet `已完成`.

A story ID that resolves to nothing returns exit 1 from `collect` with a `suggestions` list — **that list is a menu, not a decision**: confirm the pick with the human, then re-run. Never invent a story, never silently switch targets.

## Gate first (zero-output refusal)

`collect` runs the gate. On exit 1 the run is over before it starts: relay the receipt's one-line reasons and its `gate.route` (diy-epics-stories) or its `suggestions` list, then stop and write nothing. A refusal never becomes a record, and a missing upstream is never worked around by packing a different story.

## Run the opener

```
python "{project-root}/.claude/skills/diy-create-story/scripts/story_context.py" collect --story <S-x> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

The receipt is this session's evidence base: `acs` (the story's ACs), `tcs` (cases binding them), `prior` (the previous story's sprint task), `decisions` (architecture decisions, summary level), `git` (last 5 commits), `warnings`. Machine anchors are copied from it — never retyped from memory.

## Draft the record

Append one record to `{output_dir}/story-context.yaml` (create the file when absent: `project: {name, created, updated}` — `name` from `diy-coder.yaml` `project.name` — plus an empty `contexts` list and `revisions: []`):

```yaml
  - id: SC-001                  # next = highest existing + 1, 3 digits; never renumber, never reuse
    story: S-3                  # the resolved story
    status: 草稿
    date: YYYY-MM-DD            # today
    epic: E-1                   # from the resolved story entry
    ac_refs: [AC-3.1]           # the story's AC ids, copied from the receipt
    tc_refs: [TC-3.1.1]         # the receipt's tcs ids
    decisions: []
    files: []
    risks: []
    verify: []
    open_questions: []
```

`ac_refs` / `tc_refs` come from the receipt; `design_ref` is added in step 2 when the ACs carry one.

An empty block is a signal, not a blank to paper over: `tcs: []` means no test binds this story's ACs — the sprint TDD gate will hold the task back until diy-test-design covers them. That fact is named in step 4 (`open_questions` / `risks`), never dropped.

## Next

Read fully and follow `./02-artifacts.md`.
