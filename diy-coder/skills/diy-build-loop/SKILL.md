---
name: diy-build-loop
description: Drive ONE sprint task from its current state to a terminal state (done/blocked) in a single invocation - the dev loop (TDD red/green per diy-dev), the review layers (per diy-review), and bounded rework rounds, all in one run. Writes every state transition back to sprint.yaml immediately (HALT protocol) so an external runner can resume from the breakpoint. Ambiguity it cannot resolve itself becomes blocked with a named reason - never spin. Use when the user says "run one iteration" / "iterate this task", or when the runner invokes it headless.
---

# diy-build-loop — 单次迭代（编码→自测→review→修复，YAML 单一源）

You are an iteration driver. Input: `sprint.yaml` + ONE target task. You orchestrate the disciplines of diy-dev and diy-review inside this run — you do not reinvent them, you do not skip them. The task must end this run in a terminal state (`done` or `blocked`) with every transition already written to sprint.yaml. You never pick up the next task; scheduling belongs to the runner (or the user).

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `paths.output_dir`. Speak it for the entire run. Instance resolution (FR-4.5/D-9): if the activation args carry an instance name (`--instance <name>` or 「实例 <name>」), resolve `output_dir` as `<output_dir>/<name>/` (the directory IS the instance; absent → generate from zero) — this run reads/writes ONLY that instance dir; mainline and other instances get zero changes. No instance arg → mainline flat path (zero migration, zero behavior change). Instance name must match `[A-Za-z0-9][A-Za-z0-9._-]*`, else refuse.
2. Hard gate: `{output_dir}/sprint.yaml` `project.status: final`. On failure stop and route back to diy-sprint.
3. Resolve target: explicit story ID from the invocation args, else the first non-terminal task (`pending` → full run; `in-progress` → resume at dev stage; `review` → resume at review stage). A `done`/`blocked` target is refused with its state named — terminal means no work left.
4. TDD gate (inherited from diy-dev): a `pending`/`in-progress` target whose `test_refs` are empty OR unresolvable in test-plan.yaml is set `blocked` with `blocked_reason` naming the missing/broken TC IDs (AC-9.2: ambiguity becomes blocked, not guessing). Zero implementation is produced. Refusal is a stop, not a workaround.

## Design Discipline

- **Orchestrate, don't duplicate.** Dev-stage behavior (red before green, minimal implementation, trace comments, evidence lines, static_checks before green) follows the diy-dev skill exactly; review-stage behavior (three layers, four routes, verdict rules) follows the diy-review skill exactly. This skill adds the loop, the bounds, and the HALT — nothing else.
- **Terminal or nothing.** The run ends only with the target `done` or `blocked` (AC-9.1). No exiting in an intermediate state, no deferring the state write.
- **HALT protocol (FR-3.6).** Every state transition (`pending→in-progress`, `in-progress→review`, `review→done`, `review→in-progress`, `any→blocked`) is written to sprint.yaml the moment it happens, with `project.updated` bumped. Interruption at any point leaves a truthful state on disk; the next invocation resumes from it (idempotent: existing evidence entries are kept, only missing TCs are run).
- **Rework rounds are bounded.** Each `review: fail → dev rework → review` cycle counts one round. Maximum **2** rework rounds per run (aligns with R-4's retry cap). Exhausted with findings unresolved → `blocked`, `blocked_reason` citing the unresolved findings and the round count. Never loop to entertain yourself.
- **bad_spec routes to blocked.** A review finding routed `bad_spec` means the spec is wrong — fixing stories.yaml/test-plan.yaml belongs to humans/upstream skills, not to the executor. The task goes `blocked` with the finding quoted in `blocked_reason`; the user corrects the spec, then re-runs. Never edit spec documents to unblock yourself.
- **No falsification round in auto mode.** diy-review's optional post-pass falsification round stays user-triggered; this skill does not run it. Record nothing extra — its absence is not a finding.
- **Narrow ownership.** This skill writes only the target task's entry: statuses along the cycle, `loop` summary, plus the evidence/review blocks its stages produce. It never touches other tasks and never rewrites `test_refs`.
- Any judgment call carries the `[ASSUMPTION]` prefix in the YAML value.

## Single-Run Protocol

```
resume-at = pending ? dev : (in-progress ? dev : review)
rounds = 0
if resume-at == dev:
    pending → in-progress (HALT write)
    dev stage: for each test_refs TC — red line, minimal impl, static_checks, green line (evidence written per diy-dev)
    in-progress → review (HALT write)
loop:
    review stage: three layers + routing per diy-review; write review block (HALT write)
    pass  → review → done (HALT write); stop
    fail:
        if any finding routed bad_spec → blocked (reason quotes it); stop
        if rounds == 2                  → blocked (reason: rounds exhausted + unresolved findings); stop
        rounds += 1
        review → in-progress (HALT write)
        dev stage: rework ONLY the routed findings; evidence appended per reworked TC
        in-progress → review (HALT write); repeat loop
```

A red that cannot turn green during any dev stage → `blocked` with `blocked_reason` (per diy-dev honesty rule) — same terminal exit, no weakened tests.

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

1. Resolve gates and target; restate in one line: target task, its state, resume point.
2. Execute the Single-Run Protocol; write every transition to sprint.yaml as it happens.
3. Render via diy-viewer at the terminal state; report the path.
4. Close with counts: TCs red/green this run, rework rounds used, findings by route, final status + reason (if blocked, name the exact unblock step: fix spec → diy-test-design, or clarify intent → re-run with args).
