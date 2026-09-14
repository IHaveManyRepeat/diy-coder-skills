---
name: diy-create-story
description: 'Create the implementation context pack for one story — the acceptance criteria it must satisfy, the tests that verify them, the architecture decisions it must follow, the files it will touch with their current state, and the carry-over from prior work — referenced by ID and path, never copied. Use when the user says "create the next story" or "create story [story identifier]".'
phase: 4-implementation
precededBy: [diy-sprint]
followedBy: [diy-dev]
required: false
line: mainline
outputs: story-context.yaml
---

# diy-create-story — 故事实施上下文包（引用式，YAML 单一源）

You are a story context engine. Input: one story in `stories.yaml` + `test-plan.yaml` / `sprint.yaml` / `architecture.yaml` + the code it will touch. Output: one `SC-###` record in `{output_dir}/story-context.yaml`. Your job is to stop the classic implementation disasters — reinventing wheels, wrong libraries, wrong file locations, breaking regressions, lying about completion — by **pointing at** the existing truths (IDs and paths), never by copying their words.

**Boundary with the loop.** This skill produces the context for one story; it never writes `stories.yaml` / `test-plan.yaml` / `sprint.yaml`, never moves a task state, never touches source code. The next mainline step is diy-dev.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (risks, verify, carry-over) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Settle the target story: an explicit story ID from the user, else the first non-`done` task in `{output_dir}/sprint.yaml` `tasks[]`, else ask. Then run the deterministic opener:
   `python "{project-root}/.claude/skills/diy-create-story/scripts/story_context.py" collect --story <S-x> --project-root "{project-root}" --output-dir "{output_dir}" --json`
   Exit 1 is a refusal with zero output: relay its one-line reasons and its `gate.route` (or the `suggestions` list), then stop — a refusal never becomes a record.
3. Read budget: the config file, the `collect` receipt, and exactly one file under `steps/` at a time — never batch-load the five step files. `{output_dir}/story-context.yaml` is opened only to mint the next `SC-###` or to amend one record by its `story:` line; AC / TC / decision / prior facts come from the receipt, never from re-reading `stories.yaml` / `test-plan.yaml` / `architecture.yaml` by hand. This schema defines no `detail` fields — nothing to skip.
4. Read `steps/01-target.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload or batch-load the five step files; front-load — present a whole step's output in one message, no mid-step questions; every cross-document fact is an ID reference or a CWD-relative path, never a restated copy; write artifact prose in `document_output_language` while speaking `communication_language`.

1. `steps/01-target.md` — settle the story, run `collect`, draft the record from the receipt.
2. `steps/02-artifacts.md` — take the upstreams from the receipt (`acs` / `tcs` / `decisions` / `prior` / `git`) instead of reading the documents: reference the ACs and TCs, pick the applicable decisions, distil the carry-over.
3. `steps/03-code-survey.md` — survey every file the story touches: read each `update` target in full and record `current_state` + `preserve`; place `new` files by the existing project structure.
4. `steps/04-compose.md` — risks, command-level `verify`, open questions; confirm the pack with the human.
5. `steps/05-finish.md` — final gate, deliver, route to diy-dev.

Record writes: create the record as `draft` at the end of step 1 (machine anchors copied from the receipt, never retyped from memory), fill each section as its step completes, settle it in step 5.

Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved).

## Schema

`{output_dir}/story-context.yaml` — single source, collection form (top-level shape follows `bug-log.yaml`):

```yaml
project: {name, created, updated}
contexts:
  - id: SC-001                  # SC-### — sequential, stable, never renumbered or reused
    story: S-x                  # existing story in stories.yaml (one record per story)
    status: draft|final
    date: YYYY-MM-DD
    epic: E-x                   # must equal the story's epic in stories.yaml
    ac_refs: [AC-x.y]           # the story's ACs by ID — their text stays in stories.yaml
    tc_refs: [TC-x.y.z]         # cases binding those ACs (test-plan.yaml)
    design_ref: P-x             # optional: primary page when the story's ACs carry design_ref
    decisions: [D-x]            # applicable architecture decisions, by ID
    files:                      # files this story will touch (surveyed, never guessed)
      - path: <relative>        # CWD-relative, forward slashes
        action: new|update
        why: <one-line>
        current_state: <string> # update only, required: what the file does today
        preserve: <string>      # update only, required at --final: behavior not to break
    prior_story:                # optional (first story in the project → omit)
      ref: S-y
      carryover: [<string>]     # each line names its source (sprint S-y note / evidence)
    risks: [<string>]
    verify: [<string>]          # command-level completion criteria
    open_questions: [<string>]  # empty before final, or per line prefixed [CLOSED] with the call
revisions: []                   # {date, change, reason} — appended when a record changes
```

## Rules

1. Write scope: `{output_dir}/story-context.yaml` only — records and their `revisions`. Never write `stories.yaml`, `test-plan.yaml`, `sprint.yaml`, `architecture.yaml`, or source code. Moving a task state belongs to diy-dev.
2. Reference discipline (the core diy change): every cross-document fact is an ID (`S-x` / `AC-x.y` / `TC-x.y.z` / `D-x` / `P-x`) or a path — never a paraphrase or copy of another document's prose. The dev agent reads the referenced source; a copy drifts away from it.
3. One record per story, rewritten in place: a record is keyed by `story`; a re-run updates that record and appends to `revisions` — it never mints a second record for the same story. IDs are `SC-###`, sequential, stable, never renumbered or reused. No `--previous` round is needed — this skill rewrites one record in place and no ID set can shrink.
4. Gate (zero output): `stories.yaml` missing, unparsable or `status != final`, or the target story absent → refuse, relay the reason plus the route (diy-epics-stories) or the `suggestions` list, and write nothing. `sprint.yaml` / `test-plan.yaml` / `architecture.yaml` absent → warnings only: the run continues on a thinner reference surface.
5. The file survey is not optional: every `update` entry carries `current_state`, and at final `preserve`. "READ FILES BEING MODIFIED" is the source workflow's non-negotiable — skipping it is the primary cause of implementation failures and review cycles.
6. `[ASSUMPTION]` prefixes an inferred claim; final requires zero — clear it or land it as an open question closed with the human. `open_questions` must be empty at final, or each entry prefixed `[CLOSED]` with the call taken.
7. Rendering follows the silent-side-step line in Workflow — command only; no browser interaction point, no path report that blocks, no waiting.
8. Final gate (mechanical): write `status: final` first — `final` is what the gate inspects, not a product of it — then run `python "{project-root}/.claude/skills/diy-create-story/scripts/story_context.py" check --final --json`, passing the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
