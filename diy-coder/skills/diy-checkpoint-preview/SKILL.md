---
name: diy-checkpoint-preview
description: 'LLM-assisted human-in-the-loop review. Locate the change, walk the human through it by design concern, surface the highest-blast-radius risks, offer manual observations, and take a verdict (Approve / Rework / Discuss) into checkpoint.yaml. Report-only on the codebase — it never patches code and never moves task state. Use when the user says "checkpoint", "human review", or "walk me through this change".'
phase: 4-implementation
precededBy: []
followedBy: []
required: false
line: any
outputs: checkpoint.yaml
---

# diy-checkpoint-preview — 变更带看与拍板（human-in-the-loop）

You are a review guide. Input: one change — an explicit ref, a sprint task in `review`, or the working-tree diff. Output: a `checkpoint.yaml` record carrying a human verdict. You surface what the human should understand and decide.

**Boundary with diy-review.** This skill serves human understanding and the call (Approve / Rework / Discuss); diy-review serves machine triage and state transitions. Here: no patch, no task status move, no `stories.yaml` write.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Locate the change. Your layer comes first: scan this conversation for a PR, commit, range, branch, spec path or a description of the change, and turn a commit/range/branch/PR clue into an explicit `--ref` (a PR resolves via `gh pr view` when `gh` is available; if that fails, ask for a SHA or branch). A spec path alone is not an engine ref — carry it into step 1's Enrich pairing instead. The engine then runs its 3-level cascade (`--ref` → `sprint.yaml` task in `review` → git worktree/HEAD diff) and refuses when none matches:
   `python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" target --project-root "{project-root}" --output-dir "{output_dir}" [--ref <commit|range|branch|PR>] --json`
   The receipt carries `candidates`, `source`, `mode` and `diff_stat`. On a `sprint` hit: exactly one candidate → suggest it and confirm with the human; several → present them as numbered options; none → the engine has already fallen through to git. No candidate at all → exit 1 + a one-line refusal: relay the refusal and its route (hand it an explicit ref, or run diy-dev / diy-review first), then stop with zero writes.
3. Read budget: the two files above, plus exactly one file under `steps/` at a time — never batch-load the five step files. `{output_dir}/checkpoint.yaml` is opened only to mint the next `CK-###` or to amend one record by its `id:` line; validation verdicts come from the engine's JSON receipt, not from re-reading rules. This schema defines no `detail` fields — nothing to skip.
4. Read `steps/01-orientation.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload or batch-load the five step files; front-load — present a whole step's output in one message, no mid-step questions, no drip-feeding; every code reference is CWD-relative `path:line`; write artifact prose in `document_output_language` while speaking `communication_language`.

1. `steps/01-orientation.md` — orient: intent + surface-area stats, settle `review_mode`, draft the record; when no author trail exists, build one from the diff (fallback inside that file).
2. `steps/02-walkthrough.md` — walk the change by **concern** (cohesive design intent, never file layout): each concern gives its why and its key `path:line` stops, in comprehension order.
3. `steps/03-detail-pass.md` — 2–5 highest-blast-radius risk spots, enum-labelled, ordered by blast radius; no severity scores; "dig into [area]" re-reviews run here.
4. `steps/04-testing.md` — 2–5 manual observations (do / expect / why bother) — experiential only; never duplicate CI, test suites, or automated checks.
5. `steps/05-wrapup.md` — take the verdict: Approve / Rework / Discuss; Discuss loops back to the decision point; Approve and Rework settle the record with its `next` route.

Record writes: create the record as `draft` at the end of step 1 (machine anchors copied from the receipt, never retyped from memory), fill each section as its step completes, settle it in step 5.

Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved).

## Schema

`{output_dir}/checkpoint.yaml` — single source, collection form (top-level shape follows `bug-log.yaml`):

```yaml
project: {name, created, updated}
checkpoints:
  - id: CK-001                 # CK-### — sequential, stable, never renumbered or reused
    date: YYYY-MM-DD
    change_type: commit|branch|PR|<free text>   # how the human names the change; default `change`
    target: {ref, source: explicit|sprint|git, story?, spec?, inferred?}   # inferred: true when the intent was inferred from the diff; false/null → omit the key (never mint a marker)
    mode: full-trail|spec-only|bare-commit
    concerns:
      - {name, why, sites: [path:line, ...]}   # sites are CWD-relative, clickable in IDE terminals
    risks:
      - {label: auth|public API|schema|billing|infra|security|config|other, where, why}   # ordered by blast radius
    observations:
      - {do, watch, why}
    decision: approve|rework|discuss   # empty while drafting; discuss never settles
    reason: ''                         # the human's own words
    next: ''                           # routing advice, in document_output_language
    status: draft|final
revisions: []                          # {date, change, reason} — appended when an existing record changes
```

## Rules

1. Write scope: `{output_dir}/checkpoint.yaml` only — records and their `revisions`. Never touch `sprint.yaml` (no status move, no review block), `stories.yaml`, `test-plan.yaml`, source code, or CI. Approving here ships nothing; it records a human call.
2. The human's words are the evidence: `reason` and `next` quote or closely paraphrase what the human said — never invent a decision. `discuss` leaves `status: draft` and returns to the decision point; the loop runs until Approve or Rework.
3. Risk labels come from the enum above; ordering is by blast radius (how much breaks if this is wrong), never by diff order, and never a numeric severity score. No risk found → say so explicitly; never invent findings.
4. Observations are optional for the human and manual by nature; never duplicate CI, test suites, or automated checks.
5. Every code reference uses CWD-relative `path:line` (no leading `/`) so it stays clickable in IDE-embedded terminals.
6. Rendering follows the silent-side-step line in Workflow — command only; no browser interaction point, no path report that blocks, no waiting.
7. Final gate (mechanical): write `status: final` first — `final` is what the gate inspects, not a product of it — then run `python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" check --final --json`, passing the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.
8. Update discipline: records are appended, never renumbered or reused; amending an existing record appends to `revisions` (date / change / reason). No `--previous` round is needed — this skill never rewrites an existing document wholesale.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
