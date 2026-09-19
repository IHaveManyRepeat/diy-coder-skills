# Step 4 — Finalize（复核·定稿·交付）

Progress: `Scan → Context → Rules → [Finalize]`

**Read (input):** the whole `{output_dir}/project-context.yaml` — this is the one step that reads it end to end.
**Write (output):** the settled file; the rendered view; the closing summary.

## Review pass

Read the file as its consumer does — an agent that will act on it tomorrow with no memory of this conversation.

- **Completeness.** Every part in `scan.parts` has a `stack` row and an `architecture` entry; every rule has `rule` / `why` / `where`; every part the human named in step 1 appears. A section that should exist and does not is a gap to close now — the source workflow's `_(To be generated)_` marker has no counterpart here: gaps are fixed, not marked. `[假设]` values are resolved with the human and the prefix removed.
- **Efficiency.** Cut restatements, obvious advice and duplicated rules; merge rules that share a witness; keep commands and paths verbatim while the prose around them shrinks. Density is the feature.
- **Accuracy.** Every claim traces to a file, a command, or the human's own words. A stale rule (a directory that moved, a command that changed) is corrected, not kept.

Present the review with the counts, then halt before the gate if anything still needs the human.

## Rewrite check

**重扫** / **深挖** — the two modes that reshape a file which already exists — and only when step 1 made a `.prev` copy:

```
python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" check --previous {output_dir}/project-context.yaml.prev --json
```

Exit 0 means no `PC-###` rule was lost. `ID_UNSTABLE` names each dropped rule: restore it, or re-add it with a `revisions` entry explaining the removal — a silent disappearance is exactly what this gate exists to catch. Delete the `.prev` file once it passes.

## Final gate

Run, with the same arguments as activation:

```
python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" check --final --json
```

Exit 0 is the only pass — fix every reported violation and re-run. The receipt's `violations` / `warnings` / `counts` are the close-out evidence: no `[假设]` left, rules non-empty with `rule` / `why` / `where` filled, `stack` non-empty, `scan.parts` non-empty. Only after exit 0: render the file and finish the run.

## Deliver and route

Render via diy-viewer — the silent side-step command from SKILL.md (append `--instance <name>` when one was resolved); no browser interaction point, no path-waiting. Then close with the path, the mode, and the receipt's counts (`parts`, `rules`, `deep_dives`), and name the route in one line:

- a brownfield feature or PRD next → **diy-prd**, which reads this file as its brownfield input (this file is the retrieval entry point the old doc set called the master index);
- a change to the system's shape instead → **diy-architecture**;
- another area to document exhaustively → back to `./05-deep-dive.md`.

## Exit

The run ends here once the gate exits 0. A further deep dive re-enters at `./05-deep-dive.md`; otherwise no further `steps/` file is read.
