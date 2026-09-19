# Step 3 — Code Survey（代码现场勘察）

Progress: `Target → Artifacts → [Code Survey] → Compose → Finish`

**Read (input):** every file this story will touch — each `更新` target in full.
**Write (output):** `files[]` in the record (`path` / `action` / `why` / `current_state` / `preserve`).

## Non-negotiable: read what you will modify

The source workflow marks this critical, and it is the rule this skill keeps at full strength:

> A story implementation must leave the system working end-to-end — not just satisfy its stated ACs. If a behavior is required for the feature to work correctly in the existing system, it is a requirement whether or not it is explicitly written in the story.

That is why `更新` entries carry `current_state` and `preserve`: the dev agent cannot honor a behavior nobody wrote down. Skipping the read is the primary cause of implementation failures and review cycles.

## Enumerate the files

Build the list from what the story actually demands — the ACs' semantics, the `design_ref` page when present, the code the git intel points at, and the project's directory layout. For each candidate decide `action: 新建|更新` and write `why` in one line: which AC needs it, or what it changes.

**Before marking anything `新建`, search for an existing implementation** of the same thing (a helper, a client, a model, a page). Reinventing a wheel is the first mistake the context pack exists to prevent — an equivalent that already exists becomes an `更新` entry, not a parallel file.

## Survey each 更新 target

Read the file completely. A search hit, a symbol name, or someone's summary is not a read. Then record:

- `current_state` — what the file does today: its state machine, API calls, data shapes, existing behaviors, in one line.
- `preserve` — the existing interactions and behaviors this story must not break: the contract other code depends on, the shape a caller passes, the behavior a test asserts.

Both are one-liners, not essays: the dev agent opens the file for detail, the pack tells it what to look for.

## Place each new file

Path by the existing structure, never by convenience: naming conventions, package layout, where tests live, where fixtures live. A new file in the wrong directory is the "wrong file locations" disaster, and it is invisible to every downstream gate. `why` names the AC that requires it.

## Bound the blast radius

Every plausible failure you can already see goes to `risks` in step 4 — not here. Here you decide the file set; anything you are not sure belongs in it goes to `open_questions` rather than being silently included or silently dropped.

## Next

Read fully and follow `./04-compose.md`.
