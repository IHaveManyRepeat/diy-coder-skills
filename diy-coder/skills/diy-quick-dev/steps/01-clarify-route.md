# Step 1 — Clarify & Route（澄清与路由）

Progress: `[Clarify & Route] → Plan → Implement → Review → Present` (一次成型: `[Clarify & Route] → One-Shot`)

**Read (input):** the conversation that triggered this run; `{output_dir}/spec.yaml` when it exists; the artifact listing.
**Write (output):** the draft record in `{output_dir}/spec.yaml` (`id` / `date` / `title` / `type` / `route` / `status: 草稿` / `intent` / `boundaries`).

## Intent check (do this first)

The prompt that triggered this run IS the intent — not a hint. Check in this order and stop at the first clear answer:

1. **Explicit pointer** — a spec file or an `SP-xxx` this message names. Read its record and route by `status`: `草稿` → `./02-plan.md`; `就绪` / `进行中` → `./03-implement.md`; `审查中` → `./04-review.md`; `已完成` → read-only: summarize it and stop, do not resume; `已阻塞` → name the blocker and stop (unblock is a human call). Anything else (an intent file, an external doc, a plan, a description) → ingest as starting intent and continue below; never infer a workflow state from it.
2. **Recent conversation** — the last few messages clearly show the work. Same routing.
3. **Scan and ask** — list the active records (`草稿` / `就绪` / `进行中` / `审查中`) from `{output_dir}/spec.yaml` and HALT: resume one, or `[N]` for new work.

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

Create the record first: append to `{output_dir}/spec.yaml` (create the file when absent: `project: {name, status: 草稿, created, updated}` — `name` from `diy-coder.yaml` `project.name` — plus an empty `specs` list and `revisions: []`).

```yaml
  - id: SP-001                  # next = highest existing + 1, 3 digits; never renumber, never reuse
    title: <one line, from the clarified intent>
    type: 新功能|缺陷修复|重构|杂务
    route: <decided below>
    status: 草稿
    date: YYYY-MM-DD            # today
    intent: {problem: <what is broken or missing and why it matters>, approach: <the what, not the how>}
    boundaries: {总是: [<invariant rules>], 先问: [<human-gated decisions>], 从不: [<non-goals and forbidden approaches>]}
```

- **一次成型** — zero blast radius: no plausible path by which this change causes unintended consequences elsewhere, clear intent, no architectural decisions. → **EARLY EXIT**: read fully and follow `./06-oneshot.md`.
- **计划-编码-审查** — everything else. When unsure whether the blast radius is truly zero, choose this.

## Next

Read fully and follow `./02-plan.md`. (On the 一次成型 route that file is never read — the early exit above replaces it.)
