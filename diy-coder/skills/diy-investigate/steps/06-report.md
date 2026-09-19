# Step 6 — Report（结案与交接）

Progress: `Acknowledge → Stronghold → Perimeter → Reasoning → Source Trace → [Report]`

**Read (input):** the record as filled by steps 2–5; the human's confirmations along the way.
**Write (output):** the settled record (`handoff_brief` / `conclusion` / `status`) in `{output_dir}/investigation.yaml`; the rendered view; the hand-off menu.

## Finalize the record

- **`handoff_brief`** — rewrite to final form: 3 sentences, a 15-second read (what happened / where the case stands / what's needed next).
- **`conclusion.text`** with **`conclusion.confidence`**: `高` (已确证 root cause, deterministic reproduction) / `中` (已推断; minor uncertainty) / `低` (假设中; clear data gap).
- **`conclusion.fix_direction`** when applicable (categorize by mechanism when several combine); **`conclusion.diagnostic_steps`** if uncertainty remains; **`conclusion.reproduction`** when applicable — for exploration cases, a verification plan instead.
- **`side_findings`** — tangential observations surfaced along the way (evidence-graded, `ref` optional): observed, **not followed up**. They belong here — not in `backlog` (that is the to-explore queue) and not in `evidence` (that is this thread's proof). Optional; omit when there are none.
- **record `status`**: `调查中` / `已结论` / `待证据阻塞`.

## Completion check

The case is complete when one holds: the root cause is `已确证`; the root cause is `假设中` with an explicit data gap; the mental model suffices for the user's stated goal (exploration); the `backlog` holds only items needing unavailable evidence; the user explicitly concludes.

## Final gate (mechanical)

1. Write `project.status: 已定稿` first — `已定稿` is what the gate inspects, not a product of it.
2. Run `python "{project-root}/.claude/skills/diy-investigate/scripts/investigation.py" check --final --json` with the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run. The JSON receipt (counts included) is the close-out evidence.
3. Render via diy-viewer — the silent side-step command from SKILL.md — only after exit 0; no browser interaction point, no path report that blocks.

## Re-entry (resume)

Append one `follow_ups` entry (`date` / `note`) — same-day re-entries are fine. Earlier history is never rewritten; a changed hypothesis is updated in place (status + resolution), never deleted.

## Route menu (recommend the highest-value action, one line each)

| Finding | Route |
| --- | --- |
| Trivial fix (one-liner) | `diy-quick-dev` |
| Scope / plan needs to change | `diy-correct-course` |
| Worth tracking as a story | `diy-create-story` |
| The fix needs a fresh review | `diy-review` |

Mitigations and workarounds are generated only on explicit request — investigation stops at the diagnosis. Close with the route plus the counts from the receipt (`counts` included).

## Exit

This is the last step file — the run ends here once the final gate exits 0. `handoff_brief` + `conclusion` carry the outcome, the record's `status` closes the case; no further `steps/` file is read.
