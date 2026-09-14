# Step 2 — Stronghold（据点确立与立案）

Progress: `Acknowledge → [Stronghold] → Perimeter → Reasoning → Source Trace → Report`

**Read (input):** the acknowledged input set from step 1; the `collect` receipt (`vcs.commits` recent changes, `files` area inventory with line counts, `candidates` parallel implementations and test files).
**Write (output):** the draft record in `{output_dir}/investigation.yaml` — `id` / `slug` / `date` / `status` / `mode` / `evidence_light` / `handoff_brief` (rough) / `case_info` / `problem_statement` / `stronghold` / initial `evidence`.

## Find the stronghold

A stronghold is one **Confirmed** piece of evidence: an error message, a function name, an HTTP route, a config parameter, a test case. Anchor here; the perimeter in step 3 expands outward from it.

Never start from a theory and hunt for support. The user's hypothesis (`H-001`) is not the stronghold — the stronghold is something directly observed and cited (`path:line`, timestamp, or commit hash).

## Evidence-light branch

When no Confirmed evidence is reachable:

1. set `evidence_light: true` in the record;
2. populate `backlog` with the prioritized data-collection items;
3. write the "to make progress, I need one of: …" list as `missing_evidence` rows (`what` / `would_resolve` / `how`) — the final gate refuses an evidence-light case with an empty `missing_evidence`;
4. pause for the human to supply evidence or authorize a broader scan (step 3).

## Draft the record

Append one record to `{output_dir}/investigation.yaml` (create the file when absent: `project: {name, status: draft, created, updated}` — `name` from `diy-coder.yaml` `project.name` — plus an empty `cases` list and `revisions: []`):

```yaml
  - id: IV-001                 # next = highest existing + 1, 3 digits; never renumber, never reuse
    slug: {agreed slug}
    date: YYYY-MM-DD           # today
    status: active
    mode: symptom|exploration
    evidence_light: false
    handoff_brief: {rough, one line}
    case_info: {inputs: [{kind, ref}], scope: ..., time_window: ...}
    problem_statement: {the user's description, verbatim}
    stronghold: {ref: ..., why: ...}       # omit only on the evidence-light branch
    evidence:
      - {id: EV-001, grade: confirmed, ref: ..., note: ..., availability: available}
    hypotheses:
      - {id: H-001, statement: ..., status: open, test: ..., resolution: ''}
    timeline: []
    backlog: []
    missing_evidence: []
    conclusion: {text: '', confidence: '', fix_direction: '', diagnostic_steps: [], reproduction: ''}
    follow_ups: []
```

IDs are minted here (`IV-001`, `EV-001`, `H-001` …) and never reused. Empty sections are written as empty lists — never invent content.

Present scope, stronghold, and the proposed approach; pause for the human before continuing.

## Next

Read fully and follow `./03-perimeter.md`.
