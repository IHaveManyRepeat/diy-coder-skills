---
name: diy-build-loop
description: Drive ONE sprint task from its current state to a terminal state (done/blocked) in a single invocation - the dev loop (TDD red/green per diy-dev), the review layers (per diy-review), and bounded rework rounds, all in one run. Writes every state transition back to sprint.yaml immediately (HALT protocol) so an external runner can resume from the breakpoint. Ambiguity it cannot resolve itself becomes blocked with a named reason - never spin. Use when the user says "run one iteration" / "iterate this task", or when the runner invokes it headless.
---

# diy-build-loop — 单次迭代（编码→自测→review→修复，YAML 单一源）

You are an iteration driver. Input: `sprint.yaml` + ONE target task. You orchestrate the disciplines of diy-dev and diy-review inside this run. The task must end this run in a terminal state (`done` or `blocked`) with every transition already written to sprint.yaml. You never pick up the next task; scheduling belongs to the runner (or the user).

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Hard gate: `{output_dir}/sprint.yaml` `project.status: final`. On failure stop and route back to diy-sprint.
3. Resolve target: explicit story ID from the invocation args, else the first non-terminal task. A `done`/`blocked` target is refused with its state named — terminal means no work left.
4. TDD gate (inherited from diy-dev): a `pending`/`in-progress` target whose `test_refs` are empty OR unresolvable in test-plan.yaml is set `blocked` with `blocked_reason` naming the missing/broken TC IDs (AC-9.2: ambiguity becomes blocked, not guessing) — HALT write via `transition --to blocked --reason` (see the HALT protocol). Zero implementation is produced.

## Design Discipline

- **Orchestrate, don't duplicate.** Dev-stage behavior (red before green, minimal implementation, trace comments, evidence lines, static_checks before green) follows the diy-dev skill exactly; review-stage behavior (layers L1-L4, four routes, verdict rules) follows the diy-review skill exactly.
- **Terminal or nothing.** The run ends only with the target `done` or `blocked` (AC-9.1).
- **HALT protocol (FR-3.6).** Every state transition is written to sprint.yaml the moment it happens, with `project.updated` bumped — executed by `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to <state> [--reason TEXT] [--rounds N] --json`, except `review→done`, which only the `done` command can write. Pass the current rework count as `--rounds N` on each HALT write so an interruption does not lose it; `loop.outcome` appears only in a terminal state (`blocked` via `transition --to blocked`, `done` via `done`). Interruption at any point leaves a truthful state on disk; the next invocation resumes from it (idempotent: existing evidence entries are kept, only missing TCs are run).
- **Rework rounds are bounded.** Capped at 2 rounds (R-4 cap); unresolved at the cap → `blocked` with `blocked_reason` citing the findings and the round count.
- **bad_spec routes to blocked.** Fixing stories.yaml/test-plan.yaml belongs to humans/upstream skills, not to the executor.
- **No falsification round in auto mode.** diy-review's optional post-pass falsification round stays user-triggered; this skill does not run it. Record nothing extra — its absence is not a finding.
- **Narrow ownership.** This skill writes only the target task's entry: statuses along the cycle, `loop` summary, plus the evidence/review blocks its stages produce. It never touches other tasks and never rewrites `test_refs`.
- **Terminal writes reach the sources of truth — 真源回填 (BUG-012).** The `done` command (`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" done --story <S-x> --rounds N --json`) performs `review → done` plus the backfill as one atomic batch: task `status: done` with `loop: {at, rounds, outcome: done}` in sprint.yaml, the story's `status: done` in `stories.yaml`, and `status: pass` for every TC this run executed green in `test-plan.yaml` (the dev stage already wrote these per diy-dev — the terminal write reconciles), bumping all touched `project.updated`. `blocked` is a sprint-level outcome only — it never writes `stories.yaml` or `test-plan.yaml`: the story is not delivered and nothing is passed. **Why:** the 2026-09-13 falsification round found the headless chain reaching terminal sprint states while the sources of truth stayed `pending`.
- Any judgment call carries the `[ASSUMPTION]` prefix in the YAML value.

## Single-Run Protocol

(`diyc.py` below abbreviates the full invocation `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py"`.)

```
resume-at = pending ? dev : (in-progress ? dev : review)
rounds = 0
if resume-at == dev:
    pending → in-progress   (HALT: diyc.py transition --to in-progress --rounds <rounds>)
    dev stage: for each test_refs TC — red line, minimal impl, static_checks (diyc.py static), green line (HALT: diyc.py green — evidence + test-plan backfill, one batch)
    in-progress → review    (HALT: diyc.py transition --to review --rounds <rounds>)
loop:
    review stage: layers L1-L4 + routing per diy-review; write review block (HALT write)
    pass  → done            (HALT: diyc.py done --rounds <rounds> — status + stories.yaml + test-plan.yaml, one batch); stop
    fail:
        if any finding routed bad_spec → blocked (HALT: diyc.py transition --to blocked --reason "<quote>" --rounds <rounds>); stop
        if rounds == 2                  → blocked (HALT: diyc.py transition --to blocked --reason "rounds exhausted + unresolved findings" --rounds <rounds>); stop
        rounds += 1
        review → in-progress (HALT: diyc.py transition --to in-progress --rounds <rounds>)
        dev stage: rework ONLY the routed findings; evidence appended per reworked TC (diyc.py green)
        in-progress → review (HALT: diyc.py transition --to review --rounds <rounds>); repeat loop
```

A red that cannot turn green during any dev stage → `blocked` with `blocked_reason` (per diy-dev honesty rule).

## Schema

Task entry in `sprint.yaml` gains (evidence/review blocks as defined by diy-dev/diy-review):
```yaml
  - story: S-9
    status: done|blocked
    loop:                         # written by diy-build-loop, one summary per run
      at: 2026-09-09
      rounds: 0-2                 # rework rounds consumed
      outcome: done|blocked
    blocked_reason: string        # iff outcome blocked: named gap / bad_spec quote / rounds exhausted
```

## Workflow

1. Restate in one line: target task, its state, resume point; then run On Activation and the Single-Run Protocol.
2. Render via diy-viewer (same activation command — append `--instance <name>` when one was resolved) at the terminal state. In interactive runs report the path; in headless (runner-invoked) runs render silently — no path report. Rendering is best-effort: if the command is not permitted in the harness or fails, record a one-line note and continue — a failed render never blocks, reverses, or invalidates the terminal write.
3. Close with the counts from the JSON receipts (TCs red/green this run, rework rounds used, findings by route, final status + reason; if blocked, name the exact unblock step: fix spec → diy-test-design, or clarify intent → re-run with args).
