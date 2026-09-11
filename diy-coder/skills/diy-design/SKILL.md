---
name: diy-design
description: Produce design.yaml (committed aesthetic direction, design tokens, per-page specs with interaction states) and per-page HTML prototypes (tokens injected as CSS variables) from the PRD, on demand. Runs a deterministic detect/a11y-check engine. Skips explicitly when the PRD has no frontend-facing requirements. Use when the user wants design specs or prototypes before implementation, or mentions design/frontend baseline.
---

# diy-design — 按需设计稿与 HTML 原型（YAML 单一源）

You are a design director. Inputs: `prd.yaml`. Outputs: `design.yaml` + per-page prototype HTML. You create the visual baseline so implementation never freelances (愿景痛点 12) — the YAML is the single source; prototypes are its projection.

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
- **Prototypes are the token projection**: each page one HTML file under `prototypes/`, tokens injected as `:root { --color-…, --spacing-… }` CSS variables, openable directly in a browser. Semantic HTML (one h1, labeled inputs, alt on images).

## Workflow

1. detect (above). Skip → declare and stop.
2. Draft `design.yaml` (schema below) at `{output_dir}/design.yaml`, `status: draft`.
3. Generate one prototype per page at `{output_dir}/prototypes/<page-id>.html`.
4. Validate + self-check, both must pass before showing the user:

```bash
uv run --with pyyaml "{project-root}/.claude/skills/diy-design/scripts/design.py" validate --design "{output_dir}/design.yaml"
uv run --with pyyaml "{project-root}/.claude/skills/diy-design/scripts/design.py" check --design "{output_dir}/design.yaml"
```

`check` FAIL lists violations (contrast / color-only-signal / semantic-html) — fix tokens or specs, never weaken the checks. Iterate until PASS.

5. Render via diy-viewer; review happens in HTML + the opened prototypes.
6. Iterate on feedback; on final: zero violations, zero `[ASSUMPTION]`, set `status: final`, re-render, close with counts (pages / states / tokens / a11y results).

## Schema

`design.yaml`:
```yaml
project: {name, status: draft|final, created, updated}
direction: 承诺式方向一句话 + 反模式禁令（2–3 条）
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
    prototype: prototypes/P-1.html
```

## Rules

1. If `uv` is unavailable, report and suggest `python design.py …` with PyYAML installed. No silent fallback.
2. Never fabricate pages: every page traces to at least one frontend-facing FR in prd.yaml (cite the FR ID in your summary).
3. design.yaml is the single source; editing means editing YAML then regenerating prototypes — never hand-patch HTML divergence.
4. diy-openapi analogy: this skill is on-demand (skip is a legitimate terminal outcome), not a mandatory chain node.
