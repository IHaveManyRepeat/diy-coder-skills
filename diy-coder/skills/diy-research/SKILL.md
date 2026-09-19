---
name: diy-research
description: 'Conduct market, technical, and domain research with current web data and verified sources into one research.yaml. Use when the user says they need market research. Use when the user says they would like to do or produce a technical research report. Use when the user says wants to do domain research for a topic or industry.'
phase: 1-analysis
precededBy: []
followedBy: []
required: false
line: mainline
outputs: research.yaml
---

# diy-research — 联网调研三维度（market / technical / domain，YAML 单一源）

You are a research facilitator working with an expert partner: you bring research methodology and web search capability, the user brings domain knowledge and research direction. One research record = one dimension of one topic; several records may live in the same file. The output is **one YAML file** — never a markdown copy, never a duplicated document.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (topic, scope, claims, synthesis) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Target file: `{output_dir}/research.yaml`. Present → **Update** (append a new record; changing an existing record appends to `revisions`); absent → **Create**. Mint the record ID as the highest existing `RS-###` + 1; never renumber, never reuse.
3. Read budget: this file, plus exactly one file under `steps/` at a time — never batch-load the step files. `{output_dir}/research.yaml` is opened only to mint the next `RS-###` or to amend one record by its `id:` line; validation verdicts come from the engine's JSON receipt, not from re-reading rules. This schema defines no `detail` fields — nothing to skip.
4. Read `steps/01-scope.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload the four steps of a dimension; front-load — present a whole step's output in one message, no mid-step questions, no drip-feeding; halt at every `[C]` gate until the user answers; write each finding into the YAML as it is confirmed, never batch them to the end; write artifact prose in `document_output_language` while speaking `communication_language`.

1. `steps/01-scope.md` — topic, goals, scope, dimension confirmed; no research yet; create the draft record.
2. Route by `dimension` and read that dimension's four analysis steps in order:
   - market → `steps/market/02-customer-behavior.md` → `03-pain-points.md` → `04-decisions.md` → `05-competitive.md`
   - technical → `steps/technical/02-stack.md` → `03-integration.md` → `04-architecture.md` → `05-implementation.md`
   - domain → `steps/domain/02-industry.md` → `03-competitive-landscape.md` → `04-regulatory.md` → `05-trends.md`
3. `steps/06-synthesis.md` — synthesis, final gate, render, close.

Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved).

## Schema

`{output_dir}/research.yaml` — single source, collection form (top-level shape follows `bug-log.yaml`):

```yaml
project: {name, created, updated}
researches:
  - id: RS-001                  # RS-### — sequential, stable, never renumbered or reused
    dimension: market|technical|domain
    topic: <string>             # the user's own words
    goals: [<string>]           # research goals, captured in step 1
    scope: <string>             # scope and methodology
    date: YYYY-MM-DD
    status: draft|final         # final only after this record passes the final gate
    findings:                   # flat list; every claim carries its sources
      - {area: <dimension sub-area, e.g. customer-behavior/regulatory>, claim, sources: [{title, url, accessed}], confidence: high|medium|low}
    synthesis: {executive_summary, key_points: [<string>], open_questions: [<string>]}
distillate: {problem, target_users, value_props: [<string>], constraints: [<string>], open_questions: [<string>]}
                                # 交出面：跨全部 researches[] 记录的汇总裁面（字段级映射定义在 diy-prd 侧）；
                                # problem = 研究问题；value_props = 已验证的机会点；constraints = 证据支持的边界与限制
revisions: []                   # {date, change, reason} — appended when an existing record changes
```

## Rules

1. **Hard prerequisite.** Web search is required — if it is unavailable, abort and tell the user. Nothing is researched or written from training data alone, and the record is not created.
2. Write scope: `{output_dir}/research.yaml` only — records and their `revisions`. Never touch upstream artifacts (`prd.yaml`, `sprint.yaml`, `stories.yaml`) or source code; research informs them, it never edits them.
3. Citation discipline: every claim carries at least one source (`title` + http(s) `url` + `accessed` date) and a confidence level. Present conflicting sources rather than averaging them; a claim with no source is not a finding. Research gaps and limitations are recorded as `open_questions`, never smoothed over.
4. ID discipline: `RS-###` is assigned once, stable and never reused. A new topic or dimension appends a new record; amending an existing record appends `{date, change, reason}` to `revisions`.
5. Update safety: before rewriting an existing record wholesale, `cp {output_dir}/research.yaml {output_dir}/research.yaml.prev`; after drafting run `python "{project-root}/.claude/skills/diy-research/scripts/research.py" check --previous {output_dir}/research.yaml.prev --json` (exit 0 = no record lost); then delete the `.prev` file.
6. Final gate (mechanical): write `status: final` first — `final` is what the gate inspects, not a product of it — then run `python "{project-root}/.claude/skills/diy-research/scripts/research.py" check --final --json`, passing the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.
7. Rendering follows the silent-side-step line in Workflow — command only; no browser interaction point, no path report that blocks, no waiting.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
