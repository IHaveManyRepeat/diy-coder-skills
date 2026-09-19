# Step 5 — Wrap-Up（拍板）

Progress: `Orientation → Walkthrough → Detail Pass → Testing → [Wrap-Up]`

**Read (input):** this run's draft record (its `concerns` / `risks` / `observations` as filled so far); the review conversation.
**Write (output):** the settled record (`decision` / `reason` / `next` / `status`) in `{output_dir}/checkpoint.yaml`; the rendered view; the closing summary.

## Prompt for decision

```
---

Review complete. What's the call on this {change_type}?
- **`批准`** — ship it (I record the call; any fix needed first is a diy-dev job, not mine)
- **`返工`** — back to the drawing board (revert, revise the spec, try a different approach)
- **`讨论`** — something's still on your mind
```

HALT — do not proceed until the human makes their choice. A choice given earlier (steps 2–4 early exit) already satisfies this prompt; use it.

## Act on decision

- **`批准`** — acknowledge briefly, settle the record, and write a `next` route naming the ship path (e.g. hand the task to diy-review for the state move when the target is a sprint task). If the target is a PR and `gh` is available, offer to approve via `gh pr review --approve` — an optional path, and confirm before executing: it is a visible action on a shared resource. If the human wants a patch first, that is diy-dev's job: this skill never edits code.
- **`返工`** — ask what went wrong: the approach, the spec, or the implementation? Help the human pick the next step (revert the commit, open an issue, revise the spec) and write it into `next`. When the change is someone else's PR, help draft specific feedback tied to `path:line`. Executing the revert is not this skill's job.
- **`讨论`** — open conversation: answer questions, explore concerns, dig into any aspect. The record stays non-final (`status: 草稿`); after the discussion, return to the prompt above.

## Settle the record

1. Fill `decision` (`批准` / `返工` / `讨论`), `reason` (the human's own words) and `next` (routing advice, in `document_output_language`). Sections that were never reached stay empty — never invent them.
2. Structural check after any write: `python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" check --project-root "{project-root}" --output-dir "{output_dir}" --json` — exit 0 means the record is structurally valid; fix violations and re-run.
3. **`批准` / `返工` → final gate (mechanical):** write `status: 已定稿` first — `已定稿` is what the gate inspects, not a product of it — then run `python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" check --final --json` with the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as above. Exit 0 is the only pass; fix every reported violation and re-run. The JSON receipt (counts included) is the close-out evidence; rendering and close-out wait for exit 0.
4. **`讨论` → loop:** keep `status: 草稿` and return to the decision prompt; the final gate does not apply until the human lands on `批准` or `返工`.
5. **Amending an existing record** (a `讨论` record settled later, a verdict revised): append `{date, change, reason}` to the top-level `revisions` list — never renumber or reuse the `CK-###` id, never rewrite the earlier history.

## Close

Render via diy-viewer — the silent side-step command from SKILL.md (append `--instance <name>` when one was resolved); no browser interaction point, no path-waiting. Then close with the verdict and the counts from the receipt (`counts` included), and name the `next` route in one line.

## Exit

This is the last step file — the run ends here once the final gate exits 0 (`批准` / `返工`) or the `讨论` loop is handed back to the human. The record's `next` field carries the route; no further `steps/` file is read.
