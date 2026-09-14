# Step 2 — The Press Release（新闻稿锻造）

Progress: `Ignition → [Press Release] → Customer FAQ → Internal FAQ → Verdict`

**Read (input):** `prfaq.essentials` and `prfaq.concept_type` from `{output_dir}/prfaq.yaml`; the concept as developed in Step 1; the merged subagent findings.
**Write (output):** the press release message; `prfaq.press_release` (the nine keys) plus `prfaq.stage: 2` and `updated` in one write; `distillate` updates.

## Goal

Produce a press release that would make a real customer stop scrolling and pay attention. Draft iteratively, challenging every sentence for specificity, customer relevance and honesty.

## Concept type adaptation

Check `prfaq.concept_type`. For non-commercial concepts (internal tool, open-source, community/nonprofit), adapt the framing: "announce the initiative" not "announce the product"; "How to Participate" not "Getting Started"; "Community Member quote" not "Customer quote". The structure stays — the language shifts to match the audience.

## The Forge — what each section forces

| Section | What It Forces |
| --- | --- |
| **Headline** | Can you say what this is in one sentence a customer would understand? |
| **Subheadline** | Who benefits and what changes for them? |
| **Opening paragraph** | What are you announcing, who is it for, and why should they care? |
| **Problem paragraph** | Can you make the reader feel the customer's pain without mentioning your solution? |
| **Solution paragraph** | What changes for the customer? (Not: what did you build.) |
| **Leader quote** | What's the vision beyond the feature list? |
| **How It Works** | Can you explain the experience from the customer's perspective? |
| **Customer quote** | Would a real person say this? Does it sound human? |
| **Getting Started** | Is the path to value clear and concrete? |

## Coaching approach

Draft each section yourself first, then model critical thinking by challenging your own draft out loud before inviting the user to sharpen it. That is the cycle: **draft → self-challenge → invite → deepen**. Push one level deeper on every response — a generality earns a demand for the specific. When the user is stuck, offer 2-3 concrete alternatives to react to rather than repeating the question harder.

## Quality bars

Hold the press release to these. Don't enumerate them to the user — embody them in your challenges:

- **No jargon** — if a customer wouldn't use the word, neither should the press release.
- **No weasel words** — "significantly", "revolutionary", "best-in-class" are banned; replace them with specifics.
- **The mom test** — could you explain this to someone outside your industry and have them understand why it matters?
- **The "so what?" test** — every sentence should survive "so what?"; if it can't, cut it or sharpen it.
- **Honest framing** — compelling without being dishonest; if you're overselling, the customer FAQ will expose it.

## Headless mode

Draft the complete press release from the available inputs without interaction. Apply the quality bars internally — challenge yourself, produce the strongest version you can — and write directly to the document.

## Write the section

Write the nine keys under `prfaq.press_release`:

```yaml
  press_release: {headline, subheadline, opening, problem, solution, leader_quote,
                  how_it_works, customer_quote, getting_started}
```

Update `prfaq.stage: 2` and `project.updated` in the same write. Partial drafting is fine — the engine only rejects a key that is present but empty; the nine-key obligation is enforced at `--final`.

## Coaching notes capture → `notes` + distillate

Append one `notes` entry (`{stage: 2, content}`) with the process narrative: which headline framings were tried and how the drafting round went.

Then update `distillate` with the downstream facts: positioning that survived goes to `distillate.value_props`; rejected framings, differentiators explored but not used, and the out-of-scope details the user mentioned (technical constraints, timeline, team context) go to `distillate.constraints` — each rejection written as `Not <X>: because <Y>` so the PRD cannot re-propose it.

## Stage complete

Complete when the full press release reads as a coherent, compelling announcement a real customer would find relevant — the user should feel proud of what they've written, and confident every sentence earned its place.

## Next

Read fully and follow `./03-customer-faq.md`.
