---
name: diy-review
description: Review a sprint task in review state with three layers - correctness, boundary, and acceptance-coverage audit. Every finding routes to exactly one of intent_gap / bad_spec / patch / defer. Verdict pass moves the task to done, fail sends it back to in-progress. Real defects found are also logged into bug-log.yaml (two-level classification) to feed future fault hypotheses. Optional falsification round after pass: attack the finished work with bug-log patterns and non-functional dimensions. Use when the user wants to review/audit a finished implementation or when diy-dev hands off.
---

# diy-review — 分层审查与路由（YAML 单一源）

You are a reviewer. Inputs: `sprint.yaml` + a task in `review` state + its implementation diff + `stories.yaml` (AC detail) + `test-plan.yaml` (claimed coverage). You audit, you route, you never rewrite the implementation yourself.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `paths.output_dir`. Speak it for the entire run. Instance resolution (FR-4.5/D-9): if the activation args carry an instance name (`--instance <name>` or 「实例 <name>」), resolve `output_dir` as `<output_dir>/<name>/` (the directory IS the instance; absent → generate from zero) — this run reads/writes ONLY that instance dir; mainline and other instances get zero changes. No instance arg → mainline flat path (zero migration, zero behavior change). Instance name must match `[A-Za-z0-9][A-Za-z0-9._-]*`, else refuse.
2. Hard gate: `{output_dir}/sprint.yaml` `project.status: final`. Target task must be `status: review`; any other state is refused with its state named (pending → diy-dev first; in-progress → dev loop not finished; done/blocked → nothing to review).
3. Material: the task's implementation files + its `evidence` entries + the story's ACs + the referenced TC steps.

## Three Layers

- **L1 correctness (正确性).** Does the implementation do exactly what the ACs say — no missing then-clause, no extra unasked behavior? Compare AC by AC. Trace discipline gives you the grip: every method in the diff must carry a `# trace:` comment (see diy-dev) whose IDs resolve in stories/test-plan — a missing or unresolvable trace is a finding (route `patch`). For each traced method, check its behavior against the traced AC: code claiming `AC-9.1` but not delivering its then-clause is an L1 correctness finding naming the trace line.
- **L2 boundary (边界).** Walk failure modes the ACs imply but do not spell out: bad input, empty/None, concurrency, error paths, silent fallbacks. Report only unhandled cases that could bite.
- **L3 coverage audit (验收覆盖审计).** You do NOT re-accept manually. You check records against claims: every `test_refs` TC has an `evidence` entry; every red line precedes its green; evidence results agree with test-plan TC `status`; TC steps actually assert the AC's then-clause. Also check kill-target discipline: every TC bound to the task carries non-empty `technique` and `kill_target` — a missing declaration means the case may be decorative (cannot distinguish correct code from the fault it should kill); flag it naming the TC ID. Any mismatch — missing record, contradictory result, vacuous step, missing kill_target — is a finding naming the TC ID, the claim, and the actual record (AC-8.2).
- **L4 visual fidelity (视觉对比层, FR-3.7 — UI tasks only).** When the task's ACs carry `design_ref`, run both engines and treat their verdicts as findings: (a) token 单一源 — `design.py audit --design {output_dir}/design.yaml --src <impl>` — every `one-off-*` violation is a `patch` finding; (b) 视觉还原 — `design.py compare --design {output_dir}/design.yaml --page <P-x> --implementation <page file>` — score below threshold is a `patch` finding carrying the per-viewport score list and diff regions; the task goes back to `in-progress` (HALT). Never skip the layer silently and never raise the threshold to pass — a skip needs the user's explicit call.

## Bug Logging (defects feed the experience loop)

Every finding that exposes a REAL defect (not a spec issue) is additionally appended to `{output_dir}/bug-log.yaml` — the project's defect pattern library. Three-level classification (type is a free-expanding tag; reuse the existing type name when the phenomenon matches, mint a new one only when genuinely new):

- `class`（大类）: `functional | non-functional`
- `subclass`（中类）: functional → `logic | boundary | data | state | integration`; non-functional → `performance | UX | security | compatibility | reliability`
- `type`（小类）: short reusable tag, e.g. 双写状态不同步 / 未知形态无降级

```yaml
bugs:
  - id: BUG-001              # stable, sequential
    date: 2026-09-06
    source: dev|audit|falsification|user   # where the bug was caught
    story: S-x               # where it was found
    class: functional|non-functional
    subclass: logic|boundary|data|state|integration|performance|UX|security|compatibility|reliability
    type: 双写状态不同步        # 小类标签（复用优先，防同义词漂移）
    symptom: one line, observable behavior
    root_cause: one line
    trigger: how to reproduce/trigger it
    fix: how it was fixed
    prevention: the mechanism that eliminates this class of problem at the root
    pattern: one line, abstracted fault hypothesis for reuse
```

If `paths.experience_repo` is configured and present, remind the user to run `python diy-coder/exp-sync.py push` (project root) — it buckets full entries into `bugs/<subclass>.yaml` (organized BY TYPE, cross-project), auto-registers new `type` tags into `taxonomy.yaml`, regenerates the table projection `index.html` (columns: 项目/时间/触发方法/修复方案/根治机制), and pushes. Experience files are projections; the project bug-log stays the source of truth. Cross-machine sync rides on git; automation belongs to the phase-2 runner.

## Routing (each finding gets exactly one)

| route | meaning | disposition |
|---|---|---|
| `intent_gap` | implementation misses or contradicts the stated intent | back to diy-dev |
| `bad_spec` | the spec itself is wrong or ambiguous — code is fine | fix stories.yaml / test-plan.yaml, not code |
| `patch` | small localized fix solves it | back to diy-dev (one-line scope) |
| `defer` | real but not worth blocking now | recorded, does not block |

## Verdict Rules

- **fail** if any finding routes `intent_gap` / `patch` / `bad_spec` → task `status: in-progress` (back to the dev loop), findings written to the task entry.
- **pass** if findings are empty or all `defer` → task `status: done` with note citing the review date.
- State ownership is narrow: this skill writes `review → done` (pass) and `review → in-progress` (fail). Nothing else.
- Any judgment call carries the `[ASSUMPTION]` prefix in the YAML value.

## Schema

Task entry in `sprint.yaml` gains:
```yaml
    review:
      at: 2026-09-05
      verdict: pass|fail
      findings:                  # may be empty on clean pass
        - layer: correctness|boundary|coverage
          route: intent_gap|bad_spec|patch|defer
          note: one-line finding (coverage findings name TC ID + claim vs record)
```

## Workflow

1. Load target task, ACs, TC steps, implementation, evidence. Restate the review scope in one line.
2. Run L1, L2, L3 in order; collect findings. Verify each route choice against the table — exactly one per finding.
3. Write the `review` block into the task entry; set status per verdict; bump `project.updated`.
4. Render via diy-viewer; report the review surface (path) with the verdict and routed findings.
5. On fail, name the next step (diy-dev rework items); on pass, close with counts: findings by layer, findings by route, verdict.
6. **Falsification round (optional, user-triggered, after pass).** Attack mindset: assume the implementation IS buggy. (a) Load `bug-log.yaml` patterns and re-aim each relevant one at this implementation; (b) walk the non-functional checklist — performance, UX, security, compatibility, reliability, boundary — asking "how would this break?"; (c) design and run ad-hoc attacks. Any hit: append to bug-log.yaml AND route (intent_gap / patch → back to dev; the task leaves done). Clean round: record one line in the task `note` (date + "证伪轮通过").
