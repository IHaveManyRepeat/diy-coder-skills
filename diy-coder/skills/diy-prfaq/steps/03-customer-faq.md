# Step 3 — Customer FAQ（客户拷问）

Progress: `Ignition → Press Release → [Customer FAQ] → Internal FAQ → Verdict`

**Read (input):** the press release written in Step 2; `prfaq.concept_type`; what the user shared in Steps 1-2.
**Write (output):** the question landscape message; `prfaq.customer_faq` entries plus `prfaq.stage: 3` and `updated` in one write; `distillate` updates.

## Goal

Validate the value proposition by asking the hardest questions a real user would ask — and crafting answers that hold up under scrutiny.

## The devil's advocate

You are now the customer: not a friendly early adopter, but a busy, skeptical person who has been burned by promises before. You've read the press release. Now you have questions.

**Generate 6-10 customer FAQ questions** covering these angles:

- **Skepticism:** "How is this different from [existing solution]?" / "Why should I switch from what I use today?"
- **Trust:** "What happens to my data?" / "What if this shuts down?" / "Who's behind this?"
- **Practical concerns:** "How much does it cost?" / "How long does it take to get started?" / "Does it work with [thing I already use]?"
- **Edge cases:** "What if I need to [uncommon but real scenario]?" / "Does it work for [adjacent use case]?"
- **The hard question they're afraid of:** every product has one question the team hopes nobody asks. Find it and ask it.

**Don't generate softball questions.** "How do I sign up?" is not a FAQ — it's a CTA. Real customer FAQs are the objections standing between interest and adoption.

**Calibrate to `prfaq.concept_type`.** For non-commercial concepts (internal tools, open-source, community projects) adapt the framing: replace "cost" with "effort to adopt", "competitor switching" with "why change from the current workflow", "trust / company viability" with "maintenance and sustainability".

## Coaching the answers

1. **Present all questions at once** — let the user see the full landscape of customer concern.
2. **Work through the answers together.** The user drafts (or you draft and they react). For each answer:
   - *Is it honest?* If the answer is "we don't do that yet", say so — and explain the roadmap or the alternative.
   - *Is it specific?* "We have enterprise-grade security" is not an answer. What certifications? What encryption? What SLA?
   - *Would a customer believe it?* Marketing language in FAQ answers destroys credibility.
3. **An answer reveals a real gap →** name it directly and force a decision: is this a launch blocker, a fast-follow, or an accepted trade-off?
4. **The user can add their own questions too** — often they know the scary ones better than anyone.

## Headless mode

Generate the questions and best-effort answers from the available context. Mark every low-confidence answer with the `[ASSUMPTION]` prefix (`a: '[ASSUMPTION] ...'` — quoted, since an unquoted leading `[` breaks YAML) so a human can review it; the final gate requires zero.

## Write the section

Append to `prfaq.customer_faq` as `{id: PQ-###, q, a}` — IDs continue the one document-wide sequence shared with `internal_faq` (Step 1 has zero questions, so this stage normally opens with `PQ-001`). The hardest question goes first. Update `prfaq.stage: 3` and `project.updated` in the same write.

## Coaching notes capture → `notes` + distillate

Append one `notes` entry (`{stage: 3, content}`) with the process narrative: how the customer questions were worked through and how the trade-off calls felt in the room.

Then update `distillate` with the downstream facts: trade-off decisions (launch blocker / fast-follow / accepted) and scope signals go to `distillate.constraints` — a rejection as `Not <X>: because <Y>`; competitive intelligence that affects adoption goes to `distillate.constraints` when settled, to `distillate.open_questions` when still open.

## Stage complete

Complete when every question has an honest, specific answer — and the user has confronted the hardest customer objections their concept faces. No softballs survived.

## Next

Read fully and follow `./04-internal-faq.md`.
