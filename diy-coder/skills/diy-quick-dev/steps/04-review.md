# Step 4 — Review（审查与路由）

Progress: `Clarify & Route → Plan → Implement → [Review] → Present`

**Read (input):** the record at `status: in-progress`; the diff since `baseline` (tracked and untracked); the changed files where a hunk is not enough.
**Write (output):** the record's `review` block (`rounds` / `findings`), `change_log` entries on `bad_spec` loopbacks, `deferred` entries, and the next `status`.

Set the record's `status: in-review` before continuing. The layers and the routing are diy-review's — this step runs them; it never builds a second review system.

## Construct the diff

Diff everything since `baseline` (`NO_VCS` → best effort from the conversation and file mtimes). Read-only inspection: never `git add`, never stage.

## Layers

- **L1 correctness.** Does the implementation do exactly what `acceptance` says — no missing then-clause, no extra unasked behavior? Compare criterion by criterion. A deviation from the record's `boundaries` (`always` / `never`) is a finding.
- **L2 boundary.** Walk the failure modes the criteria imply but do not spell out: bad input, empty/None, concurrency, error paths, silent fallbacks. Report only unhandled cases that could actually bite — noise is not a finding.
- **L3 acceptance coverage.** Every `acceptance` entry must have a `verification` command whose recorded `result` is real and matches the claim. A criterion without a command, or with a result that does not support its claim, is a finding naming the acceptance index — never re-accept it by eye.

When a sub-agent is available, launch it at the same model capability as this session, without the conversation context (a reviewer that inherits the author's reasoning is anchored), and take back findings only. No sub-agent → run the same pass inline; never write a separate review-prompt file (this skill's single source is `spec.yaml`).

## Classify

1. Deduplicate all findings.
2. Route each finding **exactly once**:
   - `intent_gap` — the change contradicts or misses the frozen `intent`. Do not infer intent unless there is exactly one possible reading.
   - `bad_spec` — caused by the change, including direct deviations from the record; the non-frozen sections should have prevented it. When in doubt between `bad_spec` and `patch`, prefer `bad_spec` — a spec-level fix produces more coherent code.
   - `patch` — caused by the change and trivially fixable without human input.
   - `defer` — real, but pre-existing and not this change's problem. When unsure between `defer` and dropping it, drop it: only defer findings you are confident are real.
3. Process in cascading order — `intent_gap` / `bad_spec` trigger a loopback and lower findings become moot; increment `rounds` on each loopback; above 5 HALT and escalate to the human.

## Apply the route

- **intent_gap** — root cause is inside the frozen `intent`. Revert the code changes, loop back to the human to renegotiate the intent, then re-run `./02-plan.md` → this step. The human owns this edit; you never rewrite `intent` yourself.
- **bad_spec** — root cause is outside `intent`. Before reverting: extract KEEP instructions (what worked and must survive). Revert the code, respect every existing `change_log` constraint, append one new `change_log` entry (`finding` / `amended` / `avoided` / `keep`), then re-run `./03-implement.md` → this step.
- **patch** — fix it now. These are the only findings that survive loopbacks.
- **defer** — append `{finding, why, date}` to `deferred`. Recorded, does not block.
- Anything without a route — noise. Drop it silently and say so only in the aggregate ("N rejected").

Write the `review` block: `rounds` (loopbacks consumed) and `findings` (`layer` / `route` / `note`, one line each; the block may be empty on a clean pass).

## Structural check

Before leaving, run `python "{project-root}/.claude/skills/diy-quick-dev/scripts/spec.py" check --project-root "{project-root}" --output-dir "{output_dir}" --json` — exit 0 means the record (including the review block) is structurally valid. Fix violations and re-run.

## Next

Read fully and follow `./05-present.md`.
