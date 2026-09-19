# Step 1 — Acknowledge（输入确认与路由）

Progress: `[Acknowledge] → Stronghold → Perimeter → Reasoning → Source Trace → Report`

**Read (input):** the input itself — ticket ID, archive path, log / stack trace, free-text description, code area, commit range, or a path to an existing case; the `collect` receipt from On Activation.
**Write (output):** nothing yet — the record is drafted in step 2. This step produces the route decision and the acknowledged input set.

## Acknowledge each input shape (reference only — bulk reads wait for step 3)

| Input shape | What to record now |
| --- | --- |
| Issue tracker ticket | Fetch full details via the available MCP tools; record the ID. |
| Diagnostic archive | Record path, file count, time window. |
| Log file or stack trace | Record path and time window; only the stack frame already in the user's message is in scope here. |
| Free-text description | Capture verbatim; treat it as a hypothesis. |
| Code area (no symptom) | Record the entry point; set `mode: 探索`. |
| Recent commit range | Record the commit range; re-run `collect --since <commit>` when the range needs refreshing. |

Symptom-driven input (`mode: 症状驱动`) chases a defect; an area input (`mode: 探索`) builds a mental model — the same discipline applies on both ends.

## Route: resume or new case

Test the slug first: the ticket ID when one was given, otherwise a short descriptive name agreed with the human (lowercase alphanumeric with hyphens).

- **Slug hit in an existing case** → resume. Surface, in this order: open hypotheses (`status: 待验证`) with their `test` criteria; open backlog (`status != 已完成`); `missing_evidence` rows; the last `conclusion` with its `confidence`. Ask which thread to pull, then continue at the step that thread needs (typically `./03-perimeter.md` or `./04-reasoning.md`) and finish through `./06-report.md`; append one `follow_ups` entry at the close.
- **Collision but a separate case is wanted** → rename the new slug to `slug-YYYY-MM-DD`.
- **No hit** → new case: settle the scope below, then read `./02-stronghold.md`.

## Settle the scope (new case only)

State three things and confirm them with the human: scope (which system / area / subsystem), time window (when the symptom or change occurred), and what "done" means for this case (root cause / sufficient mental model).

**The user's hypothesis is never the starting point.** Register it as `H-001` (`status: 待验证`, `test` = what would confirm or refute it); the stronghold in step 2 is found independently, and it is one of the things that validates or refutes H-001.

Pause here for the human before continuing — a scope they did not confirm is a case nobody asked for.

## Next

Read fully and follow `./02-stronghold.md` (on a resume, go to the step the pulled thread needs instead, and finish through `./06-report.md`).
