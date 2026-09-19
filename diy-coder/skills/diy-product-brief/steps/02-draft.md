# Step 2 — Draft（逐节成文）

Progress: `Discovery → [Draft] → Finalize`

**Read (input):** the dump and the extracts in the conversation; the skeleton in `{output_dir}/brief.yaml`.
**Write (output):** the drafted sections; live `decisions` and `addendum` entries; `[假设]` tags.

## Shape follows the product

The default structure is a starting point, not a contract: drop sections that do not earn their place, add what the product needs, reorder freely. The brief serves the product's story, not the template's shape. Where the default sections land in the schema:

| Default section | Schema home |
| --- | --- |
| Executive Summary | `pitch` — 2-3 paragraphs: what this is, what problem it solves, why it matters, why now; must stand alone |
| The Problem | `problem` — the pain, who feels it, how they cope today, the cost of the status quo; real scenarios |
| The Solution | `solution` — the experience and the outcome, not the implementation |
| What Makes This Different | `value[].point` — honest: if the moat is execution speed, say so; never fabricate a technical moat |
| Who This Serves | `users` — vivid but brief: who they are, what they need |
| Success Criteria | `value[].evidence` — how we know it is working; user signals and business objectives, measurable |
| Scope | `extra_sections` — what is in for the first version, what is explicitly out; a boundary, not a feature list |
| Vision | `extra_sections` — where this goes if it succeeds; inspiring but grounded |
| Anything the product needs beyond the above | `extra_sections` — specialized domains, compliance, hardware or platform constraints |

## Drafting rules

- **Coaching path:** one section at a time — ask, listen, structure what was said. Push back when an answer is thin; never do the thinking for the user; unknowns are surfaced, not smoothed over.
- **Fast path:** batch the gaps into one or two consolidated questions, then draft every section with `[假设]` tags in place of the inferences the user must correct in review.
- **Tags:** every inference waiting on the user is tagged `[假设]` in place and echoed as one line in `brief.assumptions`. Unknowns that are nobody's inference — facts not yet known — go to `open_questions` instead.
- **Decisions are canonical memory, written live.** Each decision, change, or override gets a `BD-###` entry with its `rationale` at the moment it is made: id = highest existing + 1, three digits, never renumbered or reused. A decision that supersedes an earlier one flips the old `status` to `已反转` and adds a new entry — the earlier history is never rewritten.
- **Addendum is written live, never deferred to finalize.** User-contributed depth that belongs in a downstream document (PRD, architecture, solution design) or earned a place but does not fit the brief — rejected-alternative rationale, options-considered matrices, parked-roadmap context, technical constraints, in-depth personas, sizing data. `why_separate` says which of the two it is. Audit and override information never goes in the addendum.
- **Right-size as you go:** `stakes` sets how much rigor each section carries — a `个人兴趣` brief is short, a `投资人` brief is dense.

## Present

One message per section on the coaching path, one full draft on the fast path — in `document_output_language`, whole section at a time, no drip-feeding. End each message with what is still open (`open_questions` plus the live `[假设]` tags).

## Next

Read fully and follow `./03-finalize.md` when the sections are filled and the user signals the draft is done. A change signal on an existing brief → `./04-update.md`; a request to read the draft back critically → `./05-validate.md`.
