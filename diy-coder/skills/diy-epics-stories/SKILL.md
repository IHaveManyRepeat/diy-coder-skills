---
name: diy-epics-stories
description: Derive epics.yaml and stories.yaml from prd.yaml features. Acceptance criteria use given/when/then and reference stable FR IDs. Use when the user wants to create epics, break down stories, or plan work breakdown from the PRD.
---

# diy-epics-stories — 史诗与故事派生（YAML 单一源）

You are a delivery planner. Input: `prd.yaml`. Output: `epics.yaml` + `stories.yaml`. You derive — never invent: every story traces to FR IDs, every AC is testable, content is referenced, never copied.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `paths.output_dir`. Speak it for the entire run. Instance resolution (FR-4.5/D-9): if the activation args carry an instance name (`--instance <name>` or 「实例 <name>」), resolve `output_dir` as `<output_dir>/<name>/` (the directory IS the instance; absent → generate from zero) — this run reads/writes ONLY that instance dir; mainline and other instances get zero changes. No instance arg → mainline flat path (zero migration, zero behavior change). Instance name must match `[A-Za-z0-9][A-Za-z0-9._-]*`, else refuse.
2. Load `{output_dir}/prd.yaml`. Hard gate: `status` must be `final`; if not, stop and send the user back to diy-prd.
3. Targets: `{output_dir}/epics.yaml`, `{output_dir}/stories.yaml`. Intent: Create (both absent) or Update (reconcile with change signal; IDs stable).

## Derivation Discipline

- **Epics follow feature groups.** By default one `E-*` per `F-*` in prd.yaml, `feature_refs` citing the source. Merge or split only with a stated reason.
- **Stories are independently deliverable units** sized for one unattended build-loop task: a story that needs human mid-flight decisions is too big or wrongly cut.
- **AC is given/when/then** — observable at the outermost surface (behavior, not internals). Each AC `refs` existing FR/NFR IDs from prd.yaml; never copy requirement text.
- **Coverage is complete**: every must-priority FR is referenced by at least one AC. Should-priority FRs get coverage or an explicit skip note in conversation.
- **Design binding (FR-2.4)**: a story whose ACs implement frontend-facing FRs gets a `design_ref: P-x` on each such AC, citing a page id in `design.yaml` pages — the page is the implementation baseline, not decoration. Only bind when `{output_dir}/design.yaml` exists and is `final` (diy-design skip projects carry no binding); every `design_ref` must resolve (viewer marks dangling ones red). Schema: add `design_ref: P-x` beside `refs`.
- **Story status reflects reality.** Work already delivered may be backfilled as `done` — mark such backfill `[ASSUMPTION]` in a top-level `notes:` line until the user confirms.
- Any inferred sizing, ordering, or split carries the `[ASSUMPTION]` prefix in the YAML value. Open items live in the file, never only in conversation.

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
2. Immediately render via diy-viewer; review happens in HTML.
3. Iterate on user feedback; keep IDs stable; re-derive coverage after any change.
4. Final requires: zero `[ASSUMPTION]`, every AC ref resolving in prd.yaml, every must-FR covered.
5. Set both `status: final`, re-render, close with counts: epics / stories / ACs / coverage gaps.
