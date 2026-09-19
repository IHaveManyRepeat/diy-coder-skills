---
name: diy-help
description: Dynamic workflow navigator. Scans diy-output artifacts (existence + status) and recommends the exact next skill, or names the blocking file when something is not 已定稿. Use when the user asks where they are, what to do next, or wants to start/continue the diy-coder workflow.
---

# diy-help — 工作流状态机导航（FR-4.2）

You are a thin navigator. A deterministic script computes the position; you only interpret and route. This skill never writes artifacts — it is read-only.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`. This skill is read-only and writes no artifacts — `document_output_language` does not apply. Speak `communication_language` for the entire run. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Run exactly once, without changing the working directory:

```bash
python "{project-root}/.claude/skills/diy-help/scripts/help.py" --project-root "{project-root}"
```

Append `--instance <name>` when resolved above; append `--json` only if the caller is another script.

## How to Read the Result

Relay the script's output as-is. When `blocked` is present, present it verbatim and focus there — skip optional suggestions entirely; never soften it into a menu of options. When `next_skill` is present, name the skill and recommend a fresh context window.

## Rules

1. The script requires PyYAML on the host Python. If it fails with `ModuleNotFoundError`, report the error and suggest `pip install pyyaml`. Do not silently fall back.
2. Never invent positions or skills beyond the script result. If the result surprises the user, re-run with `--json` and show the raw data — the YAML files are the source of truth, not this skill.
3. Reply in `project.communication_language`. Keep it under 10 lines; the user asked where they are, not for a manual.
