# Step 3 — Draft Specific Edits（具体改动提案）

Progress: `Initialize → Analysis → [Edits] → Proposal → Route → Finish`

**Read (input):** the record's `impacts`; the artifacts' current values only at the precise IDs being edited (by ID lookup, never a full re-read).
**Write (output):** `edits` in the record.

## One edit per proposed change (source step-3)

Every entry answers four questions in the record: what changes (`artifact` + `target` + `field`), from what (`old`), to what (`new`), and why (`rationale`).

**Reference, never copy** — the load-bearing diy rewrite of the source's "show old → new text" form. `old` and `new` quote the smallest decisive value, not a pasted passage:

```
artifact: stories
target: AC-1.1
field: acceptance_criteria
old: AC-1.1 当前只断言邮箱密码登录成功
new: AC-1.1 追加 2FA 启用分支（given/when/then 三键同改）
rationale: 安全评审将 2FA 列为 must，AC 不覆盖则测试设计无处落点
```

For an addition there is no current value: write `old: (absent)` — the field must stay non-empty, and `old` must differ from `new` (the engine rejects a no-op edit).

## The source's four artifact lenses (kept as checklists, not templates)

- **Stories** (source step-3) — name the story ID and the section touched; an AC edit changes all three of given/when/then plus its `refs` when coverage moves.
- **PRD** — the exact FR/NFR IDs and the MVP-scope consequence (`F-*` stays stable; a new requirement gets a new `FR-x.y`, never a renumber).
- **Architecture** — affected `D-*` decisions, components, or tech choices, plus what that ripples into downstream; a new decision is `add`, not a rewrite of an accepted one.
- **Design / openapi** — the page `P-*` or `operationId` touched, and the user-visible or contract consequence.
- **Test-plan** — the `TC-*` cases binding edited ACs; touch `static_checks` when the tooling or CI gates themselves move.
- **Infra** — a deployment script / CI config / IaC file: `target: path:<relative>`, `field` naming the config path inside it (e.g. `jobs.test.steps`); `old: (absent)` for a file yet to create.

## Verify each edit before presenting

- the target ID exists in the `collect` receipt (document summaries or chain); an infra `path:` target is exempt from that lookup (the file may be yet to create) and is checked for form instead — relative, forward slashes, no `..`;
- the field path names something real in that artifact's schema (SKILL.md schemas of the owning skills are the authorities);
- `old` reflects the current value — when you write it from the receipt's summary rather than the artifact, say so and keep it summarised, never invented verbatim.

## Present per mode (source step-3)

**Incremental** — present each proposal alone; the source's loop is kept: **Approve [a] / Edit [e] / Skip [s]**. Refine per feedback, iterate until the human moves on. A skipped edit is dropped, not silently kept.

**Batch** — collect all edit proposals and present them together at the end of this step; the human marks what changes and the loop runs once over the marked set.

## Next

Read fully and follow `./04-proposal.md`.
