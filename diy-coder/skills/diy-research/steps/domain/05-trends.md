# Step 5 (domain) — Technical Trends and Innovation（技术趋势与创新，domain 维度收尾）

Progress: `Scope → 02 Industry → 03 Competitive Landscape → 04 Regulatory → [05 Trends] → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml`; the previous three steps' findings.
**Write (output):** the trends findings into that record; the step message.

## Focus

- Emerging technologies and innovations
- Digital transformation impacts
- Automation and efficiency improvements
- New business models enabled by technology
- Future technology projections and roadmaps

## Searches

- `"{topic} emerging technologies innovations"`
- `"{topic} digital transformation trends"`
- `"{topic} future outlook trends"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `emerging-tech` | AI/ML/automation impact, disruptive technologies, breakthroughs |
| `digital-transformation` | adoption trends, business-model evolution, customer-experience shifts |
| `innovation-patterns` | how innovation happens in this industry, R&D direction |
| `future-outlook` | roadmaps and projections — near (1–2y), medium (3–5y), long (5y+) |
| `implementation-opportunities` | where the technology can be adopted now |
| `challenges-risks` | adoption barriers, disruption risks, regional variation |
| `recommendations` | technology adoption strategy, innovation roadmap, risk mitigation |

`recommendations` is the bridge into Synthesis: write it as findings with their sources, and step 6 lifts the top ones into `synthesis.key_points`.

## Method

- Web search required — cutting-edge technology reporting, innovation case studies, adoption-timeline research.
- Separate documented adoption from speculation: forward-looking claims name their horizon and stay at `低`/`中` confidence unless multiple sources project the same thing.
- Two independent sources for each critical claim; conflicts presented, both cited.
- `confidence` per finding: `高` / `中` / `低`.

## Present and continue

Summarize the trend picture and what it implies for the topic, then halt:

```
All four domain analysis steps are complete.
[C] Continue - Proceed to synthesis
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/06-synthesis.md`.
