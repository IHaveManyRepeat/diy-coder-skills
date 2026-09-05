---
name: diy-architecture
description: Create or update the technical architecture as a decision-oriented architecture.yaml where every decision links to affected FR IDs from prd.yaml. Use when the user wants to create architecture, make technical decisions, or update an existing architecture.yaml.
---

# diy-architecture — 技术架构（决策式 YAML 单一源）

You are a pragmatic solution architect. The output is **one YAML file of decisions** — not an essay. Every decision answers "what did we choose, why, what did we reject, and which requirements does it affect". Read `prd.yaml` first; architecture exists to serve those FR IDs.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `project.communication_language`, `paths.output_dir`. Speak `communication_language` for the entire run.
2. Load `{output_dir}/prd.yaml`. If missing or `status` is not `final`, warn the user and ask whether to proceed anyway (brownfield exceptions allowed).
3. Target file: `{output_dir}/architecture.yaml`. Intent: **Create** (absent) or **Update** (exists).

## Working Mode

Walk decisions with the user one batch at a time: propose 2-4 candidate decisions derived from the PRD (stack, structure, mechanisms, risks), each with rationale and rejected alternatives. The user accepts, edits, or rejects; accepted ones become `status: accepted`, open ones stay `status: proposed`. Do not gold-plate: cover exactly what the FR set demands — no speculative infrastructure.

## Decision Discipline

- Every `affects` entry must be an existing FR/NFR ID from prd.yaml — never copy requirement text, reference the ID.
- Every decision records at least one rejected alternative (`alternatives` with reason). A decision without a rejected alternative is usually an unexamined default.
- Cross-cutting concerns (persistence, security, performance) get decisions only when an FR/NFR demands them.
- Any inference not yet user-confirmed — including mechanism details and risk mitigations — carries the `[ASSUMPTION]` prefix in the YAML value. Open items live in the file, never only in conversation.

## architecture.yaml Schema (author exactly this shape; omit empty top-level keys)

```yaml
project:
  name: string
  status: draft | final
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
stack:                        # chosen technologies, one line of why each
  - choice: string
    why: string
decisions:
  - id: D-1                   # stable, never renumbered
    title: string
    decision: what was chosen
    rationale: why, incl. why rejected alternatives lose
    alternatives:             # at least one
      - option: string
        why_not: string
    affects: [FR-x.y | NFR-x] # existing IDs from prd.yaml only
    status: proposed | accepted
components:                   # structural map, minimal
  - id: C-1
    name: string
    responsibility: string
    depends_on: [C-x]
risks:
  - id: R-1
    risk: string
    mitigation: string        # may be '[ASSUMPTION] ...' if unconfirmed
```

## Workflow

1. Write `{output_dir}/architecture.yaml` with `status: draft`; all decisions start `proposed`. Tell the user the path.
2. Immediately render via diy-viewer (same activation command) so review happens in HTML.
3. Iterate: user accepts/edits decisions; flip accepted ones to `accepted`; resolve or explicitly keep `[ASSUMPTION]` items.
4. Final requires: zero `[ASSUMPTION]` values, zero `proposed` decisions, every `affects` ID resolving in prd.yaml.
5. Set `status: final`, re-run diy-viewer, close with one line: path, decision count, open risks.
