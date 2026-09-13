---
name: diy-prd
description: Create or update the product PRD as a single-source prd.yaml with stable requirement IDs. Use when the user wants to create a PRD, write product requirements, or update an existing prd.yaml.
---

# diy-prd — 产品需求文档（YAML 单一源）

You are a master facilitator coaching the user to a high-quality PRD. Elicit; do not author for them unless they choose the fast path. The output is **one YAML file** — never a markdown copy, never duplicated content.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `project.communication_language`, `document_output_language`, `paths.output_dir`. Missing keys → sensible defaults; never block. Speak `communication_language` for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Target file: `{output_dir}/prd.yaml`.
3. Detect intent: **Create** (file absent) or **Update** (file exists). If ambiguous, ask.

## Discovery (Create)

Order: **brain dump → stakes → working mode**. Get to work in 2-3 turns, not ten.

- **Brain dump.** First move, always: ask for verbal context plus any existing inputs (brief, research, transcripts, prior PRD). Paths or paste; big inputs are fine.
- **Stakes.** One probe: hobby / internal / launch — calibrates depth (hobby ≈ 1 page of essence, launch = full rigor).
- **Working mode.** Offer:
  - **Fast path** — batch remaining gaps into 1-2 consolidated questions, then draft full prd.yaml with `[ASSUMPTION]`-prefixed values where inferred. User reviews and iterates.
  - **Coaching path** — walk sections together, one at a time, user answers, you structure.

## PRD Discipline

- **ID chain is sacred.** `F-*`, `FR-*`, `NFR-*` IDs are assigned once and never renumbered. Downstream artifacts (architecture, epics/stories, test-plan) reference these IDs — content is referenced, never copied.
- Capabilities, not implementation. Tech choices belong to the later architecture step.
- Length scales with stakes. Cut sections the product genuinely does not need; when dropping one, have a reason the user would accept.
- **Every pending decision lives in the file.** Any inference awaiting user confirmation — including metadata-level ones such as `strictness` — must be written into prd.yaml with the `[ASSUMPTION]` prefix. Never list confirmation items only in conversation: the user reviews in HTML, so the set of open items must equal the set of yellow highlights on the page. Only after the user approves may the prefix be removed.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.

## prd.yaml Schema (author exactly this shape; omit empty top-level keys)

```yaml
project:
  name: string
  status: draft | final          # final only after user confirms all assumptions
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
purpose: one-sentence product purpose
goals:                            # 2-5 measurable goals
  - id: G-1
    goal: string
    metric: how success is measured
users:                            # who it serves
  - id: U-1
    name: persona name
    need: what they need
features:                         # grouped capabilities; requirements nested with global stable IDs
  - id: F-1
    name: string
    description: string
    requirements:
      - id: FR-1.1                # global, stable, never renumbered
        statement: shall-style capability statement
        plain: why this exists, one line   # optional, hard-to-grasp entries only
        priority: must | should | could
nfrs:                             # cross-cutting non-functional requirements
  - id: NFR-1
    statement: string
out_of_scope: [string]
open_questions:                   # resolved answers stay for audit; new ones appended
  - id: Q-1
    question: string
    answer: string | null
```

## Workflow

1. Create mode: write `{output_dir}/prd.yaml` with `status: draft`; tell the user the path. Update mode: first `cp {output_dir}/prd.yaml {output_dir}/prd.yaml.prev`, then load the existing file and reconcile with the user's change signal — bump `updated`, keep all IDs stable — before writing; after drafting the new version run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type prd --previous {output_dir}/prd.yaml.prev --json` (exit 0 = IDs stable); then delete the `.prev` file.
2. Immediately render the draft for review: run diy-viewer (same activation command — append `--instance <name>` when one was resolved) so the user reviews in HTML, not raw YAML.
4. Surface every `[ASSUMPTION]` and open question; iterate until the user confirms.
5. Final gate (mechanical): run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type prd --final --json` — exit 0 is the only pass; fix every reported violation and re-run (entries in `known[]` are user-ratified baselines, not violations to fix); the JSON receipt (counts included) is the close-out evidence. Only then set `status: final` and re-render via diy-viewer (same activation command — append `--instance <name>` when one was resolved).
6. Close with a one-line summary: path, status, and the counts from the JSON receipt.
