# Step 3 — Detail Pass（风险详查）

Progress: `Orientation → Walkthrough → [Detail Pass] → Testing → Wrap-Up`

**Read (input):** the diff; the spec (its `## Spec Change Log` when present); the concerns written in step 2.
**Write (output):** the risk-spot message; the `risks[]` section of the draft record.

## Rules for this step

- Surface what the human should **think about**, not what the code got wrong. Machine hardening already handled correctness.
- You detect the risk category by pattern; the human judges significance. Do not assign severity scores or numeric rankings — ordering by blast radius below is sequencing for readability, not a severity judgment.
- If no high-risk spot exists, say so explicitly. Do not invent findings.

## Identify risk spots

Scan the diff for risk-sensitive patterns; pick 2–5 spots where a mistake would have the highest blast radius — not the most complex code, but the code where being wrong costs the most.

- `[auth]` — authentication, authorization, session, token, permission, access control
- `[public API]` — new/changed endpoints, exports, public methods, interface contracts
- `[schema]` — database migrations, schema changes, data model modifications, serialization
- `[billing]` — payment, pricing, subscription, metering, usage tracking
- `[infra]` — deployment, CI/CD, environment variables, config files, infrastructure
- `[security]` — input validation, sanitization, crypto, secrets, CORS, CSP
- `[config]` — feature flags, environment-dependent behavior, defaults
- `[other]` — anything risk-sensitive outside the above (concurrency, data privacy, backwards compatibility); use a descriptive tag

Sequence the spots highest blast radius first (how much breaks if this is wrong), not by diff order or file order. More than 5 qualifying spots → show the top 5 and note "N additional spots omitted — ask if you want the full list".

When no spot matches these patterns, state: "No high-risk spots found in this change — the diff speaks for itself." Do not force findings.

## Surface machine hardening findings

Check whether the spec has a `## Spec Change Log` section with entries (populated by adversarial review loops).

- **Entries exist:** read them and surface what is instructive for the human — not bugs already fixed, but decisions the review loop flagged that the human should know about. Format: a brief summary of what was flagged and what was decided.
- **No entries, or no spec:** skip this section entirely — do not mention it.

## Present

One message:

```
Orientation → Walkthrough → [Detail Pass] → Testing → Wrap-Up

### Risk Spots

- `path:line` — [tag] reason-phrase
```

Example:

```
- `src/auth/middleware.ts:42` — [auth] New token validation bypasses rate limiter
- `migrations/003_add_index.sql:7` — [schema] Index on high-write table, check lock behavior
- `api/routes/billing.ts:118` — [billing] Metering calculation changed, verify idempotency
```

Only when hardening findings exist, add:

```
### Machine Hardening

- Finding summary — what was flagged, what was decided
```

End with:

```
---

You've seen the design and the risk landscape. From here:
- **"dig into [area]"** — I'll deep-dive that specific area with correctness focus
- **"next"** — I'll suggest how to observe the behavior
```

## Write the record

Append to this run's record, in blast-radius order:

```yaml
    risks:
      - {label: auth|public API|schema|billing|infra|security|config|other, where: path:line, why: reason-phrase}
```

## Targeted re-review (repeatable)

When the human says "dig into [area]" (e.g. "dig into the auth changes", "dig into the schema migration"):

1. If the area maps to no code in the diff, say so — "I don't see [area] in this change — did you mean something else?" — and return to the closing menu.
2. Identify every location in the diff relevant to the area.
3. Read each location in full context — surrounding code, not just the hunk.
4. Shift to **correctness mode**: trace edge cases, check boundary conditions, verify error handling, look for off-by-one errors, races, resource leaks.
5. Present findings compactly — each is `path:line` + what you found + why it matters.
6. Nothing concerning → say so: "Looked closely at [area] — nothing concerning. The implementation is solid."
7. After presenting, show only the closing menu (not the risk-spot list again).

Multiple re-reviews are allowed; each round presents new findings and the closing menu only.

## Next

Default: read fully and follow `./04-testing.md`. Early exit: when the human signals a decision about this {change_type}, confirm their intent and go to `./05-wrapup.md`; if you misread them, acknowledge and continue here.
