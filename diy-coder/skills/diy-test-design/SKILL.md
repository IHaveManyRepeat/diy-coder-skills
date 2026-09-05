---
name: diy-test-design
description: Derive test-plan.yaml from stories.yaml acceptance criteria. Every test case binds an AC ID with type and priority; uncovered ACs surface as explicit coverage gaps for user decision. Use when the user wants test cases designed before coding (TDD-first).
---

# diy-test-design — 测试用例设计（YAML 单一源）

You are a test designer. Input: `stories.yaml`. Output: `test-plan.yaml`. You derive cases from acceptance criteria — never invent coverage: every case binds an AC ID, every gap is explicit.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `paths.output_dir`. Speak it for the entire run.
2. Load `{output_dir}/stories.yaml`. Hard gate: `status` must be `final`; if not, stop and send the user back to diy-epics-stories.
3. Target: `{output_dir}/test-plan.yaml`. Intent: Create (absent) or Update (reconcile with change signal; TC IDs stable).

## Design Discipline

- **One AC, at least one case.** Every pending/in-progress story AC gets ≥1 case. Done-story ACs are exempt — list them in `coverage_gaps` as `decision: waived` citing the story status and prior confirmation; never silently omit.
- **Cases are executable.** A case states concrete verification (schema assertion, fixture render, command + expected output), not restated AC prose. If you cannot state how to verify, that is a coverage gap or a bad AC — flag it, don't fake a case.
- **Type maps to layer**: `unit` (single-component code check, e.g. viewer.py/runner.py function with fixtures), `integration` (cross-artifact check, scriptable without agent), `e2e` (full skill/workflow run driven by agent or operator).
- **Priority maps to risk**: `P0` = must-FR AC, `P1` = should-FR AC, `P2` = supplementary case beyond the AC minimum.
- **Gaps are decisions, not omissions.** Any AC without a case appears in `coverage_gaps` with a reason and `decision: pending` — the user decides (add a case / accept the gap). Only prior user confirmation justifies `waived`.
- Any inferred exemption or priority judgment carries the `[ASSUMPTION]` prefix in the YAML value. Open items live in the file, never only in conversation.

## Schema

`test-plan.yaml`:
```yaml
project: {name, status: draft|final, created, updated}
test_cases:
  - id: TC-5.1.1          # stable: AC id minus prefix + .{seq}
    title: string
    ac: AC-5.1            # existing AC ID in stories.yaml (required)
    type: unit|integration|e2e
    priority: P0|P1|P2
    status: pending|pass|fail   # pass/fail written back by diy-dev / diy-build-loop
    steps: [string]       # concrete verification steps; expected outcome stated
coverage_gaps:
  - ac: AC-x.y
    story: S-x
    reason: string
    decision: pending|waived|accept-gap
    note: string          # waived must cite prior user confirmation (date + what)
```

## Workflow

1. Write `test-plan.yaml` with `status: draft`. Tell the user the path.
2. Immediately render via diy-viewer; review happens in HTML.
3. Iterate on user feedback; keep TC IDs stable; re-derive coverage after any stories.yaml change.
4. Final requires: zero `[ASSUMPTION]`, zero `decision: pending` gaps, every `ac` resolving in stories.yaml.
5. Set `status: final`, re-render, close with counts: cases / ACs covered / gaps by decision.
