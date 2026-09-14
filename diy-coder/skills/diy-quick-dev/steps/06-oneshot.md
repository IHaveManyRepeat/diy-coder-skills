# Step 6 — One-Shot（零爆炸半径快通道）

Progress: `[Clarify & Route] → One-Shot` (reached by early exit from step 1; steps 2–5 are never read)

**Read (input):** the draft record with `route: one-shot`; the intent it carries.
**Write (output):** the code; the record's `baseline`, `status`, `tasks[].done`, `verification[].result`, `review`, `deferred`, `review_order`.

Reached only for zero blast radius: no plausible path by which this change causes unintended consequences elsewhere, clear intent, no architectural decisions. If that stopped being true — the change turns out to touch shared state, an interface, or a decision — stop and route to `./02-plan.md` instead; a mis-routed one-shot is how "small" changes break things.

## Implement

Record `baseline` (HEAD or `NO_VCS`) and set the record's `status: in-progress` first, then implement the clarified intent directly — least code, project conventions, inside `code_map`, respecting `boundaries` (`ask_first` still HALTs for the human).

## Verify

Run every `verification` command and write its real `result`. The engine refuses a record reaching `in-review` / `done` with empty commands (`EMPTY_FIELD`) — in this channel there is no red/green ledger, but there is no unverified claim either.

## Review (one adversarial pass)

Run a single pass that assumes the change IS broken: attack it with diy-review's lenses — L1 correctness against the acceptance criteria, L2 the boundary cases the criteria imply. Use a sub-agent with no conversation context when one is available. Three dispositions only:

- **patch** — trivially fixable. Fix it now.
- **defer** — real but pre-existing. Append `{finding, why, date}` to `deferred`.
- Anything else — dropped silently.
- A finding caused by this change but too big for a trivial patch → **HALT** and present it to the human for a decision before proceeding; do not quietly grow the change.

Write the `review` block (`rounds: 1`, `findings` may be empty) and mark every `tasks[]` entry done.

## Build the trace

Fill the record so it stands on its own as the change's lightweight trace: `title` from the clarified intent, `type`, `route: one-shot`, `date`, and `review_order` built exactly as `./05-present.md` describes (concerns, not files; entry point first; peripherals last; `{path, line, why}` per stop). This is richer than the source's one-shot trace (frontmatter + intent + review order only): the diy record must pass the same mechanical gate as the full route, so acceptance, verification and review live here too.

## Settle and close

1. Set `project.status: final` and the record's `status: done`.
2. Run the final gate: `python "{project-root}/.claude/skills/diy-quick-dev/scripts/spec.py" check --final --id SP-xxx --json` — exit 0 is the only pass; fix and re-run otherwise.
3. Render via diy-viewer (silent side step, command only) and display the summary: files changed with one-line descriptions (CWD-relative `path:line`), findings — patches applied, items deferred, items dropped (say so if all were dropped) — and the spec path carrying its `review_order`.
4. **No commit, no push, no editor.** Close with one suggested conventional commit message the human can run themselves, and an offer to draft a PR description. Then HALT and wait for the human.

## Exit

This is the last step of the one-shot route — the run ends here once the final gate exits 0.
