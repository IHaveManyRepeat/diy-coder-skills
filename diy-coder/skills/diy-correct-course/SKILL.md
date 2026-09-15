---
name: diy-correct-course
description: 'Manage significant changes during sprint execution. Analyze impact across artifacts, draft concrete old-to-new edits, and hand the proposal off by scope. Use when the user says "correct course" or "propose sprint change". Produces one proposal record in change-proposal.yaml.'
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: change-proposal.yaml
---

# diy-correct-course — 执行期变更导航（只出提案，不改真源）

You are a change navigator. Input: one trigger issue surfaced mid-sprint. Output: one proposal record in `{output_dir}/change-proposal.yaml` carrying the impact set, the concrete edits, and the handoff route. You analyze and propose — the owning skills execute.

**Boundary: proposals only, never the source.** This skill writes neither `prd.yaml`, `epics.yaml`, `stories.yaml`, `architecture.yaml`, `openapi.yaml`, `design.yaml` nor `sprint.yaml` — `handoff.route` names the skill whose update mode performs the rewrite. A proposal recorded here changes nothing by itself.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (trigger, why, rationale, note) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Run the deterministic opener — gate + six-document impact summary + delegated diyc cross-document checks + reference chain:
   `python "{project-root}/.claude/skills/diy-correct-course/scripts/change_proposal.py" collect --project-root "{project-root}" --output-dir "{output_dir}" [--target <ID>] --json`
   Exit 1 is a refusal with zero output: relay its one-line reasons and `gate.route`, then stop — a refusal never becomes a record.
3. Read budget: the config file, the `collect` receipt, and exactly one file under `steps/` at a time — never batch-load the six step files. `{output_dir}/change-proposal.yaml` is opened only to mint the next `CP-###` or to amend one record by its `id:` line; document summaries, `diyc.check.violations` and the `chain` come from the receipt, never from re-reading the artifacts. This schema defines no `detail` fields — nothing to skip.
4. Read `steps/01-init.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload or batch-load the six step files; front-load — one step's output in one message, no mid-step questions; every impact and edit carries its target (a stable ID, or `path:<relative>` for infra files); write artifact prose in `document_output_language` while speaking `communication_language`.

1. `steps/01-init.md` — confirm the trigger from the user's own words, settle `mode`, draft the record.
2. `steps/02-analysis.md` — walk the systematic analysis perspective list; the mechanical half is the receipt, the judgment half produces `impacts`.
3. `steps/03-edits.md` — draft the concrete edits: one `old → new` per change, each with a rationale.
4. `steps/04-proposal.md` — settle the recommended path (`approach`), `ripple`, `effort`; write the record; present it for review.
5. `steps/05-route.md` — take the explicit approval, classify `scope`, set `handoff`.
6. `steps/06-finish.md` — summarize, pass the final gate, hand off.

Record writes: create the record as `draft` at the end of step 1 (facts copied from the receipt, never retyped from memory), fill each section as its step completes, settle it in step 6.

Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved).

## Schema

`{output_dir}/change-proposal.yaml` — single source, collection form (top-level shape follows `bug-log.yaml`):

```yaml
project: {name, created, updated}
proposals:
  - id: CP-001                # CP-### — sequential, stable, never renumbered or reused
    date: YYYY-MM-DD
    status: draft|final|approved|rejected
    trigger: <string>         # the issue — the user's own words first
    mode: incremental|batch
    scope: minor|moderate|major
    impacts:                  # reference-only impact list
      - {artifact: prd|epics|stories|architecture|openapi|design|test-plan, target: FR-x.y|F-x|S-x|AC-x.y|D-x|TC-x.y.z|..., kind: modify|add|remove, why: <string>}
      - {artifact: infra, target: 'path:<relative>', kind: modify|add|remove, why: <string>}   # deployment scripts / CI / IaC files — file targets, never product IDs
    edits:                    # the concrete proposal (source old→new); `old` quotes the current value or writes (absent)
      - {artifact: <same enum>, target: <ID or path:<relative>>, field: <path>, old: <string>, new: <string>, rationale: <string>}
    ripple: [<string>]        # downstream fallout along the reference chain
    effort: {estimate, risk, timeline_impact}
    approach: {path: direct-adjustment|rollback|mvp-review, why: <string>}
    handoff: {route: <diy skill name>, note: <string>}
    open_questions: [<string>]
revisions: []                 # {date, change, reason} — appended when an existing record changes
```

## Rules

1. Write scope: `{output_dir}/change-proposal.yaml` only — records and their `revisions`. This skill never edits the source artifacts (`prd.yaml` / `epics.yaml` / `stories.yaml` / `architecture.yaml` / `openapi.yaml` / `design.yaml` / `sprint.yaml`); `handoff.route` names who executes, and the fix is theirs.
2. Reference, never copy: `impacts.target` and `edits.target` carry a stable ID (product artifacts) or `path:<relative>` (`artifact: infra` — deployment / CI / IaC files; never a product ID); `old` / `new` quote the smallest decisive value (an ID plus a one-line gist), never a pasted section. The full rewrite is the owning skill's job.
3. Impact facts come from the `collect` receipt: document summaries, `diyc.check.violations` and the `chain` are copied, never re-derived by hand. Cross-document mechanics (ID chains, reference resolution) belong to diyc — never re-check them by eye.
4. An unclear trigger stops the run (source HALT): no proposal is written from a vague issue. Every impact names the evidence that showed it — never invent impact. Drafting may mark an unconfirmed inference with an `[ASSUMPTION]` prefix; the final gate requires zero — resolve it with the human or land it as an explicit `open_questions` entry.
5. Records are appended, never renumbered or reused; amending an existing record appends to `revisions` (date / change / reason). No `--previous` round is needed — proposal records are append-only, never rewritten wholesale.
6. Rendering follows the silent-side-step line in Workflow — command only; no browser interaction point, no path report that blocks, no waiting.
7. Final gate (mechanical): write `status: final` (or `approved`) first — the gate inspects it, it is not a product of the gate — then run `python "{project-root}/.claude/skills/diy-correct-course/scripts/change_proposal.py" check --final --json`, passing the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.
8. Route by scope (the gate enforces the pairing, allow-lists in step 5): minor → one owning skill implements directly; moderate → diy-sprint / diy-epics-stories / diy-prd rework the backlog; major → the planning layer (diy-prd / diy-architecture / diy-epics-stories) replans. Approval precedes routing — an unapproved proposal never gets handed off.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
