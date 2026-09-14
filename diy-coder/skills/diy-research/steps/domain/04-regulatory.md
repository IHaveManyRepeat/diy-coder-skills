# Step 4 (domain) — Regulatory Focus（监管与合规）

Progress: `Scope → 02 Industry → 03 Competitive Landscape → [04 Regulatory] → 05 Trends → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml`; the previous steps' findings.
**Write (output):** the regulatory findings into that record; the step message.

## Focus

- Specific regulations and compliance frameworks
- Industry standards and best practices
- Licensing and certification requirements
- Data protection and privacy regulations
- Environmental and safety requirements

## Searches

- `"{topic} regulations compliance requirements"`
- `"{topic} standards best practices"`
- `"data privacy regulations {topic}"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `regulations` | applicable regulations by name, enforcing body, recent changes |
| `standards` | industry technical standards, guidelines, certification requirements |
| `compliance-frameworks` | frameworks, quality assurance, audit obligations |
| `data-privacy` | GDPR / CCPA and sector-specific privacy duties, consent and data handling |
| `licensing-certification` | licences, certifications and who must hold them |
| `implementation-considerations` | what compliance costs in practice (process, tooling, staffing) |
| `regulatory-risk` | regulatory and compliance risks, penalties, timelines |

## Method

- Web search required — regulation text, regulator websites, official government and association sources over commentary.
- Cite effective dates and compliance timelines; jurisdictional differences are named explicitly.
- Two independent sources for each critical claim; ambiguous or pending rules are flagged in the claim.
- `confidence` per finding: `high` / `medium` / `low` — regulatory claims without a primary source stay at `low`.

## Present and continue

Summarize the binding requirements and the practical burden they create, then halt:

```
Ready to proceed to technical trends?
[C] Continue - Proceed to technical trends
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/domain/05-trends.md`.
