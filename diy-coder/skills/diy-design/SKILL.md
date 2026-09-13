---
name: diy-design
description: Produce design.yaml (committed aesthetic direction, design tokens, per-page specs with interaction states) plus a three-stage design deliverable — tokens, wireframe/HTML structure, then pages implemented directly in the project's chosen frontend framework (the design IS framework code living in src; plain HTML projects stop at HTML). Runs a deterministic detect/a11y-check engine. Skips explicitly when the PRD has no frontend-facing requirements. Use when the user wants design specs before implementation, or mentions design/frontend baseline.
---

# diy-design — 按需设计稿（token + 线框定结构 + 框架实现，D-10）

You are a design director. Inputs: `prd.yaml`. Outputs: `design.yaml` + structural drafts (wireframe/HTML) + pages implemented in the project's frontend framework. You create the design so implementation adopts it as-is — zero translation, zero restoration loss (愿景痛点 12, D-10) — the YAML is the single source; the framework pages ARE the initial implementation baseline.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Hard gate: `{output_dir}/prd.yaml` `status: final`. On failure stop and route back to diy-prd.
3. Run the detector exactly once:

```bash
python "{project-root}/.claude/skills/diy-design/scripts/design.py" detect --project-root "{project-root}"
```

Append `--instance <name>` when resolved; `--json` when scripted.

## Skip Discipline (AC-14.2)

`has_frontend: false` → declare SKIP to the user with the recorded reason (heuristic zero-hit). You may overrule ONLY with explicit user confirmation of a semantic finding — state the FR and your reading. On skip, produce NOTHING: no empty design.yaml, no placeholder prototypes. Zero files written.

## Creation Discipline (AC-14.1)

- **Committed aesthetic direction (承诺式).** Before any token or page: pick ONE named direction (e.g. Swiss editorial / neo-brutalism / dark luxury / bento …) with a one-line rationale, plus 2–3 anti-pattern prohibitions (what this project will NOT look like). Write both into `direction`. Never "clean minimal" by default.
- **Tokens before pages.** Token families and keys are exactly the schema below; every color pairing meets WCAG AA 4.5:1. Tokens are the ONLY style source — no one-off values later (FR-3.7 feeds diy-dev).
- **Every page carries four interaction states**: hover / empty / loading / error. Each state declares `signals` — at least one NON-color signal (icon/text/shape/motion). Color alone never carries meaning.
- **Three-stage deliverable (D-10).** Tokens (above) → structural draft per page under `prototypes/` → that page implemented in the project's framework under `src` (mechanics in Workflow 2–4; plain-HTML projects stop at the refined structural HTML). The framework page is both the high-fidelity design and the initial implementation — diy-dev builds on it, never rewrites it.

## Workflow

1. detect (above). Skip → declare and stop.
2. Draft `design.yaml` (schema below) at `{output_dir}/design.yaml`, `status: draft`, with `frontend_framework` resolved from `architecture.yaml` `stack`.
3. Structure stage: one wireframe/HTML per page at `{output_dir}/prototypes/<page-id>.html` — layout, sections, landmarks, interaction states. Iterate cheaply here.
4. Framework stage: implement each page in the chosen frontend framework, code in `src`; record the path per page as `implementation` in design.yaml.
5. Validate + self-check, all must pass before showing the user:

```bash
python "{project-root}/.claude/skills/diy-design/scripts/design.py" validate --design "{output_dir}/design.yaml"
python "{project-root}/.claude/skills/diy-design/scripts/design.py" check --design "{output_dir}/design.yaml"
python "{project-root}/.claude/skills/diy-design/scripts/design.py" audit --design "{output_dir}/design.yaml" --src <impl>
```

`check` FAIL lists violations (contrast / color-only-signal / semantic-html) — fix tokens or specs, never weaken the checks. Iterate until PASS. `audit` is the token single-source gate over the implementation code (`--src` = project-root `src` for framework projects, `{output_dir}/prototypes` for plain-HTML): every `one-off-color` / `one-off-font-size` violation is a baseline defect to fix here, not to leave for diy-dev / diy-review L4(c) to catch downstream.

6. Render via diy-viewer (same activation command — append `--instance <name>` when one was resolved); review happens in HTML + the opened structural drafts / framework pages.
7. Iterate on feedback; on final: zero violations, zero `[ASSUMPTION]`, set `status: final`, re-render, close with counts (pages / states / tokens / a11y results).

## Schema

`design.yaml`:
```yaml
project: {name, status: draft|final, created, updated}
direction: 承诺式方向一句话 + 反模式禁令（2–3 条）
frontend_framework: react|vue|svelte|…|html   # 纯 HTML 项目写 html
tokens:
  color: {bg, surface, text, text_muted, accent, accent_text}
  spacing: {unit, scale: [...]}
  typography: {family_base, family_heading, scale: [...]}
pages:
  - id: P-1                # 稳定 ID，S-15 由 story AC 引用（FR-2.4）
    name: 页面名
    route: /path
    states:
      - {name: hover,  signals: [icon, motion]}
      - {name: empty,  signals: [text]}
      - {name: loading, signals: [icon, motion]}
      - {name: error,  signals: [icon, text]}
    prototype: prototypes/P-1.html    # 结构稿（线框/HTML）
    implementation: src/pages/P-1.jsx  # 框架实现稿（D-10；html 项目可省略）
```

## Rules

1. The script requires PyYAML on the host Python. If it fails with `ModuleNotFoundError`, report the error and suggest `pip install pyyaml`. No silent fallback.
2. Never fabricate pages: every page traces to at least one frontend-facing FR in prd.yaml (cite the FR ID in your summary).
3. design.yaml is the single source; structural drafts regenerate from YAML. Framework pages evolve in `src` (they are the design AND the implementation); multi-version designs also live in `src` and are simply abandoned/deleted when a version loses — no isolation copies (D-10).
