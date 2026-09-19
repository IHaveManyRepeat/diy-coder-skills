# Step 4 (technical) — Architectural Patterns（架构模式）

Progress: `Scope → 02 Stack → 03 Integration → [04 Architecture] → 05 Implementation → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml`; the step-02/03 findings.
**Write (output):** the architecture findings into that record; the step message.

## Focus

- System architecture patterns and their trade-offs
- Design principles and best practices
- Scalability and maintainability considerations
- Integration and communication patterns
- Security, data and deployment architecture

## Searches

- `"system architecture patterns best practices"`
- `"software design principles patterns"`
- `"scalability architecture patterns"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `system-architecture` | monolithic / microservices / serverless / event-driven, with trade-offs |
| `design-principles` | SOLID, clean / hexagonal architecture, API and data design principles |
| `scalability` | horizontal vs vertical scaling, load balancing, caching, consensus, capacity and performance patterns |
| `integration-communication` | boundary decisions between services and modules |
| `security-architecture` | trust boundaries, authn/authz architecture, threat posture |
| `data-architecture` | storage strategy, consistency, data ownership |
| `deployment-ops` | deployment topology, environments, operability |

## Method

- Web search required — architecture documentation, pattern catalogs, conference case studies, ADRs.
- Name the trade-off, not just the pattern: a pattern claim without its cost is incomplete.
- Two independent sources for each critical claim; conflicts presented, both cited.
- `confidence` per finding: `高` / `中` / `低`.

## Present and continue

Summarize the architecture options with their trade-offs for this topic, then halt:

```
Ready to proceed to implementation research?
[C] Continue - Proceed to implementation research
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/technical/05-implementation.md`.
