# Step 5 — The Verdict（判定与交付）

Progress: `Ignition → Press Release → Customer FAQ → Internal FAQ → [Verdict]`

**Read (input):** all three prior sections in `{output_dir}/prfaq.yaml`; the accumulating `distillate`; what remains in session memory.
**Write (output):** the verdict message; `prfaq.verdict`, `prfaq.stage: 5`, `project.status: 已定稿` and `updated` in one write; the finished `distillate`; the rendered view; the closing summary.

## The assessment

Review the entire PRFAQ — press release, customer FAQ, internal FAQ — and deliver a candid verdict.

**Concept strength** is a narrative assessment, not a score: where is the thinking sharp and where is it still soft? What survived the gauntlet and what barely held together?

**Three categories of findings** — one of them becomes `prfaq.verdict.strength`:

- **`已锤炼`（forged in steel）** — aspects that are clear, compelling and defensible: the press release sections that would actually make a customer stop, the FAQ answers that are honest and convincing.
- **`欠火候`（needs more heat）** — promising but underdeveloped: a direction without enough depth yet; these need work before they are ready for a PRD.
- **`地基裂缝`（foundation-cracks）** — genuine risks, unresolved contradictions or gaps that could undermine the whole concept; not necessarily deal-breakers, but they must be addressed deliberately.

**Present the verdict directly.** Don't soften it — the whole point of this process is to surface truth before committing resources. But frame every finding constructively: for every crack, say what it would take to address it.

## Finalize the document

1. **Polish** — the press release reads as a cohesive narrative, the FAQs flow logically, formatting is consistent.
2. **Write the verdict** — `prfaq.verdict: {strength: <one of the three>, narrative: <the assessment>}`, `prfaq.stage: 5`, and `project.status: 已定稿`, all in the same write.
3. **Complete the distillate** — always, in the same file. The four earlier stages already landed their downstream-relevant items; sweep session memory for anything still missing — requirements signals, technical constraints and platform preferences, scope signals, resource and timeline estimates, open questions. Dense bullets, each standing alone with enough context for a downstream LLM; keep the five buckets from Step 1 (`problem`, `target_users`, `value_props`, `constraints`, `open_questions`), with the verdict's `欠火候` and `地基裂缝` findings as actionable `open_questions` entries.
4. **Close the notes** — anything left that is process narrative rather than a downstream fact (why the verdict landed where it did, how the gauntlet went) becomes the stage-5 entry in `notes`: `{stage: 5, content}`. Sweep once more for downstream leftovers before closing: alternative positioning and rejected framings go to `distillate.constraints` as `Not <X>: because <Y>`, and competitive intelligence that affects adoption goes to `distillate.constraints` (settled) or `distillate.open_questions` (still open). `distillate` stays the clean machine contract; `notes` carries the story.

## Final gate (mechanical)

Run `python "{project-root}/.claude/skills/diy-prfaq/scripts/prfaq.py" check --final --json` with the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation — `--output-dir` is mandatory and never defaulted. `已定稿` and `stage: 5` are written before the gate runs: they are what it inspects, not products of it. Exit 0 is the only pass; fix every reported violation and re-run. The JSON receipt (counts included) is the close-out evidence; rendering and close-out wait for exit 0.

## Present completion

"Your PRFAQ for {project_name} has survived the gauntlet." Then name the two things it produced: the single source `{output_dir}/prfaq.yaml` (with the distillate section) and the rendered view.

**Recommended next step:** carry the PRFAQ and its distillate into PRD creation — run `diy-prd` and point it at `{output_dir}/prfaq.yaml`. The PRFAQ replaces the product brief in the planning pipeline.

## Headless mode output

Emit this JSON as the run's close-out (the source emitted a separate detail-pack path; diy is a single source, so the distillate lives inside the document):

```json
{"status": "complete",
 "prfaq": "{output_dir}/prfaq.yaml",
 "verdict": "已锤炼|欠火候|地基裂缝",
 "key_risks": ["top unresolved items"],
 "open_questions": ["unresolved items from the FAQs"]}
```

## Exit

This is the terminal stage. If the user wants to revise, loop back to the relevant stage (`prfaq.stage` moves back with it) — otherwise the workflow is done. This is the last step file; the record's `distillate` and the rendered view carry the outcome, and no further `steps/` file is read.
