# Step 2 — Deep Analysis（结构化证据分析）

Progress: `Epic Discovery → [Deep Analysis] → Continuity → Review → Actions → Readiness → Finish`

**Read (input):** the `collect` receipt (`stories` / `metrics` / `bugs` / `coverage` / `warnings`); the task blocks it points at — `sprint.yaml` tasks of this epic (`note` / `evidence` / `loop` / `review.findings`), `bug-log.yaml` entries, `test-plan.yaml` coverage.
**Write (output):** `patterns` in the record — cross-story themes with evidence and counts.

## The diy transformation (read this first)

The source skill reads each story's markdown and mines "Dev Notes", "Review", "Lessons Learned", "Technical Debt", "Testing" sections. In diy those narrative sections do not exist as prose — the same evidence is already structured, and it is reached by ID, not by reading documents:

| Source evidence class | diy source (structured) |
|---|---|
| Dev Notes and Struggles | task `note` + `loop.rounds` / `loop.outcome` + `blocked_reason` in `sprint.yaml` |
| Review Feedback Patterns | task `review.findings[]` (`layer` / `route` / `note`) in `sprint.yaml` |
| Lessons Learned | `note` fields + `bug-log.yaml` `prevention` / `pattern` columns |
| Technical Debt Incurred | `blocked_reason`, `route: 后置` findings, bug `root_cause` |
| Testing and Quality Insights | `test-plan.yaml` TC `status` + `coverage_gaps` + the task `evidence` ledger |
| Velocity Patterns | `loop.rounds` aggregate = the receipt's `metrics.rounds_total` |

Two consequences: never re-derive a count the receipt already carries, and never restate an artifact's prose — cite the ID. `metrics` includes all raw numbers; a `pattern` adds the interpretation on top.

## Four analytical lenses (the source's speaking roles, kept as viewpoints)

The source ran its analysis through five speaking roles. The roles as dialogue are not carried over; what they were for — different readings of the same evidence — is. Apply all four to the evidence above:

- **Developer lens** — where did the implementation fight back? Read `loop.rounds` outliers (rounds ≫ the epic median), `blocked_reason`, re-opened tasks, `augment: 失败`. A high round count is the diy signal for "the source's underestimated complexity".
- **Product lens** — did the epic deliver what the stories promised? Read `stories.pending` (what never landed), deferred findings, and ACs left in `coverage_gaps` with `decision: 待办`.
- **QA lens** — where would defects slip through? Read `coverage` (ACs with no case), `bug-log` `subclass` clustering, and `evidence` ledgers that were written after the fact.
- **Architect lens** — which decisions aged badly? Read `bug-log` `root_cause`/`pattern` for repeated classes, deferred findings that name structure, and any `blocked_reason` citing an upstream spec.

Each lens reports its reading in the closing summary; only what survives cross-examination becomes a pattern, a challenge, or an action item.

## Synthesis rules (source step-2)

- **A pattern needs ≥2 stories** — a theme evidenced in one story is an anecdote. Each `patterns[]` entry: `theme` (one line), `evidence` (story IDs `S-x` and bug IDs `BUG-0xx`, both resolvable), `count` (how many stories showed it, ≥2, consistent with the evidence listed).
- **Recurring review feedback counts as one pattern per theme**, not per finding: group `review.findings[]` by the theme behind them and cite representative IDs.
- **Wins, challenges, insights are the analysis output of this step, not the discussion transcript.** They are filled here as raw material and finalised in step 4; keep them evidence-anchored and blame-free.
- **No time estimates anywhere** — not in patterns, not in actions. Rounds and counts are the diy proxy for velocity; hours and days are forbidden by the source skill and stay forbidden.

## No patterns found

A clean epic may genuinely have none. Write `patterns: []` and say so explicitly in the closing summary — never invent a pattern to fill the section, and never pad a one-story observation into a theme.

## Next

Read fully and follow `./03-continuity.md`.
