# Step 2 — Artifacts（工件分析：读结构化产物，引用不复制）

Progress: `Target → [Artifacts] → Code Survey → Compose → Finish`

**Read (input):** the receipt blocks `acs` / `tcs` / `decisions` / `prior` / `git`.
**Write (output):** `ac_refs` / `tc_refs` / `design_ref` / `decisions` / `prior_story` in the record.

## The transformation (read this before the blocks)

The source workflow loads the planning markdown (epics / PRD / architecture / UX) and copies the story-relevant context into the story file — a second-hand copy that drifts the moment the upstream changes. diy does not copy: the upstreams are structured single sources, so the pack **references** them by ID and proves the story knows its obligations.

Your job is not to restate an acceptance criterion. It is to make four things explicit: which ACs this story must satisfy, which tests verify them, which decisions constrain it, and what the previous story learned.

Never paste an AC's `given/when/then` into the record, never restate a decision's text, never quote a story narrative. `AC-3.1` inside `ac_refs` **is** the acceptance criterion — diy-dev reads it in `stories.yaml`.

## AC refs

The story's ACs, ids only, all of them (the receipt's `acs` block is exactly that list). When an AC carries a `design_ref`, the record's `design_ref` names the page serving this story's primary surface — the most-bound page when several ACs bind different ones. The full binding set stays on the ACs in `stories.yaml`; do not duplicate it here.

## TC refs

`tc_refs` = the receipt's `tcs` ids: every case whose `ac` belongs to this story. `status: 待办` is normal before diy-dev runs — it is not a problem to report. An empty `tcs` **is**: no test verifies this story's ACs, so the sprint TDD gate will block the task. Record it as an open question and route the human to diy-test-design.

## Decisions

`decisions` = the applicable `D-x` from the receipt — applicability is the decision's `affects` intersecting the FR/NFR ids the story's ACs `refs` (both visible in the receipt). Not every decision belongs here; an unrelated one is noise the dev agent reads anyway. A decision still `status: 待定` is not ratified: it goes to `risks` (step 4), never into the guardrails as if it were settled.

## Prior story

The receipt's `prior.ref` is the highest story number below the target. Its `carryover` lines are distilled from that story's sprint task — `note`, `evidence` (red/green records), `loop` (rounds, outcome), `blocked_reason`. Each line names its source field, e.g. `sprint S-2 note: 既有实现复用 src/app.py`, so the dev agent can go read the evidence instead of trusting a summary. Nothing worth carrying → omit `prior_story`; never write an empty shell.

## Git intelligence

`git.commits` (last 5: subject + files) is pattern evidence, not narrative: which files recent work touched, which conventions were used, what a change like this normally drags along (tests, fixtures, docs). Fold what matters into `risks` / `verify` in step 4. Never paste commit messages into the record, and never treat a commit message as a requirement.

## Next

Read fully and follow `./03-code-survey.md`.
