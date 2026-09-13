---
name: diy-tools
description: Internal deterministic CLI (diyc.py) for the diy-coder suite. Shared checker/writeback engine that host skills invoke for instance resolution, mechanical checks, TDD gates, static-check chains, and HALT writeback. Not user-facing - host skills call it, never the user for workflow decisions.
---

# diy-tools — diyc 检查器/写回器（内部工具，非用户直调）

Internal engine for the diy-coder skill suite. A host skill (diy-dev, diy-sprint, diy-review, ...) invokes it; the user never calls it directly. All rules and thresholds live in the scripts — this file only declares the command surface and the invocation path.

## Invocation

```bash
python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" <subcommand> [options]
```

Common options (every subcommand): `--project-root R` (default `.`), `--instance NAME`, `--json` (single-line machine-readable receipt).
Exit codes: `0` ok / `1` violations or refusal (illegal transition, unknown story, invalid instance name) / `2` usage error.

## Commands

| Command | Purpose |
| --- | --- |
| `resolve` | Resolve `output_dir` (config + instance). The only instance-resolution entry point; host skills take its `output_dir` as their sole read/write root. |
| `check --type T [--final] [--previous PA] [--story S-x]` | Mechanical checks for T ∈ prd/architecture/openapi/epics/stories/test-plan/sprint/review. exit 0 is the only pass; `--previous` guards stable IDs; `--final` runs the final-obligation list. |
| `trace [--src P]...` | Audit `# trace:` / `// trace:` comments against stories/test-plan/architecture. Unresolved IDs → exit 1. |
| `static [--timeout 600]` | Run test-plan `static_checks` in order; a blocking failure stops the chain (later layers skipped). |
| `transition --story S-x --to STATE [--reason T] [--rounds N]` | HALT state transitions. `review→done` is refused here — use `done`. |
| `green --story S-x --tc TC-a --red "..." --green "..."` | Append red/green evidence; backfill test-plan TC status. |
| `done --story S-x [--rounds N]` | review→done terminal write, with source-of-truth backfill. |
| `bug-add --entry '<json>' \| --entry-file P` | Mint BUG-0xx into bug-log.yaml. |
| `reconcile [--apply]` | Diff sprint tasks against stories/test-plan (dry-run by default; `--apply` writes). |

## Receipt

With `--json` every command prints one JSON line: `{ok, command, project_root, output_dir, instance, violations[], warnings[], counts{}, ...}`. Violations are `{code, where, msg}` with forward-slash `where` relative to project-root. Without `--json`: one line per violation (`CODE where: msg`), then a summary line.

## Rules

1. Zero new dependencies — stdlib + PyYAML only; Python 3.10+.
2. Writeback commands only ever touch the resolved `output_dir`; YAML is rewritten atomically (`tmp` + replace). Comments are not preserved — artifacts must not depend on them.
3. Files under `scripts/` are the single definition source for gates (e.g. `Docs.story_covered` drives both the TDD gate and reconcile). Never re-implement a rule inline in a prompt — call the command and read the receipt.
