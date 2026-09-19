# Step 2 — Plan（计划与批准）

Progress: `Clarify & Route → [Plan] → Implement → Review → Present`

**Read (input):** this run's draft record; the artifacts and code the intent touches.
**Write (output):** the filled record in `{output_dir}/spec.yaml` — investigation results, `code_map` / `tasks` / `acceptance` / `verification` / `io_matrix` / `design_notes`, then `status: 就绪`.

## Draft resume check

If the record is being resumed from `草稿`, read it and keep its `intent` and `boundaries` verbatim — the frozen core is preserved, never re-typed.

## Investigate

Read the code the change will touch and the artifacts that constrain it. Isolate deep exploration in sub-agents where available and take distilled summaries only (context snowballing is the failure mode this prevents). Cite by ID and `path` — a document body or a code block pasted into the record is a defect, not thoroughness.

## Fill the record

- `io_matrix` — one row per meaningful input/output scenario (`scenario` / `input` / `expected` / `error_handling`). If no meaningful I/O scenarios exist, **omit the key entirely** — never write "N/A" or "None".
- `code_map` — one entry per file the change touches (`path` / `role`), populated from the investigation so nobody has to blind-search the codebase later.
- `tasks` — `task` (action) / `file` (exact path) / `done: false`. Prefer one task per file; group tightly-coupled changes when splitting would be artificial.
- `acceptance` — `given` / `when` / `then`, one line each. If an `io_matrix` exists, add a task to test its edge cases; acceptance covers system-level behavior the matrix does not.
- `verification.commands` — at least one `{cmd, expect}` per acceptance criterion (CLI commands preferred; `manual` only when no command applies). This is the lightweight channel's hard bottom: no command, no evidence, no review.
- `design_notes` — only when the approach is non-obvious; omit the key otherwise.

## Self-review (READY FOR DEVELOPMENT)

- **Actionable** — every task names a file path and a specific action.
- **Logical** — tasks ordered by dependency.
- **Testable** — every acceptance uses Given/When/Then and has a verification command.
- **Complete** — no placeholders, no TBDs, no open questions left silently.

Intent gaps are not fantasized away: HALT and ask. If the spec body exceeds ~1600 tokens, show the count and HALT: `[S] Split — carve off secondary goals` (append them to `deferred`, then **regenerate** the record for the narrowed scope — do not surgically carve sections out) | `[K] Keep full — accept the risks`.

## CHECKPOINT 1

Present the summary, then HALT: `[A] Approve` | `[E] Edit`. Show the spec path CWD-relative (no leading `/`). Before approving, the human can ask questions or request changes here. A deeper challenge pass (elicitation / party mode) is not an installed diy skill yet — a later batch brings it; until then, a separate session is the way to get a second pair of eyes without context bloat.

- **A** — re-read the record from disk.
  - **Missing:** HALT. Tell the human the record is gone and STOP — write nothing, set no status, do not proceed. Nothing below runs.
  - **Changed since it was written:** acknowledge the external edits, show a brief summary of what changed, proceed with the updated version.
  - Then set the record's `status: 就绪`. The `intent` section is now locked — from here on only the human renegotiates it. → Step 3.
- **E** — apply the requested changes, then return to CHECKPOINT 1.

## Next

Read fully and follow `./03-implement.md`.
