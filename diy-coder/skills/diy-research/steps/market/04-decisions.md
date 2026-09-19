# Step 4 (market) — Customer Decisions and Journey（客户决策与旅程）

Progress: `Scope → 02 Behavior → 03 Pain Points → [04 Decisions] → 05 Competitive → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml`; the step-02/03 findings.
**Write (output):** the decision-and-journey findings into that record; the step message.

## Focus

- Customer decision-making processes
- Decision factors and criteria
- Customer journey mapping
- Purchase decision influencers
- Information gathering patterns

## Searches (run in parallel)

- `"{topic} customer decision process"`
- `"{topic} buying criteria factors"`
- `"{topic} customer journey mapping"`
- `"{topic} decision influencing factors"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `decision-process` | stages, timelines, complexity, evaluation methods |
| `decision-factors` | primary and secondary criteria, how they are weighed, how they shift |
| `journey-mapping` | awareness → consideration → decision → purchase → post-purchase |
| `touchpoints` | digital and offline interaction points, information sources |
| `information-gathering` | research methods, trusted sources, duration, evaluation criteria |
| `influencers` | peer, expert, media, social-proof influence |
| `purchase-factors` | immediate vs delayed drivers, brand loyalty, price sensitivity |
| `decision-optimizations` | friction reduction, trust building, conversion, loyalty |

## Method

- Web search required — decision research studies, journey-mapping methodologies, buying-criteria analyses.
- Two independent sources for each critical claim; conflicts are presented, not resolved silently.
- `confidence` per finding: `高` / `中` / `低`.
- Keep journey claims anchored to the researched topic, not to a generic funnel template.

## Present and continue

Summarize the mapped journey and the factors that actually move decisions, then halt:

```
Ready to proceed to competitive analysis?
[C] Continue - Proceed to competitive analysis
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/market/05-competitive.md`.
