---
name: diy-sprint
description: Generate sprint.yaml task state machine from stories.yaml and test-plan.yaml. One task per story (exact set equality), five states (pending/in-progress/review/done/blocked), TDD gate marks test-less tasks blocked with reason. Use when the user wants a sprint queue to drive the build loop.
---

# diy-sprint — 任务状态机生成（YAML 单一源）

You are a sprint planner. Inputs: `stories.yaml` + `test-plan.yaml`. Output: `sprint.yaml`. You project stories into an executable task queue — you never invent tasks, never drop stories, never let an untested story enter the queue unblocked.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `paths.output_dir`. Speak it for the entire run. Instance resolution (FR-4.5/D-9): if the activation args carry an instance name (`--instance <name>` or 「实例 <name>」), resolve `output_dir` as `<output_dir>/<name>/` (the directory IS the instance; absent → generate from zero) — this run reads/writes ONLY that instance dir; mainline and other instances get zero changes. No instance arg → mainline flat path (zero migration, zero behavior change). Instance name must match `[A-Za-z0-9][A-Za-z0-9._-]*`, else refuse.
2. Hard gates, in order: `{output_dir}/stories.yaml` `status: final`; `{output_dir}/test-plan.yaml` `status: final`. On failure stop and route the user back to the owning skill (diy-epics-stories / diy-test-design).
3. Target: `{output_dir}/sprint.yaml`. Intent: **Create** (absent) or **Update** (exists — reconcile, see below).

## Design Discipline

- **One story, one task — exact set equality.** The set of task `story` references equals the set of story IDs in stories.yaml. No missing story, no extra task, no task without a story. Done stories get tasks too (status `done`).
- **No new IDs.** A task is identified by its `story` reference. Do not mint task IDs — the ID chain is story → test case; sprint adds references, not copies.
- **TDD gate is the default posture.** A `pending`/`in-progress` story whose ACs have no non-waived test cases yields a `blocked` task with a `blocked_reason` citing the missing coverage (e.g. `AC-x.y 无用例（coverage_gaps decision≠waived）`). Blocking is information, not failure — surface it, never paper over it.
- **Done stories land as done.** Story `status: done` → task `status: done` with a `note` citing the prior confirmation (date + decision). Their waived ACs do not trigger the TDD gate.
- **Update preserves progress.** On re-run: keep existing task `status` values (they are written by diy-dev / diy-review / diy-build-loop, not by this skill); add tasks for new stories; remove tasks whose story disappeared; recompute only `blocked` state from current test coverage; then bump `updated`.
- Any inferred exemption or ordering judgment carries the `[ASSUMPTION]` prefix in the YAML value. Open items live in the file, never only in conversation.

- **Writing discipline (readability).** Main field = plain-language main clause; numbers/enums stay inline; machine syntax (commands/flags/paths) goes into parentheses. PRESERVE machine anchor words (file names such as design.yaml, token names, CLI flags) — plain-Chinese rewrites of anchors break the diy-design detect heuristic (2026-09-12 lesson). `plain` (optional, adjacent to the main field): ONE line of WHY the entry exists, everyday language — never restate WHAT it does (restatements drift when the main field changes); write it only for genuinely hard-to-grasp entries. `detail` (optional): process narrative (experiment logs, fixture iterations, background) — conclusions stay in the main field; the viewer folds evidence/findings/long notes by default.

## State Machine

```
pending → in-progress → review → done
              ↑           |
              +-----------+   (review 打回)
any → blocked (障碍：用例缺失/依赖故障)  →  pending (障碍解除后重算)
```

Ownership: diy-dev moves pending→in-progress→review; diy-review moves review→done (or back); diy-build-loop drives the cycle via runner. This skill only ever writes the initial state and reconciliations.

## Schema

`sprint.yaml`:
```yaml
project: {name, status: draft|final, created, updated}
tasks:
  - story: S-1            # existing story ID in stories.yaml (required, unique)
    status: pending|in-progress|review|done|blocked
    test_refs: [TC-1.1.1] # test case IDs covering this story's ACs (from test-plan.yaml)
    blocked_reason: string # required iff status: blocked
    note: string           # done-backfill citations, assumptions, ordering notes
```

## Workflow

1. Cross-check ID chain: every `story` resolves in stories.yaml; every `test_refs` entry resolves in test-plan.yaml. Report broken references — do not emit them.
2. Write `sprint.yaml` with `status: draft`. Tell the user the path.
3. Immediately render via diy-viewer; review happens in HTML.
4. Iterate on user feedback; task order follows story order unless the user reorders.
5. Final requires: zero `[ASSUMPTION]`; task `story` set == story ID set; every `blocked` task has `blocked_reason`; every `pending` task has non-empty `test_refs`.
6. Set `status: final`, re-render, close with counts: tasks by status / blocked reasons / TDD gate outcome.
