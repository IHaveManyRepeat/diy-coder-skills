# Step 5 — Present（呈现与收尾）

Progress: `Clarify & Route → Plan → Implement → Review → [Present]`

**Read (input):** the record at `status: 审查中` with its `review` block; the diff since `baseline`.
**Write (output):** the record's `review_order` and `status: 已完成`; `project.status: 已定稿`; the closing summary.

## Build the review order

Construct the diff since `baseline`, then append `review_order` — an ordered trail of stops that lets a human read the change top-down:

1. **Order by concern, not by file** — group stops by the conceptual concern they address (validation logic, schema change, UI binding). One file may appear under several concerns.
2. **Lead with the entry point** — the single highest-leverage `path:line` that reveals the design intent first.
3. Inside a concern, order from most important / architecturally interesting to supporting; bias slightly toward higher-risk or boundary-crossing stops.
4. **End with peripherals** — tests, config, types, and other supporting changes come last.
5. Each stop: `{path, line, why}` — `path` CWD-relative with no leading `/`, `line` the anchor, `why` one ultra-concise line (≤15 words) saying why this approach here and what it achieves. No paragraphs.

## Settle the record

1. Set `project.status: 已定稿` and the record's `status: 已完成`.
2. **Final gate (mechanical):** run `python "{project-root}/.claude/skills/diy-quick-dev/scripts/spec.py" check --final --id SP-xxx --json` with the same `--project-root` / `--output-dir` arguments as activation (`--output-dir` is mandatory and never defaulted). Exit 0 is the only pass; fix every reported violation and re-run; the JSON receipt (counts included) is the close-out evidence. `check --final` requires a done record with every task done, non-empty acceptance, and a real `result` on each verification command.

## Close

Render via diy-viewer — the silent side-step command from SKILL.md (append `--instance <name>` when one was resolved); no browser interaction point, no path-waiting, no blocking.

Then display the summary:

- Files changed, one line each; all terminal paths CWD-relative with `:line`, never a leading `/`.
- Review breakdown: rounds used, findings by route (patched / deferred / rejected) — if every finding was dropped, say so.
- The spec path and a note that its `review_order` now carries the reading trail.
- **Commit and push are the human's move.** Never commit, never push, never open an editor — close with one suggested line (a conventional message they can run themselves, and an offer to draft a PR description). The tree stays exactly as it is.
- Close with the counts from the JSON receipt (tasks done, findings by route, verification commands run, final status).

## Exit

This is the last step of the 计划-编码-审查 route — the run ends here once the final gate exits 0. The 一次成型 route ends in `./06-oneshot.md`; no further `steps/` file is read.
