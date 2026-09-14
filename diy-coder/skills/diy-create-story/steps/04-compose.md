# Step 4 — Compose（风险、判据、人工确认）

Progress: `Target → Artifacts → Code Survey → [Compose] → Finish`

**Read (input):** the draft record and the `collect` receipt.
**Write (output):** `risks` / `verify` / `open_questions` in the record.

## Risks

What can go wrong in implementation, from the survey, the decisions and the prior carry-over: an unratified decision still `proposed`, a file whose behavior is easy to break, a TC still `pending` for a story about to start, a carry-over that historically cost a review round. Each line is actionable — what to watch and why — never a restatement of an AC and never a severity score. No risk found: leave the list empty and say so in the delivery message; never invent one to fill the field.

## Verify

Command-level completion criteria: the commands diy-dev will actually run, derived from the TC refs' execution style and the project's `static_checks` chain. Each entry is a command or a command plus its expected result (`python -m unittest discover -s tests -v` — green), never "works correctly". A criterion nobody can run is not a criterion.

## Open questions

Everything unresolved at the moment of drafting: an empty `tcs` (route diy-test-design), a story whose AC cannot be verified as written, a file boundary still under judgment. These are closed with the human **before** final — either resolved (drop the line) or closed with the call taken, prefixed `[CLOSED]` and carrying what was decided. Never leave a dangling question, and never keep one only in conversation: open items live in the file.

## Optional: external research

The source workflow's step 4 (web research for the latest library specifics) is trimmed here. The project's stack truth lives in `architecture.yaml` and `project-context.yaml`, and unsourced "latest version" claims rot fast. If a story genuinely depends on a library behavior neither document fixes, put it in `open_questions` and check the library's own docs at the moment diy-dev needs it — never invent a version, an endpoint, or an API shape and never write one into the pack as if it were settled.

## Human confirmation

Present the pack as one message: story + epic, the AC and TC refs, the decisions, the files with their `why`, the risks, the verify commands, the open questions. State plainly what the pack does **not** contain — the AC text, the decision text, the story narrative — because those live one reference away, and a reader who expects a copy here will look for it in the wrong place.

Ask for corrections on the file list first (it is the highest-leverage field and the one the survey can get wrong), then the risks. The human's answer is the evidence for any change; a correction that changes the file set sends you back to step 3, not into a silent edit.

Then render (silent side step — command only, no browser interaction point, no path-waiting, no blocking):

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

(append `--instance <name>` when one was resolved).

## Next

Read fully and follow `./05-finish.md`.
