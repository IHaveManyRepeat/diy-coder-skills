# Step 4 — UX Alignment（UX 对齐）

Progress: `Document Discovery → Requirement Inventory → Coverage Validation → [UX Alignment] → Epic Quality Review → Final Assessment`

**Read (input):** the receipt's `docs.design` / `docs.architecture`; `design.yaml` and `architecture.yaml` when present.
**Write (output):** UX findings (`area: ux`) — alignment gaps, or the implied-but-missing warning.

## Document status

In diy the design/UX single source is `design.yaml` (pages `P-x`, design tokens). The receipt says whether it exists; the source workflow's `*ux*.md` search maps onto it one-to-one — do not go looking for markdown UX files.

## When design.yaml exists — validate alignment

**UX ↔ PRD.** Every user journey the design shows must trace to PRD requirements (`FR-x.y`) or be flagged: a page carrying features no requirement backs is scope the PRD never approved (`route: diy-prd`); a requirement with a user-visible surface the design never covers is a gap (`route: diy-design`).

**UX ↔ Architecture.** Check that architecture decisions (`architecture.yaml` `D-x`) support what the design needs — responsiveness and load-time targets where the design implies them, client-side state, any UI component whose backing service no decision covers. Name the decision, or its absence, with an evidence anchor.

Findings here are `area: ux`; severity by consequence — `high` when a requirement cannot be built as designed, `medium` for alignment debt, `low` for polish.

## When design.yaml is absent — is UX implied?

Absence is legitimate (a CLI, a library, a backend service) — but never assume it (source step-4 rule "Don't assume UX is not needed"). Judge from the PRD:

- does it name user interfaces, screens, or web/mobile surfaces (`prd.yaml` features / users)?
- is this a user-facing application, or does an epic deliver something a person operates?

Implied but missing → a finding (`area: ux`, `severity: medium`, `route: diy-design`) with the implying FR IDs as evidence — the source workflow's warning, kept. Not implied → say so explicitly and record nothing; step 6 reports it as a clean area.

## Next

Read fully and follow `./05-epic-quality-review.md`.
