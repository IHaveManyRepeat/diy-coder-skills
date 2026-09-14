# Step 5 (market) — Competitive Landscape（竞争格局，market 维度收尾）

Progress: `Scope → 02 Behavior → 03 Pain Points → 04 Decisions → [05 Competitive] → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml`; the previous three steps' findings.
**Write (output):** the competitive findings into that record; the step message.

## Focus

- Key players and market share
- Competitive positioning strategies
- Strengths and weaknesses
- Market differentiation opportunities
- Competitive threats and challenges

## Searches (run in parallel)

- `"{topic} key market players market share"`
- `"{topic} competitive positioning strategies"`
- `"{topic} competitor strengths weaknesses"`
- `"{topic} market differentiation opportunities"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `key-players` | who competes, market leaders and challengers |
| `market-share` | share distribution and its source |
| `positioning` | how each player positions; value propositions in play |
| `strengths-weaknesses` | per-player strengths and weaknesses |
| `differentiation` | unserved positions and differentiation openings |
| `threats` | competitive threats and pressures |
| `opportunities` | opportunities the competitive picture leaves open |

## Method

- Web search required — industry reports, competitor sites and annual reports, competitive-intelligence analyses.
- Company self-description is a source, not a fact: corroborate market-share and strength claims independently.
- Two independent sources for each critical claim; conflicts presented, both sides cited.
- `confidence` per finding: `high` / `medium` / `low`.

## Present and continue

Summarize the competitive picture and the openings it leaves, then halt:

```
All four market analysis steps are complete.
[C] Continue - Proceed to synthesis
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/06-synthesis.md`.
