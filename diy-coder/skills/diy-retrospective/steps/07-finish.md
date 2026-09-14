# Step 7 — Finish（定稿门与路由）

Progress: `Epic Discovery → Deep Analysis → Continuity → Review → Actions → Readiness → [Finish]`

**Read (input):** the complete record; the engine's `check` receipt.
**Write (output):** `status: final` on the record; the closing summary.

## Final gate (mechanical)

Write `status: final` first — `final` is what the gate inspects, not a product of it — then run:

```
python "{project-root}/.claude/skills/diy-retrospective/scripts/retrospective.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

Exit 0 is the only pass. Fix every reported violation and re-run. In plain terms the bar is: zero `[ASSUMPTION]`; `metrics` equal to what the artifacts actually say (`SET_MISMATCH` means the numbers were edited by hand or the artifacts moved on — recompute from a fresh `collect`); `readiness` five keys non-empty; at least one action item with an owner; every `epic` / `evidence` / `next_epic.id` reference resolving. The JSON receipt (counts included) is the close-out evidence.

Rendering and close-out wait for exit 0. Render via diy-viewer (silent side step — command only, no browser interaction point, no path-waiting, no blocking):

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

append `--instance <name>` when one was resolved.

## Save and mark the epic reviewed (source step-11)

There is no `sprint-status.yaml` in diy and no retro key to flip: this record **is** the completion mark. `status: final` on the `retros` entry — plus the journey it now records — is what tells the next session the epic was reviewed. Never write a state anywhere else (`sprint.yaml` gets zero writes from this skill).

## Close-out summary

State, in the user's language and reading from the receipt:

- the epic and its completion (`stories_done / stories_total`, `partial` when set) — never a hand count;
- the metrics that matter: rounds total, blocked, augment failures, defects by class;
- patterns found (with their counts) and the wins worth repeating;
- commitments: action items by category, prep items by class, critical-path item count;
- the readiness verdict in one line, and any unresolved blocker;
- where the record lives.

Open with what the epic delivered — the source closes with acknowledgment before commitments, and so does this step: `wins` gets one sentence of recognition before the action list. Celebration is not decoration; it is what makes the challenges in the same record believable.

## Routing (source step-8/step-10/step-12 handoff)

- **`significant_changes` non-empty** → the next epic's plan is suspect: route to **diy-correct-course** with the change entries as the trigger. Do not start the next epic's work before that proposal is settled.
- **`critical_path` non-empty** → those items first; they are the precondition for the next epic's first story.
- **Blockers naming a missing case or a broken ledger** → back to diy-test-design / diy-augment, whichever owns the gap.
- **Otherwise** → the epic loop continues: the next epic's stories go through diy-create-story → diy-dev, or diy-sprint when the queue needs refreshing.
- **Never** edit the artifacts this retro analyses — a conclusion that requires changing them is a `significant_changes` entry, and its fix belongs to the owning skill.

If `paths.experience_repo` is configured and present, one line reminding the user that `bug-log.yaml` feeds the cross-project experience repo (push on their call) is enough — this skill does not sync anything.
