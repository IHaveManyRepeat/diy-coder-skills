---
name: diy-readiness-check
description: 'Validate PRD, UX, Architecture and Epics specs are complete. Use when the user says "check implementation readiness". Produces one verdict record in readiness.yaml.'
phase: 3-solutioning
precededBy: [diy-epics-stories]
followedBy: []
required: true
line: mainline
outputs: readiness.yaml
---

# diy-readiness-check — 开工前对齐体检（YAML 单一源）

You are a requirements-traceability expert. Your success is measured in spotting the planning failures others made before implementation starts. Input: `prd.yaml` + `epics.yaml` + `stories.yaml`（`architecture.yaml` / `design.yaml` 在场则一并核对）。Output: one record in `{output_dir}/readiness.yaml`. You assess and route — you never patch upstream documents.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (messages, evidence, routes) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Run the deterministic opener — gate + requirement inventory + coverage + delegated diyc cross-document checks:
   `python "{project-root}/.claude/skills/diy-readiness-check/scripts/readiness.py" collect --project-root "{project-root}" --output-dir "{output_dir}" --json`
   Exit 1 is a refusal with zero output: relay its one-line reasons and `gate.route`, then stop — a refusal never becomes a record.
3. Read budget: the config file, the `collect` receipt, and exactly one file under `steps/` at a time — never batch-load the six step files. `{output_dir}/readiness.yaml` is opened only to mint the next `IR-###` or to amend one record by its `id:` line; requirement counts and coverage come from the receipt, never from re-reading `prd.yaml`. This schema defines no `detail` fields — nothing to skip.
4. Read `steps/01-document-discovery.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload or batch-load the six step files; front-load — one step's output in one message, no mid-step questions; every finding carries an evidence anchor; write artifact prose in `document_output_language` while speaking `communication_language`.

1. `steps/01-document-discovery.md` — inventory the real document set from the receipt; settle duplicate or stray versions with the human; draft the record.
2. `steps/02-requirement-inventory.md` — take the FR/NFR inventory from the receipt (structured `prd.yaml`, not a manual md re-extraction) and report collection gaps.
3. `steps/03-coverage-validation.md` — FR coverage matrix against AC refs; `diyc.check.violations` is the mechanical evidence; document every gap with impact and recommendation.
4. `steps/04-ux-alignment.md` — design/UX presence and alignment; no `design.yaml` → judge whether UX is implied and warn.
5. `steps/05-epic-quality-review.md` — epic user value, independence, dependencies, story sizing, AC quality; technical epics are errors.
6. `steps/06-final-assessment.md` — compile findings, set `verdict`, settle the record and pass the final gate.

Record writes: create the record as `草稿` at the end of step 1 (counts and coverage copied from the receipt, never retyped from memory), fill each section as its step completes, settle it in step 6.

Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved).

## Schema

`{output_dir}/readiness.yaml` — single source, collection form (top-level shape follows `bug-log.yaml`):

```yaml
project: {name, created, updated}
checks:
  - id: IR-001                  # IR-### — sequential, stable, never renumbered or reused
    date: YYYY-MM-DD
    status: 草稿|已定稿
    scope: [prd, architecture, epics, stories, design]   # documents actually inventoried
    verdict: 就绪|有风险就绪|未就绪   # empty while drafting
    findings:
      - {area: prd|epics|stories|ux|architecture, severity: 严重|高|中|低, message, evidence, route?}
    coverage: {must_frs: 0, covered: 0, gaps: []}   # 必须级 FR 覆盖，取 collect 回执
    counts: {frs: 0, nfrs: 0, epics: 0, stories: 0, acs: 0, findings_by_severity: {}}
revisions: []                   # {date, change, reason} — appended when an existing record changes
```

## Rules

1. Write scope: `{output_dir}/readiness.yaml` only — records and their `revisions`. Never edit `prd.yaml`, `epics.yaml`, `stories.yaml`, `architecture.yaml`, or `design.yaml`: a finding's `route` names who fixes it; this skill patches nothing.
2. Verdict coherence: `就绪` ⇒ zero 严重|高 findings; `未就绪` ⇒ at least one. Findings carry an `evidence` anchor (file, ID, or quoted sentence) — never invent findings; a clean area says so explicitly. Drafting may mark an unconfirmed inference with an `[假设]` prefix; the final gate requires zero — clear them or land them as explicit routes.
3. Requirement facts come from the `collect` receipt: `counts` and `coverage` are copied, never re-derived by hand. Cross-document mechanics (ID chains, FR coverage, cross-file truth) belong to diyc — never re-check them by eye.
4. Records are appended, never renumbered or reused; amending an existing record appends to `revisions` (date / change / reason). No `--previous` round is needed — this skill never rewrites an existing document wholesale.
5. Rendering follows the silent-side-step line in Workflow — command only; no browser interaction point, no path report that blocks, no waiting.
6. Final gate (mechanical): write `status: 已定稿` first — `已定稿` is what the gate inspects, not a product of it — then run `python "{project-root}/.claude/skills/diy-readiness-check/scripts/readiness.py" check --final --json`, passing the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.
7. Upstream stays untouched and unreplaced: on `未就绪`, the finding's `route` names the owning skill (diy-prd / diy-architecture / diy-epics-stories / diy-design) — the fix is theirs, the record is yours. Next mainline step after a pass: diy-test-design.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
