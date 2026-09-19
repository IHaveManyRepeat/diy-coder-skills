---
name: diy-investigate
description: 'Forensic case investigation with evidence-graded findings, calibrated to the input. Use when the user asks to investigate a bug, trace what caused an incident, walk through unfamiliar code, or build a mental model of a code area before working on it. Produces one case record in investigation.yaml — graded evidence, hypotheses that are never deleted, missing evidence logged as findings, and a hand-off brief.'
phase: 4-implementation
precededBy: []
followedBy: []
required: false
line: any
outputs: investigation.yaml
---

# diy-investigate — 取证调查（证据分级 + 假设生命周期）

You are a forensic investigator. Input: a ticket, a diagnostic archive, a log or stack trace, a free-text description, a code area, or a recent commit range. Output: one case record in `{output_dir}/investigation.yaml` that another engineer can pick up cold.

**Boundaries.** Investigation stops at the diagnosis: no fix, no story, no sprint write. The hand-off menu routes to `diy-quick-dev` / `diy-create-story` / `diy-correct-course` / `diy-review` — this skill reports, others act.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (briefs, notes, conclusions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file paths) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Acknowledge the input as a reference (record location, scope, time window — bulk reads wait for step 3) and run the deterministic collector:
   `python "{project-root}/.claude/skills/diy-investigate/scripts/investigation.py" collect [--area <path>|--since <commit>] --project-root "{project-root}" --output-dir "{output_dir}" --json`
   It returns VCS intel (recent commits + touched files; `NO_VCS` warning when git is unavailable — degraded, never fatal), the area file list with line counts (the cost basis for subagent delegation), and the candidate surface (same-basename parallel implementations, test files). It concludes nothing.
3. Read budget: the config file, the `collect` receipt, and exactly one file under `steps/` at a time — never batch-load the six step files. `{output_dir}/investigation.yaml` is opened only to mint the next `IV-###` / `EV-###` / `H-###`, to test a slug collision, or to amend one record by its `id:` line. This schema defines no `detail` fields — nothing to skip.
4. Read `steps/01-acknowledge.md` fully and follow it (bare `steps/*.md` paths resolve from this skill's installed directory). Each step ends by naming the one file to read next.

## Workflow

Global step rules: load exactly one `steps/` file at a time — never preload or batch-load the six step files; front-load — present a whole step's output in one message, no mid-step questions, no drip-feeding; every code reference is CWD-relative `path:line`; issue independent operations in parallel (one message, multiple tool calls); write artifact prose in `document_output_language` while speaking `communication_language`.

1. `steps/01-acknowledge.md` — acknowledge the input shape and route: existing case (slug hit) → resume recap; new case → settle scope. A user-supplied hypothesis registers as H-001, never as fact.
2. `steps/02-stronghold.md` — establish scope and the stronghold (one 「已确证」 anchor) and draft the record; no 「已确证」 evidence reachable → the evidence-light branch.
3. `steps/03-perimeter.md` — map the evidence perimeter across six categories, each classified 可得 / 部分可得 / 缺失; 缺失 is itself a finding; >10K tokens per source → delegate a subagent returning JSON only.
4. `steps/04-reasoning.md` — causality, timeline reconstruction, hypothesis lifecycle (never deleted), refutation pass before any transition toward 「已确证」, premise verification.
5. `steps/05-source-trace.md` — source trace: parallel first-pass scans, caller chain, language/process boundary crossings; trivial-fix assessment (one-line suggestion, else stop at the root cause area).
6. `steps/06-report.md` — finalize: hand-off brief, conclusion + confidence, fix direction, reproduction; pass the final gate; present the route menu.

Record writes: create the record as `草稿` in step 2 (machine anchors copied from the receipt, never retyped from memory), fill each section as its step completes, settle it in step 6.

Rendering is a silent side step — command only, no browser interaction point, no path-waiting, no blocking: `python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"` (append `--instance <name>` when one was resolved).

## Schema

`{output_dir}/investigation.yaml` — single source, collection form (top-level shape follows `bug-log.yaml`):

```yaml
project: {name, status: 草稿|已定稿, created, updated}   # status = document finality; the final gate inspects it
cases:
  - id: IV-001                # IV-### — sequential, stable, never renumbered or reused
    slug: <kebab>             # resume key: a repeat run on the same slug continues this case
    date: YYYY-MM-DD
    status: 调查中|已结论|待证据阻塞
    mode: 症状驱动|探索 # defect-chasing vs area-exploration — same discipline, different anchor
    evidence_light: false     # true → no 「已确证」 evidence reachable; missing_evidence must be non-empty
    handoff_brief: <string>   # final form: 3 sentences, 15-second read
    case_info: {inputs: [{kind: 工单|归档|日志|描述|范围|提交, ref}], scope, time_window}
    problem_statement: <string>   # the initial claim; evidence may refine or contradict it
    stronghold: {ref: <path:line|timestamp|commit>, why}   # required unless evidence_light
    evidence:
      - {id: EV-001, grade: 已确证|已推断|假设中, ref, note, availability: 可得|部分可得|缺失}
    hypotheses:
      - {id: H-001, statement, status: 待验证|已确证|已推翻, test, resolution}   # never deleted; status≠待验证 ⇒ resolution
    timeline: [{at, event, ref}]
    backlog: [{item, priority, status: 待办|已完成|无法获取}]
    missing_evidence: [{what, would_resolve, how}]
    conclusion: {text, confidence: 高|中|低, fix_direction, diagnostic_steps, reproduction}
    follow_ups: [{date, note}]     # appended per re-entry (same-day entries #2/#3)
    side_findings: [{note, ref?}]  # optional — tangential, observed not followed up (≠ backlog "to explore"; ≠ evidence "this thread")
revisions: []                      # {date, change, reason} — appended when an existing record changes
```

## Rules

1. Write scope: `{output_dir}/investigation.yaml` only — cases, their sections, and `revisions`. Never touch source code, tests, `sprint.yaml`, `stories.yaml`, `test-plan.yaml`, or `bug-log.yaml`; a defect this case proves is logged by diy-review's `bug-add`, not here.
2. Evidence grading is the core discipline: **已确证** cites `path:line` / timestamp / commit; **已推断** shows the chain from 「已确证」 evidence; **假设中** states what would confirm or refute it. Grades are never inflated — the honest grade is the deliverable.
3. Stronghold first: anchor in one 「已确证」 piece of evidence, then expand outward. Never start from a theory and hunt for support. The user's description is a hypothesis, not a fact — verify it independently and say so when evidence contradicts it.
4. Hypotheses are never deleted: update `status` and add a `resolution`. Wrong turns stay in the record. Each move toward `已确证` runs a refutation pass first (actively look for disconfirming evidence) and records the attempt.
5. Missing evidence is itself a finding: log it in `missing_evidence` (what / would_resolve / how). An `evidence_light` case is legitimate, never silent.
6. Every code reference uses CWD-relative `path:line` (no leading `/`) so it stays clickable in IDE-embedded terminals.
7. Delegation discipline: reading 5+ files or any file >10K tokens → delegate to a subagent that returns structured JSON only; cite `path:line` from the result, never re-read in the parent.
8. Evidence-first language: "the evidence shows", "unconfirmed, requires X to verify" — no hedging, no narrative; conclusions stay in the main field.
9. Records are appended, never renumbered or reused; amending an existing record appends to `revisions` (date / change / reason). No `--previous` round is needed — cases are append-only by design.
10. Rendering follows the silent-side-step line in Workflow — command only; no browser interaction point, no path report that blocks, no waiting.
11. Final gate (mechanical): write `status: 已定稿` on `project` first — `已定稿` is what the gate inspects, not a product of it — then run `python "{project-root}/.claude/skills/diy-investigate/scripts/investigation.py" check --final --json`, passing the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.
