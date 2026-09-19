# Step 5 — Epic Quality Review（史诗质量评审）

Progress: `Document Discovery → Requirement Inventory → Coverage Validation → UX Alignment → [Epic Quality Review] → Final Assessment`

**Read (input):** the receipt (`diyc.check.violations` for `epics` / `stories`, `counts`); `epics.yaml` and `stories.yaml` — every epic and story; `architecture.yaml` for the starter-template check.
**Write (output):** quality findings (`area: epics` / `area: stories`) with severities.

This review runs autonomously — challenge everything, compromise on nothing (source step-5 §8). Mechanical shape checks (IDs, enums, AC references resolving) already arrived in `diyc.check.violations`; what follows is the judgment layer diyc cannot do.

## A. Epic user value

Per epic: is the title what a user can do (not a system component)? Does the goal describe a user outcome? Can anyone benefit from this epic alone?

Red flags → findings (source step-5 §2.A):

- "Setup Database" / "Create Models" — no user value;
- "API Development" / "Infrastructure Setup" — a technical milestone;
- "Authentication System" — borderline: judge whether it delivers user-visible value (login / logout / account) or only plumbing.

A technical epic is an **error**, not a style note: `severity: 严重`. The source rule is literal — find them.

## B. Epic independence

- Epic 1 stands alone; Epic 2 may use only Epic 1's output; Epic N never requires Epic N+1.
- Catch: "Epic 2 requires Epic 3 features", stories in one epic referencing components of a later epic, circular dependencies between epics.
- Forward dependencies that break independence → `严重`.

## C. Story quality

**Sizing.** Clear user value; completable without a future story. "Setup all models" is not a user story; "Create login UI (depends on Story 1.3)" is a forward dependency — `严重` when it breaks independence, `高` when it is sizing.

**Acceptance criteria.** Given/When/Then structure; each AC independently testable; error conditions covered; outcomes specific. Vague criteria ("user can login"), missing error paths, an incomplete happy path, non-measurable outcomes → `高` (source "major"); pure formatting noise → `中` / `低`.

## D. Dependencies

- Within an epic: Story 1.1 completable alone; 1.2 may use 1.1's output; nothing waits on a later story.
- Database/entity timing: each story creates what it needs; "create all tables in Story 1.1" → `高`.
- Cross-epic: a story depending on another epic's unimplemented feature → `高`, or `严重` when it inverts the epic order.

## E. Special implementation checks

- **Starter template** (source step-5 §5.A): when `architecture.yaml` specifies a starter template, Epic 1 Story 1 must be the initial project setup from it (clone, dependencies, initial configuration). Missing → `高`.
- **Greenfield vs brownfield** (source step-5 §5.B): greenfield expects an initial setup story, development-environment configuration and CI/CD early; brownfield expects integration points with existing systems and migration/compatibility stories. Missing where implied → `中`, naming what is missing.

## F. Compliance checklist (per epic)

- [ ] delivers user value
- [ ] functions independently
- [ ] stories appropriately sized
- [ ] no forward dependencies
- [ ] database tables created when needed
- [ ] clear acceptance criteria
- [ ] traceability to FRs maintained (diyc's AC `refs`)

Every unchecked box becomes a finding with a specific example and one remediation line — never a general complaint.

## Severity map (source step-5 §7)

| Source | diy `severity` |
| --- | --- |
| critical violations — technical epics, forward dependencies, epic-sized stories | `严重` |
| major issues — vague acceptance criteria, future-story dependencies, database timing | `高` |
| minor concerns — formatting, structure deviations, documentation gaps | `中` / `低` |

## Next

Read fully and follow `./06-final-assessment.md`.
