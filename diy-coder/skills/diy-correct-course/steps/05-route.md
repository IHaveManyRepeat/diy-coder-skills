# Step 5 — Finalize and Route（批准与交接）

Progress: `Initialize → Analysis → Edits → Proposal → [Route] → Finish`

**Read (input):** the presented draft record; the human's verdict.
**Write (output):** `status` (已批准 on a yes), `scope`, `handoff` in the record.

## Take the explicit approval (source step-5)

Ask the source's question: **Do you approve this change proposal for implementation? (yes / no / revise)**

- **yes** → set `status: 已批准` and continue to the routing below.
- **no / revise** → gather what needs adjusting. Changes to the edit set return to `./03-edits.md`; changes to the impact set, path, or structure are handled before that. A revised record appends `{date, change, reason}` to `revisions` — never rewrite the old reasoning out of the record.
- **no approval, no revision** (the human drops the change) → set `status: 已驳回`, keep the record for the audit trail, close without a handoff routing.

Approval is a hard prerequisite for routing in this step: an unapproved proposal is never handed off — the source's rule, enforced by the final gate's status check.

## Classify scope (source step-5 / §5)

Settle `scope` from the impact set actually recorded (step 1's value was provisional):

- **`轻微`** — the change is implementable by one owning skill directly, no replanning.
- **`中等`** — the backlog must be reworked (stories added/removed/resequenced; sprint gates recomputed).
- **`重大`** — the plan itself is invalidated; the planning layer must replan before implementation resumes.

## Set the handoff (source step-5; diy 侧角色 → 技能映射)

`handoff.route` names the diy skill that executes; `handoff.note` names what it inherits and the success criterion in one line. The route must sit in the scope's allow-list (the final gate enforces the pairing):

| Scope | Allowed routes | The route's job |
| --- | --- | --- |
| `轻微` | `diy-dev` / `diy-quick-dev` / `diy-prd` / `diy-architecture` / `diy-epics-stories` / `diy-openapi` / `diy-design` / `diy-create-story` / `diy-test-design` / `diy-e2e-tests` / `diy-review` | apply the named edits directly, then re-run its own gate |
| `中等` | `diy-sprint` / `diy-epics-stories` / `diy-prd` | reshape the backlog (`reconcile` recomputes gates), re-derive coverage |
| `重大` | `diy-prd` / `diy-architecture` / `diy-epics-stories` | replan: revise requirements / decisions / breakdown first |

This skill executes nothing itself: the rewrite of the source artifacts happens in the named skill's update mode, under its own gate. Confirm with the human which skill takes it when two are plausible, and record the exchange in `note`.

## Close the routing message

One message: scope, route, what the route inherits (the edits, in the record), and the success criterion (source: "confirm handoff completion and next steps"). Then move to the final gate.

## Next

Read fully and follow `./06-finish.md`.
