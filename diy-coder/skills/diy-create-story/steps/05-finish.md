# Step 5 — Finish（定稿、交付、路由）

Progress: `Target → Artifacts → Code Survey → Compose → [Finish]`

**Read (input):** the settled record; the `collect` receipt.
**Write (output):** `status: final` on the record; the delivery message.

## Final gate (mechanical)

Write `status: final` first — `final` is what the gate inspects, not a product of it — then run:

```
python "{project-root}/.claude/skills/diy-create-story/scripts/story_context.py" check --final --json --project-root "{project-root}" --output-dir "{output_dir}"
```

Exit 0 is the only pass. Fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. In plain terms the bar is: every `story` / `ac_refs` / `tc_refs` / `decisions` reference resolves, every `update` file exists and carries its `current_state` and `preserve`, `files` and `verify` are non-empty, there is no `[ASSUMPTION]` left, and no open question is dangling. A `status` that moved on hopium is what `STATUS_MISMATCH` names.

Then re-render with the activation command and close with the counts from the receipt.

## Deliver

One message: the record id and its path, the story and epic it covers, `files` count and which of them are `update`, the TC refs, the applicable decisions, the open questions and how each was closed. Name what the pack deliberately does not contain — copies of AC text, restated decisions, commit messages — so nobody looks for a copy that is not there and nobody treats the pack as a replacement for the upstreams.

## Route

- **Mainline next: diy-dev.** It reads the story's ACs, the TC steps and the source; the pack tells it where to look, what not to break, and how completion will be verified.
- **`tc_refs` empty** → say it plainly: the sprint TDD gate will hold this task back until diy-test-design covers the ACs. The route is diy-test-design, then re-run this skill to pick the new cases up.
- **A story with no upstream** (unknown ID, stories.yaml not final) never reaches this step — the gate refused in step 1 and wrote nothing.

## Write scope (last word)

This skill has written exactly one file: `{output_dir}/story-context.yaml`. No upstream document was touched, no task state moved, no source file edited. Re-running for the same story updates that record in place and appends to `revisions` — it never mints a second `SC-###` for the same story.

**This is the last step — no further file to read.** The next mainline skill is diy-dev.
