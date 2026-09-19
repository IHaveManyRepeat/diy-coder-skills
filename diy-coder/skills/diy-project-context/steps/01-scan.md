# Step 1 — Scan（模式与扫描）

Progress: `[Scan] → Context → Rules → Finalize` （`深挖` 模式下 `Scan → Deep-Dive → Finalize`）

**Read (input):** the `scan` block of `{output_dir}/project-context.yaml` when it exists (mode decision only); the engine's scan receipt.
**Write (output):** the draft record in `{output_dir}/project-context.yaml` (`project` + `scan`).

## Settle the mode

The target file decides. When `{output_dir}/project-context.yaml` is absent there is nothing to resume — this is a **全量** scan.

When it exists, read only its `scan` block and lead with what was recorded (mode / level / date / parts) — that block is the continuation state; there is no `project-scan-report.json` and never will be:

```
I found project context from {scan.date} — mode {scan.mode}, level {scan.level}, {n} part(s): {parts}.

1. **重扫** entire project — update every part with what changed since that date
2. **深挖** into one area — exhaustive, file-by-file documentation of a single area
3. Cancel — keep the file as-is
```

HALT — wait for the choice. **Cancel** ends the run with zero writes and a one-line closing message. **深挖** sets `mode: 深挖`, `level: 穷尽`, then runs the scan below and continues to `./05-deep-dive.md` instead of step 2 — it edits an existing file: `project` + `scan` are the only sections it writes, every other section is copied forward untouched. **重扫** sets `mode: 重扫`. Both modes reshape a file that already exists, so before any write either of them runs:

```
cp {output_dir}/project-context.yaml {output_dir}/project-context.yaml.prev
```

Keep that `.prev` until the final gate in step 4 — it is the evidence that no `PC-###` rule was lost.

## Settle the scan level

Only for **全量** / **重扫**. Offer the three levels — they change how much the engine reads, not what it records:

1. **快速** (default) — pattern analysis: manifests, directory structure, config files. No source files are read.
2. **深入** — adds source-file counts per part (critical directories of the detected project type).
3. **穷尽** — adds lines of code; reads source files, capped by built-in file and byte limits.

## Run the scan

```
python "{project-root}/.claude/skills/diy-project-context/scripts/context.py" scan --project-root "{project-root}" --output-dir "{output_dir}" --level {快速|深入|穷尽} --json
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

HALT — wait. On a correction, take the human's part list and types verbatim; on an unparsed manifest, ask what the language and framework are and record their answer. Parts and types are never invented — an unresolved one stays `未知` until the human closes it.

## Existing documentation and focus areas

Relay `docs_found` (each with its `kind`) and ask the source workflow's question: are there further important documents or key areas to focus on? Their answer is not a new field — it lands as `structure.key_dirs` entries (path + purpose) in step 2, and as `工作流` rules in step 3 when it is a process rather than a place.

## Open the draft

Write `{output_dir}/project-context.yaml` (when absent, create it) with the machine anchors copied from the receipt — never retyped:

```yaml
project: {name: <diy-coder.yaml project.name>, created: <today>, updated: <today>}
scan:
  mode: 全量|重扫|深挖
  level: 快速|深入|穷尽
  date: YYYY-MM-DD
  parts: [{name, type, path}, ...]     # as confirmed above
stack: []          # filled in step 2
structure: {}
architecture: []
rules: []
revisions: []
```

On a **重扫** or a **深挖**, copy the existing sections forward first and edit in place — `revisions` records what changed. The skeleton above is the **fresh-file** shape: writing it over an existing file would drop `stack` / `structure` / `architecture` / `rules` and every human-confirmed `PC-###` with them.

## Next

Read fully and follow `./02-context.md`. In **深挖** mode read `./05-deep-dive.md` instead; it returns here for the finalize step.
