# Step 3 — Continuity（承诺跟踪与下一 epic 预览）

Progress: `Epic Discovery → Deep Analysis → [Continuity] → Review → Actions → Readiness → Finish`

**Read (input):** the receipt's `prev_actions` / `first_retro` / `next_epic`; the current epic's `sprint.yaml` task evidence (the proof of follow-through).
**Write (output):** `prev_followup` and `next_epic` in the record.

## Part 1 — Previous retro's commitments (source step-3)

`prev_actions` carries the action items of the retro written for the previous epic (`first_retro: true` means there is none — say "first retro, nothing to follow" and continue with `prev_followup` omitted).

For each carried action, judge the actual follow-through **from this epic's evidence, not from memory**:

- `已完成` — an artifact shows it happened (cite it: an `AC-x.y` now covered, a `BUG-0xx` with the prevention in place, a `blocked_reason` that no longer recurs).
- `部分完成` — visible progress, visible gap; say which part is missing.
- `未完成` — no trace in this epic's evidence; state the consequence without blame (source facilitation rule: systems, not people).

```yaml
    prev_followup:
      - {retro: RT-yy, action: <the commitment, one line>, status: 已完成|部分完成|未完成, evidence: <anchor>}
```

An action the evidence cannot decide is `未完成` with the missing evidence named — never upgraded on optimism. Omit `prev_followup` entirely on a first retro.

## Part 2 — Next epic preview (source step-4)

`next_epic` from the receipt carries `{id, exists, title, stories, shared_frs}`; `shared_frs` is the mechanical coupling — requirements this epic and the next one both cite. The session's job is the reading, not the lookup:

- **Dependencies on this epic's work.** Name them from `shared_frs` plus the analysis readings (e.g. "E-4 reuses the validation path built in S-7"). Every dependency names what must be *stable*, not merely present.
- **Preparation needed** — the raw material for `prep_items` in step 5: technical setup, knowledge gaps, refactoring, docs, testing infrastructure, external dependencies. Do not enumerate here; step 5 owns the list.
- **Risk of NOT preparing** — the source's pivotal question. Carry one sentence per risk into step 5's critical-path reasoning.

```yaml
    next_epic: {id: E-y, exists: true, dependencies: [<the couplings named above>]}
```

- **No next epic** (`exists: false`) → `next_epic: {id: null, exists: false, dependencies: []}`, skip the preview discussion, and say plainly that the lessons stand on their own whenever the next epic is planned. Do not skip the retro.

## Part 3 — Change detection input

Note (do not yet decide) any evidence that the *plan* is now wrong: architecture assumptions disproved, scope that moved, dependencies nobody planned for, performance or security findings that change the approach. Step 5 runs the full detection list against these notes — this step only makes sure the raw material is in hand.

## Next

Read fully and follow `./04-review.md`.
