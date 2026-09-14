# Step 5 — Record（追加 TC、定稿门与摘要）

Progress: `Detect → Targets → Generate API → Generate E2E → [Record]`

**Read (input):** the executed cases with their measured status; the AC bindings from step 2; the existing `test-plan.yaml` TC ids.
**Write (output):** the case JSON file; the appended `test_cases` entries in `{output_dir}/test-plan.yaml`; the closing session summary.

## Mint the TC ids — continue, never reuse

For each case, `id = TC-{ac}.{seq}`: take the AC id, drop the `AC-` prefix, keep the dotted numbering, and append the next sequence for that AC. `AC-5.1` with `TC-5.1.1` present → `TC-5.1.2`. Look the existing maximum up in `{output_dir}/test-plan.yaml` (locate by AC id — do not re-derive the whole file). Never renumber, never reuse, never fill a gap left by a deleted case.

## Write the case file

One JSON file under a scratch path (never in `{output_dir}`):

```json
[
  {
    "id": "TC-5.1.2",
    "title": "登录流程端到端",
    "ac": "AC-5.1",
    "type": "e2e",
    "priority": "P0",
    "technique": "scenario",
    "kill_target": "用户旅程在中途静默中断（页面已跳转但状态未持久化）",
    "status": "pass",
    "steps": ["打开 /login", "填写表单并提交", "断言跳转且会话可复用"]
  }
]
```

A top-level object with a `test_cases` key is equally accepted. `type` is `e2e` and `technique` is `scenario` for every case this skill appends; `status` is the measured result, not an expectation.

## Append — the mechanical gate

```
python "{project-root}/.claude/skills/diy-e2e-tests/scripts/e2e.py" record --tc-file <cases.json> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

Exit 0 is the only pass. The engine validates the id rule and continuation, the AC resolution in `stories.yaml`, the `e2e`/`scenario`/`kill_target`/`title`/`steps` requirements and the measured `status` — and writes only when every case passes; any violation → exit 1, zero writes, the existing plan untouched. Fix the reported violations and re-run.

On success the receipt carries `appended`, `counts.cases_total`, and a `diyc` block: the engine re-checks the whole `test-plan.yaml` chain through `diyc.py check --type test-plan`. Violations there are **warnings to relay** (they may pre-date this run) — they do not invalidate the append, but they must appear in the closing summary, never be swallowed.

## Close out

Render via diy-viewer (same activation command — append `--instance <name>` when one was resolved) — silent side step, no path-waiting, no blocking; in headless runs render silently.

Summary (in-conversation — this skill writes no separate summary artifact; BMAD's `test-summary.md` is replaced by this closing report plus the appended cases):

- Cases appended by id, with the files they landed in (project test directory).
- Execution result: cases run / passed / failed, with the fix applied or the observed-vs-expected evidence for each remaining failure.
- Coverage: features covered of the confirmed target list, API vs E2E.
- Gaps and assumptions: targets skipped with their reason, `[ASSUMPTION]` bindings and the user's adjudication, `diyc` warnings.
- Next step for the user: run the suite in CI, and route remaining red cases to diy-review as findings.

## Next

None — the run ends here. If new targets surface during the summary, the user re-enters at `./02-targets.md` rather than restarting the detect step.
