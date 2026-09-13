---
name: diy-viewer
description: Render diy-coder YAML artifacts (prd.yaml, architecture.yaml, etc.) into human-friendly HTML (browser auto-opens in interactive terminals only; AI/automated runs render silently). Use when the user asks to view/see/preview any diy-output document, or after any diy-* skill produces or updates a YAML artifact.
---

# diy-viewer — YAML 单一源 → HTML 人类友好投影

You are a thin launcher. The YAML files are the single source of truth; this skill never edits them — it only renders a view.

## Run

Execute exactly once, without changing the working directory (adjust `{project-root}` to the absolute project root). Mainline is the default form; when an instance name was resolved at activation, use the instance form — the same command line plus `--instance <name>` (never switch back to the mainline path):

```bash
# Mainline
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"

# Instance (same command line + --instance <name>)
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}" --instance <name>
```

Behavior:

- `--instance <name>`: render the instance's artifacts from `<output_dir>/<name>/` into `<output_dir>/<name>/.view/` (FR-4.5/D-9). Without it: the mainline flat `output_dir`.
- Caller obligation: a diy-* skill that resolved an instance name at activation MUST append the same `--instance <name>` to its render call — never fall back to the mainline silently. Instance directory resolution and name validation are viewer.py's job.
- Optional explicit files: append their paths after the command to render only those.

## Rules

- The render command requires PyYAML on the host Python. If it fails with `ModuleNotFoundError`, report the error and suggest `pip install pyyaml`. Do not silently fall back.
- If `paths.output_dir` is missing or contains no YAML files, tell the user which directory was scanned and suggest running a diy-* workflow first; do not fabricate content.
- Pass `--open` only when the user explicitly asks to open the browser.
- After rendering, reply in `project.communication_language` (from `diy-coder.yaml`) with a one-line summary: which documents were rendered and where the HTML lives. Exception — automated/headless renders (a render step inside another skill's flow, a runner-driven session) stay silent: no path report, just continue; the render is a side step that never blocks the flow.
- This skill writes no YAML prose; the HTML projection's chrome labels are fixed Chinese by design (display-layer choice — `document_output_language` governs artifact prose in the sources, not the viewer chrome).
