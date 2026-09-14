# Step 3 (market) — Customer Pain Points and Needs（客户痛点与未满足需求）

Progress: `Scope → 02 Behavior → [03 Pain Points] → 04 Decisions → 05 Competitive → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml`; the step-02 findings.
**Write (output):** the pain-point findings into that record; the step message.

## Focus

- Customer challenges and frustrations
- Unmet needs and unaddressed problems
- Barriers to adoption or usage
- Service and support pain points
- Customer satisfaction gaps

## Searches (run in parallel)

- `"{topic} customer pain points challenges"`
- `"{topic} customer frustrations"`
- `"{topic} unmet customer needs"`
- `"{topic} customer barriers to adoption"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `challenges-frustrations` | primary frustrations, usage barriers, frequency |
| `unmet-needs` | critical unmet needs, solution gaps, market gaps |
| `adoption-barriers` | price, technical, trust, convenience barriers |
| `service-support` | customer service issues, support gaps, response times |
| `satisfaction-gaps` | expectation / quality / value-perception / trust gaps |
| `emotional-impact` | frustration severity, loyalty and retention risk, reputation impact |
| `prioritization` | high / medium / low priority, opportunity mapping |

## Method

- Web search required — search satisfaction surveys, reviews, complaint data, support forums.
- Two independent sources for each critical claim; conflicting sources are both presented.
- `confidence` per finding: `high` / `medium` / `low`, with the reason visible in the claim.
- Priority judgements must be grounded in evidence (a documented gap), never in intuition alone.

## Present and continue

Summarize what the evidence supports and where it is thin, then halt:

```
Ready to proceed to customer decision processes?
[C] Continue - Proceed to decision processes analysis
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/market/04-decisions.md`.
