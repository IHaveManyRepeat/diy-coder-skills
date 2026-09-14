---
name: diy-quick-dev
description: 'Implements any user intent, requirement, story, bug fix or change request by producing clean working code artifacts that follow the project''s existing architecture, patterns and conventions. Use when the user wants to build, fix, tweak, refactor, add or modify any code, component or feature. Lightweight channel outside the story loop: one spec record in spec.yaml carried intent → plan → implement → review → present, with diy-review L1-L3 as its review layers; it never commits, pushes, or opens an editor.'
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: spec.yaml
---

# diy-quick-dev — 轻量通道（意图 → spec → 实现 → 审查）

You are a lightweight change driver. Input: one user intent — a request, a bug, a small feature. Output: working code plus one `{output_dir}/spec.yaml` record carrying what was asked, what was verified, and how a human should read the change.

**Boundary with diy-dev / diy-review.** diy-dev runs TDD inside the story loop (sprint task + test-plan TCs) and hands off to diy-review; diy-quick-dev carries its own channel end to end for changes too small to earn a story — no sprint entry, no TC. Review layers and routing still belong to diy-review: L1 correctness, L2 boundary, L3 acceptance coverage, and the four routes `intent_gap` / `bad_spec` / `patch` / `defer` (`reject` is a silent drop, never a finding state). The TDD difference is explicit: no formal red/green ledger, but every acceptance criterion carries a command-level `verification` entry that must actually run.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (intent, notes, why, deferred) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Resolve the run: an explicit `SP-xxx` or a spec named by the user routes by that record's `status` (draft → plan; ready / in-progress → implement; in-review → review; done → read-only; blocked → name the blocker and stop). No pointer → offer the active records (`draft` / `ready` / `in-progress` / `in-review`) as a numbered list with `[N]` for new work; an unformatted intent file is starting intent, never a resumable record.
3. Read budget: the config file, `{output_dir}/spec.yaml`, and exactly one file under `steps/` at a time — never batch-load the six step files. The artifact is opened only to mint the next `SP-###` or to amend one record by its `id:` line; structural verdicts come from the engine's JSON receipt, not from re-reading rules.
4. Read `steps/01-clarify-route.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload or batch-load the six step files; front-load — present a whole step's output in one message; every code reference shown in the terminal is CWD-relative `path:line`; write artifact prose in `document_output_language` while speaking `communication_language`.

1. `steps/01-clarify-route.md` — intent check (argument → recent conversation → ask), the numbered-question clarification loop, the multi-goal check (SCOPE STANDARD: one goal, 900–1600 tokens — a proposal with user override, never a gate), then the route: zero blast radius → one-shot; anything else → plan-code-review (when unsure, plan-code-review). Draft the record.
2. `steps/02-plan.md` — investigate, fill the record, self-review against the READY FOR DEVELOPMENT standard, then CHECKPOINT 1 (`[A]` approve / `[E]` edit) with the re-read anti-loss rule.
3. `steps/03-implement.md` — write `baseline` before touching code, implement, self-check every task, then run every `verification` command and record its real result.
4. `steps/04-review.md` — the diy-review layers L1–L3 plus the four routes; `intent_gap` loops back to the human, `bad_spec` amends the non-frozen sections and appends `change_log`, `patch` is fixed in place, `defer` lands in `deferred`; loop cap 5 → HALT.
5. `steps/05-present.md` — build `review_order` (concerns, not files) and settle the record at `done` + the final gate; then suggest — never run — commit and push.
6. `steps/06-oneshot.md` — the zero-blast-radius channel, reached by early exit from step 1: implement, one adversarial pass, three dispositions (patch → fix / defer → record / anything bigger → HALT to the human), then the same trace and gate.

Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved).

## Schema

`{output_dir}/spec.yaml` — single source, collection form (top-level shape follows `bug-log.yaml`):

```yaml
project: {name, status: draft|final, created, updated}
specs:
  - id: SP-001                  # SP-### — sequential, stable, never renumbered or reused
    title: <string>
    type: feature|bugfix|refactor|chore
    route: one-shot|plan-code-review
    status: draft|ready|in-progress|in-review|done|blocked   # ready = source ready-for-dev
    date: YYYY-MM-DD
    baseline: <commit-sha|NO_VCS>   # recorded before the first code change
    intent: {problem, approach}     # frozen after approval — only the human changes it
    boundaries: {always: [], ask_first: [], never: []}
    io_matrix: [{scenario, input, expected, error_handling}]   # optional — omit when meaningless
    code_map: [{path, role}]
    tasks: [{task, file, done}]
    acceptance: [{given, when, then}]
    change_log: [{finding, amended, avoided, keep: []}]        # append-only, on bad_spec loopbacks
    design_notes: <string>          # optional
    verification: {commands: [{cmd, expect, result}], manual: []}   # result = what actually ran
    deferred: [{finding, why, date}]
    review: {rounds: 0, findings: [{layer: correctness|boundary|coverage, route: intent_gap|bad_spec|patch|defer, note}]}
    review_order: [{concern, stops: [{path, line, why}]}]      # required once done
    open_questions: [<string>]
revisions: []                      # {date, change, reason} — appended when an existing record changes
```

## Rules

1. Write scope: `{output_dir}/spec.yaml` plus the implementation files the record names. Never touch `sprint.yaml`, `stories.yaml`, `test-plan.yaml`, or `bug-log.yaml` — a real defect belongs to diy-review's bug-add, not here.
2. The record moves through its own states: draft → ready → in-progress → in-review → done (`blocked` from anywhere with the reason named). `done` is read-only; a reopened record keeps its SP id and appends to `revisions` (date / change / reason). No `--previous` round is needed — a record is amended in place under a stable SP id, so no ID set ever contracts.
3. `intent` is frozen once the human approves: only the human renegotiates it. Every other section may be amended, and each amendment appends a `change_log` entry (finding / amended / avoided / keep) — never edit an existing entry.
4. Review is diy-review's, never a second system: L1 correctness / L2 boundary / L3 acceptance coverage, each finding routed exactly once. `intent_gap` → back to the human; `bad_spec` → amend the non-frozen sections and re-derive; `patch` → fix now; `defer` → `deferred`. Rounds cap at 5, then HALT and escalate.
5. Verification is the hard bottom: a record reaching `in-review` with empty `verification.commands` is refused by the engine (`EMPTY_FIELD`). Commands are run, never imagined — `result` records what actually happened.
6. Cross-document mechanics belong to diyc (`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type <T> --final --json` for a story loop touched by the change); never re-implement its rules here. Cut from the source with replacements: `compile-epic-context` (BMAD's md cache) → structured artifacts + diy-create-story's `story-context.yaml`; `sync-sprint-status` (BMAD's `sprint-status.yaml`) → diyc-managed `sprint.yaml`. Never reference a skill that is not installed.
7. No automation beyond the code: never commit, never push, never open an editor — close with one suggested line instead. Rendering follows the silent-side-step line in Workflow — command only; no browser interaction point, no path report that blocks, no waiting.
8. Final gate (mechanical): write `project.status: final` and the record's `status: done` first — `final` / `done` are what the gate inspects, not products of it — then run `python "{project-root}/.claude/skills/diy-quick-dev/scripts/spec.py" check --final --json`, passing the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted; add `--id SP-xxx` to gate one record). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
