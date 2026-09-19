# Step 3 — Implement（实现与实测）

Progress: `Clarify & Route → Plan → [Implement] → Review → Present`

**Read (input):** the record at `status: 就绪`; its `code_map` and `tasks`; the code those paths name.
**Write (output):** the code; the record's `baseline`, `status: 进行中`, `tasks[].done`, `verification.commands[].result`.

## Precondition

The record exists on disk with `status: 就绪` (a resume may find `进行中` — continue from the unfinished tasks). Otherwise HALT and ask which record to work on; never guess one.

## Baseline first

Record `baseline` = the current HEAD commit, or `NO_VCS` when version control is unavailable — **before** the first code change. Review (step 4) diffs against it.

## Take the record

Set the record's `status: 进行中`. This is a spec-local state: the change is outside the story loop, so nothing else moves. When the change also touches a story that is already in `sprint.yaml`, that task's state stays diyc-owned — verify cross-document truth with `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type sprint --json` and report what it says; never write `sprint.yaml` from here. (The source synced a `sprint-status.yaml` at this point; diy has no such file.)

## Implement

- The least code that satisfies the acceptance criteria, following the project's existing architecture, patterns and conventions — architecture decisions (`D-x`) that apply are read from `architecture.yaml`, never re-invented.
- Respect `boundaries`: `总是` are invariants, `从不` is forbidden, and anything under `先问` HALTs the run for a human decision before it happens.
- Keep the diff inside `code_map`; a file that turns out to be needed but is not listed is an amendment to the record (and, if the sealed sections are wrong, a step-4 `规格缺陷` loopback — never a silent extra edit).
- Trace comments (`# trace: …`, diy-dev's discipline) apply when the change touches sprint-loop code with resolvable IDs. Outside the loop there is no `S-x` / `AC-x.y` / `TC-x.y.z` to point at — do not mint one; write no trace line rather than a false one.

## Self-check

Before leaving this step, verify every `tasks[]` entry is complete and set `done: true`. An unfinished task is finished now, not deferred silently.

## Run the verification

Run every `verification.commands[].cmd` and write the real `result` (what the command actually printed, pass or fail). A failing command is either fixed here or recorded truthfully — never weakened, never omitted, never imagined. `manual` entries are recorded only when no CLI check applies. The record cannot reach `审查中` with empty `verification.commands` (the engine refuses it: `EMPTY_FIELD`).

## Next

Read fully and follow `./04-review.md`.
