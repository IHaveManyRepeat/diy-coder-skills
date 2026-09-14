# Step 2 (market) — Customer Behavior and Segments（客户行为与分层）

Progress: `Scope → [02 Behavior] → 03 Pain Points → 04 Decisions → 05 Competitive → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml` (`topic` / `goals` / `scope`).
**Write (output):** the customer-behavior findings into that record; the step message.

## Focus

- Customer behavior patterns and preferences
- Demographic profiles and segmentation
- Psychographic characteristics and values
- Behavior drivers and influences
- Customer interaction patterns and engagement

## Searches (run in parallel)

Independent areas — use parallel searches or research subagents when available:

- `"{topic} customer behavior patterns"`
- `"{topic} customer demographics"`
- `"{topic} psychographic profiles"`
- `"{topic} customer behavior drivers"`

## Findings to write

One `findings[]` entry per area, written to the record as each search lands — never batched to the end. `area` values are the stable handles:

| `area` | what the claim asserts |
| --- | --- |
| `customer-behavior` | behavior patterns, preferences, decision habits |
| `demographics` | age / income / geography / education segmentation |
| `psychographics` | values and beliefs, lifestyle, attitudes, personality traits |
| `segments` | named segment profiles (demographics + psychographics + behavior) |
| `behavior-drivers` | emotional, rational, social, economic influences |
| `interaction-patterns` | research and discovery, purchase process, post-purchase, loyalty |

## Method

- Web search required for every claim — training data alone is a failure mode, not a shortcut.
- Two independent sources for each critical claim; when sources disagree, present both rather than averaging them.
- `confidence` per finding: `high` (multiple authoritative sources agree) / `medium` (one credible source or partial coverage) / `low` (uncertain or dated).
- Note data currency and its limitations inside the claim.
- Focus on actionable customer insights; authoritative research sources over aggregator noise.

## Present and continue

Summarize the key findings — what was verified, what stayed thin — then halt:

```
Ready to proceed to customer pain points?
[C] Continue - Proceed to pain points analysis
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/market/03-pain-points.md`.
