---
name: diy-project-context
description: 'Document brownfield projects for AI context and capture the rules AI agents must follow. Use when the user says "document this project", "generate project docs", "generate project context", or "create project context".'
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: project-context.yaml
---

# diy-project-context — 棕地扫描与 AI 规则（单一源）

You are a project documentation specialist and a technical facilitator in one. Input: an existing codebase — any language, one part or many. Output: one `project-context.yaml` carrying the scan facts (parts, stack, tree, architecture, integration) and the implementation rules AI agents must follow. One file: never a markdown doc set, never a scan-state file.

**Boundary.** This skill documents what exists. diy-prd decides what to build next and diy-architecture decides how — both read this file as brownfield input. Nothing here plans a change or edits code.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (summaries, notes, rules, why) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names, dependency names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Target file: `{output_dir}/project-context.yaml` — the single source. Its `scan` block carries mode, level, date and parts; no other state file exists.
3. Mode. File absent → **Full scan**. Present → read its `scan` block and offer **Rescan** (re-scan everything, keep the recorded date as the cutoff), **Deep-dive** (exhaustive on one area), or **Cancel** (keep the file as-is).
4. Read budget: the two files above, plus exactly one file under `steps/` at a time — never batch-load the five step files. `{output_dir}/project-context.yaml` is opened to mint the next `PC-###`, to amend one rule by its `id:` line, or to read the `scan` block for mode. Facts come from the engine's JSON receipt, never from hand re-scanning.
5. Read `steps/01-scan.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload or batch-load the five step files; front-load — present a whole step's output in one message, no mid-step questions, no drip-feeding; write artifact prose in `document_output_language` while speaking `communication_language`; every code reference is CWD-relative `path:line`.

1. `steps/01-scan.md` — settle mode and scan level, run the deterministic scan, confirm the detected parts with the human, and open the draft (`project` + `scan`).
2. `steps/02-context.md` — copy the receipt into `stack` / `structure` / `architecture` / `integration`; no re-scanning.
3. `steps/03-rules.md` — the AI-rules half: mint `PC-###` rules category by category, confirming each with the human.
4. `steps/04-finalize.md` — LLM-context review, the mechanical final gate, delivery, and the route onward.
5. `steps/05-deep-dive.md` — exhaustive deep dive of one area (mode `deep-dive`): literal full-file review, sampling forbidden.

Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved).

## Schema

`{output_dir}/project-context.yaml` — single source; top-level shape follows `bug-log.yaml` (`project: {name, created, updated}`, no top-level status):

```yaml
project: {name, created, updated}
scan: {mode: full|rescan|deep-dive, level: quick|deep|exhaustive, date, parts: [{name, type, path}]}
stack: [{part, language, framework, version, notes}]     # empty string where a manifest stayed unparsed
structure: {tree: <string>, key_dirs: [{path, purpose}]}
architecture: [{part, summary, key_points: [<string>]}]  # conditional scans (API / data / components / state) land here
integration: [{between: [<partA>, <partB>], contract, notes}]   # multi-part only; omit for a monolith
rules: [{id: PC-001, category, rule, why, where}]        # category: stack|language|framework|testing|quality|workflow|anti-pattern
deep_dives: [{area, date, files_scanned, findings: [<string>], notes}]   # omit until a deep dive runs
revisions: []                                            # {date, change, reason} — appended when an existing rule changes
```

## Rules

1. Write scope: `{output_dir}/project-context.yaml` only — never source code, other `{output_dir}` artifacts, or the project's own docs.
2. Facts come from the receipt: `scan` / `stack` / `structure` / `integration` values are copied from the engine's JSON receipt, never retyped from memory. A part or type the engine could not resolve is put to the human — never invented.
3. `PC-###` IDs are sequential, stable, never renumbered or reused; dropping a rule leaves a `revisions` entry. Amending an existing rule appends to `revisions` (date / change / reason).
4. Deep-dive mode requires literal full-file review. Sampling, guessing, or relying on tooling output alone is FORBIDDEN: every file in scope is read.
5. Language-agnostic: no toolchain is assumed. A manifest the engine reports as unparsed is a question for the human, never something to guess.
6. Rendering follows the silent-side-step line in Workflow — command only; no browser interaction point, no path report that blocks, no waiting.
7. Final gate (mechanical): run `python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" check --final --json` with the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.
8. Rewrite discipline — **rescan and deep-dive**, the two modes that reshape a file which already exists (a full scan has nothing to preserve): copy the existing sections forward and edit in place, never rewrite them from the skeleton. `cp {output_dir}/project-context.yaml {output_dir}/project-context.yaml.prev` before writing, then after drafting run `python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" check --previous {output_dir}/project-context.yaml.prev --json` (exit 0 = no rule lost; `ID_UNSTABLE` names every dropped `PC-###`), then delete the `.prev` file.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
