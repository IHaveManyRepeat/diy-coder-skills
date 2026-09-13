---
name: diy-epics-stories
description: Derive epics.yaml and stories.yaml from prd.yaml features. Acceptance criteria use given/when/then and reference stable FR IDs. Use when the user wants to create epics, break down stories, or plan work breakdown from the PRD.
---

# diy-epics-stories — 史诗与故事派生（YAML 单一源）

You are a delivery planner. Input: `prd.yaml`. Output: `epics.yaml` + `stories.yaml`. You derive — never invent: every story traces to FR IDs, every AC is testable, content is referenced, never copied.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root (mainline flat path when no instance arg; absent instance dir → generate from zero; other instances get zero changes; invalid names are refused by the script).
2. Load `{output_dir}/prd.yaml`. Hard gate: `status` must be `final`; if not, stop and send the user back to diy-prd.
3. Targets: `{output_dir}/epics.yaml`, `{output_dir}/stories.yaml`. Intent: Create (both absent) or Update (reconcile with change signal; IDs stable). Before rewriting existing docs: `cp {output_dir}/epics.yaml {output_dir}/epics.yaml.prev` and `cp {output_dir}/stories.yaml {output_dir}/stories.yaml.prev`; after drafting the new versions run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type epics --previous {output_dir}/epics.yaml.prev --json` and `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type stories --previous {output_dir}/stories.yaml.prev --json` (exit 0 = IDs stable); then delete both `.prev` files.

## Derivation Discipline

- **Epics follow feature groups.** By default one `E-*` per `F-*` in prd.yaml, `feature_refs` citing the source. Merge or split only with a stated reason.
- **Stories are independently deliverable units** sized for one unattended build-loop task: a story that needs human mid-flight decisions is too big or wrongly cut.
- **AC is given/when/then** — observable at the outermost surface (behavior, not internals). Each AC `refs` existing FR/NFR IDs from prd.yaml; never copy requirement text.
- **Coverage is complete**: every must-priority FR is referenced by at least one AC. Should-priority FRs get coverage or an explicit skip note in conversation.
- **Design binding (FR-2.4)**: a story whose ACs implement frontend-facing FRs gets a `design_ref: P-x` on each such AC, citing a page id in `design.yaml` pages — the page is the implementation baseline, not decoration. Only bind when `{output_dir}/design.yaml` exists and is `final` (diy-design skip projects carry no binding); every `design_ref` must resolve (viewer marks dangling ones red; the stories final gate re-checks resolution mechanically). Schema: add `design_ref: P-x` beside `refs`.
- **Story status reflects reality.** Work already delivered may be backfilled as `done` — mark such backfill `[ASSUMPTION]` in a top-level `notes:` line until the user confirms.
- Any inferred sizing, ordering, or split carries the `[ASSUMPTION]` prefix in the YAML value. Open items live in the file, never only in conversation.

- **Writing discipline (readability).** Main field = plain-language main clause; numbers/enums stay inline; machine syntax (commands/flags/paths) goes into parentheses. PRESERVE machine anchor words (file names such as design.yaml, token names, CLI flags) — plain-Chinese rewrites of anchors break the diy-design detect heuristic (2026-09-12 lesson). `plain` (optional, adjacent to the main field): ONE line of WHY the entry exists, everyday language — never restate WHAT it does (restatements drift when the main field changes); write it only for genuinely hard-to-grasp entries. `detail` (optional): process narrative (experiment logs, fixture iterations, background) — conclusions stay in the main field; the viewer folds evidence/findings/long notes by default.

## Schema

`epics.yaml`:
```yaml
project: {name, status: draft|final, created, updated}
epics:
  - id: E-1                 # stable
    title: string
    goal: string
    feature_refs: [F-x]     # existing prd feature IDs
    status: pending|in-progress|done
```

`stories.yaml`:
```yaml
project: {name, status: draft|final, created, updated}
stories:
  - id: S-1                 # stable
    epic: E-x
    title: string
    narrative: 作为…我希望…以便…
    acceptance_criteria:
      - id: AC-1.1          # stable, numbered within story
        given: string
        when: string
        then: string
        refs: [FR-x.y | NFR-x]
    status: pending|in-progress|review|done|blocked
```

## Workflow

1. Write both files with `status: draft`; story statuses per reality. Tell the user the paths.
2. Immediately render via diy-viewer (same activation command — append `--instance <name>` when one was resolved); review happens in HTML.
3. Iterate on user feedback; keep IDs stable; re-derive coverage after any change.
4. Final gate (mechanical): run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type stories --final --json` and `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type epics --final --json` — exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. In plain terms the bar is: no unconfirmed assumptions, every AC ref resolving in prd.yaml, every must-FR covered by an AC, and every `design_ref` (when present) resolving in design.yaml.
5. Only then set both `status: final`, re-render, close with the counts from the JSON receipt.
