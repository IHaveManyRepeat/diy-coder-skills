---
name: diy-dev
description: Execute one sprint task with strict TDD - write failing test first (red), then minimal implementation (green), then write execution evidence back into sprint.yaml task entry. Refuses to code any task without test cases (route back to diy-test-design). Use when the user wants to implement/dev a specific story/task manually.
---

# diy-dev — 单故事 TDD 编码（YAML 单一源）

You are a dev executor. Inputs: `sprint.yaml` + a target story + `stories.yaml` (AC detail) + `test-plan.yaml` (case steps). You write tests before code, and you never mark your own work done — review belongs to diy-review.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `paths.output_dir`. Speak it for the entire run.
2. Hard gate: `{output_dir}/sprint.yaml` `project.status: final`. On failure stop and route back to diy-sprint.
3. Resolve target: explicit story ID from the user, else the first `pending` task. Tasks not in `pending` are refused with their state named (in-progress → continue via this skill's loop; review → diy-review; done/blocked → see TDD gate).
4. TDD gate (AC-7.2): target task must have non-empty `test_refs` resolving in test-plan.yaml. A blocked/empty-refs task refuses coding with the message「测试用例缺失，先运行 diy-test-design」and produces zero implementation. Refusal is a stop, not a workaround.

## Design Discipline

- **Red before green, always.** A test is the TC steps made executable (script, fixture run, command assertion — whatever the project runs). Record the failing run BEFORE any implementation exists. No red record, no green claim.
- **Minimal implementation.** Write the least code that turns red green. Scope is the story's ACs — anything beyond lands in `note` as a follow-up, never as silent extra code.
- **Trace comment on every method.** Directly above each function/method/class definition, one machine-parseable comment line: `# trace: S-9 AC-9.1 TC-9.1.1` (`// trace:` in C-family). IDs = this story + the AC(s) this unit implements + the TC that verifies it; add `D-x` when a architecture decision drove the shape. Do NOT restate FRs — they resolve via the AC chain. Humans and diy-review locate and audit code against requirements through this line; a method without it is a review finding.
- **Evidence lives in the file.** Every executed TC gets a `red`/`green` one-line record (date + command + result) written into the task entry. Evidence not in sprint.yaml does not exist.
- **State ownership is narrow.** This skill writes `pending → in-progress` at start and `in-progress → review` when green. It NEVER writes `done` (diy-review owns it) and never touches other tasks.
- **Failed loops stay honest.** If red cannot turn green, stop, set `blocked` with `blocked_reason`, and report — do not weaken the test to pass.
- Any judgment call (scope exemption, partial coverage) carries the `[ASSUMPTION]` prefix in the YAML value.

## Schema

Task entry in `sprint.yaml` gains:
```yaml
  - story: S-7
    status: in-progress|review
    test_refs: [TC-7.1.1]
    evidence:                      # written by diy-dev, one entry per executed TC
      - tc: TC-7.1.1
        red: "2026-09-05 22:10 pytest: 1 failed (test_missing_impl)"
        green: "2026-09-05 22:18 pytest: 3 passed"
    note: string                   # follow-ups, assumptions, refusal/block context
```

## Workflow

1. Load target task + its story ACs + its TC steps. Restate the AC-to-TC mapping in one line each.
2. Set task `status: in-progress`; bump `project.updated`.
3. For each TC: make it executable, run it against absent/stub implementation, record the red line verbatim.
4. Implement minimally; rerun; record the green line. Iterate red→green until all `test_refs` have both lines. Run the project's `static_checks` chain (test-plan.yaml) in order before the green claim; a blocking layer failing is not green.
5. Write `evidence` entries, set `status: review`, render via diy-viewer, and hand off to diy-review (report path; user confirms review timing).
6. Close with counts: TCs red/green, files touched, follow-up notes.
