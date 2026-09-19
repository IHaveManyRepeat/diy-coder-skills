# Step 4 — Internal FAQ（内部拷问）

Progress: `Ignition → Press Release → Customer FAQ → [Internal FAQ] → Verdict`

**Read (input):** the press release and customer FAQ written so far; `prfaq.concept_type`; the merged subagent findings (market risks, competitive threats).
**Write (output):** the internal question landscape message; `prfaq.internal_faq` entries plus `prfaq.stage: 4` and `updated` in one write; `distillate` updates.

## Goal

Stress-test the concept from the builder's side. The customer FAQ asked "should I use this?" The internal FAQ asks "can we actually pull this off — and should we?"

## The skeptical stakeholder

You are now the internal stakeholder panel — engineering lead, finance, legal, operations, the CEO who has seen a hundred pitches. The press release was inspiring. Now prove it's real.

**Generate 6-10 internal FAQ questions** covering these angles:

- **Feasibility:** "What's the hardest technical problem here?" / "What do we not know how to build yet?" / "What are the key dependencies and risks?"
- **Business viability:** "What do the unit economics look like?" / "How do we acquire the first 100 customers?" / "What's the competitive moat — and how durable is it?"
- **Resource reality:** "What does the team need to look like?" / "What's the realistic timeline to a usable product?" / "What do we have to say no to in order to do this?"
- **Risk:** "What kills this?" / "What's the worst-case scenario if we ship and it doesn't work?" / "What regulatory or legal exposure exists?"
- **Strategic fit:** "Why us? Why now?" / "What does this cannibalize?" / "If this succeeds, what does the company look like in 3 years?"
- **The question the founder avoids:** the internal counterpart to the hard customer question — the thing that keeps them up at night but hasn't been said out loud.

**Calibrate to context.** A solo founder building an MVP needs different internal questions than a team inside a large organization: don't ask about "board alignment" for a weekend project, don't ask about "weekend viability" for an enterprise product. For non-commercial concepts (`内部` / `开源` / `社区`), replace "unit economics" with "maintenance burden", "customer acquisition" with "adoption strategy", and "competitive moat" with "sustainability and contributor / stakeholder engagement".

## Coaching the answers

Same approach as the customer FAQ — draft, challenge, refine:

1. **Present all questions at once.**
2. **Work through the answers.** Demand specificity. "We'll figure it out" is not an answer; neither is "we'll hire for that". What's the actual plan?
3. **Honest unknowns are fine — unexamined unknowns are not.** If the answer is "we don't know yet", the follow-up is: "What would it take to find out, and when do you need to know by?"
4. **Watch for hand-waving on resources and timeline** — the most commonly over-optimistic answers. Push for concrete scoping.

## Headless mode

Generate questions calibrated to context plus best-effort answers, and flag high-risk areas and unknowns prominently (low-confidence answers carry the `[假设]` prefix, quoted when it leads the scalar).

## Write the section

Append to `prfaq.internal_faq` as `{id: PQ-###, q, a}` — IDs continue the same document-wide sequence, so the first internal question follows the last customer question. The hardest internal question goes first. Update `prfaq.stage: 4` and `project.updated` in the same write.

## Coaching notes capture → `notes` + distillate

Append one `notes` entry (`{stage: 4, content}`) with the process narrative: how the panel's questions were worked through and the coaching behind the strategic positioning calls.

Then update `distillate` with the downstream facts: resource and timeline estimates, technical dependencies, and any rejected option (as `Not <X>: because <Y>`) go to `distillate.constraints`; unresolved risks, and each unknown with its "what would it take to find out" answer, go to `distillate.open_questions`.

## Stage complete

Complete when the internal questions have honest, specific answers — and the user has a clear-eyed view of what it actually takes to execute this concept. Optimism is fine. Delusion is not.

## Next

Read fully and follow `./05-verdict.md`.
