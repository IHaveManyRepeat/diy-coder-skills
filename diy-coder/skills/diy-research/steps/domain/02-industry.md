# Step 2 (domain) — Industry Analysis（行业分析）

Progress: `Scope → [02 Industry] → 03 Competitive Landscape → 04 Regulatory → 05 Trends → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml` (`topic` / `goals` / `scope`).
**Write (output):** the industry findings into that record; the step message.

## Focus

- Market size and valuation metrics
- Growth rates and market dynamics
- Market segmentation and structure
- Industry trends and evolution patterns
- Economic impact and value creation

## Searches (run in parallel)

Independent areas — use parallel searches or research subagents when available:

- `"{topic} market size value"`
- `"{topic} market growth rate dynamics"`
- `"{topic} market segmentation structure"`
- `"{topic} industry trends evolution"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `market-size` | current valuation, growth rate (CAGR), economic contribution |
| `dynamics-growth` | growth drivers, barriers, cyclical patterns, maturity stage |
| `structure-segmentation` | primary and sub-segments, geographic distribution, value chain |
| `trends-evolution` | emerging trends, recent evolution, technology's effect on the industry |
| `competitive-dynamics` | concentration, intensity, entry barriers, innovation pressure |

## Method

- Web search required — market research reports and industry analyses from named firms or associations.
- Market-size and growth figures must carry their source and year; figures that disagree are both presented.
- Two independent sources for each critical claim; extrapolations are labelled as such.
- `confidence` per finding: `high` / `medium` / `low`.

## Present and continue

Summarize the industry picture — size, direction, structure — then halt:

```
Ready to proceed to competitive landscape analysis?
[C] Continue - Proceed to competitive landscape
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/domain/03-competitive-landscape.md`.
