# Step 1 — Detect（框架探测与前置门禁）

Progress: `[Detect] → Targets → Generate API → Generate E2E → Record`

**Read (input):** the `detect` receipt; the presence of `{output_dir}/test-plan.yaml` and `{output_dir}/stories.yaml`.
**Write (output):** nothing — this step is read-only probing plus the gate. No artifact is created here.

## Hard gate — upstream artifacts first

Before any probing, confirm both files exist under `{output_dir}`:

- `test-plan.yaml` — the append target. Absent → the case would have no AC to bind and no place to land.
- `stories.yaml` — the AC source every appended case must resolve against.

Either one missing → stop with one line: name the missing file, say the append target is not ready, and route the user to **diy-test-design** (case design) — zero writes, zero probing beyond this check. Do not create an empty `test-plan.yaml`: this skill appends, it never initializes.

## Probe the framework

```
python "{project-root}/.claude/skills/diy-e2e-tests/scripts/e2e.py" detect --project-root "{project-root}" --output-dir "{output_dir}" --json
```

The engine reads the project's manifests in a language-agnostic order (`package.json` → `pyproject.toml` / `requirements*.txt` → `Cargo.toml` / `go.mod` / `pom.xml` / `build.gradle*` / `Gemfile` / `composer.json`) and reports:

- `framework` — `{name, detected_from}`, or `null` when nothing is declared.
- `project_type` — `node` / `python` / `rust` / `go` / `java` / `ruby` / `php` / `unknown`.
- `test_dirs` — existing test directories; `existing_patterns` — existing test file paths (the pattern source to imitate).
- `suggested` — the recommended framework when `framework` is `null`.
- `warnings` — a manifest that exists but cannot be parsed degrades here; the probe continues (never crash, never guess).

**Use whatever the project already has.** When `framework` is set, adopt its runner, its file naming and its directory layout from `test_dirs` / `existing_patterns` — do not introduce a second framework.

## No framework → the user decides

`framework: null` is a decision point, not a dead end. Present `suggested` (with `project_type` as the reason) and ask the user to confirm or name another framework. **Never install anything** — no package manager command, no manifest edit; installation is the user's call, made outside this skill.

The user's answer is recorded in the closing summary; the run continues only on their confirmation. On refusal, stop cleanly — the target feature list and the case files are simply never produced.

## Hand off

Carry forward: the confirmed framework, its runner command (the project's own test command), the test directory and the file-naming pattern. State them in one line each — they drive steps 3 and 4.

## Next

Read fully and follow `./02-targets.md`.
