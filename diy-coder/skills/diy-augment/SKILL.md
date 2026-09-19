---
name: diy-augment
description: Coded-post test augmentation. After a task reaches done, run the project's coverage toolchain against the implementation, triage uncovered branches, condition combinations, and paths, then append complementary cases (覆盖分支 / MC-DC 覆盖 / 白盒路径) to test-plan.yaml with stable per-AC TC IDs, execute them, write back status, and leave the verdict (通过 / 失败 / 已跳过) on the task's augment field in sprint.yaml. When a mutation toolchain is configured, also run it against a sandboxed copy and close survivors with 变异杀伤 cases, recording the run in mutation-report.yaml. Report-only on failures — this skill never reopens a task; reopening is a user verdict executed via runner --reopen-failed. Invoked by runner.py after each done task; standalone invocation with a task ID is equivalent.
---

# diy-augment — 编码后补测（覆盖率驱动追加 TC）

You are a coverage-gap closer. Input: a `已完成` task plus its implementation. Output: appended cases in `test-plan.yaml` that kill the faults the pre-coding plan could not foresee. You never invent coverage: every appended case binds an existing AC, cites the coverage evidence that motivated it, and declares its `kill_target`. Zero gaps → zero writes.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in document_output_language; converse in communication_language. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Load `{output_dir}/sprint.yaml`; locate the task named in the activation prompt. Hard gate: its `status` must be `已完成` — augmentation is post-coding only; any other status → one-line report and stop. The task's `augment` field, if present (`通过` / `失败` / `已跳过`), marks a prior verdict: the run reconciles against it instead of duplicating cases.
3. Load `{output_dir}/test-plan.yaml` and `{output_dir}/stories.yaml`; resolve the story's ACs and the existing per-AC TC sequence (highest seq per AC).
4. Write scope (four surfaces, nothing else): appended cases in `{output_dir}/test-plan.yaml`; the verdict on this task's `augment` field in `sprint.yaml`; the appended TC IDs merged into this task's `test_refs` in `sprint.yaml`; the mutation run (only when one was executed) in `{output_dir}/mutation-report.yaml`. `status`, `blocked_reason`, and `note` are never touched; `stories.yaml`, source code, and other artifacts get zero writes. The sandbox copy is never the working tree — it is created and discarded by the mutation runner.

## Augmentation Discipline

- **Coverage first, cases second.** Run the project's coverage toolchain (derive from architecture.yaml / static_checks) against the task's implementation surface (the files the task changed). Only reported gaps become cases — an untested item the coverage run never flags is out of scope.
- **Gap maps to technique.** Uncovered branch → `覆盖分支`; uncovered condition combination (MC/DC) → `MC-DC 覆盖`; uncovered execution path → `白盒路径`. Never pick the nine design techniques here — they belong to diy-test-design.
- **Mutation survivors are first-class gaps — 变异驱动 (2026-09-15).** When the project configures a mutation toolchain, run it against a **sandboxed copy** of the project (never the working tree), scoped to this task's implementation surface. A survivor — a mutant the suite failed to kill — means the code was executed yet no assertion distinguished wrong from right: a gap of higher order than an uncovered branch. Map each survivor to `变异杀伤` and derive one case pinpointing the mutated behavior (the mutant's fault IS the kill_target). **Equivalent mutants are never cases** — list them in the report for user adjudication; they feed the gate's `waivers`, they must not lower the score. The run is recorded in `{output_dir}/mutation-report.yaml`: `{project, runs: [{date, task, scope, killed, total, score, survivors: [{mutant, file, line}], equivalents: [{mutant, reason}]}], revisions}`. Toolchain absent or not permitted → one-line note, no report, not a verdict.
- **Sequence continues, IDs stay stable.** New TC ID = AC id minus prefix + next seq for that AC (AC-5.1 with TC-5.1.1 existing → TC-5.1.2). Never renumber, never reuse.
- **kill_target mandatory.** Name the concrete fault the case kills — typically a missing-branch, inverted-condition, or unexercised-path hypothesis made real by the coverage evidence. A case whose failure would not distinguish correct code from that fault is decorative — cut it.
- **No placeholder cases.** Zero gaps → report zero and write nothing. No speculative cases "for future safety".
- **Verdict is mandatory — always leave one.** End every run with exactly one `augment` value on the task: `通过` (all executed cases green), `失败` (at least one case red — the defect is real and awaits a user verdict), `已跳过` (coverage toolchain unavailable or not permitted; nothing was executed). The verdict is what the runner reports on and what `--augment-only` resumes from — a missing verdict is indistinguishable from "never ran".
- **Failures are verdict-only.** Write `status: 失败` on the case, set `augment: 失败`, list the case with reproduction evidence (command + observed vs expected) in the closing summary, and stop. The task's `status` stays `已完成` — this skill never reopens a task. Reopening is a user verdict: the user adjudicates collected failures and runs `runner.py --reopen-failed` to reopen, fix, and re-augment.
- **Rerun reconciles, never duplicates.** A case equivalent to an existing appended case (same AC, same technique, same kill_target) is updated in place — refresh its `status` from the rerun instead of appending a twin. New IDs only for genuinely new gaps; the verdict is overwritten with the fresh run's outcome.
- **Evidence in `note`.** Each appended case carries `note` = the coverage evidence that motivated it (tool + uncovered item), in document_output_language prose. Machine anchors (commands, IDs) stay verbatim.
- **Best-effort rendering, silent in automated runs.** Render via diy-viewer after writing — in interactive runs report the path, in automated/headless runs render silently (no path report). If the command is not permitted in the harness or fails, record a one-line note and continue — a failed render never blocks, reverses, or invalidates the write-back.

## Workflow

1. Establish the coverage baseline: run the coverage command for the project's stack against the task's implementation surface. Tool missing or not permitted → set `augment: 已跳过`, report the reason, and stop; do not install anything.
2. Triage gaps: map each uncovered item to a technique per the discipline above; drop items below the project's coverage gate unless they sit on an AC path. **When a mutation toolchain is configured, also run it against a sandboxed copy scoped to this task's surface and triage survivors the same way (`变异杀伤`; equivalents reported for adjudication, never cases), writing the run to `{output_dir}/mutation-report.yaml` — toolchain absent is a one-line note, not a verdict.** On a rerun (task already carries a verdict), first reconcile: equivalent cases are updated in place, not duplicated.
3. Derive and append cases to `test-plan.yaml` with `status: 待办`, `technique`, `kill_target`, `note`, and concrete `steps` (same schema as diy-test-design); merge the new TC IDs into this task's `test_refs`.
4. Execute the cases; write back `通过` / `失败` on each, then leave the task's verdict (`通过` / `失败` / `已跳过`) on `augment`.
5. Render via diy-viewer (same activation command — append `--instance <name>` when one was resolved):
   `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`
   Close with counts: cases appended by technique / 通过 / 失败 / verdict, and gaps remaining.

## Rules

1. Write scope is exactly four surfaces: `test-plan.yaml` (appended cases + their status), this task's `augment` field, this task's `test_refs`, and `mutation-report.yaml` (mutation runs only, when executed). The task's `status` is never written — a `已完成` task stays `已完成`; reopening is a user verdict via `runner.py --reopen-failed`. `stories.yaml`, source code, and other artifacts get zero writes.
2. Every appended case binds an existing AC and carries a schema-enum technique (`覆盖分支` | `MC-DC 覆盖` | `白盒路径` | `变异杀伤`), non-empty `kill_target`, and `note` with the evidence that motivated it (coverage item, or the mutant's identity and fault for `变异杀伤` cases).
3. The render command requires PyYAML on the host Python. If it fails with `ModuleNotFoundError`, report the error and suggest `pip install pyyaml`. Do not silently fall back.
4. Invoked by runner.py after each `已完成` task; standalone invocation with a single task ID is equivalent. Failures (coverage tool, execution, render) degrade to a report — never a blocker.
