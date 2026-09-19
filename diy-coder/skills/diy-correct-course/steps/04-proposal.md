# Step 4 — Settle the Proposal（提案成形与呈现）

Progress: `Initialize → Analysis → Edits → [Proposal] → Route → Finish`

**Read (input):** the record as filled by steps 1–3; the `chain` from the `collect` receipt.
**Write (output):** the record's `approach` / `ripple` / `effort` / `open_questions`; the draft presented for review.

## Map the source's five sections onto the record

The source compiled a five-part document; here each part is a field (no markdown report is written — the record is the report):

| Source section | Record field |
| --- | --- |
| §1 Issue summary | `trigger` (+ the evidence gathered in step 2) |
| §2 Impact analysis | `impacts` + `ripple` |
| §3 Recommended approach | `approach` + `effort` |
| §4 Detailed change proposals | `edits` |
| §5 Implementation handoff | `handoff` (route set in step 5) |

## Settle the recommended path (source §3 / checklist §4)

`approach.path` is one of three, chosen from the step-2 evaluation:

- **`直接调整`** — modify or add within the existing plan;
- **`回滚`** — revert completed work to simplify the fix;
- **`MVP 复审`** — reduce scope or move goals.

`approach.why` carries the rationale, including the alternatives you rejected and why (source: trade-offs considered). The final gate refuses a record whose path is still undecided — this is the source's "select recommended path" made mechanical.

## Ripple (source §3 连带影响)

`ripple` lists what the change pulls along **downstream of the edits** — the reference chain made readable: which ACs, TCs, or sprint tasks must be revisited after the edit lands. Take the points from the receipt's `chain`; add semantic couplings the chain cannot see (a report format another story consumes, a naming convention) as plain-language lines, each naming its ID. The chain is the evidence, not the limit — but never invent fallout without naming where it lands.

## Effort (source §3)

`effort` carries the three source dimensions: `estimate` (how much work), `risk` (what could go wrong), `timeline_impact` (what it does to the sprint). One line each — this is decision input, not a novel.

## Present the complete proposal (source step-4 ask)

Render via diy-viewer — the silent side-step command from SKILL.md — then present the record in one message: trigger, impacts, edits, path and why, ripple, effort, open questions. Ask the source's question: **Continue [c] or Edit [e]?** Edits go back to `./03-edits.md`; structural changes (impact set, path) are handled here.

The record stays `status: 草稿` until step 5's approval.

## Next

Read fully and follow `./05-route.md`.
