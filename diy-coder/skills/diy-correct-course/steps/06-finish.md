# Step 6 — Close Out（定稿门与收尾）

Progress: `Initialize → Analysis → Edits → Proposal → Route → [Finish]`

**Read (input):** this run's record as filled by steps 1–5.
**Write (output):** the settled record (`status` / `handoff` final) in `{output_dir}/change-proposal.yaml`; the rendered view; the closing summary.

## Final gate (mechanical)

1. Write the terminal status first — `final` (analysis settled, not yet approved) or `approved` (the human said yes) — `final` / `approved` is what the gate inspects, not a product of it.
2. Run `python "{project-root}/.claude/skills/diy-correct-course/scripts/change_proposal.py" check --final --json` with the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run. The JSON receipt (counts included) is the close-out evidence.
3. The gate enforces what routing requires: `handoff.route` present and inside its scope's allow-list, `impacts` non-empty, the path settled (`approach`), zero `[ASSUMPTION]` — an unconfirmed inference is resolved with the human or lands as an explicit `open_questions` entry before the gate.
4. Render via diy-viewer — the silent side-step command from SKILL.md — only after exit 0; no browser interaction point, no path report that blocks.

## Summarize (source step-6)

One closing message carrying the source's four facts plus the next step:

- **Issue addressed** — the `trigger` in one line;
- **Change scope** — `scope` and why it landed there;
- **Artifacts affected** — the distinct `artifact` values across `impacts` (and the edit count);
- **Routed to** — `handoff.route` and what it inherits;
- **Next** — the route runs its own gate; this record changes nothing until then. If the change is later implemented and new evidence arrives, a fresh `CP-###` is opened — this record is never rewritten.

## Exit

This is the last step file — the run ends here once the final gate exits 0. The record's `handoff.route` carries the outcome; no further `steps/` file is read.
