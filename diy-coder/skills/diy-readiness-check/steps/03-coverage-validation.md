# Step 3 — Coverage Validation（FR 覆盖校验）

Progress: `Document Discovery → Requirement Inventory → [Coverage Validation] → UX Alignment → Epic Quality Review → Final Assessment`

**Read (input):** the `collect` receipt (`coverage`, `diyc.check.violations`, `counts`); `stories.yaml` / `epics.yaml` only to resolve the mapping behind a specific finding.
**Write (output):** `coverage` in the record (confirmed) plus the coverage findings.

## Coverage comes from the receipt

`collect` computed `coverage` under the same rule diyc enforces for `stories.yaml` (every 必须-priority FR is referenced by at least one AC), and ran diyc for the mechanical verdict:

- `coverage.must_frs` / `coverage.covered` / `coverage.gaps` — the numbers to record;
- `diyc.check.violations` with `type: stories` — `SET_MISMATCH` when no AC references a 必须 FR, `UNKNOWN_ID` when an AC's `refs` points at an FR/NFR ID absent from `prd.yaml`.

Neither is re-derived here. Your work is the matrix's human column: which story/AC carries each FR, and what to do about the gaps.

## Build the coverage matrix

For every 必须-priority FR — and every 应该/可选 FR that produced a finding — name the covering AC and story:

```
FR-1.1 (必须) — covered by S-1 / AC-1.1 (epic E-1)
FR-1.2 (必须) — NOT FOUND
```

Work from `stories.yaml` `acceptance_criteria[].refs`: an FR is covered by AC reference, never by narrative resemblance. When a story's text obviously serves an FR its ACs do not reference, that is a finding (`area: stories`, `route: diy-epics-stories`) — the reference is the contract.

**The reverse direction.** The source workflow also noted FRs claimed in epics that the PRD never asked for. diyc rules AC `refs` resolution but deliberately leaves `epics.feature_refs` and `stories.epic` unresolved (diyc_check_docs.py:12 — out of that ruling's scope), so while building the matrix, if an epic claims a feature ID (`F-x`) that `prd.yaml` does not define, or a story names a missing epic (`E-x`), that is a finding with `route: diy-epics-stories`. Report what you see next to the matrix — never re-scan the whole document set for it.

## Document every gap (source step-3 §5)

For each uncovered FR:

- the FR ID and why it matters — a 必须 FR with no AC cannot enter the sprint cleanly (diy-sprint's gate blocks it, or the work silently drops);
- the impact, in plain words;
- the recommendation: which epic should carry it, or that the PRD should drop it (`route: diy-prd`).

Severity: uncovered **必须** FR → `严重`; uncovered 应该/可选 FR with real product value → `高`; deliberately deferred or low-value → `中`/`低` with the reason in the message.

## Coverage statistics

Copy `coverage` into the record exactly as the receipt gives it — the final gate checks that `must_frs == covered + len(gaps)`. State the ratio to the human in one line: `covered / must_frs`.

## Next

Read fully and follow `./04-ux-alignment.md`.
