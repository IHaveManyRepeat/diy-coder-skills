# Step 1 — Scan（模式与扫描）

Progress: `[Scan] → Context → Rules → Finalize` （`deep-dive` 模式下 `Scan → Deep-Dive → Finalize`）

**Read (input):** the `scan` block of `{output_dir}/project-context.yaml` when it exists (mode decision only); the engine's scan receipt.
**Write (output):** the draft record in `{output_dir}/project-context.yaml` (`project` + `scan`).

## Settle the mode

The target file decides. When `{output_dir}/project-context.yaml` is absent there is nothing to resume — this is a **full scan**.

When it exists, read only its `scan` block and lead with what was recorded (mode / level / date / parts) — that block is the continuation state; there is no `project-scan-report.json` and never will be:

```
I found project context from {scan.date} — mode {scan.mode}, level {scan.level}, {n} part(s): {parts}.

1. Rescan entire project — update every part with what changed since that date
2. Deep-dive into one area — exhaustive, file-by-file documentation of a single area
3. Cancel — keep the file as-is
```

HALT — wait for the choice. **Cancel** ends the run with zero writes and a one-line closing message. **Deep-dive** sets `mode: deep-dive`, `level: exhaustive`, then runs the scan below and continues to `./05-deep-dive.md` instead of step 2 — it edits an existing file: `project` + `scan` are the only sections it writes, every other section is copied forward untouched. **Rescan** sets `mode: rescan`. Both modes reshape a file that already exists, so before any write either of them runs:

```
cp {output_dir}/project-context.yaml {output_dir}/project-context.yaml.prev
```

Keep that `.prev` until the final gate in step 4 — it is the evidence that no `PC-###` rule was lost.

## Settle the scan level

Only for full / rescan. Offer the three levels — they change how much the engine reads, not what it records:

1. **Quick** (default) — pattern analysis: manifests, directory structure, config files. No source files are read.
2. **Deep** — adds source-file counts per part (critical directories of the detected project type).
3. **Exhaustive** — adds lines of code; reads source files, capped by built-in file and byte limits.

## Run the scan

```
python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" scan --project-root "{project-root}" --output-dir "{output_dir}" --level {quick|deep|exhaustive} --json
```

The engine is deterministic and read-only: it writes nothing. Take everything from the receipt — `repository_type`, `parts`, `stack`, `docs_found`, `tree`, `stats`, `warnings`, `counts` — and never re-derive a part, type or version by hand. A non-zero exit is a refusal: relay its one-line reason and stop with zero writes.

A `MANIFEST_UNPARSED` warning is not a failure — it is the engine declining to guess. Collect every one of them: they become questions for the human below.

## Confirm the classification

Present what was detected and ask for a verdict, the way the source workflow does:

```
I classified this project:

- repository type: {repository_type}
- {part.name} ({part.path}) — {part.type}
  stack: {stack row} / manifests: {part.manifests}

Does this look correct? [y/n/edit]
```

HALT — wait. On a correction, take the human's part list and types verbatim; on an unparsed manifest, ask what the language and framework are and record their answer. Parts and types are never invented — an unresolved one stays `unknown` until the human closes it.

## Existing documentation and focus areas

Relay `docs_found` (each with its `kind`) and ask the source workflow's question: are there further important documents or key areas to focus on? Their answer is not a new field — it lands as `structure.key_dirs` entries (path + purpose) in step 2, and as `workflow` rules in step 3 when it is a process rather than a place.

## Open the draft

Write `{output_dir}/project-context.yaml` (when absent, create it) with the machine anchors copied from the receipt — never retyped:

```yaml
project: {name: <diy-coder.yaml project.name>, created: <today>, updated: <today>}
scan:
  mode: full|rescan|deep-dive
  level: quick|deep|exhaustive
  date: YYYY-MM-DD
  parts: [{name, type, path}, ...]     # as confirmed above
stack: []          # filled in step 2
structure: {}
architecture: []
rules: []
revisions: []
```

On a rescan or a deep-dive, copy the existing sections forward first and edit in place — `revisions` records what changed. The skeleton above is the **fresh-file** shape: writing it over an existing file would drop `stack` / `structure` / `architecture` / `rules` and every human-confirmed `PC-###` with them.

## Next

Read fully and follow `./02-context.md`. In **deep-dive** mode read `./05-deep-dive.md` instead; it returns here for the finalize step.
