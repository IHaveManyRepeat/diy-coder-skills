---
name: diy-viewer
description: Render diy-coder YAML artifacts (prd.yaml, architecture.yaml, etc.) into human-friendly HTML and open in browser. Use when the user asks to view/see/preview any diy-output document, or after any diy-* skill produces or updates a YAML artifact.
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

- No args: renders every `*.yaml` under the configured `paths.output_dir` (from `diy-coder.yaml`, default `diy-output`).
- `--instance <name>`: render the instance's artifacts from `<output_dir>/<name>/` into `<output_dir>/<name>/.view/` (FR-4.5/D-9, directory IS the instance). Without it: the mainline flat `output_dir` (status quo, zero migration). Invalid instance names (must start with an alphanumeric character, must not end with a dot; `.` `_` `-` allowed inside) are refused with exit 1.
- Caller obligation: a diy-* skill that resolved an instance name at activation MUST append the same `--instance <name>` to its render call — never fall back to the mainline silently. Instance directory resolution and name validation are viewer.py's job.
- Optional explicit files: append their paths after the command to render only those.
- Output lands in `<output_dir>/.view/` — `index.html` plus one HTML page per document. This directory is disposable; delete freely.

## Rules

1. The render command requires PyYAML on the host Python. If it fails with `ModuleNotFoundError`, report the error and suggest `pip install pyyaml`. Do not silently fall back.
2. If `paths.output_dir` contains no YAML files, tell the user which directory was scanned and suggest running a diy-* workflow first (e.g. diy-prd). Do not fabricate content.
3. `viewer.auto_open: true` in config opens the browser automatically. On failure, print the generated HTML path so the user can open it manually.
4. Never modify YAML content while rendering. If a YAML file fails to parse, report the file and error, render the remaining files, and continue.
5. After rendering, reply in `project.communication_language` (from `diy-coder.yaml`) with a one-line summary: which documents were rendered and where the HTML lives.
6. This skill writes no YAML prose; the HTML projection's chrome labels are fixed Chinese by design (display-layer choice — `document_output_language` governs artifact prose in the sources, not the viewer chrome).
