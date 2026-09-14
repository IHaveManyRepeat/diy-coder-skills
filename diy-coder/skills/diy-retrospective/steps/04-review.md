# Step 4 — Epic Review（回顾讨论）

Progress: `Epic Discovery → Deep Analysis → Continuity → [Review] → Actions → Readiness → Finish`

**Read (input):** the patterns and lens readings from step 2; the follow-through table from step 3.
**Write (output):** `wins` / `challenges` / `insights` in the record.

## Facilitation rules (source facilitation guidelines, dialogue stripped)

The source ran this discussion as a scripted five-role dialogue. The roles are gone; the rules that made the discussion useful are not:

- **Psychological safety first.** No blame, no judgment, no names attached to failures. Every challenge is phrased as a system, process or tooling fact — "the schema changed mid-story", never "X changed it".
- **Specific examples beat generalisations.** Every win and every challenge cites its anchor (a story ID, a bug ID, an AC that stayed uncovered, a task that burned rounds).
- **Present the analysis, then open the floor.** Lead with what the evidence showed (patterns, rounds, defects), then explicitly ask for the user's read.
- **Balance.** Celebrate real wins — the retro that only lists problems trains people to hide problems. Then state the challenges honestly.
- **Forward-looking.** Every challenge is worth stating only if it points at a change; if nothing can be done about it, say so rather than parking it as an action item.

## The interaction point (source step-6 WAIT)

Two questions to the user, in this order — and wait for the answers:

1. *What stood out to you as going well in this epic?* — their answer frequently names a win the evidence cannot see (process, communication, product feedback). It belongs in `wins`.
2. *Where did we struggle?* — then route the answer back to the evidence: does an artifact corroborate it? If yes, cite the anchor. If no, record it as the user's read without an `[ASSUMPTION]` prefix — the user's word is a source, not an inference — and say the anchor is missing.

Disagreement between the user's read and the evidence is itself a finding worth one line in `challenges` — do not smooth it over, and do not let it become a blame statement.

## Filling the three lists

- **`wins`** — what worked and should be repeated; each cites an anchor (a pattern, a recovered blocker, a defect class extinguished, a clean augment round).
- **`challenges`** — what slowed the epic down or threatens the next one; systems-framed, anchor-cited, one line each. Deferred findings that will bite the next epic belong here even if they were deliberately deferred.
- **`insights`** — what was learned that changes future behaviour; the source's "key takeaways". Three good ones beat ten restatements of the challenges.

Keep the main clause plain — the narrative of who said what stays out of the record. The discussion is communication; the three lists are the artifact.

## Next

Read fully and follow `./05-actions.md`.
