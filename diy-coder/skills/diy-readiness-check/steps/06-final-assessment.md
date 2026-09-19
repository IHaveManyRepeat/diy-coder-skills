# Step 6 — Final Assessment（总评与定稿）

Progress: `Document Discovery → Requirement Inventory → Coverage Validation → UX Alignment → Epic Quality Review → [Final Assessment]`

**Read (input):** this run's record as filled by steps 1–5; the `collect` receipt counts.
**Write (output):** the settled record (`verdict` / `counts` / `status: 已定稿`) in `{output_dir}/readiness.yaml`; the rendered view; the closing summary.

## Settle the verdict

Three states, decided from the findings just recorded:

- **`就绪`** — nothing blocking and nothing worth a route: the build can start.
- **`有风险就绪`** — non-blocking findings worth recording (`中` / `低`): start, eyes open.
- **`未就绪`** — at least one `严重` or `高` finding: an upstream document must change first.

The final gate enforces the two hard implications: `就绪` carries no 严重/高 finding; `未就绪` carries at least one. Never soften a 严重 finding into 中 to reach `就绪` — "don't soften the message" is why this skill exists.

## Compile (source step-6 §2/§3)

- Every finding kept carries `message` (why it matters) plus `evidence` (the anchor that shows it — file, ID, quoted sentence) and, when it belongs to another skill, `route`.
- `counts.findings_by_severity` must equal the findings actually recorded, zero keys omitted (the final gate recomputes the tally); `coverage` stays exactly as the receipt gave it.
- Close the message with what the source report carried: the verdict, the critical issues requiring action, recommended next steps (1–3 concrete items), and "N findings across M areas" — in `document_output_language`. No markdown report is written: the record is the report.

## Final gate (mechanical)

1. Write `status: 已定稿` first — `已定稿` is what the gate inspects, not a product of it.
2. Run `python "{project-root}/.claude/skills/diy-readiness-check/scripts/readiness.py" check --final --json` with the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run. The JSON receipt (counts included) is the close-out evidence.
3. Render via diy-viewer — the silent side-step command from SKILL.md — only after exit 0; no browser interaction point, no path report that blocks.

## Hand off

- `就绪` / `有风险就绪` → diy-test-design (test-plan.yaml), then diy-sprint; name the route in one line.
- `未就绪` → the owning skill in each 严重/高 finding's `route` (diy-prd / diy-architecture / diy-epics-stories / diy-design); re-run this skill once they land.

## Exit

This is the last step file — the run ends here once the final gate exits 0. `verdict` and `findings[].route` carry the outcome; no further `steps/` file is read.
