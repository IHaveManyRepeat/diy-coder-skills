# Step 1 — Epic Discovery（epic 发现与收尾校验）

Progress: `[Epic Discovery] → Deep Analysis → Continuity → Review → Actions → Readiness → Finish`

**Read (input):** `{output_dir}/epics.yaml` and `{output_dir}/stories.yaml` for the epic inventory; the `collect` receipt after it runs.
**Write (output):** the draft record in `{output_dir}/retrospective.yaml` (`id` / `epic` / `status` / `date` / `partial` / empty sections).

## Pick the epic — three levels, in order (source step-1 priority logic)

1. **Engine-side suggestion.** Scan `stories.yaml` for the highest-numbered epic that has at least one story with `status: done` — that is the epic just finished; present it as the suggestion.
2. **The user's word is final.** The user names another epic → that is the epic under review, no debate.
3. **Nothing detectable.** List the epics that have any `done` story with their `done/total` counts as numbered options and ask. Never guess an epic into existence.

## Run the deterministic opener

```
python "{project-root}/.claude/skills/diy-retrospective/scripts/retrospective.py" collect --epic <E-x> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

The engine owns the gate and the numbers:

- **Gate (exit 1, zero output):** `stories.yaml` + `epics.yaml` present and `project.status: final`; the epic resolves in `epics.yaml`; at least one `done` story in it. On refusal relay the receipt's one-line reasons and `gate.route` (diy-epics-stories), then stop — a refusal never becomes a record.
- **Everything else comes from the receipt, never by re-reading the artifacts by hand:** `stories` (total / done / pending), `metrics`, `bugs`, `coverage`, `prev_actions`, `first_retro`, `next_epic`. These are the diy transformation of the source's "read every story file and count" step — structured artifacts plus one mechanical pass, not a hand tally.

## Completion check and the partial branch (source step-1, three options)

Read `stories[].pending` from the receipt:

- **Empty** → the epic is closed; say so and continue.
- **Non-empty** → the epic is unfinished. The engine already emitted a `PENDING_DECISION` warning. Common the choice to the user:
  1. **Finish the remaining stories first** (recommended) → stop here, write nothing, name the pending story IDs and route to diy-dev / diy-build-loop.
  2. **Partial retrospective** → only with the user's explicit confirmation; draft the record with `partial: true` and note the pending IDs in `challenges`.
  3. **Refresh the sprint queue instead** → route to diy-sprint when the tracking no longer matches reality.

`partial: true` is a user call, never a facilitator convenience. A partial retro that later gets a follow-up keeps its own record — records are appended, never rewritten.

## Draft the record

Append one record to `{output_dir}/retrospective.yaml` (create the file when absent: `project: {name, created, updated}` — `name` from `diy-coder.yaml` `project.name` — plus an empty `retros` list and `revisions: []`):

```yaml
  - id: RT-001                    # next = highest existing + 1, 3 digits; never renumber, never reuse
    epic: E-x                     # copied from the receipt
    status: draft
    date: YYYY-MM-DD              # today
    partial: false                # true only on a user-confirmed partial retrospective
    metrics:                      # copied from the receipt verbatim, never retyped from memory
      stories_total: 0
      stories_done: 0
      rounds_total: 0
      blocked_count: 0
      augment_fail: 0
      bugs: {functional: 0, non-functional: 0}
    patterns: []
    wins: []
    challenges: []
    insights: []
    action_items: []
    prep_items: []
    critical_path: []
    readiness: {testing: '', deployment: '', acceptance: '', tech_health: '', blockers: ''}
    next_epic: {}                 # filled in step 3
```

Machine anchors (IDs, counts, file names) are copied from the receipt — never recomputed by eye. `partial: true` implies the epic is unfinished; an unfinished epic without `partial: true` is a drafting error.

## Stage the epic (source step-5 metrics block)

Before any discussion, present the epic in one message — all of it from the receipt, nothing retyped:

- completion: `stories_done / stories_total` (and `partial` when set), pending IDs when any;
- delivery shape: `rounds_total`, `blocked_count`, `augment_fail`, defects by class (`bugs`);
- quality shape: AC coverage (`coverage`) and the epic's defect list by ID;
- what comes next: the `next_epic` line (id / title / story count) — the preview is analysed in step 3.

Framing rule: numbers tell a story only with their context ("5 rounds across 6 tasks", not "5"). Do not editorialise the metrics before step 2 has read them through the four lenses.

## Next

Read fully and follow `./02-deep-analysis.md`.
