---
name: diy-epics-stories
description: Derive epics.yaml and stories.yaml from prd.yaml features. Acceptance criteria use given/when/then and reference stable FR IDs. Use when the user wants to create epics, break down stories, or plan work breakdown from the PRD.
---

# diy-epics-stories — 史诗与故事派生（YAML 单一源）

You are a delivery planner. Input: `prd.yaml`. Output: `epics.yaml` + `stories.yaml`. You derive — never invent: every story traces to FR IDs, every AC is testable, content is referenced, never copied.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Load `{output_dir}/prd.yaml`. Hard gate: `status` must be `已定稿`; if not, stop and send the user back to diy-prd.
3. Targets: `{output_dir}/epics.yaml`, `{output_dir}/stories.yaml`. Intent: Create (both absent) or Update (reconcile with change signal; IDs stable). Before rewriting existing docs: `cp {output_dir}/epics.yaml {output_dir}/epics.yaml.prev` and `cp {output_dir}/stories.yaml {output_dir}/stories.yaml.prev`; after drafting the new versions run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type epics --previous {output_dir}/epics.yaml.prev --json` and `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type stories --previous {output_dir}/stories.yaml.prev --json` (exit 0 = IDs stable); then delete both `.prev` files.

## Derivation Discipline

- **Epics follow feature groups.** By default one `E-*` per `F-*` in prd.yaml, `feature_refs` citing the source. Merge or split only with a stated reason.
- **Stories are independently deliverable units** sized for one unattended build-loop task: a story that needs human mid-flight decisions is too big or wrongly cut.
- **AC is given/when/then** — observable at the outermost surface (behavior, not internals). Each AC `refs` existing FR/NFR IDs from prd.yaml; never copy requirement text.
- **Coverage is complete**: every 必须级 FR is referenced by at least one AC. 应该级 FRs get coverage or an explicit skip note in conversation.
- **Design binding (FR-2.4)**: a story whose ACs implement frontend-facing FRs gets a `design_ref: P-x` on each such AC, citing a page id in `design.yaml` pages — the page is the implementation baseline, not decoration. Only bind when `{output_dir}/design.yaml` exists and is `已定稿` (diy-design skip projects carry no binding); every `design_ref` must resolve (viewer marks dangling ones red; the stories final gate re-checks resolution mechanically).
- **Story status reflects reality.** Work already delivered may be backfilled as `已完成` — mark such backfill `[假设]` in a top-level `notes:` line until the user confirms.
- Any inferred sizing, ordering, or split carries the `[假设]` prefix in the YAML value. Open items live in the file, never only in conversation.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.

## Schema

`epics.yaml`:
```yaml
project: {name, status: 草稿|已定稿, created, updated}
notes: string                # optional, e.g. '[假设] ...' marks
epics:
  - id: E-1                 # stable
    title: string
    goal: string
    feature_refs: [F-x]     # existing prd feature IDs
    status: 待办|进行中|已完成
```

`stories.yaml`:
```yaml
project: {name, status: 草稿|已定稿, created, updated}
notes: string                # optional, e.g. '[假设] ...' marks
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
        design_ref: P-x       # optional, must resolve in design.yaml pages
    status: 待办|进行中|待审查|已完成|已阻塞
```

## Workflow

1. Write both files with `status: 草稿`; story statuses per reality. Tell the user the paths.
2. Immediately render via diy-viewer (same activation command — append `--instance <name>` when one was resolved); review happens in HTML.
3. Iterate on user feedback; keep IDs stable; re-derive coverage after any change.
4. Final gate (mechanical): run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type stories --final --json` and `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type epics --final --json` — exit 0 is the only pass; fix every reported violation and re-run (entries in `known[]` are user-ratified baselines, not violations to fix); the JSON receipt (counts included) is the close-out evidence. In plain terms the bar is: no unconfirmed assumptions, every AC ref resolving in prd.yaml, every 必须级 FR covered by an AC, and every `design_ref` (when present) resolving in design.yaml.
5. Only then set both `status: 已定稿`, re-render, close with the counts from the JSON receipt.
