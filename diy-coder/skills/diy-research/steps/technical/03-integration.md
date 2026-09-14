# Step 3 (technical) — Integration Patterns（集成模式）

Progress: `Scope → 02 Stack → [03 Integration] → 04 Architecture → 05 Implementation → Synthesis`

**Read (input):** the record in `{output_dir}/research.yaml`; the step-02 findings.
**Write (output):** the integration findings into that record; the step message.

## Focus

- API design patterns and protocols
- Communication protocols and data formats
- System interoperability approaches
- Microservices integration patterns
- Event-driven architectures and messaging

## Searches (run in parallel)

- `"{topic} API design patterns protocols"`
- `"{topic} communication protocols data formats"`
- `"{topic} system interoperability integration"`
- `"{topic} microservices integration patterns"`

## Findings to write

One `findings[]` entry per area, written as each search lands:

| `area` | what the claim asserts |
| --- | --- |
| `api-design` | REST / GraphQL / RPC / webhook patterns and their trade-offs |
| `protocols` | HTTP(S), WebSocket, message-queue, gRPC/Protobuf in play |
| `data-formats` | JSON/XML, binary serialization, flat files, domain standards |
| `interoperability` | point-to-point, API gateway, service mesh, ESB |
| `microservices` | gateway, service discovery, circuit breaker, saga |
| `event-driven` | pub/sub, event sourcing, message brokers, CQRS |
| `integration-security` | OAuth 2.0 / JWT, API keys, mutual TLS, data encryption |

## Method

- Web search required — API guides, protocol specifications, case studies.
- Protocol and pattern claims must cite an authoritative source (spec, vendor doc, documented case), not a blog summary alone.
- Two independent sources for each critical claim; conflicts are presented as such.
- `confidence` per finding: `high` / `medium` / `low`.

## Present and continue

Summarize which integration approaches fit the researched topic and why, then halt:

```
Ready to proceed to architectural patterns analysis?
[C] Continue - Proceed to architectural patterns
```

HALT — wait for the user. On 'C', read fully and follow the next file.

## Next

Read fully and follow `steps/technical/04-architecture.md`.
