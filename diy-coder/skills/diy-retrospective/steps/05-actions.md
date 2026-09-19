# Step 5 — Actions（行动项与重大变更检测）

Progress: `Epic Discovery → Deep Analysis → Continuity → Review → [Actions] → Readiness → Finish`

**Read (input):** `challenges` / `insights` from step 4; `next_epic.dependencies` and the preparation material from step 3; the receipt's `bugs` and `coverage`.
**Write (output):** `action_items` / `prep_items` / `critical_path` / `significant_changes` in the record.

## Action items — SMART, owned, no time estimates (source step-8)

Every action item closes one gap the retro surfaced (a challenge, a missed commitment from step 3, a defect class, an uncovered AC):

```yaml
    action_items:
      - {id: AI-001, action: <one line, imperative>, owner: <who>, done_when: <observable completion>, category: 流程|技术|文档|团队}
```

- **`id`** — `AI-###`, sequential within the record, never reused.
- **`action`** — specific and achievable; "improve testing" is not an action, "add a case for every must-FR AC before the next sprint starts" is.
- **`owner`** — a named owner (a person or an explicit role). An action without an owner is a wish; the gate rejects the record.
- **`done_when`** — the observable completion test, **not a date and not an estimate**: "AC-4.2 has a case with a kill_target", "the blocked_reason template is in diy-sprint". The source skill forbids all time predictions — this is where that rule bites.
- **`category`** — `流程` / `技术` / `文档` / `团队`.

Zero action items on a finalised retro is a gate failure — the retro's whole point is the commitments.

## Preparation items (source step-7, next-epic preparation)

For each preparation need: an owner, a criticality class, and a realistic effort word (never hours/days):

```yaml
    prep_items:
      - {item: <what must exist before the next epic>, class: 关键|可并行|锦上添花, owner: <who>, effort: <small|medium|large>}
```

- `关键` — must complete before the next epic starts; `可并行` — can run during its early stories; `锦上添花` — helps, does not block.
- The source's compromise is preserved: a `关键` item that early stories do not depend on may move to `可并行` — but only after checking the next epic's stories really do not depend on it.

## Critical path (blockers before the next epic)

The subset of preparation that would cause rework if skipped — each with its *why*:

```yaml
    critical_path:
      - {item: <item>, why: <what breaks if skipped>, owner: <who>}
```

Readiness items from step 6 that turn out to be blocking land here, not only in `readiness`.

## Significant change detection (source step-8 CRITICAL ANALYSIS)

Walk this list against the epic's evidence. Any hit means the plan for the next epic is built on an assumption this epic disproved:

1. architecture assumptions from planning proven wrong; 2. major scope change or descoping; 3. technical approach needs fundamental change; 4. dependencies the next epic does not account for; 5. user needs materially different from the original understanding; 6. performance / scalability findings that change the design; 7. security or compliance findings that change the approach; 8. integration assumptions proven incorrect; 9. team capacity or skill gaps more severe than planned; 10. technical debt at an unsustainable level without intervention.

```yaml
    significant_changes:
      - {change: <what changed>, impact: <on which plan>, recommended_action: <one line>}
```

- **A hit is a proposal, not an edit.** This skill never patches `epics.yaml` / `stories.yaml` / `prd.yaml` / `architecture.yaml`; the change is routed in step 7 to diy-correct-course.
- **No hits** → omit the key (or write `[]`) and say in the closing summary that the next epic's plan still stands; the source states this explicitly and so do we.
- A speculative worry is not a significant change — it needs evidence, like everything else here.

## Next

Read fully and follow `./06-readiness.md`.
