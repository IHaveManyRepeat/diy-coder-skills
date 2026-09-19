# Step 1 — Initialize Change Navigation（触发确认与立案）

Progress: `[Initialize] → Analysis → Edits → Proposal → Route → Finish`

**Read (input):** the `collect` receipt from On Activation; the user's description of the issue.
**Write (output):** the draft record in `{output_dir}/change-proposal.yaml` (`id` / `date` / `status` / `trigger` / `mode` / `scope` / empty lists).

## Gate first (zero-output refusal)

`collect` already ran the gate. On exit 1 the run is over before it starts: relay the receipt's one-line reasons and its `gate.route` (`diy-prd` / `diy-epics-stories`), then stop and write nothing. A refusal never becomes a record; a missing upstream document is never worked around by analyzing something else.

## Confirm the trigger (source step-1)

Ask what needs navigating, then listen — the user's own words are the record's `trigger`:

- **What specific issue or change has been identified?** One sentence, their phrasing first.
- **What showed it?** An error message, a stakeholder signal, a technical constraint discovered mid-implementation — this becomes the evidence anchoring the analysis (source checklist §1.3).
- **Which story surfaced it?** The story ID (if one exists) goes into the analysis in step 2.

**HALT if the trigger is unclear** (source step-1 and checklist §1 halt-condition): "Cannot navigate change without a clear understanding of the triggering issue." Do not proceed on a vague issue, and never fill the gap with assumptions of your own — a proposal built on a guessed trigger misroutes real work.

## Settle the mode (source step-1)

- **`增量`** (recommended) — each edit proposal is presented and refined one at a time before the next.
- **`批量`** — every edit proposal is collected and presented together at the end of step 3.

Record it in `mode`; it changes how step 3 presents, nothing else.

## Draft the record

Append one record to `{output_dir}/change-proposal.yaml` (create the file when absent: `project: {name, created, updated}` — `name` from `diy-coder.yaml` `project.name` — plus an empty `proposals` list and `revisions: []`):

```yaml
  - id: CP-001                  # next = highest existing + 1, 3 digits; never renumber, never reuse
    date: YYYY-MM-DD            # today
    status: 草稿
    trigger: <the user's own words>
    mode: 增量           # or 批量
    scope: 轻微                # provisional; step 5 settles it and the final gate enforces the pairing
    impacts: []
    edits: []
    open_questions: []
```

The provisional `scope` keeps the record loadable through the drafting steps; step 5 corrects it before the gate.

## Next

Read fully and follow `./02-analysis.md`.
