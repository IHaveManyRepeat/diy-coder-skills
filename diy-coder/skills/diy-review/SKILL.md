---
name: diy-review
description: Review a sprint task in review state with layered audits - L1 correctness, L2 boundary, L3 acceptance-coverage, plus L4 design adoption for UI tasks whose ACs carry design_ref. Every finding routes to exactly one of intent_gap / bad_spec / patch / defer. Verdict pass moves the task to done after backfilling stories.yaml and test-plan.yaml; a fail with bad_spec blocks the task for upstream spec repair, any other fail sends it back to in-progress. Real defects found are also logged into bug-log.yaml (three-level classification) to feed future fault hypotheses. Optional falsification round after pass (--falsify <story|all>, accepted on done targets): attack the finished work with bug-log patterns and non-functional dimensions. Use when the user wants to review/audit a finished implementation or when diy-dev hands off.
---

# diy-review — 分层审查与路由（YAML 单一源）

You are a reviewer. Inputs: `sprint.yaml` + a task in `review` state + its implementation diff + `stories.yaml` (AC detail) + `test-plan.yaml` (claimed coverage). You audit, you route, you never rewrite the implementation yourself.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root (mainline flat path when no instance arg; absent instance dir → generate from zero; other instances get zero changes; invalid names are refused by the script).
2. Hard gate: `{output_dir}/sprint.yaml` `project.status: final`. Target task must be `status: review`; any other state is refused with its state named (pending → diy-dev first; in-progress → dev loop not finished). Exception: `--falsify <story|all>` also accepts `done` targets — that run executes ONLY step 6 (falsification), never the layer audits. `blocked` is always refused.
3. Material: the task's implementation files + its `evidence` entries + the story's ACs + the referenced TC steps.

## Layers

- **L1 correctness (正确性).** Does the implementation do exactly what the ACs say — no missing then-clause, no extra unasked behavior? Compare AC by AC. Trace discipline gives you the grip: every method in the diff must carry a `# trace:` comment (see diy-dev) whose IDs resolve in stories/test-plan — run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" trace --json` and take every entry in its `unresolved` list as a finding (route `patch`); a missing `# trace:` line remains a human read of the diff. For each traced method, check its behavior against the traced AC: code claiming `AC-9.1` but not delivering its then-clause is an L1 correctness finding naming the trace line.
- **L2 boundary (边界).** Walk failure modes the ACs imply but do not spell out: bad input, empty/None, concurrency, error paths, silent fallbacks. Report only unhandled cases that could bite.
- **L3 coverage audit (验收覆盖审计).** You do NOT re-accept manually. Run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type review --story <S-x> --json` — it mechanically checks the four ledger items: every `test_refs` TC has an `evidence` entry; every red line precedes its green; evidence results agree with test-plan TC `status`; every TC bound to the task carries non-empty `kill_target` and a `technique` valid against the test-plan schema enum (diy-test-design) — a missing or out-of-enum declaration means the case may be decorative (cannot distinguish correct code from the fault it should kill), so flag it naming the TC ID. What remains a human read: whether the TC steps actually assert the AC's then-clause. Any mismatch — reported by the script or found by the read — is a finding naming the TC ID, the claim, and the actual record (AC-8.2). Entries in the receipt's `known[]` are user-ratified baselines, not violations to fix.
- **L4 design adoption (设计采用审查, FR-3.7/D-10 — UI tasks only).** When the task's ACs carry `design_ref`, verify ADOPTION — the design deliverable (framework pages written by diy-design) is the baseline the implementation must build on. Screenshot comparison is deprecated (pixel diff proved unreliable; the `compare` engine was deleted 2026-09-12). Check four things, each violation a `patch` finding, task back to `in-progress` (HALT): (a) 结构对照 — implementation page structure must match the 线框（wireframe/HTML）structural draft (`prototype` in design.yaml): sections, hierarchy, landmark order; (b) 零重写 — implementation builds ON the design code (`implementation` paths in design.yaml), not a re-implementation of it; a rewritten UI is a finding even if it looks similar; (c) token 单一源 — `python design.py audit --design {output_dir}/design.yaml --src <impl>` — every `one-off-*` violation is a finding; (d) accessibility — `python design.py check --design {output_dir}/design.yaml` violations are findings. Never skip the layer silently — a skip needs the user's explicit call.

- **Writing discipline (readability).** Main field = plain-language main clause; numbers/enums stay inline; machine syntax (commands/flags/paths) goes into parentheses. PRESERVE machine anchor words (file names such as design.yaml, token names, CLI flags) — plain-Chinese rewrites of anchors break the diy-design detect heuristic (2026-09-12 lesson). `plain` (optional, adjacent to the main field): ONE line of WHY the entry exists, everyday language — never restate WHAT it does (restatements drift when the main field changes); write it only for genuinely hard-to-grasp entries. `detail` (optional): process narrative (experiment logs, fixture iterations, background) — conclusions stay in the main field; the viewer folds evidence/findings/long notes by default.

## Bug Logging (defects feed the experience loop)

Every finding that exposes a REAL defect (not a spec issue) is additionally appended to `{output_dir}/bug-log.yaml` — the project's defect pattern library — via `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" bug-add --entry '<json-object>' --json` (`--entry-file PATH` for long entries). The command validates the taxonomy, mints the next sequential `id` (`BUG-0xx`), and writes atomically; a rejected entry (exit 1) is not written. Entry fields: `source story class subclass type symptom root_cause trigger fix prevention pattern` (`date` optional, defaults to today). Three-level classification (type is a free-expanding tag; reuse the existing type name when the phenomenon matches, mint a new one only when genuinely new):

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

If `paths.experience_repo` is configured and present, remind the user to run `python diy-coder/exp-sync.py push` from the project root — add `--instance <name>` in instance runs (the bug-log lives in the instance dir). It buckets entries by `subclass` into the cross-project experience repo and registers new `type` tags. The experience repo is a projection; this task's `bug-log.yaml` stays the source of truth.

## Routing (each finding gets exactly one)

| route | meaning | disposition |
|---|---|---|
| `intent_gap` | implementation misses or contradicts the stated intent | back to diy-dev |
| `bad_spec` | the spec itself is wrong or ambiguous — code is fine | fix stories.yaml / test-plan.yaml, not code |
| `patch` | small localized fix solves it | back to diy-dev (one-line scope) |
| `defer` | real but not worth blocking now | recorded, does not block |

## Verdict Rules

- **fail** if any finding routes `intent_gap` / `patch` / `bad_spec`; findings written to the task entry. Disposition via `transition`: any `bad_spec` present → `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to blocked --reason "<finding quote>" --json` — the spec is fixed upstream, never by an executor (matches diy-build-loop); else → `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to in-progress --json` (back to the dev loop).
- **pass** if findings are empty or all `defer` → write the review block + `note` (citing the review date) into the task entry, then `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" done --story <S-x> --json`.
- **真源回填 (BUG-012).** The `done` command performs `review → done` and the backfill as one atomic batch: the task's `status: done`, the story's `status: done` in `stories.yaml`, and `status: pass` for every TC this task confirmed green in L3 in `test-plan.yaml` (`diy-dev` writes the TC lines per green line; the terminal write reconciles), bumping all touched `project.updated`. `blocked` never writes either file — nothing is delivered or passed. **Why:** the 2026-09-13 quality analysis found this standalone path reporting `done` while the sources of truth stayed `pending` (same class as BUG-012 in the headless chain).
- Task-state ownership in `sprint.yaml`: `review → done` (pass — only via `done`; `transition` refuses this edge), `review → in-progress` (fail), `review → blocked` (bad_spec), and `done → in-progress` (a falsification hit — step 6), the latter three via `transition`. Nothing else.
- Any judgment call carries the `[ASSUMPTION]` prefix in the YAML value.

## Schema

Task entry in `sprint.yaml` gains:
```yaml
    review:
      at: 2026-09-05
      verdict: pass|fail
      findings:                  # may be empty on clean pass
        - layer: correctness|boundary|coverage|design   # design = L4; a falsification hit uses the layer it belongs to
          route: intent_gap|bad_spec|patch|defer
          note: one-line finding (coverage findings name TC ID + claim vs record)
```

## Workflow

1. Load the material named in On Activation; restate the review scope in one line. (With `--falsify` on a `done` target, skip straight to step 6.)
2. Run L1 → L2 → L3 → L4 in order; L4 runs only when the task's ACs carry `design_ref` — a skip is stated in the report, never silent. Collect findings; verify each route against the table — exactly one per finding.
3. Write the `review` block into the task entry; run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type review --story <S-x> --json` — exit 0 confirms the block is structurally valid (verdict/layer/route enums, pass/fail consistency, ledger) — then set status and write-backs per Verdict Rules (`done` for pass; `transition` for fail/blocked; those commands bump `project.updated`).
4. Render via diy-viewer (same activation command — append `--instance <name>` when one was resolved); report the review surface (path) with the verdict and routed findings.
5. On fail, name the next step (diy-dev rework items; blocked → the upstream spec fix in stories.yaml / test-plan.yaml); on pass, close with the counts from the JSON receipt (findings by layer, findings by route, verdict).
6. **Falsification round (optional — `--falsify <story|all>`, accepted on `done` targets; `all` = every done task in the sprint).** Goal: break the finished work — assume it IS buggy. Aim the `bug-log.yaml` patterns at this implementation, walk the non-functional checklist (performance, UX, security, compatibility, reliability, boundary) asking "how would this break?", and run ad-hoc attacks. Any hit: append via `bug-add`, route it (`intent_gap` / `patch`), and the task leaves `done` → `in-progress` (HALT write: `transition --story <S-x> --to in-progress --json`). Clean round: record one line in the task `note` (date + "证伪轮通过").
