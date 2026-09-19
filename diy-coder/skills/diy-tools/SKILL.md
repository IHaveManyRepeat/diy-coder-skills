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
| `check --type T [--final] [--previous PA] [--story S-x] [--strict]` | Mechanical checks for T ∈ prd/architecture/openapi/epics/stories/test-plan/sprint/review. exit 0 is the only pass; `--previous` guards stable IDs; `--final` runs the final-obligation list. Consumes the baseline ledger (see Receipt). |
| `trace [--src P]... [--strict]` | Audit `# trace:` / `// trace:` comments against stories/test-plan/architecture. Unresolved IDs → exit 1. |
| `static [--timeout 600] [--strict]` | Run test-plan `static_checks` in order; a blocking failure stops the chain (later layers skipped). |
| `transition --story S-x --to STATE [--reason T] [--rounds N]` | HALT state transitions. `待审查→已完成` is refused here — use `done`. |
| `green --story S-x --tc TC-a --red "..." --green "..."` | Append red/green evidence; backfill test-plan TC status. |
| `done --story S-x [--rounds N]` | 待审查→已完成 terminal write, with source-of-truth backfill. |
| `bug-add --entry '<json>' \| --entry-file P` | Mint BUG-0xx into bug-log.yaml. |
| `defer-add --entry '<json>' \| --entry-file P` | Queue a deferred action into `deferred-actions.yaml` (mints `DA-0xx`; `reason` ∈ `用户配置`/`破坏性操作`/`越界改动`/`仅人工可做`). For actions the side-effect discipline keeps user-confirmed: queue instead of blocking — the user confirms and runs them later. |
| `reconcile [--apply]` | Diff sprint tasks against stories/test-plan (dry-run by default; `--apply` writes). |
| `baseline-add --code C --where W --reason R` | Append one known-legacy entry to `{output_dir}/diyc-baseline.yaml` (stamps `on`: today, `by`: user). Duplicate `(code, where)` → `BASELINE_DUPLICATE`, corrupt ledger → `BASELINE_INVALID`; both refuse with zero writes. Only after explicit user ratification (rule 4). |

## Receipt

With `--json` every command prints one JSON line: `{ok, command, project_root, output_dir, instance, violations[], warnings[], counts{}, ...}`. Violations are `{code, where, msg}` with forward-slash `where` relative to project-root. Without `--json`: one line per violation (`CODE where: msg`), then a summary line.

Audit commands (`check`, `trace`, `static`) also consume the baseline ledger `{output_dir}/diyc-baseline.yaml` — user-ratified known-legacy entries (`code`, `where`, `reason`, `on`, `by`). A violation whose `(code, where)` matches an entry is demoted to `known[]` (carrying the entry's `reason`) and counted in `counts.known` — entries there are ratified debt, not violations to fix, and never affect the exit code. An entry that goes unmatched while this run still reports the same code in the entry's file scope becomes `BASELINE_STALE` (exit 1): delete it, the ledger only shrinks (scope matching keeps commands like `trace` from flagging unrelated entries; `check --story S-x` is a task-scoped spot check and skips STALE entirely — a narrowed run cannot prove an entry is dangling). A corrupt ledger or an entry missing a required field yields `BASELINE_INVALID` (exit 1) with the whole ledger inert — violations are never silently swallowed. Demotion is judgment-level only — detail arrays and counts (`unresolved`, `layers`, `counts.unresolved`, …) still show what the run observed; read them as facts, not verdicts. Writeback commands (`transition`, `green`, `done`, `bug-add`, `defer-add`, `reconcile`) do not consume the baseline. `--strict` ignores the ledger entirely (no demotion, no STALE) for release/CI re-checks. `baseline-add` is the ledger's only writer and itself never consumes it: it appends one entry and refuses a duplicate `(code, where)` (`BASELINE_DUPLICATE`) or a corrupt/invalid ledger (`BASELINE_INVALID`) with zero writes; a missing `output_dir` is refused (`MISSING_FILE`) rather than created. Any unexpected internal failure (permissions, path occupied by a directory, disk-full) surfaces as an `INTERNAL_ERROR` violation with exit 1 and a well-formed receipt — never a silent empty stdout, never a `.tmp` residue.

## Rules

1. Zero new dependencies — stdlib + PyYAML only; Python 3.10+.
2. Writeback commands only ever touch the resolved `output_dir`; YAML is rewritten atomically (`tmp` + replace, and the tmp file is cleaned up when the write fails). Comments are not preserved — artifacts must not depend on them.
3. Files under `scripts/` are the single definition source for gates (e.g. `Docs.story_covered` drives both the TDD gate and reconcile). Never re-implement a rule inline in a prompt — call the command and read the receipt.
4. Baseline entries are written to the ledger only after explicit user ratification — a host skill proposes `(code, where, reason)`, the user decides, and `baseline-add` is the only writer; never self-enrol a violation to clear a gate.
