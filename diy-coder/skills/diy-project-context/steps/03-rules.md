# Step 3 — Rules（AI 关键规则）

Progress: `Scan → Context → [Rules] → Finalize`

**Read (input):** the receipt's `stack` and `docs_found`; the code the rules point at, only where a claim needs a witness.
**Write (output):** `rules[]` in `{output_dir}/project-context.yaml` — one `PC-###` at a time.

## What qualifies

A rule here is an **unobvious detail an AI agent would otherwise miss** — the reason this file exists. Test each candidate:

- Would a competent agent get this wrong without being told? If not, cut it (obvious advice is context tax).
- Is it specific and actionable, or a generality? "Use TypeScript strict mode and forbid `any`; `tsc --noEmit` gates it" is a rule; "write clean code" is not.
- Does it carry a witness? `where` names the file or the command that proves it — no rule without a witness.

Work one category at a time, in this order (the seven rule domains of the source workflow):

1. `stack` — version constraints and compatibility boundaries agents must respect.
2. `language` — configuration, imports/exports, error handling, async conventions of the actual language in use.
3. `framework` — the framework's patterns in this codebase (hooks, routing, middleware, state).
4. `testing` — structure, mocks, boundaries, coverage expectations; the real command.
5. `quality` — lint/format gates, file and folder conventions, naming, documentation requirements.
6. `workflow` — branches, commits, PR/review gates, deployment procedure, and the development/operations facts: prerequisites, install / build / run / test commands, environment setup, CI. Commands and paths verbatim — never paraphrased.
7. `anti-pattern` — what must not happen: forbidden shortcuts, the edge cases that burned this project, security and performance traps.

## Per category

Draft the category's rules, show them, and wait:

```
{drafted rules for <category> — rule / why / where for each}

[C] Continue — save these and move to the next category
[E] Edit — change a rule, drop one, or add your own
```

HALT — wait for the choice. On **C** write the category's rules into `rules[]`; on **E** revise and present again.

Advanced-elicitation and party-mode passes are not wired to this skill (their B4 skills do not exist yet) — when the human wants deeper scrutiny, run the scrutiny in conversation and keep the same rule shape.

## Minting and amending

- `id` — `PC-###`, three digits: next = highest existing + 1. IDs are sequential, stable, never renumbered or reused. Read the file to find the highest — do not guess.
- Amend an existing rule by editing its entry in place, then append `{date, change, reason}` to `revisions`. Never mint a second ID for a changed rule.
- Drop a rule only with a `revisions` entry naming what went and why — the rescan gate in step 4 fails on a silent disappearance (`ID_UNSTABLE`).

## Lean by default

These rules are read by an agent on every future task, so length is a cost. One line per rule field; combine rules that share a witness; cut any rule the human cannot tie to a real file or command.

## Next

Read fully and follow `./04-finalize.md`.
