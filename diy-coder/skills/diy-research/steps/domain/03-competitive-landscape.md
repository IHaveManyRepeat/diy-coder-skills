# Step 3 (domain) — Competitive Landscape and Ecosystem（竞争格局与生态）

Progress: `Scope → 02 Industry → [03 Competitive Landscape] → 04 Regulatory → 05 Trends → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml`; the step-02 findings.
**Write (output):** the competitive-and-ecosystem findings into that record; the step message.

## Focus

- Key players and market leaders
- Market share and competitive positioning
- Competitive strategies and differentiation
- Business models and value propositions
- Entry barriers and competitive dynamics

## Searches (run in parallel)

- `"{topic} key players market leaders"`
- `"{topic} market share competitive landscape"`
- `"{topic} competitive strategies differentiation"`
- `"{topic} entry barriers competitive dynamics"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `key-players` | leaders, major competitors, emerging players, global vs regional split |
| `market-share-positioning` | share distribution, positioning, value propositions, segments served |
| `strategies-differentiation` | cost leadership, differentiation, niche focus, innovation approach |
| `business-models` | how players make money, revenue streams, customer relationship models |
| `dynamics-entry-barriers` | entry barriers, intensity, consolidation trends, switching costs |
| `ecosystem-partnerships` | suppliers, distribution channels, technology alliances, value-chain control |

## Method

- Web search required — competitive-intelligence reports, company sites, annual reports, investor material.
- Company self-description is a source, not a fact: corroborate positioning and share claims independently.
- Two independent sources for each critical claim; conflicts presented, both cited.
- `confidence` per finding: `high` / `medium` / `low`.

## Present and continue

Summarize the players, their strategies and the ecosystem's shape, then halt:

```
Ready to proceed to regulatory focus analysis?
[C] Continue - Proceed to regulatory focus
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/domain/04-regulatory.md`.
