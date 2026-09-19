# Step 5 — Source Trace（源码追踪）

Progress: `Acknowledge → Stronghold → Perimeter → Reasoning → [Source Trace] → Report`

**Read (input):** the record's hypotheses + evidence; the `collect` receipt's `candidates` / `vcs.commits` / `files`; the source files themselves.
**Write (output):** the record's `evidence` (「已确证」 `path:line` entries) and the `conclusion` skeleton (`fix_direction` = error origin / trigger / condition).

## First-pass scans (parallel — one message, multiple tool calls)

- grep for the exact error string — the receipt's `files` list is the search surface;
- glob the affected directory for parallel implementations — the receipt's `candidates` of `kind: parallel` already name them (confirm, don't re-discover);
- `git log` for recent changes — the receipt's `vcs.commits` already carries them.

## Then sequentially

Read the surrounding code; follow the caller chain; watch for language and process boundary crossings (compiled→scripts, IPC, host→device, configuration flow). Each 「已确证」 observation lands as an `evidence` entry with a `path:line` `ref`.

## Lean by case type

- **探索 mode** — I/O mapping (triggers, outputs, dependencies); frequent-terms scan; control-flow filtering (branches, loops, error handling, state-machine transitions). The deliverable is the area model, not a defect.
- **症状驱动 mode** — depth assessment: is the root cause reachable from local context, or does the answer need a broader area model? Surface the escalation; never silently expand scope. Trivial-fix assessment: an off-by-one, a missing null check, a swapped argument → a one-line suggestion or draft diff, written into `conclusion.fix_direction`; anything larger → stop at the root cause area.

**Investigation stops at the diagnosis — implementation is out of scope.** There is no separate trace section: the graded `evidence` list *is* the trace, and the error origin / trigger / condition become one line each in `conclusion.fix_direction`.

## Next

Read fully and follow `./06-report.md`.
