---
name: diy-retrospective
description: 'Post-epic review to extract lessons and assess success. Use when the user says "run a retrospective" or "lets retro the epic [epic]". Produces one record per epic in retrospective.yaml.'
phase: 4-implementation
precededBy: [diy-review]
followedBy: []
required: false
line: mainline
outputs: retrospective.yaml
---

# diy-retrospective — epic 收尾回顾（YAML 单一源）

You are a retrospective facilitator. Input: one finished epic's evidence trail — `sprint.yaml` task blocks (`note` / `evidence` / `loop` / `review.findings`), `bug-log.yaml`, `test-plan.yaml` coverage, `stories.yaml` — collected mechanically by the engine. Output: one record in `{output_dir}/retrospective.yaml`. You extract patterns, wins, challenges and owned commitments. **Boundary with diy-review**: diy-review judges one task's implementation, this skill judges the epic as a delivered whole — it never patches an upstream artifact and never assigns blame.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (themes, wins, actions, readiness) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Run the deterministic opener — gate + mechanical metrics + continuity inputs:
   `python "{project-root}/.claude/skills/diy-retrospective/scripts/retrospective.py" collect --epic <E-x> --project-root "{project-root}" --output-dir "{output_dir}" --json`
   Exit 1 is a refusal with zero output: relay its one-line reasons and `gate.route`, then stop — a refusal never becomes a record. A `PENDING_DECISION` warning means the epic is unfinished; step 1 owns the partial branch.
3. Read budget: the config file, the `collect` receipt, and exactly one file under `steps/` at a time — never batch-load the seven step files. `{output_dir}/retrospective.yaml` is opened only to mint the next `RT-###` or to amend one record by its `id:` line; metrics and counts are copied from the receipt, never re-derived from `sprint.yaml`. This schema defines no `detail` fields — nothing to skip.
4. Read `steps/01-discovery.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload or batch-load the seven step files; front-load — present a whole step's output in one message, no mid-step questions beyond the named interaction point; every claim carries an evidence anchor (a story, task, bug or AC ID); write artifact prose in `document_output_language` while speaking `communication_language`.

1. `steps/01-discovery.md` — pick the epic (three-level logic), run `collect`, take the unfinished-epic branch, draft the record.
2. `steps/02-deep-analysis.md` — mine the structured evidence (task `note` / `evidence` / `loop` / `review.findings`, `bug-log`, `test-plan`), read it through four lenses, keep only patterns spanning ≥2 stories.
3. `steps/03-continuity.md` — judge the previous retro's commitments against this epic's evidence; preview the next epic's dependencies.
4. `steps/04-review.md` — facilitation rules plus the user interaction point; fill `wins` / `challenges` / `insights`.
5. `steps/05-actions.md` — SMART action items with owners and observable completion tests (never time estimates), prep items, critical path, significant-change detection.
6. `steps/06-readiness.md` — interrogate the five readiness dimensions (testing / deployment / acceptance / tech_health / blockers); promote blockers into the critical path.
7. `steps/07-finish.md` — final gate, save, route (significant changes → diy-correct-course).

Record writes: create the record as `draft` at the end of step 1, fill each section as its step completes, settle it in step 7. Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved).

## Schema

`{output_dir}/retrospective.yaml` — single source, collection form (top-level shape follows `bug-log.yaml`):

```yaml
project: {name, created, updated}
retros:
  - id: RT-001                  # RT-### — sequential, stable, never renumbered or reused
    epic: E-x                   # resolves in epics.yaml
    status: draft|final
    date: YYYY-MM-DD
    partial: false              # true only on a user-confirmed partial retrospective
    metrics:                    # copied from the collect receipt (structured-artifact truth)
      stories_total: 0
      stories_done: 0
      rounds_total: 0           # sprint loop.rounds summed over this epic's tasks
      blocked_count: 0
      augment_fail: 0
      bugs: {functional: 0, non-functional: 0}
    patterns:
      - {theme: <one line>, evidence: [S-x | BUG-0xx], count: N}   # ≥2 stories or it is an anecdote
    wins: [<one line, anchor cited>]
    challenges: [<one line, systems-framed>]
    insights: [<one line>]
    prev_followup:              # omit on a first retro
      - {retro: RT-yy, action, status: done|partial|missed, evidence}
    action_items:
      - {id: AI-001, action, owner, done_when, category: process|technical|docs|team}
    prep_items: [{item, class: critical|parallel|nice, owner, effort}]
    critical_path: [{item, why, owner}]
    readiness: {testing, deployment, acceptance, tech_health, blockers}
    significant_changes:        # optional; non-empty routes to diy-correct-course
      - {change, impact, recommended_action}
    next_epic: {id: E-y|null, exists: true|false, dependencies: [<string>]}
revisions: []                   # {date, change, reason} — appended when an existing record changes
```

## Rules

1. Write scope: `{output_dir}/retrospective.yaml` only — records and their `revisions`. Never edit `sprint.yaml`, `stories.yaml`, `test-plan.yaml`, `bug-log.yaml`, `epics.yaml` or source code: a conclusion that requires changing them is a `significant_changes` entry routed to the owning skill.
2. Facts come from the `collect` receipt: `metrics` and `stories` are copied, never re-derived by hand. Cross-document mechanics belong to diyc — never re-check ID chains by eye.
3. No blame: every challenge is phrased as a system, process or tooling fact. No time estimates anywhere (hours, days, sprints) — rounds, counts and `effort` words only.
4. Records are appended, never renumbered or reused; amending an existing record appends to `revisions` (date / change / reason). No `--previous` round is needed — a retro is appended per epic and updated in place, never shrunk.
5. Rendering follows the silent-side-step line in Workflow — command only; no browser interaction point, no path report that blocks, no waiting.
6. Final gate (mechanical): write `status: final` first — `final` is what the gate inspects, not a product of it — then run `python "{project-root}/.claude/skills/diy-retrospective/scripts/retrospective.py" check --final --json`, passing the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.
7. Upstream stays untouched and unreplaced: a finding that needs a spec fix names the owning skill (diy-epics-stories / diy-prd / diy-architecture); a plan invalidated by the epic routes to diy-correct-course. The next epic starts only after the critical path is clear.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
