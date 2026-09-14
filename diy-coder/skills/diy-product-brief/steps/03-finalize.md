# Step 3 — Finalize（决策日志审计 → 润色 → 交付）

Progress: `Discovery → Draft → [Finalize]`

**Read (input):** `{output_dir}/brief.yaml` — brief, `decisions`, `addendum`; the conversation.
**Write (output):** the settled `brief.yaml` (`project.status` / `updated`); the delivery message; the rendered projection (silent side step).

## 1. Decision-log audit + addendum review

End this step with an explicit, shared accounting of how the meaningful contents of `decisions` — and of `addendum` — were handled. Every entry lands in exactly one of three buckets, and the user agrees out loud:

- captured in the brief itself,
- living in the addendum (with its `why_separate` intact),
- set aside as process noise.

Nothing silently disappears and no entry goes unreviewed. Then close the loose ends: clear every `[ASSUMPTION]` (the user confirms it and the tag is dropped, or it becomes an `open_questions` line) and resolve or explicitly defer every `open_questions` entry.

## 2. Polish

Apply the house document standards to the brief's prose in three passes, broadest first, then the same three passes to `addendum`:

1. structure — cuts, reorganisation, section sizing (anything that outgrew 1-2 pages belongs in the addendum);
2. voice and conventions — terminology, tone, compliance constraints;
3. prose mechanics — grammar, clarity, typos.

The two editorial skills this job names upstream are not built in diy yet (B4 backlink) — run the passes inline rather than waiting on them. Polish `brief` first, then `addendum`, so the user reviews one settled draft instead of a moving target.

## 3. Deliver and route

Tell the user it is ready: the local path of `{output_dir}/brief.yaml`, in the user's language. Name the next step in the chain — `diy-prd` turns the brief into requirements once it is final; `diy-help` maps the rest of the suite. External handoffs are out of diy scope: the YAML plus the viewer projection is the delivery.

## 4. Final gate (mechanical)

Write `project.status: final` first — `final` is what the gate inspects, not a product of it — then run, with the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation (`--output-dir` is mandatory and never defaulted):

```
python "{project-root}/.claude/skills/diy-product-brief/scripts/brief.py" check --final --json
```

Exit 0 is the only pass; fix every reported violation and re-run. The JSON receipt (counts included) is the close-out evidence. Rendering and close-out wait for exit 0.

## Close

Render via diy-viewer — the silent side-step command from SKILL.md (append `--instance <name>` when one was resolved); no browser interaction point, no path-waiting. Close with the route in one line and the counts from the receipt.

## Next

The create path ends here once the final gate exits 0. A later change signal → `./04-update.md`; a request for a critical read-back → `./05-validate.md`.
