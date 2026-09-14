# Step 6 — Readiness（就绪度五维深挖）

Progress: `Epic Discovery → Deep Analysis → Continuity → Review → Actions → [Readiness] → Finish`

**Read (input):** the receipt (`coverage` / `metrics` / `bugs`), the record's `critical_path`, and the user — this step is an interrogation, not a form fill.
**Write (output):** `readiness` in the record; blockers promoted into `critical_path`.

## The five dimensions (source step-9)

The source's closing question is the one to hold: *the epic is marked complete — is it really done?* Five dimensions, each answered in one plain sentence (the engine rejects empty values at the final gate):

- **`testing`** — what verification actually ran? Anchor it in `coverage` and TC status. An uncovered must-AC is named here, not hidden. Gaps that remain open become critical-path items if the next epic depends on that behaviour.
- **`deployment`** — live, scheduled, or still local? If not deployed, the deployment milestone belongs on the critical path.
- **`acceptance`** — has the user / stakeholder accepted the deliverables, or is feedback still pending? Pending acceptance is a rework risk for the next epic; say so.
- **`tech_health`** — how does the codebase feel after this epic: stable and maintainable, or fragile? Anchor the answer in evidence: deferred findings still open, defect clusters from `bugs`, round counts that spiked.
- **`blockers`** — any unresolved blocker, defect or debt carried forward. Each one is asked: what does it break in the next epic, and who owns the fix?

## Rules

- **Ask, do not assume.** Each dimension gets its direct question to the user, and the answer is what gets recorded. A dimension where the evidence and the user disagree keeps both readings in the sentence.
- **No optimistic defaults.** "Deployed" without a fact is "not deployed". "Stakeholder happy" without a word from them is "acceptance pending". The source's rule holds: better to catch it now than three stories into the next epic.
- **A concern becomes work.** Anything that fails this check either lands in `critical_path` (blocking) or as an `action_items` entry (non-blocking). A concern with neither is not a concern.
- **All clear is a valid outcome.** Say it explicitly — "fully complete, clear to proceed" — rather than manufacturing a worry to look thorough.

## Next

Read fully and follow `./07-finish.md`.
