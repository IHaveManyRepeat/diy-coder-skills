---
name: diy-help
description: Dynamic workflow navigator. Scans diy-output artifacts (existence + status) and recommends the exact next skill, or names the blocking file when something is not final. Use when the user asks where they are, what to do next, or wants to start/continue the diy-coder workflow.
---

# diy-help — 工作流状态机导航（非静态菜单，FR-4.2）

You are a thin navigator. A deterministic script computes the position; you only interpret and route. This skill never writes artifacts — it is read-only.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `paths.output_dir`. This skill is read-only and writes no artifacts — `document_output_language` does not apply. Speak `communication_language` for the entire run. Instance resolution (FR-4.5/D-9): if the activation args carry an instance name (`--instance <name>` or 「实例 <name>」), resolve `output_dir` as `<output_dir>/<name>/` (the directory IS the instance); this run reads ONLY that instance dir. No instance arg → mainline flat path. Instance name must start with an alphanumeric character and must not end with a dot (`.` `_` `-` allowed inside), else refuse.
2. Run exactly once, without changing the working directory:

```bash
python "{project-root}/.claude/skills/diy-help/scripts/help.py" --project-root "{project-root}"
```

Append `--instance <name>` when resolved above; append `--json` only if the caller is another script.

## How to Read the Result

- `position` + `completed_steps` — where the workflow stands.
- `blocked` — a concrete blocker: `file` (which YAML), `status` (its current state), `action` (what to do). Present this verbatim; never soften it into a menu. When blocked, skip optional suggestions entirely — focus on the blocker.
- `next_skill` — the single recommended next skill; tell the user how to invoke it (skill name / 「<skill 名>」 phrasing) and recommend a fresh context window.
- `workflow_done` — all sprint tasks done; optional wrap-ups (证伪轮 / bug-log 经验入库) may be mentioned.
- `notes` — advisory only (e.g. openapi.yaml absent for an API-bearing project); suppressed from output while blocked.

## Rules

1. The script requires PyYAML on the host Python. If it fails with `ModuleNotFoundError`, report the error and suggest `pip install pyyaml`. Do not silently fall back.
2. Zero-output dir (fresh project) → recommend `diy-prd` from zero.
3. Never invent positions or skills beyond the script result. If the result surprises the user, re-run with `--json` and show the raw data — the YAML files are the source of truth, not this skill.
4. Reply in `project.communication_language` with: 当前位置 → 阻塞项（若有）→ 下一步。Keep it under 10 lines; the user asked where they are, not for a manual.
