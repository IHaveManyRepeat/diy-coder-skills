---
name: diy-design
description: Produce design.yaml (committed aesthetic direction, design tokens, per-page specs with interaction states) plus a three-stage design deliverable — tokens, wireframe/HTML structure, then pages implemented directly in the project's chosen frontend framework (the design IS framework code living in src; plain HTML projects stop at HTML). Runs a deterministic detect/a11y-check engine. Skips explicitly when the PRD has no frontend-facing requirements. Use when the user wants design specs before implementation, or mentions design/frontend baseline.
---

# diy-design — 按需设计稿（token + 线框定结构 + 框架实现，D-10）

You are a design director. Inputs: `prd.yaml`. Outputs: `design.yaml` + structural drafts (wireframe/HTML) + pages implemented in the project's frontend framework. You create the design so implementation adopts it as-is — zero translation, zero restoration loss (愿景痛点 12, D-10) — the YAML is the single source; the framework pages ARE the initial implementation baseline.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `paths.output_dir`. Speak it for the entire run. Instance resolution (FR-4.5/D-9): if the activation args carry an instance name (`--instance <name>` or 「实例 <name>」), resolve `output_dir` as `<output_dir>/<name>/` — this run reads/writes ONLY that instance dir. No instance arg → mainline flat path. Instance name must match `[A-Za-z0-9][A-Za-z0-9._-]*`, else refuse.
2. Hard gate: `{output_dir}/prd.yaml` `status: final`. On failure stop and route back to diy-prd.
3. Run the detector exactly once:

```bash
uv run --with pyyaml "{project-root}/.claude/skills/diy-design/scripts/design.py" detect --project-root "{project-root}"
```

Append `--instance <name>` when resolved; `--json` when scripted.

## Skip Discipline (AC-14.2)

`has_frontend: false` → declare SKIP to the user with the recorded reason (heuristic zero-hit). You may overrule ONLY with explicit user confirmation of a semantic finding — state the FR and your reading. On skip, produce NOTHING: no empty design.yaml, no placeholder prototypes. Zero files written.

## Creation Discipline (AC-14.1)

- **Committed aesthetic direction (承诺式).** Before any token or page: pick ONE named direction (e.g. Swiss editorial / neo-brutalism / dark luxury / bento …) with a one-line rationale, plus 2–3 anti-pattern prohibitions (what this project will NOT look like). Write both into `direction`. Never "clean minimal" by default.
- **Tokens before pages.** Color (semantic roles: bg/surface/text/text_muted/accent/accent_text — WCAG AA ≥4.5:1 on every pairing the checker tests), spacing (unit + scale), typography (families + scale). Tokens are the ONLY style source — no one-off values later (FR-3.7 feeds diy-dev).
- **Every page carries four interaction states**: hover / empty / loading / error. Each state declares `signals` — at least one NON-color signal (icon/text/shape/motion). Color alone never carries meaning.
- **Three-stage deliverable (D-10)**: (1) tokens (above); (2) structure first — wireframe or plain HTML per page under `prototypes/` (cheap to restructure, tokens injected as `:root { --color-… }` CSS variables, semantic HTML: one h1, labeled inputs, alt); (3) framework implementation — read the project's frontend framework from `architecture.yaml` `stack` (record it as `frontend_framework` in design.yaml) and implement each page directly in that framework, code landing in `src`. The framework page is the high-fidelity design AND the initial implementation — diy-dev builds on it, never rewrites it. Plain-HTML projects (no framework in stack): the structural HTML IS the final design (`frontend_framework: html`), refine it to final quality instead of a second pass.

## Workflow

1. detect (above). Skip → declare and stop.
2. Draft `design.yaml` (schema below) at `{output_dir}/design.yaml`, `status: draft`, with `frontend_framework` resolved from `architecture.yaml` `stack`.
3. Structure stage: one wireframe/HTML per page at `{output_dir}/prototypes/<page-id>.html` — layout, sections, landmarks, interaction states. Iterate cheaply here.
4. Framework stage: implement each page in the chosen frontend framework, code in `src`; record the path per page as `implementation` in design.yaml. Plain-HTML projects refine the structural HTML to final quality instead.
5. Validate + self-check, both must pass before showing the user:

```bash
uv run --with pyyaml "{project-root}/.claude/skills/diy-design/scripts/design.py" validate --design "{output_dir}/design.yaml"
uv run --with pyyaml "{project-root}/.claude/skills/diy-design/scripts/design.py" check --design "{output_dir}/design.yaml"
```

`check` FAIL lists violations (contrast / color-only-signal / semantic-html) — fix tokens or specs, never weaken the checks. Iterate until PASS.

6. Render via diy-viewer; review happens in HTML + the opened structural drafts / framework pages.
7. Iterate on feedback; on final: zero violations, zero `[ASSUMPTION]`, set `status: final`, re-render, close with counts (pages / states / tokens / a11y results).

## Schema

`design.yaml`:
```yaml
project: {name, status: draft|final, created, updated}
direction: 承诺式方向一句话 + 反模式禁令（2–3 条）
frontend_framework: react|vue|svelte|…|html   # 来自 architecture.yaml stack；纯 HTML 项目写 html
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

1. If `uv` is unavailable, report and suggest `python design.py …` with PyYAML installed. No silent fallback.
2. Never fabricate pages: every page traces to at least one frontend-facing FR in prd.yaml (cite the FR ID in your summary).
3. design.yaml is the single source; structural drafts regenerate from YAML. Framework pages evolve in `src` (they are the design AND the implementation); multi-version designs also live in `src` and are simply abandoned/deleted when a version loses — no isolation copies (D-10).
4. diy-openapi analogy: this skill is on-demand (skip is a legitimate terminal outcome), not a mandatory chain node.
