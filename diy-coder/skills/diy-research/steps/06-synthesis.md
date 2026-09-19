# Step 6 — Synthesis（综合成文与定稿，共享收尾步）

Progress: `Scope → 02–05 (dimension) → [Synthesis]`

**Read (input):** the record in `{output_dir}/research.yaml` — its `topic` / `goals` / `scope` and all findings so far.
**Write (output):** the record's `synthesis` (`executive_summary` / `key_points` / `open_questions`) and `status: 已定稿`; the rendered view; the closing summary.

## Synthesize

Integrate the findings across the dimension's analysis steps — not a re-listing of them:

- What the evidence supports overall, and with what confidence.
- Where the sources converge and where they conflict.
- What the findings mean against the recorded `goals` (goal by goal) and which recommendation findings (`技术` / `领域` dimensions carry an `recommendations` area) survive scrutiny.

Run targeted follow-up searches when a cross-cutting claim needs them — e.g. `"{topic} significance importance"` for the framing, market-entry or risk-framework queries where the synthesis reaches beyond what steps 02–05 covered. New evidence still lands as a `findings[]` entry with its source; the synthesis cites findings, it never asserts unsourced facts.

## Write the synthesis

Fill the record's `synthesis` (all three keys are required for `--final`):

- `executive_summary` — 2–3 paragraphs: scope, the most critical findings, and the strategic implication. This is the artifact's overview; the source template's "Research Overview" placeholder role lives here.
- `key_points` — the 3–7 points a decision-maker must retain: goal achievement with its evidence, the top recommendations, and the material risks.
- `open_questions` — research gaps, limitations, and what further investigation would resolve. Source limitations and low-confidence areas belong here rather than being smoothed over; this is where draft-time `[假设]` markers must land before finalizing.

The three-dimension long-form document structure of the source skills (TOC, numbered chapters, appendices) is carried by the YAML record instead: every chapter's content is a finding with its `area` and sources, the executive summary is `synthesis.executive_summary`, and methodology/source documentation is the findings' `sources` plus the search trail you ran. Nothing is double-written into prose.

## Source documentation and QA

Before finalizing, audit the record as a reviewer would:

- Every finding has at least one source with `url` + `accessed`, and its `confidence` matches the evidence (multiple authoritative sources → `高`; single or partial → `中`; uncertain or dated → `低`).
- Critical claims each carry two independent sources; disagreements are visible, not averaged away.
- Market-size / version / regulatory claims carry their date, and stale data is labelled.

## Final gate

1. Write `status: 已定稿` on the record first — `已定稿` is what the gate inspects, not a product of it.
2. Run `python "{project-root}/.claude/skills/diy-research/scripts/research.py" check --final --json` with the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run. The JSON receipt (counts included) is the close-out evidence.
3. Render via diy-viewer — the silent side-step command from SKILL.md (append `--instance <name>` when one was resolved); no browser interaction point, no path-waiting.
4. Close with the record's `topic`, `status`, and the counts from the receipt (researches / findings / sources / open_questions), and name what the research can feed next (`diy-product-brief`, `diy-prfaq`, `diy-prd`).

## Next

This is the last step file — the run ends here once the final gate exits 0. To research another dimension of the same topic, append a new record (`RS-###`) starting again from `steps/01-scope.md`; to amend this record, append `{date, change, reason}` to `revisions` and keep its ID.
