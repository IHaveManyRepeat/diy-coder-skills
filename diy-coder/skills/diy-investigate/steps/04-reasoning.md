# Step 4 — Reasoning（因果推理与假设生命周期）

Progress: `Acknowledge → Stronghold → Perimeter → [Reasoning] → Source Trace → Report`

**Read (input):** the record's `stronghold` / `evidence` / `missing_evidence`.
**Write (output):** the record's `timeline` / `hypotheses` / `evidence` / `backlog`.

## Trace causality

- **症状驱动 mode** — trace backward from the symptom to its producing conditions and the state that emerged.
- **探索 mode** — trace backward from outputs (returns, side effects, messages sent) to their producing conditions.

Same technique, different anchor.

## Reconstruct the timeline

Cross-reference logs, system events, version control, and user observations into `timeline` rows (`at` / `event` / `ref`). Every row cites its source; conflicting rows both stay — a contradiction is evidence too.

## Hypothesis lifecycle (the discipline that matters)

For every hypothesis: state it → write `test` (what would confirm and what would refute it) → search → grade `status` (`已确证` / `已推翻` / `待验证`) → when the status leaves `待验证`, write the `resolution` (which evidence settled it). The final gate refuses a hypothesis that is not 待验证 without a `resolution`.

- **Never delete a hypothesis.** Wrong turns are part of the deliverable.
- **Refutation pass:** each time a hypothesis moves toward `已确证`, actively look for disconfirming evidence *first*; record the attempt in `resolution` even when it finds nothing.
- **Verify the user's premise:** if the evidence contradicts the user's description, say so explicitly — in the conversation and in the record.
- Newly discovered paths go to `backlog`; stay on the current thread.

Grading rule: `已确证` = directly observed with a citation (`path:line` / timestamp / commit); `已推断` = logically follows from 「已确证」 evidence **and the chain is shown**; `假设中` = plausible, unconfirmed, with a stated `test`. Grades are never inflated — the honest grade is the deliverable.

Present the current causal chain and hypothesis states; pause for the human before continuing.

## Next

Read fully and follow `./05-source-trace.md`.
