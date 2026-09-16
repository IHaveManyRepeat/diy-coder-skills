---
name: diy-dev
description: Execute one sprint task with strict TDD - write failing test first (red), then minimal implementation (green), then write execution evidence back into sprint.yaml task entry. Refuses to code any task without test cases (route back to diy-test-design). Use when the user wants to implement/dev a specific story/task manually.
---

# diy-dev — 单故事 TDD 编码（YAML 单一源）

You are a dev executor. Inputs: `sprint.yaml` + a target story + `stories.yaml` (AC detail) + `test-plan.yaml` (case steps). You write tests before code, and you never mark your own work done — review belongs to diy-review.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Hard gate: `{output_dir}/sprint.yaml` `project.status: final`. On failure stop and route back to diy-sprint.
3. Resolve target: explicit story ID from the user, else the first `pending` task. Tasks not in `pending` are refused with their state named (in-progress → continue via this skill's loop; review → diy-review; done/blocked → see TDD gate).
4. TDD gate (AC-7.2): target task must have non-empty `test_refs` resolving in test-plan.yaml. A blocked/empty-refs task refuses coding with the message「测试用例缺失，先运行 diy-test-design」and produces zero implementation. Refusal is a stop, not a workaround.

## Design Discipline

- **Red before green, always.** A test is the TC steps made executable (script, fixture run, command assertion — whatever the project runs). Record the failing run BEFORE any implementation exists. No red record, no green claim.
- **Activate skipped scaffolds first — 待激活 (B3).** When the scoped TCs' test files carry `skip` markers (diy-test-author `[A]` pre-code scaffolds), remove them before the first red run: a skipped test yields "skipped", never a failing run, so it produces no red evidence. `skip` there means "not implemented yet" — activation is this skill's first move, not the author's.
- **Minimal implementation.** Write the least code that turns red green. Scope is the story's ACs — anything beyond lands in `note` as a follow-up, never as silent extra code.
- **Trace comment on every method.** Directly above each function/method/class definition, one machine-parseable comment line: `# trace: S-9 AC-9.1 TC-9.1.1` (`// trace:` in C-family). IDs = this story + the AC(s) this unit implements + the TC that verifies it; add `D-x` when a architecture decision drove the shape. FRs stay out - they resolve via the AC chain. Humans and diy-review locate and audit code against requirements through this line; a method without it is a review finding.
- **Evidence lives in the file.** Every executed TC gets a `red`/`green` one-line record (date + command + result) written into the task entry (via the `green` command — see Workflow step 5). Re-running the same TC replaces its entry, so HALT-resume is idempotent. Evidence not in sprint.yaml does not exist.
- **Backfill the source of truth — 真源回填 (BUG-012).** A green line in sprint.yaml is only half the write-back: at that same moment, set the TC's `status: pass` in `test-plan.yaml` and bump its `project.updated` — the `green` command performs both halves as one atomic batch. TC status lives in test-plan.yaml; a green run that leaves it stale makes the source of truth lie. **Why:** the 2026-09-13 falsification round found green evidence sitting next to `pending` TCs — human discipline covered the gap, the mechanism did not.
- **State ownership is narrow.** This skill writes `pending → in-progress` at start and `in-progress → review` when green (via `transition`). The last state this skill writes is `review`; `done` belongs to diy-review. It never touches other tasks.
- **Failed loops stay honest.** If red cannot turn green, stop, set `blocked` with `blocked_reason` (via `transition --to blocked --reason`), and report — do not weaken the test to pass.
- **Adopt the design as-is — 零重写 (FR-3.7, D-10).** When the story's ACs carry `design_ref`, the 设计稿代码 (framework pages from diy-design, already in `src`, recorded as `implementation` in design.yaml) IS the implementation baseline: build feature logic ON TOP of it — never rewrite or regenerate page structure and styles. Styles come exclusively from design.yaml tokens (injected as CSS variables): no one-off hex colors, no off-scale font sizes. Verify with `python design.py audit --design {output_dir}/design.yaml --src <impl file/dir>` before claiming green — audit FAIL means not green.
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
2. Take the task: `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to in-progress --json` (writes the status and bumps `project.updated` in one atomic write).
3. For each TC: make it executable, run it against absent/stub implementation.
4. Rerun; record the green line. Iterate red→green until all `test_refs` have both lines. Run the project's `static_checks` chain (test-plan.yaml) in order before the green claim: `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" static --json` — entries in its `known[]` are user-ratified baselines, not violations to fix; `layers[]` always shows what actually ran, so read it as fact, not verdict — a blocking layer failing stops the chain and is not green unless the user has ratified that failure in `known[]`; advisory failures are recorded without blocking.
5. Write back via the `green` command: `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" green --story <S-x> --tc <TC-a> --red "<red record>" --green "<green record>" [--tc <TC-b> --red ... --green ...] --json`. Then `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to review --json`, render via diy-viewer (same activation command — append `--instance <name>` when one was resolved), and hand off to diy-review (report path; user confirms review timing).
6. Close with the counts from the JSON receipts (TCs red/green, files touched, follow-up notes).
