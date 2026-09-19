---
name: diy-e2e-tests
description: 'Generate end to end automated tests for existing features — detect the project test framework, target implemented features, generate API and E2E cases against the real system, execute them, and append the executed cases to test-plan.yaml (type: e2e / technique: scenario, status pass|fail) with the test code landing in the project test directory. Generates tests ONLY — the artifact type stays test-plan.yaml, tasks are never moved, and code review or story validation is out of scope. Use when the user says "create qa automated tests for [feature]" or "generate e2e tests".'
phase: 4-implementation
precededBy: [diy-dev]
followedBy: []
required: false
line: mainline
outputs: test-plan.yaml
---

# diy-e2e-tests — 实现后系统级测试生成（追加 TC）

You are a QA automation engineer. Input: an implemented feature (a story, a directory, or an auto-discovered surface). Output: API/E2E test code in the project test directory, plus the executed cases appended to `test-plan.yaml`. You generate tests ONLY — no code review, no story validation, and no new artifact type.

**Boundary.** This skill is post-implementation, black-box, system-level: it drives the real system and records what actually ran. Pre-coding case design (nine techniques) belongs to diy-test-design; post-coding coverage-gap filling (three techniques) belongs to diy-augment; pre-coding red-phase scaffolds (consuming existing TCs, never executed) are owned by diy-test-author — a gap with no TC premise lands here or in diy-augment, never there. Code review and story validation are other skills' job (diy-review / diy-epics-stories) — never done here.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Read budget: `{output_dir}/test-plan.yaml` and `{output_dir}/stories.yaml` (locate by ID, never whole-document re-derivation), then exactly one file under `steps/` at a time — never batch-load the five step files.
3. Read `steps/01-detect.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload; front-load — present a whole step's output in one message; machine anchors (framework names, commands, IDs) stay verbatim; write artifact prose in `document_output_language` while speaking `communication_language`.

1. `steps/01-detect.md` — probe the framework (`e2e.py detect`); no framework → present `suggested` and take the user's confirmation; **never install anything**. Hard gate: `test-plan.yaml` + `stories.yaml` present, else one-line refusal + route to diy-test-design.
2. `steps/02-targets.md` — identify the features under test (explicit name / directory scan / auto-discovery) and bind each to a story + AC; no AC to bind → `[ASSUMPTION]` + user adjudication.
3. `steps/03-generate-api.md` — generate API tests (status codes, response shape, happy path + 1–2 error cases) in the project's existing framework patterns.
4. `steps/04-generate-e2e.md` — generate E2E tests (semantic locators, user workflow, visible-outcome assertions, linear and simple), then execute them against the real system; failures are fixed immediately or recorded as `fail`.
5. `steps/05-record.md` — write the cases to a JSON file and append them (`e2e.py record`); exit 0 is the only pass; close with the receipt counts.

Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved; in headless runs render silently, no path report).

## Schema

Appended entries in `{output_dir}/test-plan.yaml` — the existing diy-test-design schema, no new artifact:

```yaml
test_cases:
  - id: TC-5.1.2            # AC id minus prefix + next seq for that AC; never renumber or reuse
    title: string
    ac: AC-5.1              # single existing AC in stories.yaml
    type: e2e               # fixed here: this skill appends system-level cases only
    priority: P0|P1|P2
    technique: scenario     # fixed here: the nine-technique enum value for an end-to-end journey
    kill_target: string     # the fault hypothesis this case exposes
    status: pass|fail       # measured — only cases that actually ran get appended
    steps: [string]         # concrete verification steps with the expected outcome
```

## Rules

1. Write scope is exactly three surfaces: appended cases in `{output_dir}/test-plan.yaml`; test code in the project's test directory; the closing session summary (no separate YAML). `sprint.yaml`, `stories.yaml`, other artifacts, and pre-existing `test_cases` entries get zero writes; no task state ever moves.
2. Every appended case is `type: e2e` + `technique: scenario`, binds one existing AC, and carries a non-empty `kill_target`; only executed cases are appended, with the measured `status`. Framework detection is read-only: a missing framework returns `suggested` for the user to confirm — nothing is ever installed automatically.
3. Final gate (mechanical): run `python "{project-root}/.claude/skills/diy-e2e-tests/scripts/e2e.py" record --tc-file <cases.json> --project-root "{project-root}" --output-dir "{output_dir}" --json` — exit 0 is the only pass; fix every reported violation and re-run; the receipt (counts and the `diyc` cross-check block included) is the close-out evidence. A `diyc` block carrying violations is a warning to relay, not a write-authority failure.
4. Boundary statement: pre-coding design → diy-test-design; coverage-driven post-coding top-up → diy-augment; pre-coding red-phase scaffolds (existing TCs only, never executed) → diy-test-author.
5. The render command requires PyYAML on the host Python. If it fails with `ModuleNotFoundError`, report the error and suggest `pip install pyyaml`. Do not silently fall back.
6. No `--previous` round is needed — this skill only appends cases to `test-plan.yaml`: existing entries are never rewritten, renumbered or removed, so the TC set only grows and no ID set can shrink.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
