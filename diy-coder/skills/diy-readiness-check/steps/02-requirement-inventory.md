# Step 2 — Requirement Inventory（需求清点）

Progress: `Document Discovery → [Requirement Inventory] → Coverage Validation → UX Alignment → Epic Quality Review → Final Assessment`

**Read (input):** the `collect` receipt (`requirements`, `counts`, `diyc.check`); `prd.yaml` only when a human question needs one requirement's exact wording.
**Write (output):** the `counts` block of the record (confirmed); findings for anything the inventory exposed.

## What changed from the source workflow (read this first)

The source step-2 read the whole PRD (whole or sharded markdown) and hand-extracted every FR and NFR into prose sections of a report. That extraction was itself a failure surface: hand-counting drifts, and a requirement missed once silently vanishes from the coverage matrix that follows.

In diy the PRD is structured (`prd.yaml`), so the inventory is machine-derived. The `collect` receipt's `requirements.frs` lists every FR with its `priority` and owning `feature`, `requirements.nfrs` every NFR, and `counts` the tallies. Do not re-extract, do not re-summarize — present the receipt.

- An FR the human expects but the receipt lacks is not an extraction miss: it is absent from `prd.yaml`. Record it as a finding with `route: diy-prd`, or say so and let the human decide.
- Statement text is referenced, never copied into the record — point at the ID (`prd.yaml features[F-1].requirements[FR-1.1]`).

## Present the inventory

One message, front-loaded:

- FR count with its must/should/could split; NFR count; the FR list as `FR-x.y (must) — feature F-x`;
- epics / stories / AC counts from the receipt;
- open questions the PRD still carries — the `diyc.check` receipt reports unclosed `open_questions` as `PENDING_DECISION`; a PRD with open questions is not settled input.

Halt for the human to scan the list: this is the last chance to catch a missing requirement before coverage is judged.

**Completeness read** (source step-2 §6, "PRD Completeness Assessment"). Say plainly whether the PRD reads complete and unambiguous for the build: the receipt covers the mechanics (enums, unclosed questions, duplicate IDs), your read covers clarity — a requirement whose statement cannot be turned into an AC without guessing is a finding (`area: prd`, `route: diy-prd`), with the FR ID as evidence.

## Additional requirements (never labeled FR/NFR)

The source workflow also looked for constraints, assumptions and technical requirements that no label captured. In the diy shape they live in `prd.yaml` `out_of_scope` / `open_questions` / `nfrs` and in `architecture.yaml` decisions. If the human knows a constraint that lives in none of them, that is a finding (`area: prd`, `route: diy-prd`) — never something carried silently.

## Evidence from diyc

The `diyc.check` receipt for `prd` carries the mechanical side (enums, ID uniqueness, unclosed questions, zero `[ASSUMPTION]`). Relay each violation as an inventory gap with its `where`; do not re-check it by eye.

## Next

Read fully and follow `./03-coverage-validation.md`.
