# Step 1 — Document Discovery（文档发现）

Progress: `[Document Discovery] → Requirement Inventory → Coverage Validation → UX Alignment → Epic Quality Review → Final Assessment`

**Read (input):** the `collect` receipt from On Activation; the documents it inventoried.
**Write (output):** the draft record in `{output_dir}/readiness.yaml` (`id` / `date` / `scope` / `status` / `findings` / `coverage` / `counts`).

## Gate first (zero-output refusal)

`collect` already ran the gate. On exit 1 the run is over before it starts: relay the receipt's one-line reasons and its `gate.route` (diy-prd / diy-epics-stories), then stop and write nothing. A refusal never becomes a record, and a missing upstream document is never worked around by assessing something else instead.

## Inventory the real document set

Take the list from the receipt's `docs` block — do not re-scan the directories by hand:

- `prd`, `epics`, `stories` — present, and for epics/stories `project.status: final` (the gate's requirement).
- `architecture` — optional: absent arrives as a warning in the receipt; carry it into the final assessment, it does not block.
- `design` — optional: absent is a legitimate state; step 4 decides whether UX was implied and warns.

`scope` in the record = the documents actually inventoried, a subset of `[prd, architecture, epics, stories, design]`.

## Duplicate or stray versions (human judgment)

The engine knows only the canonical filenames; everything else is a conversational read:

- leftover drafts (`*.prev`, `*.bak`, dated copies of the same artifact), legacy markdown twins (`prd.md` beside `prd.yaml`), another instance's directory bleeding into this one;
- sharded legacy documents (a `prd/` folder beside `prd.yaml`) — the diy single source is the YAML file.

Name what is there and settle which version is authoritative before assessing anything. Proceeding with an unresolved duplicate is a system failure (source step-1 rule); a duplicate the human cannot settle becomes a finding with a route, never a silent choice.

## Draft the record

Append one record to `{output_dir}/readiness.yaml` (create the file when absent: `project: {name, created, updated}` — `name` from `diy-coder.yaml` `project.name` — plus an empty `checks` list and `revisions: []`):

```yaml
  - id: IR-001                    # next = highest existing + 1, 3 digits; never renumber, never reuse
    date: YYYY-MM-DD              # today
    status: draft
    scope: [prd, epics, stories]  # documents actually inventoried
    findings: []
    coverage: {must_frs: 0, covered: 0, gaps: []}   # copied from the receipt
    counts: {frs: 0, nfrs: 0, epics: 0, stories: 0, acs: 0, findings_by_severity: {}}
```

Counts and coverage are copied from the receipt verbatim — machine anchors are never retyped from memory.

## Next

Read fully and follow `./02-requirement-inventory.md`.
