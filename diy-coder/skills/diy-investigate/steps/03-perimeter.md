# Step 3 — Perimeter（证据边界测绘）

Progress: `Acknowledge → Stronghold → [Perimeter] → Reasoning → Source Trace → Report`

**Read (input):** the draft record from step 2; the `collect` receipt.
**Write (output):** the record's `evidence` / `missing_evidence` / `backlog` sections.

## Survey the scene

Inventory evidence across six independent categories — issue these as parallel operations in one message:

1. diagnostic archives; 2. issue tracker; 3. version control (the receipt's `vcs.commits`); 4. test results; 5. static analysis; 6. source code (the receipt's `files` + `candidates`).

**Delegation discipline:** any category exceeding ~10K tokens goes to a subagent that returns a JSON manifest only (paths, sizes, time windows, key fragments cited as `path:line`). Cite the fragment from the result; never re-read the source in the parent.

## Classify and record

Each source gets an `availability` value:

- `available` — fully readable now;
- `partial` — readable but incomplete (truncated logs, one of several shards);
- `missing` — not obtainable now.

**Missing is itself a finding**: every gap becomes a `missing_evidence` row (`what` / `would_resolve` / `how`) — what the gap would resolve and how to obtain it. Never silently drop a category.

Add discovered paths to `backlog` (`item` / `priority` / `status: open`); stay on the current thread — do not chase everything surfaced here.

Present the perimeter (available / partial / missing + the missing-evidence rows); pause for the human before continuing.

## Next

Read fully and follow `./04-reasoning.md`.
