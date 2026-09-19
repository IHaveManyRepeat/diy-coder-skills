# Step 2 (technical) — Technology Stack（技术栈）

Progress: `Scope → [02 Stack] → 03 Integration → 04 Architecture → 05 Implementation → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml` (`topic` / `goals` / `scope`).
**Write (output):** the stack findings into that record; the step message.

## Focus

- Programming languages and their evolution
- Development frameworks and libraries
- Database and storage technologies
- Development tools and platforms
- Cloud infrastructure and deployment platforms

## Searches (run in parallel)

Independent areas — use parallel searches or research subagents when available:

- `"{topic} programming languages frameworks"`
- `"{topic} development tools platforms"`
- `"{topic} database storage technologies"`
- `"{topic} cloud infrastructure platforms"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `languages` | popular and emerging languages, evolution, performance characteristics |
| `frameworks` | dominant frameworks and use cases, micro-frameworks, ecosystem maturity |
| `databases` | relational, NoSQL, in-memory, warehousing options |
| `dev-tools` | editors/IDEs, version control, build systems, testing tooling |
| `cloud-infra` | cloud providers, containers, serverless, CDN/edge |
| `adoption-trends` | migration patterns, emerging vs legacy technology, community trends |

## Method

- Web search required — trend reports, developer surveys, official documentation, open-source projects and their tech choices.
- Two independent sources for each critical claim; when sources disagree (benchmarks especially), present both.
- `confidence` per finding: `高` / `中` / `低`.
- Prefer current release and adoption facts; version-sensitive claims must carry their date.

## Present and continue

Summarize the stack picture and where adoption is moving, then halt:

```
Ready to proceed to integration patterns analysis?
[C] Continue - Proceed to integration patterns
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/technical/03-integration.md`.
