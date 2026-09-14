# Step 1 — Clarify & Route（澄清与路由）

Progress: `[Clarify & Route] → Plan → Implement → Review → Present` (one-shot: `[Clarify & Route] → One-Shot`)

**Read (input):** the conversation that triggered this run; `{output_dir}/spec.yaml` when it exists; the artifact listing.
**Write (output):** the draft record in `{output_dir}/spec.yaml` (`id` / `date` / `title` / `type` / `route` / `status: draft` / `intent` / `boundaries`).

## Intent check (do this first)

The prompt that triggered this run IS the intent — not a hint. Check in this order and stop at the first clear answer:

1. **Explicit pointer** — a spec file or an `SP-xxx` this message names. Read its record and route by `status`: `draft` → `./02-plan.md`; `ready` / `in-progress` → `./03-implement.md`; `in-review` → `./04-review.md`; `done` → read-only: summarize it and stop, do not resume; `blocked` → name the blocker and stop (unblock is a human call). Anything else (an intent file, an external doc, a plan, a description) → ingest as starting intent and continue below; never infer a workflow state from it.
2. **Recent conversation** — the last few messages clearly show the work. Same routing.
3. **Scan and ask** — list the active records (`draft` / `ready` / `in-progress` / `in-review`) from `{output_dir}/spec.yaml` and HALT: resume one, or `[N]` for new work.

Never ask extra questions once the intent is clear.

## Load context (reference, never copy)

- Read the structured artifacts the intent needs — `stories.yaml` / `architecture.yaml` / `epics.yaml` / `design.yaml` when present — and cite them by ID (`S-x`, `D-x`, `AC-x.y`). Do not paste document bodies into the record: the diy single source is the artifact, the record carries references.
- When the intent is a story inside an epic and a fuller implementation context is wanted, the diy context pack is diy-create-story's `story-context.yaml` — suggest it, never inline its content here. (The source cached this as a per-epic markdown file; diy reads structured artifacts, so no cache is compiled.)
- Change the state of nothing: this skill never writes `sprint.yaml`. When the change touches a story that is already in the loop, cross-document truth is diyc's (`diyc.py check --type sprint --json`) and sprint state stays diyc-owned. (The source synced a `sprint-status.yaml`; diy has no such file.)

## Clarify

Do not fantasize and do not leave open questions. Ask as a numbered list; when the human replies, verify **every** numbered question was answered — if any were ignored, HALT and re-ask only the missing ones before proceeding. Keep looping until the intent is implementable.

## Version control sanity check

Read-only: is the working tree clean, and does the current branch make sense for this intent? A dirty tree or an obviously mismatched branch → surface it and ask before proceeding. Version control unavailable → skip.

## Multi-goal check (SCOPE STANDARD)

The spec targets **one user-facing goal** within **900–1600 tokens**. Multi-goal means ≥2 top-level independent shippable deliverables — each could be reviewed, tested and shipped separately without breaking the others. Never count surface verbs, "and" conjunctions, or noun phrases; never split cross-layer details inside one goal.

- Split: "add a dark-mode toggle AND refactor auth to JWT AND build an admin dashboard".
- Don't split: "add validation and display errors" / "support drag-and-drop AND paste AND retry".

The token range is **a proposal, not a gate** — the human overrides it. When the intent fails the single-goal test, present the distinct goals as a bullet list, explain in 2–4 sentences why each is independently shippable, name any coupling risk, recommend which to take first, then HALT: `[S] Split — take the first goal, defer the rest` | `[K] Keep all — accept the risks`. On **S**: append the deferred goals to the record's `deferred` (finding / why / date) and narrow scope to the first goal. On **K**: continue as-is.

## Route (exactly one)

Create the record first: append to `{output_dir}/spec.yaml` (create the file when absent: `project: {name, status: draft, created, updated}` — `name` from `diy-coder.yaml` `project.name` — plus an empty `specs` list and `revisions: []`).

```yaml
  - id: SP-001                  # next = highest existing + 1, 3 digits; never renumber, never reuse
    title: <one line, from the clarified intent>
    type: feature|bugfix|refactor|chore
    route: <decided below>
    status: draft
    date: YYYY-MM-DD            # today
    intent: {problem: <what is broken or missing and why it matters>, approach: <the what, not the how>}
    boundaries: {always: [<invariant rules>], ask_first: [<human-gated decisions>], never: [<non-goals and forbidden approaches>]}
```

- **one-shot** — zero blast radius: no plausible path by which this change causes unintended consequences elsewhere, clear intent, no architectural decisions. → **EARLY EXIT**: read fully and follow `./06-oneshot.md`.
- **plan-code-review** — everything else. When unsure whether the blast radius is truly zero, choose this.

## Next

Read fully and follow `./02-plan.md`. (On the one-shot route that file is never read — the early exit above replaces it.)
